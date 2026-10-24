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

  // The page renders every user twice by design — a stacked card below
  // `sm`, a table row from `sm` up (same reasoning as ReportsListPage /
  // AuditLogPage) — so text and actions that appear once per user now
  // appear twice in the DOM; `getAllByText(...)[0]` stands in for
  // `getByText` throughout, and clicking either instance drives the same
  // shared state.

  it('lists users with their role, status, and last login', async () => {
    mockedApiFetch.mockResolvedValue({ items: [user()], total: 1, page: 1, page_size: 100 })

    renderPage()

    await waitFor(() => expect(screen.getAllByText('Expert Demo').length).toBeGreaterThan(0))
    expect(screen.getAllByText('نشط').length).toBeGreaterThan(0)
    expect(screen.getAllByText('خبير').length).toBeGreaterThan(0)
  })

  it('shows "never logged in" instead of a date when last_login_at is null', async () => {
    mockedApiFetch.mockResolvedValue({ items: [user({ last_login_at: null })], total: 1, page: 1, page_size: 100 })

    renderPage()

    await waitFor(() => expect(screen.getAllByText('لم يسجل الدخول بعد').length).toBeGreaterThan(0))
  })

  it('does not offer "deactivate" for an already-inactive user', async () => {
    mockedApiFetch.mockResolvedValue({ items: [user({ is_active: false })], total: 1, page: 1, page_size: 100 })

    renderPage()

    await waitFor(() => expect(screen.getAllByText('معطل').length).toBeGreaterThan(0))
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
    await waitFor(() => expect(screen.getAllByText('Expert Demo').length).toBeGreaterThan(0))

    // First click only arms the confirmation — no request yet.
    await userEventInstance.click(screen.getAllByText('إعادة تعيين كلمة المرور')[0])
    expect(mockedApiFetch).toHaveBeenCalledTimes(1) // only the initial list fetch
    await userEventInstance.click(screen.getAllByText('تأكيد')[0])

    await waitFor(() => expect(screen.getAllByText('Xk9-temp-pw').length).toBeGreaterThan(0))
  })

  it('does not call the API when the inline deactivate confirmation is cancelled', async () => {
    mockedApiFetch.mockResolvedValue({ items: [user()], total: 1, page: 1, page_size: 100 })
    const userEventInstance = userEvent.setup()

    renderPage()
    await waitFor(() => expect(screen.getAllByText('Expert Demo').length).toBeGreaterThan(0))
    mockedApiFetch.mockClear()

    await userEventInstance.click(screen.getAllByText('تعطيل')[0])
    await userEventInstance.click(screen.getAllByText('إلغاء')[0])

    expect(mockedApiFetch).not.toHaveBeenCalled()
  })
})
