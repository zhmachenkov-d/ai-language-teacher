/** Pure helpers for ScheduleWeekGrid — half-hour snap + coalesce. */

import type { WeeklySlot } from "../services/teacherClient";

/** Hours shown in the initial working band (matches calendar HOUR_START…HOUR_END exclusive). */
export const GRID_BAND_START = 7;
export const GRID_BAND_END = 21; // exclusive — labels 07:00 … 20:00
export const GRID_HOUR_COUNT = 24;
export const GRID_ROW_HEIGHT_PX = 52;

/**
 * Snap `start_minute` to the nearest :00 / :30.
 * On an exact midpoint tie (:15 / :45), pick the earlier half.
 * Result is always in [0, 23*60+30].
 */
export function snapStartMinute(minute: number): number {
  const clamped = Math.max(0, Math.min(1439, Math.trunc(minute)));
  const lower = Math.floor(clamped / 30) * 30;
  if (clamped === lower) {
    return lower;
  }
  const upper = lower + 30;
  const distLower = clamped - lower;
  const distUpper = upper - clamped;
  let snapped: number;
  if (distLower < distUpper) {
    snapped = lower;
  } else if (distUpper < distLower) {
    snapped = upper;
  } else {
    snapped = lower; // earlier-on-tie
  }
  const maxHalf = 23 * 60 + 30;
  return Math.min(snapped, maxHalf);
}

export function slotKey(slot: WeeklySlot): string {
  return `${slot.weekday}:${slot.start_minute}`;
}

/** Snap every slot, drop invalid weekdays, then coalesce by (weekday, start_minute). */
export function normalizeWeeklySlots(slots: WeeklySlot[]): {
  slots: WeeklySlot[];
  didSnap: boolean;
} {
  let didSnap = false;
  const snapped: WeeklySlot[] = [];
  for (const slot of slots) {
    if (
      !Number.isInteger(slot.weekday) ||
      slot.weekday < 0 ||
      slot.weekday > 6
    ) {
      continue;
    }
    const start_minute = snapStartMinute(slot.start_minute);
    if (start_minute !== slot.start_minute) {
      didSnap = true;
    }
    snapped.push({ weekday: slot.weekday, start_minute });
  }
  const seen = new Set<string>();
  const out: WeeklySlot[] = [];
  for (const slot of snapped) {
    const key = slotKey(slot);
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    out.push(slot);
  }
  return { slots: out, didSnap };
}

export function formatHourLabel(hour: number): string {
  return `${String(hour).padStart(2, "0")}:00`;
}

export function formatHalfLabel(hour: number, half: 0 | 30): string {
  return `${String(hour).padStart(2, "0")}:${String(half).padStart(2, "0")}`;
}

export function hourOfMinute(startMinute: number): number {
  return Math.floor(startMinute / 60);
}

/** Scroll offset so `hour` row is at the top of the viewport (clamped). */
export function scrollTopForHour(hour: number): number {
  return Math.max(0, Math.min(hour, GRID_HOUR_COUNT - 1)) * GRID_ROW_HEIGHT_PX;
}

/**
 * INITIAL_VIEW: prefer working band 7–20; if any selected mark is outside,
 * scroll that hour into view instead.
 */
export function initialScrollHour(slots: WeeklySlot[]): number {
  const outside = slots
    .map((s) => hourOfMinute(s.start_minute))
    .filter((h) => h < GRID_BAND_START || h >= GRID_BAND_END);
  if (outside.length > 0) {
    return Math.min(...outside);
  }
  return GRID_BAND_START;
}
