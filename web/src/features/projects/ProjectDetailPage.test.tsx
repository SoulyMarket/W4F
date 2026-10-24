import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '../auth/AuthContext'
import i18n from '../../i18n'
import { apiFetch } from '../../lib/api'
import { ProjectDetailPage } from './ProjectDetailPage'
import type { ProjectDetailDto } from './projectsApi'

vi.mock('../../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../../lib/api')>('../../lib/api')
  return { ...actual, apiFetch: vi.fn() }
})

const mockedApiFetch = vi.mocked(apiFetch)

const DOUAR_LIST = {
  items: [{ id: 'd1', name_ar: 'دوار الأمل', name_fr: 'Douar Al Amal', commune_id: 'c1', lat: null, lon: null, population: null, families_count: null, notes: null }],
  total: 1,
  page: 1,
  page_size: 100,
}

const MANAGER_ME = {
  id: 'u1',
  full_name: 'Responsable Demo',
  email: 'manager@w4f.ma',
  role: 'manager',
  preferred_language: 'ar',
  territories: [],
}

function detail(overrides: Partial<ProjectDetailDto> = {}): ProjectDetailDto {
  return {
    id: 'p1',
    report_id: 'r1',
    douar_id: 'd1',
    title: 'إصلاح القناة الرئيسية',
    solution_type: 'pipe_repair',
    description: null,
    status: 'in_study',
    owner_id: 'u1',
    planned_start: null,
    planned_end: null,
    actual_start: null,
    actual_end: null,
    progress_percent: 20,
    created_at: '2026-10-01T10:00:00Z',
    updates: [],
    ...overrides,
  }
}

function renderPage(projectId = 'p1') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/projects/${projectId}`]}>
        <AuthProvider>
          <Routes>
            <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ProjectDetailPage', () => {
  beforeEach(() => {
    mockedApiFetch.mockReset()
    void i18n.changeLanguage('ar')
    localStorage.clear()
  })

  it('renders the douar name, progress, and empty updates state for an unauthenticated viewer', async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path.startsWith('/projects/')) return Promise.resolve(detail())
      if (path.startsWith('/douars')) return Promise.resolve(DOUAR_LIST)
      return Promise.reject(new Error(`unexpected path: ${path}`))
    })

    renderPage()

    await waitFor(() => expect(screen.getByText('دوار الأمل')).toBeInTheDocument())
    expect(screen.getByText('لا توجد تحديثات بعد')).toBeInTheDocument()
    // Not a manager (no session) — the status-change form must not render.
    expect(screen.queryByText('تحديث الحالة')).not.toBeInTheDocument()
  })

  it('shows the status-change form for a manager, limited to the allowed transitions', async () => {
    localStorage.setItem('w4f_access_token', 'manager-token')
    localStorage.setItem('w4f_refresh_token', 'manager-refresh')
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === '/auth/me') return Promise.resolve(MANAGER_ME)
      if (path.startsWith('/projects/')) return Promise.resolve(detail({ status: 'in_study' }))
      if (path.startsWith('/douars')) return Promise.resolve(DOUAR_LIST)
      return Promise.reject(new Error(`unexpected path: ${path}`))
    })

    renderPage()

    await waitFor(() => expect(screen.getByText('تحديث الحالة')).toBeInTheDocument())
    // in_study's only allowed transitions are approved/cancelled.
    expect(screen.getByRole('option', { name: 'تمت الموافقة' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'ملغى' })).toBeInTheDocument()
    expect(screen.queryByRole('option', { name: 'قيد الإنجاز' })).not.toBeInTheDocument()
  })

  it('shows the no-transitions message once a project is completed', async () => {
    localStorage.setItem('w4f_access_token', 'manager-token')
    localStorage.setItem('w4f_refresh_token', 'manager-refresh')
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === '/auth/me') return Promise.resolve(MANAGER_ME)
      if (path.startsWith('/projects/')) return Promise.resolve(detail({ status: 'completed', progress_percent: 100 }))
      if (path.startsWith('/douars')) return Promise.resolve(DOUAR_LIST)
      return Promise.reject(new Error(`unexpected path: ${path}`))
    })

    renderPage()

    await waitFor(() =>
      expect(screen.getByText('لا يمكن تغيير الحالة بعد وصول المشروع إلى هذه المرحلة')).toBeInTheDocument(),
    )
  })

  it('submits a status update and reflects the new status after refetch', async () => {
    localStorage.setItem('w4f_access_token', 'manager-token')
    localStorage.setItem('w4f_refresh_token', 'manager-refresh')
    let currentStatus = 'in_study'
    mockedApiFetch.mockImplementation((path: string, options?: { method?: string }) => {
      if (path === '/auth/me') return Promise.resolve(MANAGER_ME)
      if (path.startsWith('/douars')) return Promise.resolve(DOUAR_LIST)
      if (path === '/projects/p1/updates' && options?.method === 'POST') {
        currentStatus = 'approved'
        return Promise.resolve({ id: 'u1', project_id: 'p1', author_id: 'u1', old_status: 'in_study', new_status: 'approved', progress_percent: 30, note: null, created_at: '2026-10-24T10:00:00Z' })
      }
      if (path === '/projects/p1') return Promise.resolve(detail({ status: currentStatus, progress_percent: currentStatus === 'approved' ? 30 : 20 }))
      return Promise.reject(new Error(`unexpected request: ${options?.method ?? 'GET'} ${path}`))
    })
    const user = userEvent.setup()

    renderPage()
    await waitFor(() => expect(screen.getByText('تحديث الحالة')).toBeInTheDocument())

    await user.selectOptions(screen.getByLabelText('الحالة الجديدة'), 'approved')
    await user.click(screen.getByRole('button', { name: 'تحديث' }))

    await waitFor(() => expect(screen.getByText('تم تحديث المشروع')).toBeInTheDocument())
    expect(mockedApiFetch).toHaveBeenCalledWith('/projects/p1/updates', expect.objectContaining({ method: 'POST' }))
  })
})
