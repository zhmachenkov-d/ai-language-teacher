<script setup lang="ts">
/**
 * Real multi-stage placement (Story 2.3): briefing → written (timer) →
 * listening (TTS play/pause → comprehension) → speaking (local mic → STT).
 * One LLM-generated item set per run; server enforces listening+speaking
 * before `placement_complete` — this view only renders/gates the UI side.
 */
import { computed, onMounted, onUnmounted, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import {
  fetchLearner,
  generatePlacementItems,
  getTeacherAuth,
  patchLearner,
  synthesizeListeningAudio,
  transcribeSpeakingAudio,
  TeacherApiError,
  type LearnerProfile,
  type PlacementItemsPublic,
  type TeacherAuth,
} from "../services/teacherClient";

const WRITTEN_TIME_LIMIT_SEC = 300;

interface ApiErrorInfo {
  code: string;
  message: string;
}

const router = useRouter();

const loading = ref(true);
const loadError = ref<string | null>(null);

const auth = ref<TeacherAuth>({ state: "starting", base_url: "", bearer: null });
const learner = ref<LearnerProfile | null>(null);
const items = ref<PlacementItemsPublic | null>(null);

const stage = computed(() => learner.value?.placement_stage ?? "briefing");

// briefing → written (item generation)
const generating = ref(false);
const generateError = ref<ApiErrorInfo | null>(null);

// written
const writtenAnswers = ref<number[]>([]);
const writtenTimeLeftSec = ref(WRITTEN_TIME_LIMIT_SEC);
const savingWritten = ref(false);
const writtenSaveError = ref<string | null>(null);
let writtenTimerHandle: ReturnType<typeof setInterval> | null = null;

// listening
const listeningAudioUrl = ref<string | null>(null);
const listeningAudioLoading = ref(false);
const listeningAudioError = ref<ApiErrorInfo | null>(null);
const listeningPlayedLocal = ref(false);
const listeningPlaybackError = ref<string | null>(null);
const listeningAnswers = ref<number[]>([]);
const savingListening = ref(false);
const listeningSaveError = ref<string | null>(null);
const audioEl = ref<HTMLAudioElement | null>(null);

// speaking
const recording = ref(false);
const micError = ref<string | null>(null);
const transcribing = ref(false);
const speakingSaveError = ref<ApiErrorInfo | null>(null);
let mediaRecorder: MediaRecorder | null = null;
let mediaChunks: Blob[] = [];
let mediaStream: MediaStream | null = null;
let acquiringMic = false;
let lastRecordingBase64: string | null = null;
let lastRecordingMimeType = "audio/webm";

// complete
const completing = ref(false);
const completeError = ref<string | null>(null);

const writtenTimeLabel = computed(() => {
  const sec = Math.max(0, writtenTimeLeftSec.value);
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
});

const generateErrorMessage = computed(() => {
  const err = generateError.value;
  if (!err) {
    return "";
  }
  if (err.code === "llm_config_missing") {
    return "Настройте ключ ИИ в Настройках, чтобы начать проверку уровня.";
  }
  if (err.code === "llm_generation_failed") {
    return "ИИ не смог подготовить задания. Попробуйте ещё раз.";
  }
  return err.message;
});

function apiErrorInfo(err: unknown, fallbackMessage: string): ApiErrorInfo {
  if (err instanceof TeacherApiError) {
    return { code: err.code, message: err.message };
  }
  return { code: "unknown", message: fallbackMessage };
}

function stopWrittenTimer(): void {
  if (writtenTimerHandle !== null) {
    clearInterval(writtenTimerHandle);
    writtenTimerHandle = null;
  }
}

function startWrittenTimer(): void {
  stopWrittenTimer();
  writtenTimeLeftSec.value = WRITTEN_TIME_LIMIT_SEC;
  writtenTimerHandle = setInterval(() => {
    writtenTimeLeftSec.value -= 1;
    if (writtenTimeLeftSec.value <= 0) {
      stopWrittenTimer();
      void onWrittenSubmit();
    }
  }, 1000);
}

/** Reuse persisted answers on resume when their length still matches the item
 * set; otherwise start blank (-1 = unanswered). */
function restoreAnswers(persisted: readonly number[], expectedLength: number): number[] {
  if (persisted.length === expectedLength) {
    return [...persisted];
  }
  return Array.from({ length: expectedLength }, () => -1);
}

function hydrateItems(profile: LearnerProfile): void {
  items.value = profile.placement_items;
  if (items.value) {
    writtenAnswers.value = restoreAnswers(
      profile.placement_written_answers,
      items.value.written.length,
    );
    listeningAnswers.value = restoreAnswers(
      profile.placement_listening_answers,
      items.value.listening.questions.length,
    );
  }
}

async function ensureItemsGenerated(): Promise<boolean> {
  generateError.value = null;
  generating.value = true;
  try {
    const publicItems = await generatePlacementItems(auth.value);
    items.value = publicItems;
    writtenAnswers.value = publicItems.written.map(() => -1);
    listeningAnswers.value = publicItems.listening.questions.map(() => -1);
    return true;
  } catch (err) {
    generateError.value = apiErrorInfo(err, "Не удалось получить задания от ИИ");
    return false;
  } finally {
    generating.value = false;
  }
}

async function ensureListeningAudio(): Promise<void> {
  if (listeningAudioUrl.value || listeningAudioLoading.value) {
    return;
  }
  listeningAudioLoading.value = true;
  listeningAudioError.value = null;
  try {
    const audio = await synthesizeListeningAudio(auth.value);
    const binary = atob(audio.audio_base64);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    const blob = new Blob([bytes], { type: audio.mime_type });
    listeningAudioUrl.value = URL.createObjectURL(blob);
  } catch (err) {
    listeningAudioError.value = apiErrorInfo(err, "Не удалось получить аудио");
  } finally {
    listeningAudioLoading.value = false;
  }
}

async function load(): Promise<void> {
  loading.value = true;
  loadError.value = null;
  try {
    auth.value = await getTeacherAuth();
    if (auth.value.state !== "running" || !auth.value.bearer) {
      loadError.value = auth.value.message ?? "Учитель не запущен";
      return;
    }
    const profile = await fetchLearner(auth.value);
    if (profile.placement_complete) {
      await router.replace({ name: "onboarding-plan" });
      return;
    }
    if (!profile.consent_complete) {
      await router.replace({ name: "onboarding-consent" });
      return;
    }
    learner.value = profile;
    hydrateItems(profile);

    if (profile.placement_stage !== "briefing" && !items.value) {
      // Resume edge case: stage advanced but the item set is missing — regenerate.
      await ensureItemsGenerated();
    }
    if (profile.placement_stage === "written") {
      startWrittenTimer();
    }
    if (profile.placement_stage === "listening" && items.value) {
      await ensureListeningAudio();
    }
  } catch (err) {
    loadError.value =
      err instanceof TeacherApiError ? err.message : "Не удалось загрузить профиль";
  } finally {
    loading.value = false;
  }
}

async function onBriefingNext(): Promise<void> {
  if (generating.value) {
    return;
  }
  const ok = await ensureItemsGenerated();
  if (!ok) {
    return;
  }
  try {
    const updated = await patchLearner(auth.value, { placement_stage: "written" });
    learner.value = updated;
    startWrittenTimer();
  } catch (err) {
    generateError.value = apiErrorInfo(err, "Не удалось начать письменную часть");
  }
}

function setWrittenAnswer(index: number, optionIndex: number): void {
  const next = [...writtenAnswers.value];
  next[index] = optionIndex;
  writtenAnswers.value = next;
}

async function onWrittenSubmit(): Promise<void> {
  if (savingWritten.value) {
    return;
  }
  stopWrittenTimer();
  savingWritten.value = true;
  writtenSaveError.value = null;
  try {
    const updated = await patchLearner(auth.value, {
      placement_written_answers: writtenAnswers.value,
      placement_stage: "listening",
    });
    learner.value = updated;
    await ensureListeningAudio();
  } catch (err) {
    writtenSaveError.value =
      err instanceof TeacherApiError ? err.message : "Не удалось сохранить ответы";
  } finally {
    savingWritten.value = false;
  }
}

function setListeningAnswer(index: number, optionIndex: number): void {
  const next = [...listeningAnswers.value];
  next[index] = optionIndex;
  listeningAnswers.value = next;
}

const LISTENING_PLAYBACK_ERROR_MESSAGE =
  "Не удалось воспроизвести запись. Проверьте динамики/наушники и попробуйте снова.";

function onPlayPause(): void {
  const el = audioEl.value;
  if (!el) {
    return;
  }
  listeningPlaybackError.value = null;
  try {
    if (el.paused) {
      const playResult = el.play();
      if (playResult && typeof playResult.then === "function") {
        playResult.catch(() => {
          listeningPlaybackError.value = LISTENING_PLAYBACK_ERROR_MESSAGE;
        });
      }
    } else {
      el.pause();
    }
  } catch {
    // Some headless/test environments throw synchronously.
    listeningPlaybackError.value = LISTENING_PLAYBACK_ERROR_MESSAGE;
  }
}

function onAudioEnded(): void {
  listeningPlayedLocal.value = true;
}

async function onListeningSubmit(): Promise<void> {
  if (savingListening.value) {
    return;
  }
  listeningSaveError.value = null;
  if (!listeningPlayedLocal.value) {
    listeningSaveError.value = "Сначала прослушайте запись до конца";
    return;
  }
  savingListening.value = true;
  try {
    const updated = await patchLearner(auth.value, {
      placement_listening_played: true,
      placement_listening_answers: listeningAnswers.value,
      placement_stage: "speaking",
    });
    learner.value = updated;
  } catch (err) {
    listeningSaveError.value =
      err instanceof TeacherApiError ? err.message : "Не удалось сохранить ответы";
  } finally {
    savingListening.value = false;
  }
}

function micAvailable(): boolean {
  return (
    typeof navigator !== "undefined" &&
    typeof navigator.mediaDevices?.getUserMedia === "function" &&
    typeof window.MediaRecorder !== "undefined"
  );
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      const result = String(reader.result ?? "");
      resolve(result.split(",")[1] ?? "");
    };
    reader.onerror = () => reject(reader.error ?? new Error("read failed"));
    reader.readAsDataURL(blob);
  });
}

async function attemptTranscribe(base64: string, mimeType: string): Promise<void> {
  transcribing.value = true;
  speakingSaveError.value = null;
  try {
    const updated = await transcribeSpeakingAudio(auth.value, {
      audio_base64: base64,
      mime_type: mimeType,
    });
    learner.value = updated;
  } catch (err) {
    speakingSaveError.value = apiErrorInfo(err, "Не удалось распознать речь");
  } finally {
    transcribing.value = false;
  }
}

async function onRecordingStopped(): Promise<void> {
  const mimeType = mediaRecorder?.mimeType || "audio/webm";
  const blob = new Blob(mediaChunks, { type: mimeType });
  mediaChunks = [];
  const base64 = await blobToBase64(blob);
  lastRecordingBase64 = base64;
  lastRecordingMimeType = mimeType;
  await attemptTranscribe(base64, mimeType);
}

async function onRetryTranscribe(): Promise<void> {
  if (!lastRecordingBase64 || transcribing.value) {
    return;
  }
  await attemptTranscribe(lastRecordingBase64, lastRecordingMimeType);
}

async function onRecordToggle(): Promise<void> {
  if (!micAvailable()) {
    micError.value =
      "Микрофон недоступен. Проверьте разрешения приложения или устройство ввода в Настройках.";
    return;
  }
  micError.value = null;
  if (recording.value) {
    recording.value = false;
    mediaRecorder?.stop();
    mediaStream?.getTracks().forEach((track) => track.stop());
    return;
  }
  // A second click while getUserMedia is still pending must not open a duplicate stream.
  if (acquiringMic) {
    return;
  }
  acquiringMic = true;
  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaChunks = [];
    mediaRecorder = new MediaRecorder(mediaStream);
    mediaRecorder.ondataavailable = (event: BlobEvent) => {
      if (event.data.size > 0) {
        mediaChunks.push(event.data);
      }
    };
    mediaRecorder.onstop = () => {
      void onRecordingStopped();
    };
    mediaRecorder.start();
    recording.value = true;
  } catch {
    // MediaRecorder construction/start can throw after getUserMedia already
    // opened the mic — always release the track rather than leaving it open.
    mediaStream?.getTracks().forEach((track) => track.stop());
    mediaStream = null;
    mediaRecorder = null;
    micError.value = "Не удалось получить доступ к микрофону. Проверьте разрешения.";
  } finally {
    acquiringMic = false;
  }
}

async function onFinish(): Promise<void> {
  if (completing.value) {
    return;
  }
  completing.value = true;
  completeError.value = null;
  try {
    const updated = await patchLearner(auth.value, {
      placement_stage: "complete",
      placement_complete: true,
    });
    learner.value = updated;
    await router.replace({ name: "onboarding-plan" });
  } catch (err) {
    completeError.value =
      err instanceof TeacherApiError
        ? err.message
        : "Не удалось завершить проверку уровня";
  } finally {
    completing.value = false;
  }
}

onMounted(() => {
  void load();
});

onUnmounted(() => {
  stopWrittenTimer();
  if (listeningAudioUrl.value) {
    URL.revokeObjectURL(listeningAudioUrl.value);
  }
  mediaStream?.getTracks().forEach((track) => track.stop());
});
</script>

<template>
  <main class="placement" data-testid="onboarding-placement">
    <div v-if="loading" class="status" data-testid="placement-loading">Загрузка…</div>
    <div v-else-if="loadError" class="status error-block" role="alert">
      <p>{{ loadError }}</p>
      <button type="button" class="cta" @click="load">Повторить</button>
    </div>

    <template v-else-if="stage === 'briefing'">
      <section class="surface" data-testid="placement-briefing">
        <span class="accent-rule" aria-hidden="true" />
        <h1>Проверка уровня</h1>
        <p class="body">
          Сейчас пройдём три части: письменные задания, слушание с
          вопросами на понимание и говорение с распознаванием речи.
        </p>
        <ul class="brief-list">
          <li>Письменная часть — 5 заданий, лимит 5 минут.</li>
          <li>Слушание — короткая запись и 3 вопроса на понимание.</li>
          <li>Говорение — говорите в микрофон, речь распознаётся локально.</li>
          <li>Результат учитывается при составлении учебного плана.</li>
        </ul>
      </section>
      <p
        v-if="generateError"
        class="error error-block"
        role="alert"
        data-testid="generate-error"
      >
        {{ generateErrorMessage }}
        <RouterLink
          v-if="generateError.code === 'llm_config_missing'"
          class="settings-link"
          :to="{ name: 'settings' }"
        >
          Открыть Настройки
        </RouterLink>
      </p>
      <button
        type="button"
        class="cta"
        data-testid="briefing-next"
        :disabled="generating"
        @click="onBriefingNext"
      >
        {{ generating ? "Готовим задания…" : "Далее" }}
      </button>
    </template>

    <template v-else-if="stage === 'written' && items">
      <section class="surface" data-testid="placement-written">
        <span class="accent-rule" aria-hidden="true" />
        <p class="timer" data-testid="written-timer">Осталось: {{ writtenTimeLabel }}</p>
        <ol class="item-list">
          <li v-for="(item, index) in items.written" :key="index" class="item">
            <p class="prompt">{{ item.prompt }}</p>
            <div class="options" role="radiogroup" :aria-label="item.prompt">
              <button
                v-for="(option, optionIndex) in item.options"
                :key="optionIndex"
                type="button"
                class="chip"
                :class="{ selected: writtenAnswers[index] === optionIndex }"
                role="radio"
                :aria-checked="writtenAnswers[index] === optionIndex"
                @click="setWrittenAnswer(index, optionIndex)"
              >
                {{ option }}
              </button>
            </div>
          </li>
        </ol>
      </section>
      <p v-if="writtenSaveError" class="error" role="alert" data-testid="written-save-error">
        {{ writtenSaveError }}
      </p>
      <button
        type="button"
        class="cta"
        data-testid="written-submit"
        :disabled="savingWritten"
        @click="onWrittenSubmit"
      >
        Далее
      </button>
    </template>

    <template v-else-if="stage === 'listening' && items">
      <section class="surface" data-testid="placement-listening">
        <span class="accent-rule" aria-hidden="true" />
        <p class="hint">Прослушайте запись, затем ответьте на вопросы.</p>

        <div v-if="listeningAudioLoading" class="status" data-testid="listening-audio-loading">
          Готовим аудио…
        </div>
        <div
          v-else-if="listeningAudioError"
          class="error-block"
          role="alert"
          data-testid="listening-audio-error"
        >
          <p>Не удалось получить аудио. Повторите попытку или проверьте Настройки → Голос.</p>
          <div class="actions">
            <button type="button" class="secondary" @click="ensureListeningAudio">
              Повторить
            </button>
            <RouterLink class="settings-link" :to="{ name: 'settings' }">
              Открыть Настройки
            </RouterLink>
          </div>
        </div>
        <template v-else-if="listeningAudioUrl">
          <audio
            ref="audioEl"
            :src="listeningAudioUrl"
            data-testid="listening-audio"
            @ended="onAudioEnded"
          />
          <button
            type="button"
            class="secondary"
            data-testid="listening-play"
            @click="onPlayPause"
          >
            Слушать / Пауза
          </button>
          <p
            v-if="listeningPlaybackError"
            class="error"
            role="alert"
            data-testid="listening-playback-error"
          >
            {{ listeningPlaybackError }}
          </p>
          <p v-if="!listeningPlayedLocal" class="hint">Дослушайте запись до конца.</p>
        </template>

        <ol class="item-list">
          <li
            v-for="(question, index) in items.listening.questions"
            :key="index"
            class="item"
          >
            <p class="prompt">{{ question.prompt }}</p>
            <div class="options" role="radiogroup" :aria-label="question.prompt">
              <button
                v-for="(option, optionIndex) in question.options"
                :key="optionIndex"
                type="button"
                class="chip"
                :class="{ selected: listeningAnswers[index] === optionIndex }"
                role="radio"
                :aria-checked="listeningAnswers[index] === optionIndex"
                @click="setListeningAnswer(index, optionIndex)"
              >
                {{ option }}
              </button>
            </div>
          </li>
        </ol>
      </section>
      <p
        v-if="listeningSaveError"
        class="error"
        role="alert"
        data-testid="listening-save-error"
      >
        {{ listeningSaveError }}
      </p>
      <button
        type="button"
        class="cta"
        data-testid="listening-submit"
        :disabled="savingListening"
        @click="onListeningSubmit"
      >
        Далее
      </button>
    </template>

    <template v-else-if="stage === 'speaking' && items">
      <section class="surface" data-testid="placement-speaking">
        <span class="accent-rule" aria-hidden="true" />
        <p class="hint">Ответьте вслух на все вопросы одной записью.</p>
        <ul class="brief-list">
          <li v-for="(prompt, index) in items.speaking_prompts" :key="index">
            {{ prompt }}
          </li>
        </ul>
        <button
          type="button"
          class="secondary"
          data-testid="speaking-record"
          :disabled="transcribing"
          @click="onRecordToggle"
        >
          {{ recording ? "Остановить запись" : "Начать запись" }}
        </button>
        <p v-if="transcribing" class="hint" data-testid="speaking-transcribing">
          Распознаём речь…
        </p>
        <p v-if="micError" class="error" role="alert" data-testid="mic-error">
          {{ micError }}
        </p>
        <p
          v-if="learner?.placement_speaking_transcript"
          class="hint"
          data-testid="speaking-transcript"
        >
          Распознано: «{{ learner.placement_speaking_transcript }}»
        </p>
      </section>
      <div
        v-if="speakingSaveError"
        class="error-block"
        role="alert"
        data-testid="speaking-save-error"
      >
        <p>{{ speakingSaveError.message }}</p>
        <div class="actions">
          <button type="button" class="secondary" @click="onRetryTranscribe">
            Повторить
          </button>
          <RouterLink
            v-if="speakingSaveError.code === 'voice_unavailable'"
            class="settings-link"
            :to="{ name: 'settings' }"
          >
            Открыть Настройки
          </RouterLink>
        </div>
      </div>
      <p v-if="completeError" class="error" role="alert" data-testid="complete-error">
        {{ completeError }}
      </p>
      <button
        type="button"
        class="cta"
        data-testid="speaking-finish"
        :disabled="!learner?.placement_speaking_transcript || completing"
        @click="onFinish"
      >
        Завершить проверку уровня
      </button>
    </template>

    <!-- Stage says complete but the complete flag never landed (e.g. a stage-only
    PATCH raced ahead of placement_complete) — still show the finish CTA so the
    learner is never stuck with no way forward. -->
    <template v-else-if="stage === 'complete' && !learner?.placement_complete">
      <section class="surface" data-testid="placement-finish-pending">
        <span class="accent-rule" aria-hidden="true" />
        <p class="hint">Осталось подтвердить завершение проверки уровня.</p>
        <p
          v-if="learner?.placement_speaking_transcript"
          class="hint"
          data-testid="speaking-transcript"
        >
          Распознано: «{{ learner.placement_speaking_transcript }}»
        </p>
      </section>
      <p v-if="completeError" class="error" role="alert" data-testid="complete-error">
        {{ completeError }}
      </p>
      <button
        type="button"
        class="cta"
        data-testid="speaking-finish"
        :disabled="!learner?.placement_speaking_transcript || completing"
        @click="onFinish"
      >
        Завершить проверку уровня
      </button>
    </template>

    <!-- Non-briefing stage with no item set (generation failed / regenerate
    still pending) — offer a real retry instead of a false "complete" screen. -->
    <template v-else-if="!items">
      <section class="surface error-block" data-testid="placement-items-missing" role="alert">
        <span class="accent-rule" aria-hidden="true" />
        <p class="hint">Не удалось получить задания для проверки уровня.</p>
        <p v-if="generateError">{{ generateErrorMessage }}</p>
        <div class="actions">
          <button
            type="button"
            class="cta"
            data-testid="items-missing-retry"
            :disabled="generating"
            @click="ensureItemsGenerated"
          >
            {{ generating ? "Готовим задания…" : "Повторить" }}
          </button>
          <RouterLink
            v-if="generateError?.code === 'llm_config_missing'"
            class="settings-link"
            :to="{ name: 'settings' }"
          >
            Открыть Настройки
          </RouterLink>
        </div>
      </section>
    </template>

    <template v-else>
      <section class="surface" data-testid="placement-complete">
        <span class="accent-rule" aria-hidden="true" />
        <p class="hint">Проверка уровня завершена.</p>
      </section>
    </template>
  </main>
</template>

<style scoped>
.placement {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 560px;
  margin: 0 auto;
  padding: 28px 20px 48px;
  background: var(--color-bg);
  color: var(--color-ink);
  min-height: 0;
  width: 100%;
  box-sizing: border-box;
}

.status {
  padding: 20px 0;
  color: var(--color-muted);
}

.error-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
  color: var(--color-ink);
}

.surface {
  padding: 16px 18px 18px;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.accent-rule {
  display: block;
  width: 24px;
  height: 3px;
  background: var(--color-coral);
  border-radius: 2px;
}

h1 {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 600;
}

.body {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
}

.hint {
  margin: 0;
  font-size: 13px;
  line-height: 1.45;
  color: var(--color-muted);
}

.timer {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-ink);
}

.brief-list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--color-muted);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.prompt {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
}

.options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  font: inherit;
  font-size: 13px;
  padding: 6px 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--color-line);
  background: var(--color-bg);
  color: var(--color-ink);
  cursor: pointer;
}

.chip.selected {
  border-color: var(--color-coral);
  background: var(--color-coral-soft);
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.settings-link {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-coral);
}

.error,
.error-block {
  margin: 0;
  font-size: 12px;
  color: var(--color-missed);
}

.cta,
.secondary {
  align-self: flex-start;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  padding: 7px 16px;
  border-radius: var(--radius-md);
  cursor: pointer;
}

.cta {
  color: var(--color-on-coral);
  background: var(--color-coral-cta);
  border: 1px solid var(--color-coral-cta);
}

.cta:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.secondary {
  color: var(--color-ink);
  background: var(--color-surface);
  border: 1px solid var(--color-line);
}

.secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cta:focus-visible,
.secondary:focus-visible {
  outline: 2px solid var(--color-coral);
  outline-offset: -2px;
}
</style>
