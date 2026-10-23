import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, apiFetch, setApiLanguage, tokenStore } from './api'

// A minimal fetch Response stand-in, not a real `Response` — jsdom (this
// suite's test environment) doesn't implement the Fetch API globals, so
// constructing a real one isn't reliably available here.
function jsonResponse(status: number, body: unknown) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: '',
    json: async () => body,
  } as Response
}

describe('apiFetch', () => {
  beforeEach(() => {
    localStorage.clear()
    setApiLanguage('ar')
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('attaches the bearer token and language header when a token is stored', async () => {
    tokenStore.setTokens('access-1', 'refresh-1')
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    await apiFetch('/ping')

    const [, init] = fetchMock.mock.calls[0]
    const headers = init.headers as Record<string, string>
    expect(headers.Authorization).toBe('Bearer access-1')
    expect(headers['Accept-Language']).toBe('ar')
  })

  it('throws an ApiError with the server-provided code and localized message', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(403, { error: { code: 'account_inactive', message: 'الحساب معطل' } }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiFetch('/anything')).rejects.toMatchObject({
      status: 403,
      code: 'account_inactive',
      message: 'الحساب معطل',
    })
  })

  it('refreshes the access token once on a 401 and retries the original request', async () => {
    tokenStore.setTokens('expired-access', 'refresh-1')
    const fetchMock = vi
      .fn()
      // Original request: rejected as expired.
      .mockResolvedValueOnce(jsonResponse(401, { error: { code: 'token_expired', message: 'expired' } }))
      // Refresh call succeeds with a new pair.
      .mockResolvedValueOnce(jsonResponse(200, { access_token: 'fresh-access', refresh_token: 'fresh-refresh' }))
      // Retried original request succeeds.
      .mockResolvedValueOnce(jsonResponse(200, { data: 'ok' }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await apiFetch<{ data: string }>('/protected')

    expect(result).toEqual({ data: 'ok' })
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(tokenStore.getAccessToken()).toBe('fresh-access')
    const retryHeaders = fetchMock.mock.calls[2][1].headers as Record<string, string>
    expect(retryHeaders.Authorization).toBe('Bearer fresh-access')
  })

  it('clears tokens and surfaces the 401 when the refresh itself fails', async () => {
    tokenStore.setTokens('expired-access', 'dead-refresh')
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse(401, { error: { code: 'token_expired', message: 'expired' } }))
      .mockResolvedValueOnce(jsonResponse(401, { error: { code: 'refresh_token_invalid', message: 'invalid' } }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiFetch('/protected')).rejects.toBeInstanceOf(ApiError)
    expect(tokenStore.getAccessToken()).toBeNull()
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('does not attempt a second refresh for a request that is already a retry', async () => {
    tokenStore.setTokens('expired-access', 'refresh-1')
    // Every call returns 401 — if the retry guard didn't work this would
    // recurse indefinitely instead of failing after exactly 2 calls.
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(401, { error: { code: 'token_expired', message: 'expired' } }))
    vi.stubGlobal('fetch', fetchMock)

    await expect(apiFetch('/protected')).rejects.toBeInstanceOf(ApiError)
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})
