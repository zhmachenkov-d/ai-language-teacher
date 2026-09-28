import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import App from './App.vue'
import { createAppRouter, setGateLearnerOverride } from './router'
import type { LearnerProfile } from './services/teacherClient'

const STORAGE_KEY = 'theme-preference'

const BASE_LEARNER: LearnerProfile = {
  id: 'learner-1',
  target_language: 'en',
  l1: 'ru',
  timezone: 'UTC',
  address_as: null,
  age: null,
  goals: [],
  desired_outcome: [],
  interests: [],
  emphasis: [],
  lesson_duration_minutes: null,
  weekly_slots: [],
  intake_step: 'greeting',
  consent_mic: false,
  consent_telegram: false,
  consent_ai: false,
  consent_privacy: false,
  consent_complete: false,
  placement_stage: 'briefing',
  placement_items: null,
  placement_written_answers: [],
  placement_written_score: null,
  placement_listening_generated: false,
  placement_listening_played: false,
  placement_listening_answers: [],
  placement_listening_score: null,
  placement_speaking_transcript: null,
  placement_speaking_score: null,
  placement_complete: false,
}

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

async function mountApp(
  hash = '#/',
  learner: LearnerProfile | null = { ...BASE_LEARNER, intake_step: 'greeting' },
) {
  setGateLearnerOverride(learner)
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

describe('App shell + onboarding GATE', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
    mockMatchMedia(false)
    setGateLearnerOverride(undefined)
    // Wizard/consent load still hits teacherClient; keep bridge present.
    Object.defineProperty(window, 'teacher', {
      configurable: true,
      value: {
        getAuth: vi.fn().mockResolvedValue({
          state: 'running',
          base_url: 'http://127.0.0.1:8765',
          bearer: 'tok',
        }),
        retry: vi.fn(),
        onStatusChange: vi.fn().mockReturnValue(() => undefined),
      },
    })
    Object.defineProperty(window, 'desktop', {
      configurable: true,
      value: {
        scaffold: '1.1',
        quit: vi.fn().mockResolvedValue(undefined),
      },
    })
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(BASE_LEARNER), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )
  })

  afterEach(() => {
    setGateLearnerOverride(undefined)
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('first launch with incomplete intake opens wizard (not calendar)', async () => {
    const { wrapper, router } = await mountApp('#/')
    expect(router.currentRoute.value.name).toBe('onboarding')
    expect(wrapper.find('[data-testid="onboarding-wizard"]').exists()).toBe(true)
    expect(wrapper.find('nav.nav').exists()).toBe(false)
    expect(wrapper.find('.empty-hint').exists()).toBe(false)
    wrapper.unmount()
  })

  it('calendar and / navigate to wizard while intake incomplete', async () => {
    const { wrapper, router } = await mountApp('#/calendar')
    expect(router.currentRoute.value.name).toBe('onboarding')
    wrapper.unmount()
  })

  it('intake complete + consent pending opens consent, not calendar', async () => {
    const { wrapper, router } = await mountApp('#/', {
      ...BASE_LEARNER,
      intake_step: 'complete',
      address_as: 'Саша',
      age: 30,
    })
    expect(router.currentRoute.value.name).toBe('onboarding-consent')
    expect(wrapper.find('[data-testid="onboarding-consent"]').exists()).toBe(true)
    expect(wrapper.find('nav.nav').exists()).toBe(false)
    wrapper.unmount()
  })

  it('consent_complete opens placement stub, not calendar', async () => {
    const { wrapper, router } = await mountApp('#/', {
      ...BASE_LEARNER,
      intake_step: 'complete',
      address_as: 'Саша',
      age: 30,
      consent_mic: true,
      consent_ai: true,
      consent_privacy: true,
      consent_complete: true,
    })
    expect(router.currentRoute.value.name).toBe('onboarding-placement')
    expect(wrapper.find('[data-testid="onboarding-placement"]').exists()).toBe(
      true,
    )
    expect(wrapper.find('nav.nav').exists()).toBe(false)
    wrapper.unmount()
  })

  it('RESUME: #/onboarding/consent with consent_complete → placement', async () => {
    const { wrapper, router } = await mountApp('#/onboarding/consent', {
      ...BASE_LEARNER,
      intake_step: 'complete',
      address_as: 'Саша',
      age: 30,
      consent_complete: true,
    })
    expect(router.currentRoute.value.name).toBe('onboarding-placement')
    expect(wrapper.find('[data-testid="onboarding-placement"]').exists()).toBe(
      true,
    )
    wrapper.unmount()
  })

  it('RESUME: #/onboarding with consent_complete → placement', async () => {
    const { wrapper, router } = await mountApp('#/onboarding', {
      ...BASE_LEARNER,
      intake_step: 'complete',
      address_as: 'Саша',
      age: 30,
      consent_complete: true,
    })
    expect(router.currentRoute.value.name).toBe('onboarding-placement')
    expect(wrapper.find('[data-testid="onboarding-placement"]').exists()).toBe(
      true,
    )
    wrapper.unmount()
  })

  it('calendar and / navigate to placement when consent_complete', async () => {
    const { wrapper, router } = await mountApp('#/calendar', {
      ...BASE_LEARNER,
      intake_step: 'complete',
      address_as: 'Саша',
      age: 30,
      consent_complete: true,
    })
    expect(router.currentRoute.value.name).toBe('onboarding-placement')
    wrapper.unmount()
  })

  it('placement_complete opens plan stub, not calendar', async () => {
    const { wrapper, router } = await mountApp('#/', {
      ...BASE_LEARNER,
      intake_step: 'complete',
      address_as: 'Саша',
      age: 30,
      consent_complete: true,
      placement_complete: true,
    })
    expect(router.currentRoute.value.name).toBe('onboarding-plan')
    expect(wrapper.find('[data-testid="onboarding-plan-stub"]').exists()).toBe(true)
    expect(wrapper.find('nav.nav').exists()).toBe(false)
    wrapper.unmount()
  })

  it('RESUME: #/onboarding/placement with placement_complete → plan stub', async () => {
    const { wrapper, router } = await mountApp('#/onboarding/placement', {
      ...BASE_LEARNER,
      intake_step: 'complete',
      address_as: 'Саша',
      age: 30,
      consent_complete: true,
      placement_complete: true,
    })
    expect(router.currentRoute.value.name).toBe('onboarding-plan')
    expect(wrapper.find('[data-testid="onboarding-plan-stub"]').exists()).toBe(true)
    wrapper.unmount()
  })

  it('calendar and / navigate to plan stub when placement_complete', async () => {
    const { wrapper, router } = await mountApp('#/calendar', {
      ...BASE_LEARNER,
      intake_step: 'complete',
      address_as: 'Саша',
      age: 30,
      consent_complete: true,
      placement_complete: true,
    })
    expect(router.currentRoute.value.name).toBe('onboarding-plan')
    wrapper.unmount()
  })

  it('null learner on placement fails closed to onboarding', async () => {
    const { wrapper, router } = await mountApp('#/onboarding/placement', null)
    expect(router.currentRoute.value.name).toBe('onboarding')
    wrapper.unmount()
  })

  it('mid-wizard resume lands on onboarding when intake_step is goals', async () => {
    const { wrapper, router } = await mountApp('#/calendar', {
      ...BASE_LEARNER,
      intake_step: 'goals',
      address_as: 'Алекс',
      age: 25,
    })
    expect(router.currentRoute.value.name).toBe('onboarding')
    expect(wrapper.find('[data-testid="onboarding-wizard"]').exists()).toBe(true)
    wrapper.unmount()
  })

  it('teacher unavailable on gated route fails toward wizard', async () => {
    const { wrapper, router } = await mountApp('#/', null)
    expect(router.currentRoute.value.name).toBe('onboarding')
    wrapper.unmount()
  })

  it('Settings remains reachable while gated; theme control works', async () => {
    const { dispatch } = mockMatchMedia(true)
    const { wrapper, router } = await mountApp('#/settings', {
      ...BASE_LEARNER,
      intake_step: 'greeting',
    })
    await flushPromises()
    expect(router.currentRoute.value.name).toBe('settings')
    expect(wrapper.find('[data-testid="settings-view"]').exists()).toBe(true)
    expect(wrapper.find('nav.nav').exists()).toBe(true)

    const radios = wrapper.findAll('[role="radio"]')
    expect(radios.map((r) => r.text())).toEqual(['Система', 'Светлая', 'Тёмная'])
    await radios[1]!.trigger('click')
    expect(localStorage.getItem(STORAGE_KEY)).toBe('light')
    expect(document.documentElement.dataset.theme).toBe('light')

    dispatch(false)
    await nextTick()
    expect(document.documentElement.dataset.theme).toBe('light')
    wrapper.unmount()
  })

  it('stub routes are title-only without calendar panel', async () => {
    for (const [hash, title] of [
      ['#/plan', 'План'],
      ['#/progress', 'Прогресс']
    ] as const) {
      const { wrapper, router } = await mountApp(hash)
      expect(router.currentRoute.value.name).not.toBe('calendar')
      expect(wrapper.find('h1').text()).toBe(title)
      expect(wrapper.find('.panel').exists()).toBe(false)
      wrapper.unmount()
    }
  })

  it('unknown hash is gated away from calendar-as-onboarded', async () => {
    const { wrapper, router } = await mountApp('#/nope/unknown')
    expect(router.currentRoute.value.name).toBe('onboarding')
    wrapper.unmount()
  })

  it('incomplete learner on consent redirects to onboarding', async () => {
    const { wrapper, router } = await mountApp('#/onboarding/consent', {
      ...BASE_LEARNER,
      intake_step: 'goals',
      address_as: 'Алекс',
      age: 25,
    })
    expect(router.currentRoute.value.name).toBe('onboarding')
    expect(wrapper.find('[data-testid="onboarding-wizard"]').exists()).toBe(true)
    wrapper.unmount()
  })

  it('null learner on consent fails closed to onboarding', async () => {
    const { wrapper, router } = await mountApp('#/onboarding/consent', null)
    expect(router.currentRoute.value.name).toBe('onboarding')
    wrapper.unmount()
  })

  it('production GATE fetch: incomplete intake → onboarding', async () => {
    setGateLearnerOverride(undefined)
    const getAuth = vi.fn().mockResolvedValue({
      state: 'running',
      base_url: 'http://127.0.0.1:8765',
      bearer: 'tok',
    })
    Object.defineProperty(window, 'teacher', {
      configurable: true,
      value: {
        getAuth,
        retry: vi.fn(),
        onStatusChange: vi.fn().mockReturnValue(() => undefined),
      },
    })
    const incomplete = { ...BASE_LEARNER, intake_step: 'greeting' as const }
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(JSON.stringify(incomplete), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )
    vi.stubGlobal('fetch', fetchMock)
    window.location.hash = '#/'
    const router = createAppRouter()
    const wrapper = mount(App, { global: { plugins: [router] } })
    await router.isReady()
    await flushPromises()
    await nextTick()
    expect(getAuth).toHaveBeenCalled()
    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8765/learner',
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer tok' }),
      }),
    )
    expect(router.currentRoute.value.name).toBe('onboarding')
    wrapper.unmount()
  })

  it('production GATE fetch: complete intake → consent', async () => {
    setGateLearnerOverride(undefined)
    const getAuth = vi.fn().mockResolvedValue({
      state: 'running',
      base_url: 'http://127.0.0.1:8765',
      bearer: 'tok',
    })
    Object.defineProperty(window, 'teacher', {
      configurable: true,
      value: {
        getAuth,
        retry: vi.fn(),
        onStatusChange: vi.fn().mockReturnValue(() => undefined),
      },
    })
    const complete = {
      ...BASE_LEARNER,
      intake_step: 'complete' as const,
      address_as: 'Саша',
      age: 30,
    }
    const fetchMock = vi.fn().mockImplementation(() =>
      Promise.resolve(
        new Response(JSON.stringify(complete), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )
    vi.stubGlobal('fetch', fetchMock)
    window.location.hash = '#/'
    const router = createAppRouter()
    const wrapper = mount(App, { global: { plugins: [router] } })
    await router.isReady()
    await flushPromises()
    await nextTick()
    expect(getAuth).toHaveBeenCalled()
    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8765/learner',
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer tok' }),
      }),
    )
    expect(router.currentRoute.value.name).toBe('onboarding-consent')
    expect(wrapper.find('[data-testid="onboarding-consent"]').exists()).toBe(true)
    wrapper.unmount()
  })
})
