/** Monday-first week/month helpers. “Today” / now-line use browser local time. */

export const WEEK_START = 1
export const HOUR_START = 7
/** Inclusive display band end (grid covers until this hour). */
export const HOUR_END = 21

export const WEEKDAY_LABELS_RU = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'] as const

const MONTH_NAMES_RU = [
  'января',
  'февраля',
  'марта',
  'апреля',
  'мая',
  'июня',
  'июля',
  'августа',
  'сентября',
  'октября',
  'ноября',
  'декабря'
] as const

const MONTH_TITLE_RU = [
  'Январь',
  'Февраль',
  'Март',
  'Апрель',
  'Май',
  'Июнь',
  'Июль',
  'Август',
  'Сентябрь',
  'Октябрь',
  'Ноябрь',
  'Декабрь'
] as const

export type CalendarGrain = 'week' | 'month'

export function startOfLocalDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}

export function isSameLocalDay(a: Date, b: Date): boolean {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  )
}

/** Monday of the week containing `date` (local). Independent of OS locale. */
export function startOfWeekMonday(date: Date): Date {
  const day = startOfLocalDay(date)
  const weekday = day.getDay() // 0=Sun … 6=Sat
  const offset = weekday === 0 ? -6 : WEEK_START - weekday
  day.setDate(day.getDate() + offset)
  return day
}

export function addDays(date: Date, days: number): Date {
  const next = new Date(date)
  next.setDate(next.getDate() + days)
  return next
}

export function addMonths(date: Date, months: number): Date {
  return new Date(date.getFullYear(), date.getMonth() + months, 1)
}

/** Hour labels for the timed week band: 07:00 … 20:00 (band ends at 21:00). */
export function weekHourLabels(): string[] {
  const labels: string[] = []
  for (let hour = HOUR_START; hour < HOUR_END; hour += 1) {
    labels.push(`${String(hour).padStart(2, '0')}:00`)
  }
  return labels
}

/**
 * Vertical position of the now-line as a fraction of the hour band [0, 1].
 * Returns null when now is outside 07:00–21:00 (caller hides the line).
 */
export function nowLineFraction(now: Date): number | null {
  const minutes = now.getHours() * 60 + now.getMinutes() + now.getSeconds() / 60
  const start = HOUR_START * 60
  const end = HOUR_END * 60
  if (minutes < start || minutes > end) {
    return null
  }
  if (minutes === end) {
    return 1
  }
  return (minutes - start) / (end - start)
}

export function weekDays(anchor: Date): Date[] {
  const monday = startOfWeekMonday(anchor)
  return Array.from({ length: 7 }, (_, i) => addDays(monday, i))
}

/** Six Monday-first weeks covering the month of `anchor`. */
export function monthGridDays(anchor: Date): Date[] {
  const firstOfMonth = new Date(anchor.getFullYear(), anchor.getMonth(), 1)
  const gridStart = startOfWeekMonday(firstOfMonth)
  return Array.from({ length: 42 }, (_, i) => addDays(gridStart, i))
}

export function formatWeekRangeTitle(anchor: Date): string {
  const days = weekDays(anchor)
  const first = days[0]!
  const last = days[6]!
  if (first.getMonth() === last.getMonth()) {
    return `Неделя ${first.getDate()}–${last.getDate()} ${MONTH_NAMES_RU[first.getMonth()]}`
  }
  return `Неделя ${first.getDate()} ${MONTH_NAMES_RU[first.getMonth()]} – ${last.getDate()} ${MONTH_NAMES_RU[last.getMonth()]}`
}

export function formatMonthTitle(anchor: Date): string {
  return `${MONTH_TITLE_RU[anchor.getMonth()]} ${anchor.getFullYear()}`
}

export function shiftAnchor(anchor: Date, grain: CalendarGrain, direction: -1 | 1): Date {
  if (grain === 'week') {
    return addDays(startOfWeekMonday(anchor), direction * 7)
  }
  return addMonths(anchor, direction)
}

export function snapToToday(grain: CalendarGrain, now = new Date()): Date {
  if (grain === 'week') {
    return startOfWeekMonday(now)
  }
  return new Date(now.getFullYear(), now.getMonth(), 1)
}
