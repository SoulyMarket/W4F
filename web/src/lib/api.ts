// Mirrors the backend's error envelope (`backend/app/core/errors.py`):
// `{"error": {"code": "...", "message": "..."}}`, `code` stable/English,
// `message` already localized server-side via `Accept-Language`.
export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

const ACCESS_TOKEN_KEY = 'w4f_access_token'
const REFRESH_TOKEN_KEY = 'w4f_refresh_token'

// Known, documented limitation (see PROGRESS.md): the backend only issues
// bearer tokens in the JSON response body (`TokenPair`), not an httpOnly
// cookie, so there is nowhere else for a browser client to keep them that
// JS doesn't also have to read to attach the Authorization header. A
// production deployment would want the backend to set an httpOnly,
// SameSite cookie instead — out of scope for this prototype.
export const tokenStore = {
  getAccessToken: () => localStorage.getItem(ACCESS_TOKEN_KEY),
  getRefreshToken: () => localStorage.getItem(REFRESH_TOKEN_KEY),
  setTokens: (accessToken: string, refreshToken: string) => {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  },
  clear: () => {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  },
}

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

// Set by AuthProvider so apiFetch can read the active UI language without
// importing the i18n module directly (keeps this module dependency-free
// and easy to unit test) — the backend renders error messages, priority
// reasons and notification text in whatever `Accept-Language` says.
let currentLanguage = 'ar'
export function setApiLanguage(lang: string) {
  currentLanguage = lang
}

// Sync, not a Promise: every concurrent 401 during an in-flight refresh
// must wait for the *same* refresh rather than each firing their own
// (which would race on the backend's one-time-use refresh-token rotation
// and revoke every request but the first).
let refreshInFlight: Promise<string | null> | null = null

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = tokenStore.getRefreshToken()
  if (!refreshToken) return null

  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        })
        if (!response.ok) {
          tokenStore.clear()
          return null
        }
        const body = (await response.json()) as { access_token: string; refresh_token: string }
        tokenStore.setTokens(body.access_token, body.refresh_token)
        return body.access_token
      } catch {
        tokenStore.clear()
        return null
      } finally {
        refreshInFlight = null
      }
    })()
  }
  return refreshInFlight
}

interface ApiFetchOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
  /** Internal: prevents retrying a request that is itself a retry. */
  _isRetry?: boolean
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { body, _isRetry, headers, ...rest } = options
  const accessToken = tokenStore.getAccessToken()

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    // Every route here is per-user/territory-scoped and none of them set
    // a `Vary: Authorization` header, so a browser's own HTTP cache (keyed
    // on URL alone) can serve one signed-in user's cached GET response
    // back to a completely different user who later requests the same
    // URL — confirmed live (a manager's own /douars request came back
    // with another user's earlier empty result). The backend now also
    // sends `Cache-Control: no-store` on every response, but that can't
    // retroactively invalidate whatever a browser already cached before
    // this fix shipped — forcing it here too means this is safe
    // regardless of what's already sitting in any given browser's cache.
    cache: 'no-store',
    headers: {
      'Content-Type': 'application/json',
      'Accept-Language': currentLanguage,
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (response.status === 401 && accessToken && !_isRetry) {
    const newAccessToken = await refreshAccessToken()
    if (newAccessToken) {
      return apiFetch<T>(path, { ...options, _isRetry: true })
    }
  }

  if (!response.ok) {
    let code = 'unknown_error'
    let message = response.statusText
    try {
      const parsed = (await response.json()) as { error?: { code: string; message: string } }
      if (parsed.error) {
        code = parsed.error.code
        message = parsed.error.message
      }
    } catch {
      // Non-JSON error body (e.g. a proxy/5xx page) — fall back to status text.
    }
    throw new ApiError(response.status, code, message)
  }

  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}
