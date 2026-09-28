import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@renderer': resolve(__dirname, 'src/renderer/src')
    }
  },
  test: {
    environment: 'happy-dom',
    environmentMatchGlobs: [['src/main/**/*.spec.ts', 'node']],
    setupFiles: ['src/renderer/src/test-setup.ts'],
    include: ['src/renderer/src/**/*.spec.ts', 'src/main/**/*.spec.ts']
  }
})
