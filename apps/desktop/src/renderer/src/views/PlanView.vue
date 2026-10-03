<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import { gateDestination, isOnboardingRoute } from "../onboarding/gate";
import {
  fetchLearner,
  fetchLivingPlan,
  getTeacherAuth,
  retryTeacher,
  TeacherApiError,
  type LivingPlanProjection,
  type TeacherAuth,
} from "../services/teacherClient";

const SOFT_EMPTY = "Пока пусто";
const LOAD_FALLBACK = "Не удалось загрузить план";

const router = useRouter();

const auth = ref<TeacherAuth>({
  state: "starting",
  base_url: "",
  bearer: null,
});
const loading = ref(true);
const loadError = ref<string | null>(null);
const notFound = ref(false);
const plan = ref<LivingPlanProjection | null>(null);
const emptyCtaLabel = ref<string | null>(null);
const emptyCtaRoute = ref<string | null>(null);

/** Bumped on every auth/plan load so in-flight work cannot overwrite newer state. */
let loadSeq = 0;

const launchFailureMessage = computed(
  () => auth.value.message ?? "Не удаётся подключиться к учителю",
);

const goals = computed(() => {
  const raw = plan.value?.goals;
  return Array.isArray(raw) ? raw : [];
});

const focusIsSoftEmpty = computed(() => {
  const focus = plan.value?.focus;
  return typeof focus !== "string" || focus.trim().length === 0;
});

const focusText = computed(() =>
  focusIsSoftEmpty.value ? SOFT_EMPTY : (plan.value?.focus as string),
);

const upcomingTopics = computed(() => {
  const raw = plan.value?.upcoming_topics;
  return Array.isArray(raw) ? raw : [];
});

function applyAuth(next: TeacherAuth, seq: number): boolean {
  if (seq !== loadSeq) {
    return false;
  }
  auth.value = next;
  return true;
}

async function resolveEmptyCta(seq: number): Promise<void> {
  emptyCtaLabel.value = null;
  emptyCtaRoute.value = null;
  try {
    const learner = await fetchLearner(auth.value);
    if (seq !== loadSeq) {
      return;
    }
    const dest = gateDestination(learner);
    if (isOnboardingRoute(dest)) {
      emptyCtaLabel.value = "Продолжить настройку";
      emptyCtaRoute.value = dest;
    } else if (dest === "calendar") {
      emptyCtaLabel.value = "К календарю";
      emptyCtaRoute.value = "calendar";
    }
  } catch {
    // Keep empty body; omit CTA when learner fetch fails.
  }
}

async function loadPlan(seq: number): Promise<void> {
  loadError.value = null;
  notFound.value = false;
  plan.value = null;
  emptyCtaLabel.value = null;
  emptyCtaRoute.value = null;

  if (auth.value.state !== "running" || !auth.value.bearer) {
    return;
  }

  try {
    const projection = await fetchLivingPlan(auth.value);
    if (seq !== loadSeq) {
      return;
    }
    plan.value = projection;
  } catch (err) {
    if (seq !== loadSeq) {
      return;
    }
    if (err instanceof TeacherApiError && err.code === "living_plan_not_found") {
      notFound.value = true;
      await resolveEmptyCta(seq);
      return;
    }
    if (
      err instanceof TeacherApiError &&
      (err.status === 401 || err.status === 403)
    ) {
      // Rehydrate auth; do not tight-loop plan retry.
      try {
        const next = await getTeacherAuth();
        applyAuth(next, seq);
      } catch {
        // keep prior auth
      }
    }
    // Client defaults "Request failed" when API omits `message` — use frozen RU.
    const apiMessage =
      err instanceof TeacherApiError ? err.message.trim() : "";
    loadError.value =
      apiMessage && apiMessage !== "Request failed"
        ? apiMessage
        : LOAD_FALLBACK;
  }
}

async function refreshStatus(): Promise<void> {
  const seq = ++loadSeq;
  loading.value = true;
  try {
    const next = await getTeacherAuth();
    if (!applyAuth(next, seq)) {
      return;
    }
    await loadPlan(seq);
  } catch {
    applyAuth(
      {
        state: "error",
        base_url: "",
        bearer: null,
        message: "Не удалось получить статус учителя",
      },
      seq,
    );
  } finally {
    if (seq === loadSeq) {
      loading.value = false;
    }
  }
}

async function retry(): Promise<void> {
  const seq = ++loadSeq;
  loading.value = true;
  const usedRestart = auth.value.state !== "running";
  try {
    if (usedRestart) {
      const next = await retryTeacher();
      if (!applyAuth(next, seq)) {
        return;
      }
    } else {
      const next = await getTeacherAuth();
      if (!applyAuth(next, seq)) {
        return;
      }
    }
    await loadPlan(seq);
  } catch {
    applyAuth(
      {
        state: "error",
        base_url: "",
        bearer: null,
        message: usedRestart
          ? "Не удалось перезапустить учителя"
          : "Не удалось получить статус учителя",
      },
      seq,
    );
  } finally {
    if (seq === loadSeq) {
      loading.value = false;
    }
  }
}

function goEmptyCta(): void {
  if (!emptyCtaRoute.value) {
    return;
  }
  void router.push({ name: emptyCtaRoute.value });
}

let unsubscribe: (() => void) | undefined;

onMounted(() => {
  void refreshStatus();
  if (typeof window !== "undefined" && window.teacher) {
    unsubscribe = window.teacher.onStatusChange((status) => {
      const seq = ++loadSeq;
      applyAuth(status, seq);
      if (status.state === "running") {
        void (async () => {
          loading.value = true;
          try {
            await loadPlan(seq);
          } finally {
            if (seq === loadSeq) {
              loading.value = false;
            }
          }
        })();
      } else {
        loading.value = false;
      }
    });
  }
});

onUnmounted(() => {
  unsubscribe?.();
});
</script>

<template>
  <main class="plan" data-testid="plan-view" aria-label="План">
    <div class="scroll">
      <h1 class="page-title">План</h1>

      <p
        v-if="loading"
        class="hint"
        data-testid="plan-loading"
      >
        Загрузка…
      </p>

      <template v-else>
        <p
          v-if="auth.state === 'starting'"
          class="hint"
          data-testid="connecting-hint"
        >
          Подключение к учителю…
        </p>
        <div
          v-else-if="auth.state !== 'running' || !auth.bearer"
          class="banner"
          role="alert"
          data-testid="launch-failure-banner"
        >
          <p>{{ launchFailureMessage }}</p>
          <button type="button" class="secondary" @click="retry">
            Повторить
          </button>
        </div>

        <div
          v-else-if="loadError"
          class="banner"
          role="alert"
          data-testid="plan-error"
        >
          <p>{{ loadError }}</p>
          <button type="button" class="secondary" data-testid="plan-retry" @click="retry">
            Повторить
          </button>
        </div>

        <section
          v-else-if="notFound"
          class="plan-section"
          data-testid="plan-empty"
          aria-labelledby="plan-empty-heading"
        >
          <span class="accent-rule" aria-hidden="true" />
          <p id="plan-empty-heading" class="empty-body">
            План обучения ещё не готов.
          </p>
          <button
            v-if="emptyCtaLabel && emptyCtaRoute"
            type="button"
            class="secondary"
            data-testid="plan-empty-cta"
            @click="goEmptyCta"
          >
            {{ emptyCtaLabel }}
          </button>
        </section>

        <template v-else-if="plan">
          <section
            class="plan-section"
            data-testid="plan-section-goals"
            aria-labelledby="section-goals"
          >
            <span class="accent-rule" aria-hidden="true" />
            <p id="section-goals" class="kicker">ЦЕЛИ</p>
            <ul v-if="goals.length > 0" class="list">
              <li v-for="(goal, index) in goals" :key="`goal-${index}`">
                {{ goal }}
              </li>
            </ul>
            <p v-else class="soft-empty" data-testid="goals-soft-empty">
              {{ SOFT_EMPTY }}
            </p>
          </section>

          <section
            class="plan-section"
            data-testid="plan-section-focus"
            aria-labelledby="section-focus"
          >
            <span class="accent-rule" aria-hidden="true" />
            <p id="section-focus" class="kicker">ФОКУС</p>
            <p
              :class="focusIsSoftEmpty ? 'soft-empty' : 'body'"
              data-testid="plan-focus"
            >
              {{ focusText }}
            </p>
          </section>

          <section
            class="plan-section"
            data-testid="plan-section-topics"
            aria-labelledby="section-topics"
          >
            <span class="accent-rule" aria-hidden="true" />
            <p id="section-topics" class="kicker">БЛИЖАЙШИЕ ТЕМЫ</p>
            <ul v-if="upcomingTopics.length > 0" class="list">
              <li
                v-for="(topic, index) in upcomingTopics"
                :key="`topic-${index}`"
              >
                {{ topic }}
              </li>
            </ul>
            <p v-else class="soft-empty" data-testid="topics-soft-empty">
              {{ SOFT_EMPTY }}
            </p>
          </section>
        </template>
      </template>
    </div>
  </main>
</template>

<style scoped>
.plan {
  flex: 1;
  display: flex;
  min-height: 0;
  min-width: 0;
  background: var(--color-bg);
  color: var(--color-ink);
  overflow: auto;
}

.scroll {
  flex: 1;
  max-width: 640px;
  margin: 0 auto;
  padding: 24px 20px 48px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 14px;
  background: var(--color-coral-soft);
  border: 1px solid var(--color-coral);
  border-radius: var(--radius-md);
}

.banner p {
  margin: 0;
  font-size: 13px;
  color: var(--color-ink);
}

.plan-section {
  position: relative;
  padding: 16px 18px 18px;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.accent-rule {
  display: block;
  width: 24px;
  height: 3px;
  background: var(--color-coral);
  border-radius: 2px;
  margin-bottom: 2px;
}

.kicker {
  margin: 0;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  color: var(--color-muted);
  text-transform: uppercase;
}

.hint {
  margin: 0;
  font-size: 13px;
  line-height: 1.45;
  color: var(--color-muted);
}

.body,
.soft-empty,
.empty-body {
  margin: 0;
  font-size: 13px;
  line-height: 1.45;
  color: var(--color-ink);
}

.soft-empty {
  color: var(--color-muted);
}

.list {
  margin: 0;
  padding-left: 1.2em;
  font-size: 13px;
  line-height: 1.45;
  color: var(--color-ink);
}

.secondary {
  align-self: flex-start;
  font: inherit;
  font-size: 13px;
  font-weight: 600;
  padding: 7px 16px;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-ink);
  background: var(--color-surface);
  border: 1px solid var(--color-line);
}

.secondary:focus-visible {
  outline: 2px solid var(--color-coral);
  outline-offset: -2px;
}
</style>
