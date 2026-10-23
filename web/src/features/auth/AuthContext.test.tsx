import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiFetch, tokenStore } from '../../lib/api'
import { AuthProvider, useAuth } from './AuthContext'

vi.mock('../../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../../lib/api')>('../../lib/api')
  return { ...actual, apiFetch: vi.fn() }
})

vi.mock('../../i18n', () => ({ setLanguage: vi.fn() }))

const mockedApiFetch = vi.mocked(apiFetch)

const ME_RESPONSE = {
  id: 'u1',
  full_name: 'Responsable Demo',
  email: 'manager@w4f.ma',
  role: 'manager',
  preferred_language: 'fr',
  territories: [],
}

function Probe() {
  const { status, user, login, logout } = useAuth()
  return (
    <div>
      <span data-testid="status">{status}</span>
      <span data-testid="name">{user?.fullName ?? ''}</span>
      <button onClick={() => void login('manager@w4f.ma', 'DemoPass1234')}>login</button>
      <button onClick={() => void logout()}>logout</button>
    </div>
  )
}

describe('AuthProvider', () => {
  beforeEach(() => {
    localStorage.clear()
    mockedApiFetch.mockReset()
  })

  it('starts unauthenticated when no token is stored', async () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    )

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('unauthenticated'))
  })

  it('becomes authenticated and exposes the user after a successful login', async () => {
    mockedApiFetch
      .mockResolvedValueOnce({ access_token: 'a1', refresh_token: 'r1' })
      .mockResolvedValueOnce(ME_RESPONSE)
    const user = userEvent.setup()

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    )
    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('unauthenticated'))

    await user.click(screen.getByText('login'))

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('authenticated'))
    expect(screen.getByTestId('name')).toHaveTextContent('Responsable Demo')
    expect(tokenStore.getAccessToken()).toBe('a1')
  })

  it('clears tokens and flips to unauthenticated on logout', async () => {
    mockedApiFetch
      .mockResolvedValueOnce({ access_token: 'a1', refresh_token: 'r1' })
      .mockResolvedValueOnce(ME_RESPONSE)
      .mockResolvedValueOnce({ ok: true })
    const user = userEvent.setup()

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    )
    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('unauthenticated'))
    await user.click(screen.getByText('login'))
    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('authenticated'))

    await user.click(screen.getByText('logout'))

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('unauthenticated'))
    expect(tokenStore.getAccessToken()).toBeNull()
  })

  it('clears a stale token and falls back to unauthenticated when /auth/me rejects it', async () => {
    tokenStore.setTokens('stale-access', 'stale-refresh')
    mockedApiFetch.mockRejectedValueOnce(new Error('401'))

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    )

    await waitFor(() => expect(screen.getByTestId('status')).toHaveTextContent('unauthenticated'))
    expect(tokenStore.getAccessToken()).toBeNull()
  })
})
