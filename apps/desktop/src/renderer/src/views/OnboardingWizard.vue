<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import {
  DURATION_OPTIONS,
  EMPHASIS_CHIPS,
  GOAL_CHIPS,
  INTEREST_CHIPS,
  OUTCOME_CHIPS,
  WEEKDAY_OPTIONS,
  detectTimezone,
  formatStartMinute,
  mergePrefList,
  nextIntakeStep,
  parseStartMinute,
  prefGroupComplete,
  resumeWizardStep,
  splitPrefList,
  type WizardStep,
} from "../onboarding/constants";
import {
  getTeacherAuth,
  patchLearner,
  fetchLearner,
  TeacherApiError,
  type LearnerProfile,
  type TeacherAuth,
  type WeeklySlot,
} from "../services/teacherClient";

const router = useRouter();

const loading = ref(true);
const saving = ref(false);
const loadError = ref<string | null>(null);
const saveError = ref<string | null>(null);
const validationError = ref<string | null>(null);

const auth = ref<TeacherAuth>({
  state: "starting",
  base_url: "",
  bearer: null,
});
const step = ref<WizardStep>("greeting");

const addressAs = ref("");
const ageText = ref("");

const goalSelected = ref<string[]>([]);
const goalOther = ref("");
const outcomeSelected = ref<string[]>([]);
const outcomeOther = ref("");

const interestSelected = ref<string[]>([]);
const interestOther = ref("");
const emphasisSelected = ref<string[]>([]);
const emphasisOther = ref("");

const duration = ref<number | null>(null);

const timezone = ref(detectTimezone());
const slots = ref<WeeklySlot[]>([]);
const draftWeekday = ref(0);
const draftTime = ref("09:00");

const stepTitle = computed(() => {
  switch (step.value) {
    case "greeting":
      return "Знакомство";
    case "goals":
      return "Цели и результат";
    case "interests":
      return "Интересы и акценты";
    case "duration":
      return "Длительность урока";
    case "schedule":
      return "Расписание";
  }
});

function hydrate(learner: LearnerProfile): void {
  addressAs.value = learner.address_as ?? "";
  ageText.value = learner.age != null ? String(learner.age) : "";

  const goals = splitPrefList(learner.goals, GOAL_CHIPS);
  goalSelected.value = goals.selected;
  goalOther.value = goals.other;
  const outcomes = splitPrefList(learner.desired_outcome, OUTCOME_CHIPS);
  outcomeSelected.value = outcomes.selected;
  outcomeOther.value = outcomes.other;

  const interests = splitPrefList(learner.interests, INTEREST_CHIPS);
  interestSelected.value = interests.selected;
  interestOther.value = interests.other;
  const emphasis = splitPrefList(learner.emphasis, EMPHASIS_CHIPS);
  emphasisSelected.value = emphasis.selected;
  emphasisOther.value = emphasis.other;

  duration.value = learner.lesson_duration_minutes;
  timezone.value = learner.timezone && learner.timezone !== "UTC"
    ? learner.timezone
    : detectTimezone();
  slots.value = [...learner.weekly_slots];
  step.value = resumeWizardStep(learner.intake_step);
}

function toggleChip(list: string[], chip: string): string[] {
  return list.includes(chip)
    ? list.filter((c) => c !== chip)
    : [...list, chip];
}

function addSlot(): void {
  validationError.value = null;
  const minute = parseStartMinute(draftTime.value);
  if (minute == null) {
    validationError.value = "Укажите время в формате ЧЧ:ММ";
    return;
  }
  const next: WeeklySlot = {
    weekday: draftWeekday.value,
    start_minute: minute,
  };
  const exists = slots.value.some(
    (s) => s.weekday === next.weekday && s.start_minute === next.start_minute,
  );
  if (!exists) {
    slots.value = [...slots.value, next];
  }
}

function removeSlot(index: number): void {
  slots.value = slots.value.filter((_, i) => i !== index);
}

function weekdayLabel(weekday: number): string {
  return WEEKDAY_OPTIONS.find((w) => w.value === weekday)?.label ?? String(weekday);
}

function validateCurrentStep(): string | null {
  switch (step.value) {
    case "greeting": {
      if (!addressAs.value.trim()) {
        return "Укажите, как к вам обращаться";
      }
      const rawAge = String(ageText.value).trim();
      const age = Number(rawAge);
      if (!Number.isInteger(age) || age < 1 || age > 120 || String(age) !== rawAge) {
        return "Укажите возраст от 1 до 120";
      }
      return null;
    }
    case "goals": {
      if (!prefGroupComplete(goalSelected.value, goalOther.value)) {
        return "Выберите цель или укажите «Другое»";
      }
      if (!prefGroupComplete(outcomeSelected.value, outcomeOther.value)) {
        return "Выберите желаемый результат или укажите «Другое»";
      }
      return null;
    }
    case "interests": {
      if (!prefGroupComplete(interestSelected.value, interestOther.value)) {
        return "Выберите интерес или укажите «Другое»";
      }
      if (!prefGroupComplete(emphasisSelected.value, emphasisOther.value)) {
        return "Выберите акцент или укажите «Другое»";
      }
      return null;
    }
    case "duration": {
      if (duration.value == null || !(DURATION_OPTIONS as readonly number[]).includes(duration.value)) {
        return "Выберите длительность урока";
      }
      return null;
    }
    case "schedule": {
      if (slots.value.length < 1) {
        return "Добавьте хотя бы один слот в расписание";
      }
      if (!timezone.value.trim()) {
        return "Не удалось определить часовой пояс";
      }
      return null;
    }
  }
}

function buildPatch(): Parameters<typeof patchLearner>[1] {
  const nextStep = nextIntakeStep(step.value);
  switch (step.value) {
    case "greeting":
      return {
        address_as: addressAs.value.trim(),
        age: Number(String(ageText.value).trim()),
        intake_step: nextStep,
      };
    case "goals":
      return {
        goals: mergePrefList(goalSelected.value, goalOther.value),
        desired_outcome: mergePrefList(outcomeSelected.value, outcomeOther.value),
        intake_step: nextStep,
      };
    case "interests":
      return {
        interests: mergePrefList(interestSelected.value, interestOther.value),
        emphasis: mergePrefList(emphasisSelected.value, emphasisOther.value),
        intake_step: nextStep,
      };
    case "duration":
      return {
        lesson_duration_minutes: duration.value!,
        intake_step: nextStep,
      };
    case "schedule":
      return {
        timezone: timezone.value,
        weekly_slots: slots.value,
        intake_step: nextStep,
      };
  }
}

async function load(): Promise<void> {
  loading.value = true;
  loadError.value = null;
  try {
    const nextAuth = await getTeacherAuth();
    auth.value = nextAuth;
    if (nextAuth.state !== "running") {
      loadError.value = nextAuth.message ?? "Учитель не запущен";
      return;
    }
    const learner = await fetchLearner(nextAuth);
    if (learner.intake_step === "complete") {
      await router.replace({ name: "onboarding-consent" });
      return;
    }
    hydrate(learner);
  } catch (err) {
    loadError.value =
      err instanceof TeacherApiError
        ? err.message
        : "Не удалось загрузить профиль";
  } finally {
    loading.value = false;
  }
}

async function onNext(): Promise<void> {
  if (saving.value) {
    return;
  }
  validationError.value = null;
  saveError.value = null;
  const localError = validateCurrentStep();
  if (localError) {
    validationError.value = localError;
    return;
  }
  if (auth.value.state !== "running") {
    saveError.value = "Учитель не запущен";
    return;
  }
  saving.value = true;
  try {
    const updated = await patchLearner(auth.value, buildPatch());
    if (updated.intake_step === "complete") {
      await router.replace({ name: "onboarding-consent" });
      return;
    }
    step.value = resumeWizardStep(updated.intake_step);
  } catch (err) {
    saveError.value =
      err instanceof TeacherApiError
        ? err.message
        : "Не удалось сохранить. Попробуйте ещё раз";
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  void load();
});
</script>

<template>
  <main class="wizard" data-testid="onboarding-wizard">
    <div v-if="loading" class="status" data-testid="wizard-loading">Загрузка…</div>
    <div v-else-if="loadError" class="status error-block" role="alert">
      <p>{{ loadError }}</p>
      <button type="button" class="cta" @click="load">Повторить</button>
    </div>
    <template v-else>
      <header class="header">
        <h1>{{ stepTitle }}</h1>
      </header>

      <section v-if="step === 'greeting'" class="surface" data-testid="step-greeting">
        <span class="accent-rule" aria-hidden="true" />
        <label class="field-label" for="address-as">Как к вам обращаться</label>
        <input
          id="address-as"
          v-model="addressAs"
          class="field"
          type="text"
          autocomplete="nickname"
          data-testid="address-as-input"
        />
        <label class="field-label" for="age">Возраст</label>
        <input
          id="age"
          v-model="ageText"
          class="field"
          type="number"
          min="1"
          max="120"
          inputmode="numeric"
          data-testid="age-input"
        />
      </section>

      <section v-else-if="step === 'goals'" class="surface" data-testid="step-goals">
        <span class="accent-rule" aria-hidden="true" />
        <p class="kicker">Цели</p>
        <div class="chips" role="group" aria-label="Цели">
          <button
            v-for="chip in GOAL_CHIPS"
            :key="chip"
            type="button"
            class="chip"
            :class="{ selected: goalSelected.includes(chip) }"
            :aria-pressed="goalSelected.includes(chip)"
            @click="goalSelected = toggleChip(goalSelected, chip)"
          >
            {{ chip }}
          </button>
        </div>
        <label class="field-label" for="goal-other">Другое</label>
        <input id="goal-other" v-model="goalOther" class="field" type="text" data-testid="goal-other" />

        <p class="kicker spaced">Желаемый результат</p>
        <div class="chips" role="group" aria-label="Желаемый результат">
          <button
            v-for="chip in OUTCOME_CHIPS"
            :key="chip"
            type="button"
            class="chip"
            :class="{ selected: outcomeSelected.includes(chip) }"
            :aria-pressed="outcomeSelected.includes(chip)"
            @click="outcomeSelected = toggleChip(outcomeSelected, chip)"
          >
            {{ chip }}
          </button>
        </div>
        <label class="field-label" for="outcome-other">Другое</label>
        <input
          id="outcome-other"
          v-model="outcomeOther"
          class="field"
          type="text"
          data-testid="outcome-other"
        />
      </section>

      <section
        v-else-if="step === 'interests'"
        class="surface"
        data-testid="step-interests"
      >
        <span class="accent-rule" aria-hidden="true" />
        <p class="kicker">Интересы</p>
        <div class="chips" role="group" aria-label="Интересы">
          <button
            v-for="chip in INTEREST_CHIPS"
            :key="chip"
            type="button"
            class="chip"
            :class="{ selected: interestSelected.includes(chip) }"
            :aria-pressed="interestSelected.includes(chip)"
            @click="interestSelected = toggleChip(interestSelected, chip)"
          >
            {{ chip }}
          </button>
        </div>
        <label class="field-label" for="interest-other">Другое</label>
        <input
          id="interest-other"
          v-model="interestOther"
          class="field"
          type="text"
          data-testid="interest-other"
        />

        <p class="kicker spaced">Акценты</p>
        <div class="chips" role="group" aria-label="Акценты">
          <button
            v-for="chip in EMPHASIS_CHIPS"
            :key="chip"
            type="button"
            class="chip"
            :class="{ selected: emphasisSelected.includes(chip) }"
            :aria-pressed="emphasisSelected.includes(chip)"
            @click="emphasisSelected = toggleChip(emphasisSelected, chip)"
          >
            {{ chip }}
          </button>
        </div>
        <label class="field-label" for="emphasis-other">Другое</label>
        <input
          id="emphasis-other"
          v-model="emphasisOther"
          class="field"
          type="text"
          data-testid="emphasis-other"
        />
      </section>

      <section
        v-else-if="step === 'duration'"
        class="surface"
        data-testid="step-duration"
      >
        <span class="accent-rule" aria-hidden="true" />
        <p class="hint">Сколько минут длится один урок?</p>
        <div class="chips" role="radiogroup" aria-label="Длительность">
          <button
            v-for="opt in DURATION_OPTIONS"
            :key="opt"
            type="button"
            class="chip"
            :class="{ selected: duration === opt }"
            :aria-checked="duration === opt"
            role="radio"
            @click="duration = opt"
          >
            {{ opt }} мин
          </button>
        </div>
      </section>

      <section
        v-else-if="step === 'schedule'"
        class="surface"
        data-testid="step-schedule"
      >
        <span class="accent-rule" aria-hidden="true" />
        <p class="hint">
          Часовой пояс:
          <strong data-testid="timezone-label">{{ timezone }}</strong>
        </p>
        <ul class="slot-list" data-testid="slot-list">
          <li v-for="(slot, index) in slots" :key="`${slot.weekday}-${slot.start_minute}-${index}`">
            <span>{{ weekdayLabel(slot.weekday) }} · {{ formatStartMinute(slot.start_minute) }}</span>
            <button
              type="button"
              class="secondary"
              :aria-label="`Удалить слот ${index + 1}`"
              @click="removeSlot(index)"
            >
              Удалить
            </button>
          </li>
        </ul>
        <div class="slot-draft">
          <label class="field-label" for="slot-weekday">День</label>
          <select id="slot-weekday" v-model.number="draftWeekday" class="field">
            <option v-for="day in WEEKDAY_OPTIONS" :key="day.value" :value="day.value">
              {{ day.label }}
            </option>
          </select>
          <label class="field-label" for="slot-time">Время</label>
          <input
            id="slot-time"
            v-model="draftTime"
            class="field"
            type="time"
            data-testid="slot-time"
          />
          <button type="button" class="secondary" data-testid="add-slot" @click="addSlot">
            Добавить слот
          </button>
        </div>
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
.wizard {
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
  font-size: 1.45rem;
  font-weight: 600;
}

.surface {
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

.kicker.spaced {
  margin-top: 10px;
}

.hint {
  margin: 0;
  font-size: 13px;
  line-height: 1.45;
  color: var(--color-muted);
}

.field-label {
  font-size: 12px;
  color: var(--color-muted);
}

.field {
  padding: 8px 10px;
  font: inherit;
  font-size: 13px;
  color: var(--color-ink);
  background: var(--color-bg);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
}

.chips {
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

.chip:focus-visible {
  outline: 2px solid var(--color-coral);
  outline-offset: 1px;
}

.slot-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.slot-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 13px;
}

.slot-draft {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 8px;
}

.error,
.error-block {
  margin: 0;
  font-size: 12px;
  color: var(--color-missed);
}

.status {
  font-size: 13px;
  color: var(--color-muted);
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

.cta:focus-visible,
.secondary:focus-visible {
  outline: 2px solid var(--color-coral);
  outline-offset: -2px;
}
</style>
