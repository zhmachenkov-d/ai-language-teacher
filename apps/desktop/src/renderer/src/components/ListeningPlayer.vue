<script setup lang="ts">
/**
 * Placement listening chrome: play/pause, scrubber seek, RESTART_ZERO «Сначала».
 * Emits sticky `ended-once` (native `ended` only) and `playback-error`.
 * DESIGN listening-card.player-chrome: ink / muted / line only.
 */
import { computed, ref } from "vue";

defineProps<{
  src: string;
}>();

const emit = defineEmits<{
  "ended-once": [];
  "playback-error": [message: string];
}>();

const PLAYBACK_ERROR_MESSAGE =
  "Не удалось воспроизвести запись. Проверьте динамики/наушники и попробуйте снова.";

const audioEl = ref<HTMLAudioElement | null>(null);
const playing = ref(false);
const currentTime = ref(0);
/** null until a finite duration is known from the media element. */
const durationSec = ref<number | null>(null);
const endedOnce = ref(false);
const scrubbing = ref(false);

const durationKnown = computed(
  () => durationSec.value !== null && Number.isFinite(durationSec.value),
);

const scrubMax = computed(() =>
  durationKnown.value ? (durationSec.value as number) : 0,
);

function formatTime(sec: number): string {
  const total = Math.max(0, Math.floor(sec));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

const elapsedLabel = computed(() => formatTime(currentTime.value));

const totalLabel = computed(() =>
  durationKnown.value ? formatTime(durationSec.value as number) : "—",
);

const timeDisplay = computed(() => `${elapsedLabel.value} / ${totalLabel.value}`);

const playAriaLabel = computed(() => (playing.value ? "Пауза" : "Слушать"));

const playButtonText = computed(() => (playing.value ? "Пауза" : "Слушать"));

function readDuration(): void {
  const el = audioEl.value;
  if (!el) {
    return;
  }
  const d = el.duration;
  if (Number.isFinite(d)) {
    durationSec.value = d;
  }
}

function onLoadedMetadata(): void {
  readDuration();
}

function onDurationChange(): void {
  readDuration();
}

function onTimeUpdate(): void {
  if (scrubbing.value) {
    return;
  }
  const el = audioEl.value;
  if (!el) {
    return;
  }
  currentTime.value = el.currentTime;
}

function onPlay(): void {
  playing.value = true;
}

function onPause(): void {
  playing.value = false;
}

function onEnded(): void {
  playing.value = false;
  const el = audioEl.value;
  if (el && Number.isFinite(el.duration)) {
    currentTime.value = el.duration;
  }
  if (!endedOnce.value) {
    endedOnce.value = true;
    emit("ended-once");
  }
}

function emitPlaybackError(): void {
  if (!audioEl.value) {
    return;
  }
  emit("playback-error", PLAYBACK_ERROR_MESSAGE);
}

function tryPlay(el: HTMLAudioElement): void {
  // Clear any stale parent banner before a new attempt (empty payload).
  emit("playback-error", "");
  try {
    const playResult = el.play();
    if (playResult && typeof playResult.then === "function") {
      playResult.catch(() => {
        emitPlaybackError();
      });
    }
  } catch {
    emitPlaybackError();
  }
}

function onMediaError(): void {
  emitPlaybackError();
}

function onPlayPause(): void {
  const el = audioEl.value;
  if (!el) {
    return;
  }
  if (el.paused) {
    tryPlay(el);
  } else {
    el.pause();
  }
}

function clampTime(value: number): number {
  const max = durationKnown.value ? (durationSec.value as number) : 0;
  return Math.min(Math.max(0, value), max);
}

function onScrubInput(event: Event): void {
  const el = audioEl.value;
  if (!el || !durationKnown.value) {
    return;
  }
  const raw = Number((event.target as HTMLInputElement).value);
  if (!Number.isFinite(raw)) {
    return;
  }
  const next = clampTime(raw);
  scrubbing.value = true;
  el.currentTime = next;
  currentTime.value = next;
}

function onScrubEnd(): void {
  scrubbing.value = false;
}

function onRestart(): void {
  const el = audioEl.value;
  if (!el) {
    return;
  }
  el.currentTime = 0;
  currentTime.value = 0;
  tryPlay(el);
}
</script>

<template>
  <div class="listening-player" data-testid="listening-player">
    <audio
      ref="audioEl"
      :src="src"
      preload="metadata"
      data-testid="listening-audio"
      @loadedmetadata="onLoadedMetadata"
      @durationchange="onDurationChange"
      @timeupdate="onTimeUpdate"
      @play="onPlay"
      @pause="onPause"
      @ended="onEnded"
      @error="onMediaError"
    />
    <div class="chrome">
      <button
        type="button"
        class="chrome-btn"
        data-testid="listening-play"
        :aria-label="playAriaLabel"
        @click="onPlayPause"
      >
        {{ playButtonText }}
      </button>
      <div class="scrub-row">
        <input
          class="scrub"
          type="range"
          data-testid="listening-scrub"
          :min="0"
          :max="scrubMax"
          :step="0.05"
          :value="currentTime"
          :disabled="!durationKnown"
          :aria-valuemin="0"
          :aria-valuemax="scrubMax"
          :aria-valuenow="currentTime"
          aria-label="Позиция воспроизведения"
          @input="onScrubInput"
          @change="onScrubEnd"
          @pointerup="onScrubEnd"
          @mouseup="onScrubEnd"
          @touchend="onScrubEnd"
        />
        <span class="times" data-testid="listening-times" aria-hidden="true">{{
          timeDisplay
        }}</span>
      </div>
      <button
        type="button"
        class="chrome-btn"
        data-testid="listening-replay"
        aria-label="Сначала"
        @click="onRestart"
      >
        Сначала
      </button>
    </div>
  </div>
</template>

<style scoped>
.listening-player {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chrome {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.chrome-btn {
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  padding: 7px 14px;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-ink);
  background: var(--color-surface);
  border: 1px solid var(--color-line);
}

.chrome-btn:focus-visible {
  outline: 2px solid var(--color-ink);
  outline-offset: 2px;
}

.scrub-row {
  flex: 1 1 160px;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.scrub {
  flex: 1;
  min-width: 80px;
  accent-color: var(--color-ink);
  cursor: pointer;
}

.scrub:disabled {
  cursor: not-allowed;
  opacity: 0.5;
}

.scrub:focus-visible {
  outline: 2px solid var(--color-ink);
  outline-offset: 2px;
}

.times {
  flex-shrink: 0;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  color: var(--color-muted);
  min-width: 5.5em;
  text-align: right;
}

@media (prefers-reduced-motion: reduce) {
  .scrub,
  .chrome-btn {
    transition: none;
  }
}
</style>
