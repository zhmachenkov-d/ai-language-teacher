import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, nextTick } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { bootstrapTheme, useTheme, type ThemePreference } from './useTheme'

const STORAGE_KEY = 'theme-preference'

type MediaListener = (event: MediaQueryListEvent) => void

function mockMatchMedia(matches: boolean): {
  media: MediaQueryList
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

  window.matchMedia = vi.fn().mockImplementation(() => {
    Object.defineProperty(media, 'matches', {
      configurable: true,
      get: () => current
    })
    return media
  })

  return {
    media,
    dispatch: (next: boolean) => {
      current = next
      Array.from(listeners).forEach((listener) => {
        listener({ matches: next } as MediaQueryListEvent)
      })
    }
  }
}

function mountThemeHost() {
  const Host = defineComponent({
    setup() {
      return useTheme()
    },
    template: '<div />'
  })
  return mount(Host)
}

describe('theme preference matrix', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('fresh install: no stored preference → system follows OS', () => {
    mockMatchMedia(true)
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull()
    bootstrapTheme()
    expect(document.documentElement.dataset.theme).toBe('dark')

    mockMatchMedia(false)
    bootstrapTheme()
    expect(document.documentElement.dataset.theme).toBe('light')
  })

  it('bootstrapTheme applies stored light/dark without mount', () => {
    localStorage.setItem(STORAGE_KEY, 'light')
    mockMatchMedia(true)
    bootstrapTheme()
    expect(document.documentElement.dataset.theme).toBe('light')

    localStorage.setItem(STORAGE_KEY, 'dark')
    mockMatchMedia(false)
    bootstrapTheme()
    expect(document.documentElement.dataset.theme).toBe('dark')
  })

  it('manual light/dark persists under theme-preference and applies immediately', async () => {
    mockMatchMedia(true)
    const wrapper = mountThemeHost()
    const vm = wrapper.vm as unknown as {
      preference: ThemePreference
      setPreference: (next: ThemePreference) => void
    }

    vm.setPreference('light')
    await nextTick()
    expect(localStorage.getItem(STORAGE_KEY)).toBe('light')
    expect(document.documentElement.dataset.theme).toBe('light')

    vm.setPreference('dark')
    await nextTick()
    expect(localStorage.getItem(STORAGE_KEY)).toBe('dark')
    expect(document.documentElement.dataset.theme).toBe('dark')

    wrapper.unmount()
  })

  it('corrupt stored preference falls back to system', () => {
    localStorage.setItem(STORAGE_KEY, 'neon')
    mockMatchMedia(false)
    bootstrapTheme()
    expect(document.documentElement.dataset.theme).toBe('light')
  })

  it('OS theme change live-retokens when preference is system', async () => {
    localStorage.setItem(STORAGE_KEY, 'system')
    const { dispatch } = mockMatchMedia(false)
    const wrapper = mountThemeHost()
    await flushPromises()
    expect(document.documentElement.dataset.theme).toBe('light')

    dispatch(true)
    await nextTick()
    expect(document.documentElement.dataset.theme).toBe('dark')

    wrapper.unmount()
  })

  it('OS theme flips are ignored when preference is light or dark', async () => {
    const { dispatch } = mockMatchMedia(true)
    const wrapper = mountThemeHost()
    const vm = wrapper.vm as unknown as {
      setPreference: (next: ThemePreference) => void
    }
    await flushPromises()

    vm.setPreference('light')
    await nextTick()
    expect(document.documentElement.dataset.theme).toBe('light')

    dispatch(false)
    await nextTick()
    expect(document.documentElement.dataset.theme).toBe('light')

    dispatch(true)
    await nextTick()
    expect(document.documentElement.dataset.theme).toBe('light')

    vm.setPreference('dark')
    await nextTick()
    expect(document.documentElement.dataset.theme).toBe('dark')

    dispatch(false)
    await nextTick()
    expect(document.documentElement.dataset.theme).toBe('dark')

    wrapper.unmount()
  })

  it('switching back to system after manual override follows OS again', async () => {
    const { dispatch } = mockMatchMedia(true)
    const wrapper = mountThemeHost()
    const vm = wrapper.vm as unknown as {
      setPreference: (next: ThemePreference) => void
    }
    await flushPromises()

    vm.setPreference('light')
    await nextTick()
    expect(localStorage.getItem(STORAGE_KEY)).toBe('light')
    expect(document.documentElement.dataset.theme).toBe('light')

    dispatch(false)
    await nextTick()
    expect(document.documentElement.dataset.theme).toBe('light')

    vm.setPreference('system')
    await nextTick()
    expect(localStorage.getItem(STORAGE_KEY)).toBe('system')
    expect(document.documentElement.dataset.theme).toBe('light')

    dispatch(true)
    await nextTick()
    expect(document.documentElement.dataset.theme).toBe('dark')

    wrapper.unmount()
  })

  it('reduce-motion stylesheet zeros transition duration at runtime', () => {
    const css = readFileSync(resolve(__dirname, '../styles/tokens.css'), 'utf8')
    const reduceMatch = css.match(
      /@media\s*\(prefers-reduced-motion:\s*reduce\)\s*\{([\s\S]*)\}\s*$/
    )
    expect(reduceMatch).toBeTruthy()

    // happy-dom does not reliably honor prefers-reduced-motion for computed styles;
    // inject the media-query rule body so getComputedStyle can observe the override.
    const style = document.createElement('style')
    style.textContent = `
      .motion-probe {
        transition: background-color 160ms ease, color 160ms ease;
      }
      ${reduceMatch![1]}
    `
    document.head.appendChild(style)

    const el = document.createElement('div')
    el.className = 'motion-probe'
    document.body.appendChild(el)

    const duration = getComputedStyle(el).transitionDuration
    const seconds = Math.max(
      ...duration.split(',').map((part) => {
        const trimmed = part.trim()
        const n = parseFloat(trimmed)
        if (Number.isNaN(n)) return 0
        return trimmed.endsWith('ms') ? n / 1000 : n
      })
    )
    expect(seconds).toBeLessThan(0.001)

    el.remove()
    style.remove()
  })
})
