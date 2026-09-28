<script setup lang="ts">
import { RouterLink, RouterView, useRoute } from 'vue-router'
import ThemeControl from './components/ThemeControl.vue'

const route = useRoute()

const navItems = [
  { name: 'calendar', label: 'Календарь' },
  { name: 'plan', label: 'План' },
  { name: 'progress', label: 'Прогресс' },
  { name: 'settings', label: 'Настройки' }
] as const
</script>

<template>
  <div class="app-shell">
    <nav class="nav" aria-label="Основная навигация">
      <div class="brand">
        <span class="mark" aria-hidden="true" />
        <span class="brand-text">Учитель</span>
      </div>
      <RouterLink
        v-for="item in navItems"
        :key="item.name"
        :to="{ name: item.name }"
        class="nav-link"
        :class="{ active: route.name === item.name }"
        :aria-current="route.name === item.name ? 'page' : undefined"
      >
        {{ item.label }}
      </RouterLink>
      <div class="nav-footer">
        <ThemeControl />
      </div>
    </nav>
    <div class="content">
      <RouterView />
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  min-height: 100vh;
  box-sizing: border-box;
  background: var(--color-bg);
  color: var(--color-ink);
  font-family: var(--font-sans);
}

.nav {
  width: 168px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 14px 0;
  background: var(--color-sidebar);
  border-right: 1px solid var(--color-line);
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 2px 14px 16px;
  font-size: 13px;
  font-weight: 700;
  color: var(--color-ink);
}

.mark {
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-coral);
  border-radius: 9999px;
  position: relative;
  flex-shrink: 0;
  box-sizing: border-box;
}

.mark::after {
  content: '';
  position: absolute;
  left: 2px;
  right: 2px;
  top: 50%;
  border-top: 1px solid var(--color-coral);
}

.nav-link {
  display: block;
  padding: 8px 14px;
  color: var(--color-muted);
  text-decoration: none;
  font-size: 13px;
  border-left: 3px solid transparent;
}

.nav-link.active {
  color: var(--color-ink);
  font-weight: 600;
  background: var(--color-surface);
  border-left-color: var(--color-coral);
}

.nav-link:focus-visible {
  outline: 2px solid var(--color-coral);
  outline-offset: -2px;
  z-index: 1;
}

.nav-footer {
  margin-top: auto;
  padding: 14px;
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}
</style>
