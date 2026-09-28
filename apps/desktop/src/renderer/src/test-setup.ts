import { afterEach, beforeEach, vi } from 'vitest'

/**
 * Renderer-only default mocks for the teacher lifecycle preload bridge and
 * `fetch`, so specs that do not care about Settings/teacher wiring can still
 * mount views that call `window.teacher` / `fetch` on mount without throwing.
 * Guarded to no-op under the `node` environment used for `src/main/**` specs.
 */
if (typeof window !== 'undefined') {
  const defaultAuth = {
    state: 'running' as const,
    base_url: 'http://127.0.0.1:8765',
    bearer: 'test-bearer-token'
  }

  beforeEach(() => {
    Object.defineProperty(window, 'teacher', {
      configurable: true,
      value: {
        getAuth: vi.fn().mockResolvedValue({ ...defaultAuth }),
        retry: vi.fn().mockResolvedValue({ ...defaultAuth }),
        onStatusChange: vi.fn().mockReturnValue(() => undefined)
      }
    })

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ configured: false }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        })
      )
    )
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })
}
