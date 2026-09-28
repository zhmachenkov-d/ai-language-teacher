import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import App from './App.vue'
import { createAppRouter } from './router'
import { HOUR_END, HOUR_START, weekHourLabels, WEEKDAY_LABELS_RU } from './calendar/calendarDates'

const STORAGE_KEY = 'theme-preference'
const EMPTY_HINT = 'выберите урок для просмотра краткой информации или истории'

type MediaListener = (event: MediaQueryListEvent) => void

function mockMatchMedia(matches: boolean): {
  dispatch: (next: boolean) => void
} {
  let current = matches
  const listeners = new Set<MediaListener>()
  const media = {
    matches: current,
    media: '(prefers-color-scheme: dark)',
    onchange: null,
    addEventListener: (_type: string, listener: EventListenerOrEventListenerObject) => {
      listeners.add(listener as MediaListener)
    },
    removeEventListener: (_type: string, listener: EventListenerOrEventListenerObject) => {
      listeners.delete(listener as MediaListener)
    },
    addListener: () => undefined,
    removeListener: () => undefined,
    dispatchEvent: () => true
  } as MediaQueryList

  window.matchMedia = vi.fn().mockImplementation((query: string) => {
    if (query === '(prefers-reduced-motion: reduce)') {
      return {
        matches: false,
        media: query,
        onchange: null,
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
        addListener: () => undefined,
        removeListener: () => undefined,
        dispatchEvent: () => true
      } as MediaQueryList
    }
    Object.defineProperty(media, 'matches', {
      configurable: true,
      get: () => current
    })
    return media
  })

  return {
    dispatch: (next: boolean) => {
      current = next
      Array.from(listeners).forEach((listener) => {
        listener({ matches: next } as MediaQueryListEvent)
      })
    }
  }
}

async function mountApp(hash = '#/calendar') {
  window.location.hash = hash
  const router = createAppRouter()
  const wrapper = mount(App, {
    global: {
      plugins: [router]
    }
  })
  await router.isReady()
  await flushPromises()
  await nextTick()
  return { wrapper, router }
}

describe('App shell + calendar home', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 8, 23, 12, 0, 0)) // Wed noon — in-band
    mockMatchMedia(false)
  })

  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('defaults to Calendar week with empty side-panel hint and theme control', async () => {
    const { wrapper, router } = await mountApp('#/')
    expect(router.currentRoute.value.name).toBe('calendar')
    expect(wrapper.find('.empty-hint').text()).toBe(EMPTY_HINT)
    expect(wrapper.find('[aria-label="Неделя"]').exists()).toBe(true)
    expect(wrapper.find('[role="radiogroup"][aria-label="Theme preference"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Календарь')
    expect(wrapper.text()).toContain('Неделя')
    const hourTexts = wrapper.findAll('.time-col .hour').map((h) => h.text())
    expect(hourTexts).toEqual(weekHourLabels())
    expect(hourTexts).toHaveLength(HOUR_END - HOUR_START)
    expect(hourTexts[0]).toBe('07:00')
    expect(hourTexts[hourTexts.length - 1]).toBe('20:00')
    wrapper.unmount()
  })

  it('stub routes are title-only without calendar panel; theme control remains', async () => {
    for (const [hash, title] of [
      ['#/plan', 'План'],
      ['#/progress', 'Прогресс']
    ] as const) {
      const { wrapper, router } = await mountApp(hash)
      expect(router.currentRoute.value.name).not.toBe('calendar')
      expect(wrapper.find('h1').text()).toBe(title)
      expect(wrapper.find('.panel').exists()).toBe(false)
      expect(wrapper.find('.empty-hint').exists()).toBe(false)
      expect(wrapper.find('[role="radiogroup"][aria-label="Theme preference"]').exists()).toBe(true)
      wrapper.unmount()
    }
  })

  it('Settings opens a full-screen sections shell (no calendar panel); theme control remains', async () => {
    const { wrapper, router } = await mountApp('#/settings')
    await flushPromises()
    expect(router.currentRoute.value.name).toBe('settings')
    expect(wrapper.find('[data-testid="settings-view"]').exists()).toBe(true)
    expect(wrapper.find('.panel').exists()).toBe(false)
    expect(wrapper.find('.empty-hint').exists()).toBe(false)
    expect(wrapper.find('[role="radiogroup"][aria-label="Theme preference"]').exists()).toBe(
      true
    )
    const kickers = wrapper.findAll('.kicker').map((k) => k.text())
    expect(kickers).toEqual([
      'TELEGRAM',
      'ГОЛОС',
      'РАСПИСАНИЕ И ДЛИТЕЛЬНОСТЬ',
      'ЦЕЛИ И АКЦЕНТЫ',
      'LLM / API'
    ])
    wrapper.unmount()
  })

  it('unknown hash redirects to Calendar', async () => {
    const { wrapper, router } = await mountApp('#/nope/unknown')
    expect(router.currentRoute.value.name).toBe('calendar')
    expect(wrapper.find('.empty-hint').exists()).toBe(true)
    wrapper.unmount()
  })

  it('grain switch shows empty month/week grids with Monday-first headers', async () => {
    const { wrapper } = await mountApp()
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
    const { wrapper } = await mountApp()
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
    const { wrapper } = await mountApp()
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
    const { wrapper } = await mountApp()
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
    const { wrapper } = await mountApp()
    expect(wrapper.findAll('.days .h.today')).toHaveLength(1)
    expect(wrapper.findAll('.day-col.today-col')).toHaveLength(1)
    expect(wrapper.find('[data-testid="now-line"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('month today shows pill + tint only (no now-line)', async () => {
    const { wrapper } = await mountApp()
    await wrapper.get('button.seg-btn:nth-child(2)').trigger('click')
    await nextTick()
    expect(wrapper.findAll('.month-cell.today')).toHaveLength(1)
    expect(wrapper.find('[data-testid="now-line"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('navigating away from today removes now-line and today-tint', async () => {
    const { wrapper } = await mountApp()
    await wrapper.get('button[aria-label="Вперёд"]').trigger('click')
    await nextTick()
    expect(wrapper.findAll('.days .h.today')).toHaveLength(0)
    expect(wrapper.findAll('.day-col.today-col')).toHaveLength(0)
    expect(wrapper.find('[data-testid="now-line"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('empty selection shows locked empty hint; grid has no fake events', async () => {
    const { wrapper } = await mountApp()
    expect(wrapper.find('.empty-hint').text()).toBe(EMPTY_HINT)
    expect(wrapper.findAll('.event').length).toBe(0)
    expect(wrapper.find('.panel').exists()).toBe(true)
    wrapper.unmount()
  })

  it('theme control works on Calendar and stubs', async () => {
    const { dispatch } = mockMatchMedia(true)
    const { wrapper } = await mountApp()
    const radios = wrapper.findAll('[role="radio"]')
    expect(radios).toHaveLength(3)

    await radios[1]!.trigger('click')
    expect(localStorage.getItem(STORAGE_KEY)).toBe('light')
    expect(document.documentElement.dataset.theme).toBe('light')
    expect(radios[1]!.attributes('aria-checked')).toBe('true')
    expect(radios[0]!.attributes('aria-checked')).toBe('false')
    expect(radios[2]!.attributes('aria-checked')).toBe('false')

    await wrapper.get('a.nav-link[href="#/settings"]').trigger('click')
    await flushPromises()
    await nextTick()
    expect(wrapper.find('h1').text()).toBe('Настройки')
    const stubRadios = wrapper.findAll('[role="radio"]')
    expect(stubRadios).toHaveLength(3)
    await stubRadios[2]!.trigger('click')
    expect(localStorage.getItem(STORAGE_KEY)).toBe('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')
    expect(stubRadios[2]!.attributes('aria-checked')).toBe('true')
    expect(stubRadios[0]!.attributes('aria-checked')).toBe('false')
    expect(stubRadios[1]!.attributes('aria-checked')).toBe('false')

    dispatch(false)
    await nextTick()
    expect(document.documentElement.dataset.theme).toBe('dark')
    wrapper.unmount()
  })

  it('now-line has no CSS transition/animation on top', async () => {
    const { wrapper } = await mountApp()
    const nowLine = wrapper.find('[data-testid="now-line"]')
    expect(nowLine.exists()).toBe(true)
    const el = nowLine.element as HTMLElement
    const cs = getComputedStyle(el)
    // Computed: fails if `transition: top …` is applied
    const transitionProps = cs.transitionProperty
      .split(',')
      .map((p) => p.trim().toLowerCase())
      .filter(Boolean)
    expect(transitionProps).not.toContain('top')
    expect(`${cs.transition} ${cs.transitionProperty}`).not.toMatch(/\btop\b/i)
    expect(cs.animationName === 'none' || cs.animationName === '' || cs.animationDuration === '0s').toBe(
      true
    )
    // Stylesheet: fails if a .now-line rule declares transition involving top
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
