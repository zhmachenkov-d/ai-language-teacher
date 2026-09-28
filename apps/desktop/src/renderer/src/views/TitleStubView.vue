<script setup lang="ts">
defineProps<{
  title: string
}>()
</script>

<template>
  <main class="stub" :aria-label="title">
    <h1>{{ title }}</h1>
  </main>
</template>

<style scoped>
.stub {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 0;
  background: var(--color-bg);
  color: var(--color-ink);
}

h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}
</style>
