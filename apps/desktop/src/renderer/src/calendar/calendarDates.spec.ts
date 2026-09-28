import { describe, expect, it } from 'vitest'
import {
  formatMonthTitle,
  formatWeekRangeTitle,
  HOUR_END,
  HOUR_START,
  isSameLocalDay,
  monthGridDays,
  nowLineFraction,
  shiftAnchor,
  snapToToday,
  startOfWeekMonday,
  weekDays,
  weekHourLabels,
  WEEKDAY_LABELS_RU
} from './calendarDates'

describe('calendarDates Monday-first', () => {
  it('startOfWeekMonday is independent of Sunday-first locales', () => {
    // 2026-09-27 is Sunday — week must still start on Monday 2026-09-21
    const sunday = new Date(2026, 8, 27, 12, 0, 0)
    const monday = startOfWeekMonday(sunday)
    expect(monday.getFullYear()).toBe(2026)
    expect(monday.getMonth()).toBe(8)
    expect(monday.getDate()).toBe(21)
    expect(monday.getDay()).toBe(1)
  })

  it('weekDays returns Пн…Вс order with Monday-first headers', () => {
    expect(WEEKDAY_LABELS_RU).toEqual(['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'])
    const days = weekDays(new Date(2026, 8, 23))
    expect(days.map((d) => d.getDay())).toEqual([1, 2, 3, 4, 5, 6, 0])
    expect(days[0]!.getDate()).toBe(21)
    expect(days[6]!.getDate()).toBe(27)
  })

  it('monthGridDays starts on Monday before the 1st when needed', () => {
    // September 2026 starts on Tuesday → grid starts Mon Aug 31
    const grid = monthGridDays(new Date(2026, 8, 15))
    expect(grid).toHaveLength(42)
    expect(grid[0]!.getDay()).toBe(1)
    expect(grid[0]!.getMonth()).toBe(7)
    expect(grid[0]!.getDate()).toBe(31)
  })
})

describe('calendarDates now-line band', () => {
  it('returns fraction when now is inside 07:00–21:00', () => {
    const noon = new Date(2026, 8, 23, 12, 0, 0)
    expect(nowLineFraction(noon)).toBeCloseTo((12 - HOUR_START) / (HOUR_END - HOUR_START))
  })

  it('returns null when now is outside 07:00–21:00', () => {
    expect(nowLineFraction(new Date(2026, 8, 23, 6, 59, 0))).toBeNull()
    expect(nowLineFraction(new Date(2026, 8, 23, 21, 0, 1))).toBeNull()
  })

  it('clamps to bottom edge at exactly 21:00', () => {
    expect(nowLineFraction(new Date(2026, 8, 23, 21, 0, 0))).toBe(1)
  })

  it('weekHourLabels cover 07:00 through 20:00', () => {
    const labels = weekHourLabels()
    expect(labels[0]).toBe('07:00')
    expect(labels[labels.length - 1]).toBe('20:00')
    expect(labels).toHaveLength(HOUR_END - HOUR_START)
  })
})

describe('calendarDates navigation', () => {
  it('Сегодня snaps to current local week/month', () => {
    const now = new Date(2026, 8, 23, 15, 0, 0)
    const week = snapToToday('week', now)
    expect(isSameLocalDay(week, new Date(2026, 8, 21))).toBe(true)
    const month = snapToToday('month', now)
    expect(month.getFullYear()).toBe(2026)
    expect(month.getMonth()).toBe(8)
    expect(month.getDate()).toBe(1)
  })

  it('prev/next shift by week or month', () => {
    const weekAnchor = new Date(2026, 8, 21)
    const nextWeek = shiftAnchor(weekAnchor, 'week', 1)
    expect(isSameLocalDay(nextWeek, new Date(2026, 8, 28))).toBe(true)
    const monthAnchor = new Date(2026, 8, 1)
    const prevMonth = shiftAnchor(monthAnchor, 'month', -1)
    expect(prevMonth.getMonth()).toBe(7)
    expect(prevMonth.getFullYear()).toBe(2026)
  })

  it('formats Russian range titles', () => {
    expect(formatWeekRangeTitle(new Date(2026, 8, 23))).toBe('Неделя 21–27 сентября')
    // Week spanning Sep–Oct (Mon 28 Sep – Sun 4 Oct 2026)
    expect(formatWeekRangeTitle(new Date(2026, 8, 30))).toBe(
      'Неделя 28 сентября – 4 октября'
    )
    expect(formatMonthTitle(new Date(2026, 8, 1))).toBe('Сентябрь 2026')
  })
})
