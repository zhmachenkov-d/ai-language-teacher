<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import { WEEKDAY_LABELS_RU } from "../calendar/calendarDates";
import type { WeeklySlot } from "../services/teacherClient";
import {
  formatHalfLabel,
  formatHourLabel,
  GRID_HOUR_COUNT,
  GRID_ROW_HEIGHT_PX,
  initialScrollHour,
  normalizeWeeklySlots,
  scrollTopForHour,
  slotKey,
} from "./scheduleGrid";

const props = defineProps<{
  slots: WeeklySlot[];
}>();

const emit = defineEmits<{
  "update:slots": [WeeklySlot[]];
  snapped: [];
}>();

const scrollEl = ref<HTMLElement | null>(null);
/** Always post-FINE_SNAP; drives chips/selection before parent round-trip. */
const localSlots = ref<WeeklySlot[]>([]);
const lastScrollHour = ref<number | null>(null);
const hours = Array.from({ length: GRID_HOUR_COUNT }, (_, h) => h);
const weekdays = Array.from({ length: 7 }, (_, d) => d);

const selectedKeys = computed(() => new Set(localSlots.value.map(slotKey)));

function slotsEqual(a: WeeklySlot[], b: WeeklySlot[]): boolean {
  return (
    a.length === b.length &&
    a.every(
      (s, i) =>
        s.weekday === b[i]?.weekday && s.start_minute === b[i]?.start_minute,
    )
  );
}

function isSelected(weekday: number, startMinute: number): boolean {
  return selectedKeys.value.has(`${weekday}:${startMinute}`);
}

function toggleHalf(weekday: number, hour: number, half: 0 | 30): void {
  const start_minute = hour * 60 + half;
  const key = `${weekday}:${start_minute}`;
  const next = localSlots.value.filter(
    (s) => !(s.weekday === weekday && s.start_minute === start_minute),
  );
  if (!selectedKeys.value.has(key)) {
    next.push({ weekday, start_minute });
  }
  localSlots.value = next;
  emit("update:slots", next);
}

function halfAriaLabel(weekday: number, hour: number, half: 0 | 30): string {
  return `${WEEKDAY_LABELS_RU[weekday]} ${formatHalfLabel(hour, half)}`;
}

function applyInitialScroll(): void {
  const el = scrollEl.value;
  if (!el) {
    return;
  }
  const hour = initialScrollHour(localSlots.value);
  if (lastScrollHour.value === hour) {
    return;
  }
  el.scrollTop = scrollTopForHour(hour);
  lastScrollHour.value = hour;
}

function syncFromProps(slots: WeeklySlot[]): void {
  const { slots: normalized, didSnap } = normalizeWeeklySlots(slots);
  localSlots.value = normalized;
  if (!slotsEqual(normalized, slots)) {
    emit("update:slots", normalized);
    if (didSnap) {
      emit("snapped");
    }
  }
  void nextTick(() => {
    applyInitialScroll();
  });
}

watch(
  () => props.slots,
  (slots) => {
    syncFromProps(slots);
  },
  { immediate: true, deep: true },
);

onMounted(() => {
  void nextTick(() => {
    applyInitialScroll();
  });
});

defineExpose({
  scrollEl,
  applyInitialScroll,
  GRID_ROW_HEIGHT_PX,
  localSlots,
});
</script>

<template>
  <div class="schedule-week-grid" data-testid="schedule-week-grid">
    <div class="days" role="row">
      <div class="h gutter" aria-hidden="true" />
      <div
        v-for="day in weekdays"
        :key="day"
        class="h"
        role="columnheader"
      >
        {{ WEEKDAY_LABELS_RU[day] }}
      </div>
    </div>
    <div
      ref="scrollEl"
      class="grid-wrap"
      data-testid="schedule-grid-scroll"
    >
      <div class="grid">
        <div class="time-col" aria-hidden="true">
          <div
            v-for="hour in hours"
            :key="hour"
            class="hour-label"
            :style="{ height: `${GRID_ROW_HEIGHT_PX}px` }"
          >
            {{ formatHourLabel(hour) }}
          </div>
        </div>
        <div
          v-for="day in weekdays"
          :key="day"
          class="day-col"
          :data-weekday="day"
        >
          <div
            v-for="hour in hours"
            :key="hour"
            class="hour-cell"
            :style="{ height: `${GRID_ROW_HEIGHT_PX}px` }"
            :data-hour="hour"
          >
            <button
              type="button"
              class="half half-top"
              :class="{ selected: isSelected(day, hour * 60) }"
              :aria-pressed="isSelected(day, hour * 60)"
              :aria-label="halfAriaLabel(day, hour, 0)"
              :data-testid="`half-${day}-${hour}-00`"
              @click="toggleHalf(day, hour, 0)"
            >
              <span
                v-if="isSelected(day, hour * 60)"
                class="chip chip-top"
                aria-hidden="true"
              >
                {{ formatHalfLabel(hour, 0) }}
              </span>
            </button>
            <button
              type="button"
              class="half half-bottom"
              :class="{ selected: isSelected(day, hour * 60 + 30) }"
              :aria-pressed="isSelected(day, hour * 60 + 30)"
              :aria-label="halfAriaLabel(day, hour, 30)"
              :data-testid="`half-${day}-${hour}-30`"
              @click="toggleHalf(day, hour, 30)"
            >
              <span
                v-if="isSelected(day, hour * 60 + 30)"
                class="chip chip-mid"
                aria-hidden="true"
              >
                {{ formatHalfLabel(hour, 30) }}
              </span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.schedule-week-grid {
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.days {
  display: grid;
  grid-template-columns: 48px repeat(7, 1fr);
  border-bottom: 1px solid var(--color-line);
  flex-shrink: 0;
  background: var(--color-surface);
}

.days .h {
  padding: 8px 4px;
  text-align: center;
  font-size: 11px;
  color: var(--color-muted);
  border-right: 1px solid var(--color-line);
}

.days .h:last-child {
  border-right: none;
}

.days .h.gutter {
  border-right: 1px solid var(--color-line);
}

.grid-wrap {
  flex: 1;
  overflow: auto;
  position: relative;
  min-height: 280px;
  max-height: 420px;
}

.grid {
  display: grid;
  grid-template-columns: 48px repeat(7, 1fr);
}

.time-col,
.day-col {
  border-right: 1px solid var(--color-line);
}

.day-col:last-child {
  border-right: none;
}

.hour-label {
  border-bottom: 1px solid var(--color-line);
  font-size: 10px;
  color: var(--color-muted);
  padding: 2px 6px 0 0;
  text-align: right;
  box-sizing: border-box;
}

.hour-cell {
  position: relative;
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid var(--color-line);
  box-sizing: border-box;
}

.half {
  position: relative;
  flex: 1;
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
  font: inherit;
  min-height: 0;
}

.half:focus-visible {
  outline: 2px solid var(--color-coral);
  outline-offset: -2px;
  z-index: 2;
}

.half.selected {
  background: transparent;
}

.chip {
  position: absolute;
  left: 3px;
  right: 3px;
  height: 18px;
  line-height: 18px;
  font-size: 10px;
  font-weight: 600;
  text-align: center;
  color: var(--color-ink);
  background: var(--color-coral-soft);
  border: 1px solid var(--color-coral);
  border-radius: var(--radius-md);
  pointer-events: none;
  box-sizing: border-box;
}

.chip-top {
  top: 2px;
}

/* Mid chip at hour-cell vertical middle (top edge of lower half). */
.chip-mid {
  top: 0;
  transform: translateY(-50%);
}
</style>
