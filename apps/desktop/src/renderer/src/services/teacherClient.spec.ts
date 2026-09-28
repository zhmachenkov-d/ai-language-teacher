import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  fetchLlmConfigStatus,
  getTeacherAuth,
  saveLlmApiKey,
  TeacherApiError,
  type TeacherAuth
} from './teacherClient'

const RUNNING: TeacherAuth = {
  state: 'running',
  base_url: 'http://127.0.0.1:8765',
  bearer: 'tok-123'
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' }
  })
}

describe('teacherClient', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    // Restore whatever preload bridge the global test-setup installs.
    Object.defineProperty(window, 'teacher', {
      configurable: true,
      value: {
        getAuth: vi.fn().mockResolvedValue(RUNNING),
        retry: vi.fn().mockResolvedValue(RUNNING),
        onStatusChange: vi.fn().mockReturnValue(() => undefined)
      }
    })
  })

  it('getTeacherAuth reports an error state when the preload bridge is missing', async () => {
    // @ts-expect-error - simulate a missing preload bridge
    delete window.teacher
    const auth = await getTeacherAuth()
    expect(auth.state).toBe('error')
  })

  it('fetchLlmConfigStatus sends Bearer auth and parses configured status', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { configured: true }))
    vi.stubGlobal('fetch', fetchMock)
    const status = await fetchLlmConfigStatus(RUNNING)
    expect(status).toEqual({ configured: true })
    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8765/config/llm',
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer tok-123' })
      })
    )
  })

  it('surfaces a shaped TeacherApiError on non-2xx without throwing raw fetch errors', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(401, { code: 'unauthorized', message: 'no', retryable: false })
      )
    )
    await expect(fetchLlmConfigStatus(RUNNING)).rejects.toMatchObject({
      code: 'unauthorized',
      retryable: false,
      status: 401
    })
  })

  it('rejects with teacher_unavailable when auth state is not running (no silent call)', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    const stopped: TeacherAuth = { state: 'stopped', base_url: '', bearer: null }
    await expect(fetchLlmConfigStatus(stopped)).rejects.toBeInstanceOf(TeacherApiError)
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('saveLlmApiKey PUTs snake_case body and returns configured status', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { configured: true }))
    vi.stubGlobal('fetch', fetchMock)
    const status = await saveLlmApiKey(RUNNING, 'sk-abc')
    expect(status).toEqual({ configured: true })
    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(init.method).toBe('PUT')
    expect(init.body).toBe(JSON.stringify({ llm_api_key: 'sk-abc' }))
  })

  it('wraps a network failure as a retryable TeacherApiError', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('ECONNREFUSED')))
    await expect(saveLlmApiKey(RUNNING, 'sk-abc')).rejects.toMatchObject({
      code: 'network_error',
      retryable: true
    })
  })
})
