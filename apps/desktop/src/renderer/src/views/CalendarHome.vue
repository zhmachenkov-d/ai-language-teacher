<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import {
  type CalendarGrain,
  formatMonthTitle,
  formatWeekRangeTitle,
  isSameLocalDay,
  monthGridDays,
  nowLineFraction,
  shiftAnchor,
  snapToToday,
  startOfWeekMonday,
  weekDays,
  weekHourLabels,
  WEEKDAY_LABELS_RU
} from '../calendar/calendarDates'

const EMPTY_HINT = 'выберите урок для просмотра краткой информации или истории'

const grain = ref<CalendarGrain>('week')
const anchor = ref(snapToToday('week'))
const now = ref(new Date())

let tickId: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  tickId = setInterval(() => {
    now.value = new Date()
  }, 30_000)
})

onUnmounted(() => {
  if (tickId !== null) {
    clearInterval(tickId)
  }
})

const rangeTitle = computed(() =>
  grain.value === 'week' ? formatWeekRangeTitle(anchor.value) : formatMonthTitle(anchor.value)
)

const days = computed(() => weekDays(anchor.value))
const hours = weekHourLabels()
const monthDays = computed(() => monthGridDays(anchor.value))

const todayVisibleInWeek = computed(() => days.value.some((d) => isSameLocalDay(d, now.value)))

const weekNowFraction = computed(() => {
  if (!todayVisibleInWeek.value) {
    return null
  }
  return nowLineFraction(now.value)
})

function setGrain(next: CalendarGrain): void {
  grain.value = next
  if (next === 'week') {
    anchor.value = startOfWeekMonday(anchor.value)
  } else {
    anchor.value = new Date(anchor.value.getFullYear(), anchor.value.getMonth(), 1)
  }
}

function goToday(): void {
  now.value = new Date()
  anchor.value = snapToToday(grain.value, now.value)
}

function localDayKey(day: Date): string {
  return `${day.getFullYear()}-${day.getMonth() + 1}-${day.getDate()}`
}

function goPrev(): void {
  anchor.value = shiftAnchor(anchor.value, grain.value, -1)
}

function goNext(): void {
  anchor.value = shiftAnchor(anchor.value, grain.value, 1)
}

function isToday(day: Date): boolean {
  return isSameLocalDay(day, now.value)
}

function isInAnchorMonth(day: Date): boolean {
  return (
    day.getMonth() === anchor.value.getMonth() && day.getFullYear() === anchor.value.getFullYear()
  )
}
</script>

<template>
  <div class="calendar-home">
    <div class="main-col">
      <header class="toolbar">
        <h1 class="range-title">{{ rangeTitle }}</h1>
        <div class="seg" role="group" aria-label="Вид календаря">
          <button
            type="button"
            class="seg-btn"
            :class="{ on: grain === 'week' }"
            :aria-pressed="grain === 'week'"
            @click="setGrain('week')"
          >
            Неделя
          </button>
          <button
            type="button"
            class="seg-btn"
            :class="{ on: grain === 'month' }"
            :aria-pressed="grain === 'month'"
            @click="setGrain('month')"
          >
            Месяц
          </button>
        </div>
        <span class="spacer" />
        <div class="chrome-nav" aria-label="Навигация по датам">
          <button type="button" class="nav-btn" aria-label="Назад" @click="goPrev">‹</button>
          <button type="button" class="today-btn" @click="goToday">Сегодня</button>
          <button type="button" class="nav-btn" aria-label="Вперёд" @click="goNext">›</button>
        </div>
      </header>

      <section v-if="grain === 'week'" class="cal" aria-label="Неделя">
        <div class="days" role="row">
          <div class="h gutter" />
          <div
            v-for="(day, index) in days"
            :key="localDayKey(day)"
            class="h"
            :class="{ today: isToday(day) }"
            role="columnheader"
          >
            {{ WEEKDAY_LABELS_RU[index] }}
            <span class="n">{{ day.getDate() }}</span>
          </div>
        </div>
        <div class="grid-wrap">
          <div class="grid">
            <div class="time-col" aria-hidden="true">
              <div v-for="label in hours" :key="label" class="hour">{{ label }}</div>
            </div>
            <div
              v-for="day in days"
              :key="localDayKey(day)"
              class="day-col"
              :class="{ 'today-col': isToday(day) }"
            >
              <div v-for="label in hours" :key="label" class="hour" />
              <div
                v-if="isToday(day) && weekNowFraction !== null"
                class="now-line"
                data-testid="now-line"
                :style="{ top: `${weekNowFraction * 100}%` }"
              />
            </div>
          </div>
        </div>
      </section>

      <section v-else class="cal month" aria-label="Месяц">
        <div class="month-head" role="row">
          <div v-for="label in WEEKDAY_LABELS_RU" :key="label" class="mh">{{ label }}</div>
        </div>
        <div class="month-grid">
          <div
            v-for="day in monthDays"
            :key="localDayKey(day)"
            class="month-cell"
            :class="{
              today: isToday(day),
              outside: !isInAnchorMonth(day)
            }"
          >
            <span class="n">{{ day.getDate() }}</span>
          </div>
        </div>
      </section>
    </div>

    <aside class="panel" aria-label="Панель урока">
      <div class="panel-body">
        <p class="empty-hint">{{ EMPTY_HINT }}</p>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.calendar-home {
  flex: 1;
  display: flex;
  min-height: 0;
  min-width: 0;
  background: var(--color-bg);
}

.main-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  border-right: 1px solid var(--color-line);
}

.toolbar {
  height: 44px;
  display: flex;
  align-items: center;
  padding: 0 14px;
  gap: 10px;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-line);
  flex-shrink: 0;
}

.range-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--color-ink);
}

.seg {
  display: flex;
  margin-left: 8px;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-surface);
}

.seg-btn {
  margin: 0;
  padding: 4px 12px;
  border: 0;
  border-right: 1px solid var(--color-line);
  background: transparent;
  color: var(--color-muted);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.seg-btn:last-child {
  border-right: 0;
}

.seg-btn.on {
  background: var(--color-sidebar);
  color: var(--color-ink);
  font-weight: 600;
}

.seg-btn:focus-visible,
.nav-btn:focus-visible,
.today-btn:focus-visible {
  outline: 2px solid var(--color-coral);
  outline-offset: -2px;
  z-index: 1;
}

.spacer {
  flex: 1;
}

.chrome-nav {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--color-muted);
  font-size: 12px;
}

.nav-btn,
.today-btn {
  margin: 0;
  font: inherit;
  font-size: 12px;
  cursor: pointer;
  color: var(--color-ink);
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
}

.nav-btn {
  padding: 4px 8px;
  color: var(--color-muted);
  border-color: transparent;
  background: transparent;
}

.today-btn {
  padding: 4px 10px;
}

.cal {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--color-surface);
}

.days {
  display: grid;
  grid-template-columns: 48px repeat(7, 1fr);
  border-bottom: 1px solid var(--color-line);
  flex-shrink: 0;
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

.days .h .n {
  display: block;
  margin: 4px auto 0;
  width: 28px;
  height: 28px;
  line-height: 28px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
  border-radius: 9999px;
  box-sizing: border-box;
}

.days .h.today {
  background: var(--color-today-tint);
}

.days .h.today .n {
  border: 2px solid var(--color-coral);
  line-height: 24px;
  font-weight: 700;
}

.grid-wrap {
  flex: 1;
  overflow: auto;
  position: relative;
  min-height: 0;
}

.grid {
  display: grid;
  grid-template-columns: 48px repeat(7, 1fr);
  min-height: 100%;
}

.time-col,
.day-col {
  border-right: 1px solid var(--color-line);
  position: relative;
}

.day-col:last-child {
  border-right: none;
}

.day-col.today-col {
  background: var(--color-today-tint);
}

.hour {
  height: 52px;
  border-bottom: 1px solid var(--color-line);
  font-size: 10px;
  color: var(--color-muted);
  padding: 2px 6px 0 0;
  text-align: right;
  box-sizing: border-box;
}

.day-col .hour {
  padding: 0;
}

.now-line {
  position: absolute;
  left: 0;
  right: 0;
  border-top: 2px solid var(--color-coral);
  z-index: 2;
  pointer-events: none;
  transition: none;
  animation: none;
}

.now-line::before {
  content: '';
  position: absolute;
  left: -4px;
  top: -5px;
  width: 8px;
  height: 8px;
  background: var(--color-coral);
  border-radius: 9999px;
}

.month-head {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  border-bottom: 1px solid var(--color-line);
  flex-shrink: 0;
}

.month-head .mh {
  padding: 8px 4px;
  text-align: center;
  font-size: 11px;
  color: var(--color-muted);
  border-right: 1px solid var(--color-line);
}

.month-head .mh:last-child {
  border-right: none;
}

.month-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-template-rows: repeat(6, 1fr);
  min-height: 0;
}

.month-cell {
  border-right: 1px solid var(--color-line);
  border-bottom: 1px solid var(--color-line);
  padding: 8px;
  min-height: 64px;
  box-sizing: border-box;
}

.month-cell:nth-child(7n) {
  border-right: none;
}

.month-cell.outside .n {
  color: var(--color-muted);
  opacity: 0.55;
}

.month-cell.today {
  background: var(--color-today-tint);
}

.month-cell .n {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-ink);
  border-radius: 9999px;
  box-sizing: border-box;
}

.month-cell.today .n {
  border: 2px solid var(--color-coral);
  font-weight: 700;
}

.panel {
  width: 300px;
  flex-shrink: 0;
  background: var(--color-surface);
  display: flex;
  flex-direction: column;
}

.panel-body {
  padding: 18px;
  flex: 1;
}

.empty-hint {
  margin: 0;
  font-size: 13px;
  line-height: 1.45;
  color: var(--color-muted);
}
</style>
