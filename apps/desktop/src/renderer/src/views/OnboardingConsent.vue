<script setup lang="ts">
/**
 * Consent + regulated copy (Story 2.2). Age comes from greeting only —
 * under-16 / missing age hard-blocks with quit IPC; otherwise mic/AI/Privacy
 * required, Telegram optional; successful PATCH → placement stub.
 */
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  fetchLearner,
  getTeacherAuth,
  patchLearner,
  TeacherApiError,
  type LearnerProfile,
  type TeacherAuth,
} from "../services/teacherClient";

const MIN_AGE = 16;

const router = useRouter();

const loading = ref(true);
const saving = ref(false);
const loadError = ref<string | null>(null);
const saveError = ref<string | null>(null);
const validationError = ref<string | null>(null);
const quitError = ref<string | null>(null);

const auth = ref<TeacherAuth>({
  state: "starting",
  base_url: "",
  bearer: null,
});
const learner = ref<LearnerProfile | null>(null);

const consentMic = ref(false);
const consentTelegram = ref(false);
const consentAi = ref(false);
const consentPrivacy = ref(false);

/** Bumps on each load() so stale errors cannot overwrite a newer hydrate. */
let loadGeneration = 0;

const ageRestricted = computed(() => {
  const age = learner.value?.age;
  return age == null || !Number.isInteger(age) || age < MIN_AGE;
});

function hydrate(profile: LearnerProfile): void {
  learner.value = profile;
  consentMic.value = profile.consent_mic;
  consentTelegram.value = profile.consent_telegram;
  consentAi.value = profile.consent_ai;
  consentPrivacy.value = profile.consent_privacy;
}

async function load(): Promise<void> {
  const generation = ++loadGeneration;
  loading.value = true;
  loadError.value = null;
  try {
    auth.value = await getTeacherAuth();
    if (auth.value.state !== "running" || !auth.value.bearer) {
      if (generation !== loadGeneration) return;
      loadError.value = "Учитель не запущен. Повторите попытку.";
      return;
    }
    const profile = await fetchLearner(auth.value);
    if (generation !== loadGeneration) return;
    hydrate(profile);
    if (profile.consent_complete) {
      await router.replace({ name: "onboarding-placement" });
    }
  } catch (err) {
    if (generation !== loadGeneration) return;
    if (err instanceof TeacherApiError) {
      loadError.value = err.message;
    } else {
      loadError.value = "Не удалось загрузить профиль";
    }
  } finally {
    if (generation === loadGeneration) {
      loading.value = false;
    }
  }
}

function validateRequired(): string | null {
  if (!consentMic.value || !consentAi.value || !consentPrivacy.value) {
    return "Отметьте обязательные пункты: микрофон, ИИ и конфиденциальность";
  }
  return null;
}

async function onNext(): Promise<void> {
  if (saving.value) return;
  validationError.value = null;
  saveError.value = null;
  const block = validateRequired();
  if (block) {
    validationError.value = block;
    return;
  }
  saving.value = true;
  try {
    const updated = await patchLearner(auth.value, {
      consent_mic: consentMic.value,
      consent_telegram: consentTelegram.value,
      consent_ai: consentAi.value,
      consent_privacy: consentPrivacy.value,
      consent_complete: true,
    });
    learner.value = updated;
    await router.replace({ name: "onboarding-placement" });
  } catch (err) {
    if (err instanceof TeacherApiError) {
      saveError.value = err.message;
    } else {
      saveError.value = "Не удалось сохранить согласие";
    }
  } finally {
    saving.value = false;
  }
}

function onQuit(): void {
  quitError.value = null;
  const quit = window.desktop?.quit;
  if (typeof quit !== "function") {
    quitError.value =
      "Не удалось закрыть приложение. Выйдите через меню трея «Выход».";
    return;
  }
  void quit();
}

onMounted(() => {
  void load();
});
</script>

<template>
  <main class="consent" data-testid="onboarding-consent">
    <div v-if="loading" class="status" data-testid="consent-loading">Загрузка…</div>
    <div v-else-if="loadError" class="status error-block" role="alert">
      <p>{{ loadError }}</p>
      <button type="button" class="cta" @click="load">Повторить</button>
    </div>
    <template v-else-if="ageRestricted">
      <header class="header">
        <h1>Доступ ограничен</h1>
      </header>
      <section class="surface" data-testid="age-hard-block">
        <span class="accent-rule" aria-hidden="true" />
        <p class="body">
          Приложение доступно только с 16 лет. По вашим данным продолжение
          онбординга невозможно — отдельного режима для младшего возраста нет.
        </p>
        <p class="hint">
          Возраст был указан на шаге знакомства и здесь не запрашивается снова.
        </p>
      </section>
      <button
        type="button"
        class="cta"
        data-testid="quit-button"
        @click="onQuit"
      >
        Закрыть приложение
      </button>
      <p
        v-if="quitError"
        class="error"
        role="alert"
        data-testid="quit-error"
      >
        {{ quitError }}
      </p>
    </template>
    <template v-else>
      <header class="header">
        <h1>Согласие</h1>
      </header>
      <section class="surface" data-testid="consent-form">
        <span class="accent-rule" aria-hidden="true" />
        <p class="hint">
          Перед проверкой уровня подтвердите условия. Возраст уже сохранён и
          здесь не спрашивается.
        </p>

        <label class="check" data-testid="consent-mic">
          <input v-model="consentMic" type="checkbox" />
          <span>
            <strong>Микрофон и голос.</strong>
            Разрешаю запись голоса на уроках и сохранение аудио для повторного
            прослушивания (replay) в истории урока. Без этого нельзя пройти
            говорение и слушание.
          </span>
        </label>

        <label class="check" data-testid="consent-telegram">
          <input v-model="consentTelegram" type="checkbox" />
          <span>
            <strong>Telegram (необязательно).</strong>
            Согласен(-на) на привязку Telegram для микро-уроков и напоминаний.
            Можно отказаться сейчас и согласиться позже в Настройках → «Привязать».
          </span>
        </label>

        <label class="check" data-testid="consent-ai">
          <input v-model="consentAi" type="checkbox" />
          <span>
            <strong>Об ИИ-учителе.</strong>
            Понимаю: это не сертифицированный преподаватель и не гарантия сдачи
            экзамена. Сертификаты, официальный уровень и «проход» экзамена
            приложение не выдаёт и не обещает.
          </span>
        </label>

        <label class="check" data-testid="consent-privacy">
          <input v-model="consentPrivacy" type="checkbox" />
          <span>
            <strong>Конфиденциальность.</strong>
            В запросы к ИИ не передаются фамилия, почтовый адрес, email и
            телефон. Не указывайте эти данные в ответах и свободном тексте.
          </span>
        </label>
      </section>

      <p
        v-if="validationError"
        class="error"
        role="alert"
        data-testid="validation-error"
      >
        {{ validationError }}
      </p>
      <p v-if="saveError" class="error" role="alert" data-testid="save-error">
        {{ saveError }}
      </p>

      <button
        type="button"
        class="cta"
        data-testid="next-button"
        :disabled="saving"
        @click="onNext"
      >
        Далее
      </button>
    </template>
  </main>
</template>

<style scoped>
.consent {
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

.header h1 {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 600;
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
  padding: 20px 22px 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.accent-rule {
  display: block;
  width: 24px;
  height: 3px;
  background: var(--color-coral);
  border-radius: 2px;
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

.check {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  font-size: 13px;
  line-height: 1.45;
  cursor: pointer;
}

.check input {
  margin-top: 3px;
  flex-shrink: 0;
}

.check strong {
  font-weight: 600;
}

.error {
  margin: 0;
  font-size: 13px;
  color: var(--color-danger, #b33);
}

.cta {
  align-self: flex-start;
  padding: 10px 18px;
  border-radius: var(--radius-md);
  background: var(--color-coral-cta);
  border: 1px solid var(--color-coral-cta);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.cta:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.cta:focus-visible {
  outline: 2px solid var(--color-coral);
  outline-offset: 2px;
}
</style>
