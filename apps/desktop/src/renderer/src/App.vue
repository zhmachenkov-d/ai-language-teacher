<script setup lang="ts">
const scaffold = typeof window !== 'undefined' && window.desktop ? window.desktop.scaffold : '—'
</script>

<template>
  <main class="placeholder">
    <h1>AI Language Teacher</h1>
    <p>Desktop scaffold (Story 1.1). Teacher service is not required to start this window.</p>
    <p class="meta">scaffold={{ scaffold }}</p>
  </main>
</template>

<style>
:root {
  color-scheme: light;
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  color: #1c1c1e;
  background: #f2f2f7;
}

body {
  margin: 0;
}

.placeholder {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 3rem 2rem;
}

h1 {
  margin: 0 0 0.75rem;
  font-size: 1.75rem;
  font-weight: 600;
}

p {
  margin: 0 0 0.5rem;
  max-width: 36rem;
  line-height: 1.45;
  color: #3a3a3c;
}

.meta {
  font-size: 0.875rem;
  color: #6c6c70;
}
</style>
