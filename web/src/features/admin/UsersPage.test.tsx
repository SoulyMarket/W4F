import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import i18n from '../../i18n'
import { apiFetch } from '../../lib/api'
import { UsersPage } from './UsersPage'
import type { UserDto } from './usersApi'

vi.mock('../../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../../lib/api')>('../../lib/api')
  return { ...actual, apiFetch: vi.fn() }
})

const mockedApiFetch = vi.mocked(apiFetch)

function user(overrides: Partial<UserDto> = {}): UserDto {
  return {
    id: 'u1',
    full_name: 'Expert Demo',
    email: 'expert@w4f.ma',
    phone: null,
    role: 'expert',
    preferred_language: 'ar',
    is_active: true,
    last_login_at: '2026-10-20T08:00:00Z',
    created_at: '2026-09-01T08:00:00Z',
    ...overrides,
  }
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <UsersPage />
    </QueryClientProvider>,
  )
}

describe('UsersPage', () => {
  beforeEach(() => {
    mockedApiFetch.mockReset()
    void i18n.changeLanguage('ar')
  })

  it('lists users with their role, status, and last login', async () => {
    mockedApiFetch.mockResolvedValue({ items: [user()], total: 1, page: 1, page_size: 100 })

    renderPage()

    await waitFor(() => expect(screen.getByText('Expert Demo')).toBeInTheDocument())
    expect(screen.getByText('نشط')).toBeInTheDocument()
    expect(screen.getByText('خبير')).toBeInTheDocument()
  })

  it('shows "never logged in" instead of a date when last_login_at is null', async () => {
    mockedApiFetch.mockResolvedValue({ items: [user({ last_login_at: null })], total: 1, page: 1, page_size: 100 })

    renderPage()

    await waitFor(() => expect(screen.getByText('لم يسجل الدخول بعد')).toBeInTheDocument())
  })

  it('does not offer "deactivate" for an already-inactive user', async () => {
    mockedApiFetch.mockResolvedValue({ items: [user({ is_active: false })], total: 1, page: 1, page_size: 100 })

    renderPage()

    await waitFor(() => expect(screen.getByText('معطل')).toBeInTheDocument())
    expect(screen.queryByText('تعطيل')).not.toBeInTheDocument()
  })

  it('shows the temporary password once the two-step confirm is completed', async () => {
    mockedApiFetch.mockImplementation((path: string, options?: { method?: string }) => {
      if (path === '/users?page_size=100') return Promise.resolve({ items: [user()], total: 1, page: 1, page_size: 100 })
      if (path === '/users/u1/reset-password' && options?.method === 'POST') {
        return Promise.resolve({ temporary_password: 'Xk9-temp-pw' })
      }
      return Promise.reject(new Error(`unexpected request: ${options?.method ?? 'GET'} ${path}`))
    })
    const userEventInstance = userEvent.setup()

    renderPage()
    await waitFor(() => expect(screen.getByText('Expert Demo')).toBeInTheDocument())

    // First click only arms the confirmation — no request yet.
    await userEventInstance.click(screen.getByText('إعادة تعيين كلمة المرور'))
    expect(mockedApiFetch).toHaveBeenCalledTimes(1) // only the initial list fetch
    await userEventInstance.click(screen.getByText('تأكيد'))

    await waitFor(() => expect(screen.getByText('Xk9-temp-pw')).toBeInTheDocument())
  })

  it('does not call the API when the inline deactivate confirmation is cancelled', async () => {
    mockedApiFetch.mockResolvedValue({ items: [user()], total: 1, page: 1, page_size: 100 })
    const userEventInstance = userEvent.setup()

    renderPage()
    await waitFor(() => expect(screen.getByText('Expert Demo')).toBeInTheDocument())
    mockedApiFetch.mockClear()

    await userEventInstance.click(screen.getByText('تعطيل'))
    await userEventInstance.click(screen.getByText('إلغاء'))

    expect(mockedApiFetch).not.toHaveBeenCalled()
  })
})
