import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import i18n from '../../i18n'
import { apiFetch } from '../../lib/api'
import { AuditLogPage } from './AuditLogPage'

vi.mock('../../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../../lib/api')>('../../lib/api')
  return { ...actual, apiFetch: vi.fn() }
})

const mockedApiFetch = vi.mocked(apiFetch)

const USERS_LIST = {
  items: [{ id: 'u1', full_name: 'Admin Demo', email: 'admin@w4f.ma', phone: null, role: 'admin', preferred_language: 'ar', is_active: true, last_login_at: null, created_at: '2026-01-01T00:00:00Z' }],
  total: 1,
  page: 1,
  page_size: 100,
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <AuditLogPage />
    </QueryClientProvider>,
  )
}

describe('AuditLogPage', () => {
  beforeEach(() => {
    mockedApiFetch.mockReset()
    void i18n.changeLanguage('ar')
  })

  it('resolves a known actor to their name and falls back to "system" when there is none', async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path.startsWith('/audit')) {
        return Promise.resolve({
          items: [
            { id: 'a1', actor_id: 'u1', action: 'login', entity_type: 'user', entity_id: 'u1', old_value: null, new_value: null, ip: null, user_agent: null, created_at: '2026-10-20T08:00:00Z' },
            { id: 'a2', actor_id: null, action: 'login_failed', entity_type: 'user', entity_id: null, old_value: null, new_value: { email: 'unknown@w4f.ma' }, ip: null, user_agent: null, created_at: '2026-10-20T08:01:00Z' },
          ],
          total: 2,
          page: 1,
          page_size: 20,
        })
      }
      if (path.startsWith('/users')) return Promise.resolve(USERS_LIST)
      return Promise.reject(new Error(`unexpected path: ${path}`))
    })

    renderPage()

    // Rendered twice by design (a stacked card below `sm`, a table row
    // from `sm` up — see TableContainer's own comment).
    await waitFor(() => expect(screen.getAllByText('Admin Demo').length).toBeGreaterThan(0))
    expect(screen.getAllByText('النظام').length).toBeGreaterThan(0)
    // Scoped to table cells: "تسجيل دخول" also appears as a <select> option
    // and in the (sm:hidden) mobile card.
    expect(screen.getByRole('cell', { name: 'تسجيل دخول' })).toBeInTheDocument()
    expect(screen.getByRole('cell', { name: 'فشل تسجيل الدخول' })).toBeInTheDocument()
  })

  it('shows the empty-state message when there are no matching entries', async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path.startsWith('/audit')) return Promise.resolve({ items: [], total: 0, page: 1, page_size: 20 })
      if (path.startsWith('/users')) return Promise.resolve(USERS_LIST)
      return Promise.reject(new Error(`unexpected path: ${path}`))
    })

    renderPage()

    await waitFor(() => expect(screen.getByText('لا توجد سجلات مطابقة')).toBeInTheDocument())
  })
})
