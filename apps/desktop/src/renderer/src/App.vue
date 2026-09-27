<script setup lang="ts">
import { useTheme, type ThemePreference } from './composables/useTheme'

const scaffold = typeof window !== 'undefined' && window.desktop ? window.desktop.scaffold : '—'
const { preference, setPreference } = useTheme()

const options: { value: ThemePreference; label: string }[] = [
  { value: 'system', label: 'System' },
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' }
]
</script>

<template>
  <main class="shell">
    <header class="chrome">
      <h1>AI Language Teacher</h1>
      <div class="theme-control" role="radiogroup" aria-label="Theme preference">
        <button
          v-for="option in options"
          :key="option.value"
          type="button"
          role="radio"
          class="theme-option"
          :aria-checked="preference === option.value"
          :class="{ active: preference === option.value }"
          @click="setPreference(option.value)"
        >
          {{ option.label }}
        </button>
      </div>
    </header>

    <section class="demo" aria-label="Design token samples">
      <p class="ink">
        Desktop scaffold (Story 1.1). Teacher service is not required to start this window.
      </p>
      <p class="muted">Muted secondary copy — cool grey chrome, coral as spark only.</p>
      <p class="meta">scaffold={{ scaffold }}</p>
      <div class="swatches" aria-hidden="true">
        <span class="swatch surface">surface</span>
        <span class="swatch line">line</span>
        <span class="swatch sidebar">sidebar</span>
        <span class="swatch today">today-tint</span>
      </div>
      <button type="button" class="cta">Sample CTA</button>
    </section>
  </main>
</template>

<style scoped>
.shell {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 2rem;
  background: var(--color-bg);
  color: var(--color-ink);
  font-family: var(--font-sans);
  transition:
    background-color 160ms ease,
    color 160ms ease;
}

.chrome {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-line);
}

h1 {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--color-ink);
}

.theme-control {
  display: inline-flex;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-surface);
}

.theme-option {
  margin: 0;
  padding: 0.4rem 0.75rem;
  border: 0;
  border-right: 1px solid var(--color-line);
  background: transparent;
  color: var(--color-muted);
  font: inherit;
  font-size: 0.875rem;
  cursor: pointer;
  transition:
    background-color 160ms ease,
    color 160ms ease;
}

.theme-option:last-child {
  border-right: 0;
}

.theme-option.active {
  background: var(--color-sidebar);
  color: var(--color-ink);
}

.theme-option:focus-visible {
  outline: 2px solid var(--color-coral);
  outline-offset: -2px;
  z-index: 1;
}

.demo {
  max-width: 36rem;
  padding: 1.25rem;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  transition:
    background-color 160ms ease,
    border-color 160ms ease;
}

.ink {
  margin: 0 0 0.5rem;
  line-height: 1.45;
  color: var(--color-ink);
}

.muted {
  margin: 0 0 0.5rem;
  line-height: 1.45;
  color: var(--color-muted);
}

.meta {
  margin: 0 0 1rem;
  font-size: 0.875rem;
  color: var(--color-muted);
}

.swatches {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.swatch {
  display: inline-flex;
  align-items: center;
  padding: 0.35rem 0.6rem;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  font-size: 0.75rem;
  color: var(--color-muted);
}

.swatch.surface {
  background: var(--color-surface);
}

.swatch.line {
  background: var(--color-bg);
  border-color: var(--color-line);
}

.swatch.sidebar {
  background: var(--color-sidebar);
}

.swatch.today {
  background: var(--color-today-tint);
}

.cta {
  margin: 0;
  padding: 0.5rem 1rem;
  border: 0;
  border-radius: var(--radius-md);
  background: var(--color-coral-cta);
  color: var(--color-on-coral);
  font: inherit;
  font-size: 0.875rem;
  cursor: pointer;
}

.cta:focus-visible {
  outline: 2px solid var(--color-ink);
  outline-offset: 2px;
}
</style>
