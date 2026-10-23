import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { setLanguage, type SupportedLanguage } from '../../i18n'
import { apiFetch, tokenStore } from '../../lib/api'

export type UserRole = 'admin' | 'manager' | 'expert' | 'moqaddem'

export interface TerritorySummary {
  id: string
  name_ar: string
  name_fr: string
  level: string
}

export interface AuthUser {
  id: string
  fullName: string
  email: string
  role: UserRole
  preferredLanguage: SupportedLanguage
  territories: TerritorySummary[]
}

interface MeResponseDto {
  id: string
  full_name: string
  email: string
  role: UserRole
  preferred_language: SupportedLanguage
  territories: TerritorySummary[]
}

type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated'

interface AuthContextValue {
  status: AuthStatus
  user: AuthUser | null
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

function fromDto(dto: MeResponseDto): AuthUser {
  return {
    id: dto.id,
    fullName: dto.full_name,
    email: dto.email,
    role: dto.role,
    preferredLanguage: dto.preferred_language,
    territories: dto.territories,
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading')
  const [user, setUser] = useState<AuthUser | null>(null)

  const loadCurrentUser = useCallback(async () => {
    if (!tokenStore.getAccessToken()) {
      setStatus('unauthenticated')
      return
    }
    try {
      const dto = await apiFetch<MeResponseDto>('/auth/me')
      setUser(fromDto(dto))
      setStatus('authenticated')
    } catch {
      tokenStore.clear()
      setUser(null)
      setStatus('unauthenticated')
    }
  }, [])

  useEffect(() => {
    void loadCurrentUser()
  }, [loadCurrentUser])

  const login = useCallback(async (email: string, password: string) => {
    const tokens = await apiFetch<{ access_token: string; refresh_token: string }>('/auth/login', {
      method: 'POST',
      body: { email, password },
    })
    tokenStore.setTokens(tokens.access_token, tokens.refresh_token)
    const dto = await apiFetch<MeResponseDto>('/auth/me')
    const loggedInUser = fromDto(dto)
    setUser(loggedInUser)
    setStatus('authenticated')
    // The user's own saved preference wins on login, overriding whatever
    // language the login screen itself happened to be in — section 2.1:
    // "apps start in that [preferred] language".
    await setLanguage(loggedInUser.preferredLanguage)
  }, [])

  const logout = useCallback(async () => {
    const refreshToken = tokenStore.getRefreshToken()
    // Server call first, tokens cleared after: /auth/logout requires a
    // valid bearer token (`require_roles`), which apiFetch reads from
    // tokenStore — clearing first (as this originally did) sent the
    // request with no Authorization header and the backend rejected it
    // with 401 every time. Still best-effort: the user is logged out
    // locally regardless of whether the server-side revoke succeeds.
    if (refreshToken) {
      try {
        await apiFetch('/auth/logout', { method: 'POST', body: { refresh_token: refreshToken } })
      } catch {
        // Ignored — see above.
      }
    }
    tokenStore.clear()
    setUser(null)
    setStatus('unauthenticated')
  }, [])

  const value = useMemo<AuthContextValue>(() => ({ status, user, login, logout }), [status, user, login, logout])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within an AuthProvider')
  return context
}
