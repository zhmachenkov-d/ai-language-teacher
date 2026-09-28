/** Pref chip labels and intake step helpers for the 2.1 onboarding wizard. */

import type { IntakeStep } from "../services/teacherClient";

export const GOAL_CHIPS = [
  "Работа / карьера",
  "Путешествия",
  "Учёба",
  "Повседневное общение",
] as const;

export const OUTCOME_CHIPS = [
  "Уверенный разговор",
  "Понимать на слух",
  "Письмо / почта",
  "Собеседования",
] as const;

export const INTEREST_CHIPS = [
  "Технологии",
  "Новости",
  "Фильмы",
  "Повседневность",
] as const;

export const EMPHASIS_CHIPS = [
  "Говорение",
  "Аудирование",
  "Словарь",
  "Грамматика",
] as const;

export const DURATION_OPTIONS = [30, 45, 60] as const;

export const WEEKDAY_OPTIONS: { value: number; label: string }[] = [
  { value: 0, label: "Пн" },
  { value: 1, label: "Вт" },
  { value: 2, label: "Ср" },
  { value: 3, label: "Чт" },
  { value: 4, label: "Пт" },
  { value: 5, label: "Сб" },
  { value: 6, label: "Вс" },
];

/** Wizard UI steps (excludes `complete`, which hands off to consent). */
export type WizardStep =
  | "greeting"
  | "goals"
  | "interests"
  | "duration"
  | "schedule";

export const WIZARD_STEPS: WizardStep[] = [
  "greeting",
  "goals",
  "interests",
  "duration",
  "schedule",
];

export function resumeWizardStep(intakeStep: IntakeStep): WizardStep {
  if (intakeStep === "complete") {
    return "schedule";
  }
  if ((WIZARD_STEPS as string[]).includes(intakeStep)) {
    return intakeStep as WizardStep;
  }
  return "greeting";
}

export function nextIntakeStep(step: WizardStep): IntakeStep {
  switch (step) {
    case "greeting":
      return "goals";
    case "goals":
      return "interests";
    case "interests":
      return "duration";
    case "duration":
      return "schedule";
    case "schedule":
      return "complete";
  }
}

/** Split persisted pref list into known chips vs optional «Другое» free text. */
export function splitPrefList(
  values: string[],
  chips: readonly string[],
): { selected: string[]; other: string } {
  const chipSet = new Set(chips);
  const selected: string[] = [];
  const others: string[] = [];
  for (const value of values) {
    if (chipSet.has(value)) {
      selected.push(value);
    } else if (value.trim()) {
      others.push(value.trim());
    }
  }
  return { selected, other: others[0] ?? "" };
}

export function mergePrefList(selected: string[], other: string): string[] {
  const out = [...selected];
  const trimmed = other.trim();
  if (trimmed) {
    out.push(trimmed);
  }
  return out;
}

export function prefGroupComplete(selected: string[], other: string): boolean {
  return selected.length > 0 || other.trim().length > 0;
}

export function detectTimezone(): string {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  } catch {
    return "UTC";
  }
}

export function formatStartMinute(minute: number): string {
  const h = Math.floor(minute / 60);
  const m = minute % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}

export function parseStartMinute(value: string): number | null {
  // `<input type="time">` may yield HH:MM or HH:MM:SS.
  const match = /^(\d{1,2}):(\d{2})(?::\d{2})?$/.exec(value.trim());
  if (!match) {
    return null;
  }
  const hours = Number(match[1]);
  const minutes = Number(match[2]);
  if (
    !Number.isInteger(hours) ||
    !Number.isInteger(minutes) ||
    hours < 0 ||
    hours > 23 ||
    minutes < 0 ||
    minutes > 59
  ) {
    return null;
  }
  return hours * 60 + minutes;
}
