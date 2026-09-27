import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import App from './App.vue'

const STORAGE_KEY = 'theme-preference'

type MediaListener = (event: MediaQueryListEvent) => void

function mockMatchMedia(matches: boolean): void {
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

  window.matchMedia = vi.fn().mockImplementation(() => {
    Object.defineProperty(media, 'matches', {
      configurable: true,
      get: () => current
    })
    return media
  })
}

describe('App theme chrome', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
    mockMatchMedia(true)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('clicking Light/Dark/System updates preference storage and dataset.theme', async () => {
    const wrapper = mount(App)
    await flushPromises()

    const radios = wrapper.findAll('[role="radio"]')
    expect(radios).toHaveLength(3)

    await radios[1]!.trigger('click')
    expect(localStorage.getItem(STORAGE_KEY)).toBe('light')
    expect(document.documentElement.dataset.theme).toBe('light')

    await radios[2]!.trigger('click')
    expect(localStorage.getItem(STORAGE_KEY)).toBe('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')

    await radios[0]!.trigger('click')
    expect(localStorage.getItem(STORAGE_KEY)).toBe('system')
    expect(document.documentElement.dataset.theme).toBe('dark')

    wrapper.unmount()
  })
})
