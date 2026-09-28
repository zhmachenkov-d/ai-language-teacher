<script setup lang="ts">
/**
 * Stub consent route for Story 2.2 handoff. Intake-complete learners land here;
 * calendar stays gated until the 2.6 climax.
 */
</script>

<template>
  <main class="consent-stub" data-testid="onboarding-consent-stub">
    <section class="surface">
      <span class="accent-rule" aria-hidden="true" />
      <h1>Согласие</h1>
      <p class="hint">
        Экран согласия появится в следующем шаге. Расписание уже сохранено —
        вернитесь позже, чтобы продолжить онбординг.
      </p>
    </section>
  </main>
</template>

<style scoped>
.consent-stub {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  min-height: 0;
  background: var(--color-bg);
  color: var(--color-ink);
  padding: 32px 20px 48px;
}

.surface {
  width: 100%;
  max-width: 520px;
  padding: 20px 22px 24px;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.accent-rule {
  display: block;
  width: 24px;
  height: 3px;
  background: var(--color-coral);
  border-radius: 2px;
}

h1 {
  margin: 0;
  font-size: 1.35rem;
  font-weight: 600;
}

.hint {
  margin: 0;
  font-size: 13px;
  line-height: 1.45;
  color: var(--color-muted);
}
</style>
