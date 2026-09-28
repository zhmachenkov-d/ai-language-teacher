<script setup lang="ts">
import { useTheme, type ThemePreference } from "../composables/useTheme";

const { preference, setPreference } = useTheme();

const options: { value: ThemePreference; label: string }[] = [
  { value: "system", label: "Система" },
  { value: "light", label: "Светлая" },
  { value: "dark", label: "Тёмная" },
];
</script>

<template>
  <div class="theme-control" role="radiogroup" aria-label="Тема оформления">
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
</template>

<style scoped>
.theme-control {
  display: inline-flex;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-surface);
}

.theme-option {
  margin: 0;
  padding: 0.35rem 0.65rem;
  border: 0;
  border-right: 1px solid var(--color-line);
  background: transparent;
  color: var(--color-muted);
  font: inherit;
  font-size: 0.75rem;
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
</style>
