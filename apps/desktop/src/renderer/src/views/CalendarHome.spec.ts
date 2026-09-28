import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import CalendarHome from './CalendarHome.vue'
import { HOUR_END, HOUR_START, weekHourLabels, WEEKDAY_LABELS_RU } from '../calendar/calendarDates'

const EMPTY_HINT = 'выберите урок для просмотра краткой информации или истории'

describe('CalendarHome empty chrome', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 8, 23, 12, 0, 0)) // Wed noon — in-band
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('renders week grid with empty side-panel hint', async () => {
    const wrapper = mount(CalendarHome)
    await nextTick()
    expect(wrapper.find('.empty-hint').text()).toBe(EMPTY_HINT)
    expect(wrapper.find('[aria-label="Неделя"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Неделя')
    const hourTexts = wrapper.findAll('.time-col .hour').map((h) => h.text())
    expect(hourTexts).toEqual(weekHourLabels())
    expect(hourTexts).toHaveLength(HOUR_END - HOUR_START)
    expect(hourTexts[0]).toBe('07:00')
    expect(hourTexts[hourTexts.length - 1]).toBe('20:00')
    wrapper.unmount()
  })

  it('grain switch shows empty month/week grids with Monday-first headers', async () => {
    const wrapper = mount(CalendarHome)
    await nextTick()
    const headers = wrapper.findAll('[role="columnheader"]')
    expect(headers.map((h) => h.text().replace(/\d+/g, '').trim())).toEqual([...WEEKDAY_LABELS_RU])

    await wrapper.get('button.seg-btn:nth-child(2)').trigger('click')
    await nextTick()
    expect(wrapper.find('[aria-label="Месяц"]').exists()).toBe(true)
    expect(wrapper.find('[data-testid="now-line"]').exists()).toBe(false)
    expect(wrapper.findAll('.month-cell.today')).toHaveLength(1)
    expect(wrapper.findAll('.month-head .mh').map((h) => h.text())).toEqual([...WEEKDAY_LABELS_RU])
    expect(wrapper.findAll('.event').length).toBe(0)

    await wrapper.get('button.seg-btn:nth-child(1)').trigger('click')
    await nextTick()
    expect(wrapper.find('[aria-label="Неделя"]').exists()).toBe(true)
    wrapper.unmount()
  })

  it('Сегодня / prev / next navigate the anchor', async () => {
    const wrapper = mount(CalendarHome)
    await nextTick()
    const titleBefore = wrapper.find('.range-title').text()
    await wrapper.get('button[aria-label="Вперёд"]').trigger('click')
    await nextTick()
    expect(wrapper.find('.range-title').text()).not.toBe(titleBefore)

    await wrapper.get('button.today-btn').trigger('click')
    await nextTick()
    expect(wrapper.find('.range-title').text()).toBe(titleBefore)

    await wrapper.get('button[aria-label="Назад"]').trigger('click')
    await nextTick()
    expect(wrapper.find('.range-title').text()).not.toBe(titleBefore)
    wrapper.unmount()
  })

  it('month toolbar prev/next and Сегодня navigate months', async () => {
    const wrapper = mount(CalendarHome)
    await nextTick()
    await wrapper.get('button.seg-btn:nth-child(2)').trigger('click')
    await nextTick()
    expect(wrapper.find('.range-title').text()).toBe('Сентябрь 2026')

    await wrapper.get('button[aria-label="Вперёд"]').trigger('click')
    await nextTick()
    expect(wrapper.find('.range-title').text()).toBe('Октябрь 2026')

    await wrapper.get('button.today-btn').trigger('click')
    await nextTick()
    expect(wrapper.find('.range-title').text()).toBe('Сентябрь 2026')
    wrapper.unmount()
  })

  it('week today in-band shows pill, now-line, and today-tint only on today', async () => {
    const wrapper = mount(CalendarHome)
    await nextTick()
    expect(wrapper.findAll('.days .h.today')).toHaveLength(1)
    expect(wrapper.findAll('.day-col.today-col')).toHaveLength(1)
    const nowLine = wrapper.find('[data-testid="now-line"]')
    expect(nowLine.exists()).toBe(true)
    expect(wrapper.findAll('.day-col.today-col [data-testid="now-line"]')).toHaveLength(1)
    const expectedTop = ((12 - 7) / (21 - 7)) * 100
    const top = Number.parseFloat(nowLine.attributes('style')?.match(/top:\s*([\d.]+)%/)?.[1] ?? '')
    expect(top).toBeCloseTo(expectedTop, 5)
    wrapper.unmount()
  })

  it('week today out-of-band hides now-line but keeps pill and tint', async () => {
    vi.setSystemTime(new Date(2026, 8, 23, 6, 0, 0))
    const wrapper = mount(CalendarHome)
    await nextTick()
    expect(wrapper.findAll('.days .h.today')).toHaveLength(1)
    expect(wrapper.findAll('.day-col.today-col')).toHaveLength(1)
    expect(wrapper.find('[data-testid="now-line"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('month today shows pill + tint only (no now-line)', async () => {
    const wrapper = mount(CalendarHome)
    await nextTick()
    await wrapper.get('button.seg-btn:nth-child(2)').trigger('click')
    await nextTick()
    expect(wrapper.findAll('.month-cell.today')).toHaveLength(1)
    expect(wrapper.find('[data-testid="now-line"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('navigating away from today removes now-line and today-tint', async () => {
    const wrapper = mount(CalendarHome)
    await nextTick()
    await wrapper.get('button[aria-label="Вперёд"]').trigger('click')
    await nextTick()
    expect(wrapper.findAll('.days .h.today')).toHaveLength(0)
    expect(wrapper.findAll('.day-col.today-col')).toHaveLength(0)
    expect(wrapper.find('[data-testid="now-line"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('empty selection shows locked empty hint; grid has no fake events', async () => {
    const wrapper = mount(CalendarHome)
    await nextTick()
    expect(wrapper.find('.empty-hint').text()).toBe(EMPTY_HINT)
    expect(wrapper.findAll('.event').length).toBe(0)
    expect(wrapper.find('.panel').exists()).toBe(true)
    wrapper.unmount()
  })

  it('now-line has no CSS transition/animation on top', async () => {
    const wrapper = mount(CalendarHome)
    await nextTick()
    const nowLine = wrapper.find('[data-testid="now-line"]')
    expect(nowLine.exists()).toBe(true)
    const el = nowLine.element as HTMLElement
    const cs = getComputedStyle(el)
    const transitionProps = cs.transitionProperty
      .split(',')
      .map((p) => p.trim().toLowerCase())
      .filter(Boolean)
    expect(transitionProps).not.toContain('top')
    expect(`${cs.transition} ${cs.transitionProperty}`).not.toMatch(/\btop\b/i)
    expect(cs.animationName === 'none' || cs.animationName === '' || cs.animationDuration === '0s').toBe(
      true
    )
    let nowLineDeclaresTopTransition = false
    for (const sheet of Array.from(document.styleSheets)) {
      let rules: CSSRuleList
      try {
        rules = sheet.cssRules
      } catch {
        continue
      }
      for (const rule of Array.from(rules)) {
        if (!(rule instanceof CSSStyleRule)) continue
        if (!rule.selectorText.includes('now-line')) continue
        const decl = `${rule.style.transition} ${rule.style.transitionProperty}`
        if (/\btop\b/i.test(decl)) {
          nowLineDeclaresTopTransition = true
        }
      }
    }
    expect(nowLineDeclaresTopTransition).toBe(false)
    wrapper.unmount()
  })
})
