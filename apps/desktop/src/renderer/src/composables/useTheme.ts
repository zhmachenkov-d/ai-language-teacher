import { onMounted, onUnmounted, ref, watch, type Ref } from 'vue'

export type ThemePreference = 'system' | 'light' | 'dark'
export type EffectiveTheme = 'light' | 'dark'

const STORAGE_KEY = 'theme-preference'
const MEDIA_QUERY = '(prefers-color-scheme: dark)'

function isThemePreference(value: string | null): value is ThemePreference {
  return value === 'system' || value === 'light' || value === 'dark'
}

function readStoredPreference(): ThemePreference {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return isThemePreference(raw) ? raw : 'system'
  } catch {
    return 'system'
  }
}

function persistPreference(preference: ThemePreference): void {
  try {
    localStorage.setItem(STORAGE_KEY, preference)
  } catch {
    // UI chrome only — ignore quota / private-mode failures
  }
}

function osPrefersDark(): boolean {
  return window.matchMedia(MEDIA_QUERY).matches
}

function resolveEffective(preference: ThemePreference): EffectiveTheme {
  if (preference === 'light' || preference === 'dark') {
    return preference
  }
  return osPrefersDark() ? 'dark' : 'light'
}

function applyTheme(theme: EffectiveTheme): void {
  document.documentElement.dataset.theme = theme
}

/** Apply stored/OS theme before Vue mounts to avoid a light-flash on dark preference. */
export function bootstrapTheme(): void {
  applyTheme(resolveEffective(readStoredPreference()))
}

export function useTheme(): {
  preference: Ref<ThemePreference>
  effective: Ref<EffectiveTheme>
  setPreference: (next: ThemePreference) => void
} {
  const preference = ref<ThemePreference>(readStoredPreference())
  const effective = ref<EffectiveTheme>(resolveEffective(preference.value))

  const sync = (): void => {
    const next = resolveEffective(preference.value)
    effective.value = next
    applyTheme(next)
  }

  const setPreference = (next: ThemePreference): void => {
    preference.value = next
    persistPreference(next)
    sync()
  }

  let media: MediaQueryList | null = null
  const onMediaChange = (): void => {
    if (preference.value === 'system') {
      sync()
    }
  }

  // Apply before first paint so stored preference / OS theme take effect without a flash.
  sync()

  onMounted(() => {
    media = window.matchMedia(MEDIA_QUERY)
    media.addEventListener('change', onMediaChange)
  })

  onUnmounted(() => {
    media?.removeEventListener('change', onMediaChange)
  })

  watch(preference, () => {
    sync()
  })

  return { preference, effective, setPreference }
}
