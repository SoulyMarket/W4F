import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthProvider } from '../auth/AuthContext'
import i18n from '../../i18n'
import { apiFetch } from '../../lib/api'
import { ReportDetailPage } from './ReportDetailPage'
import type { ReportDetailDto } from './reportsApi'

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

function detail(overrides: Partial<ReportDetailDto> = {}): ReportDetailDto {
  return {
    id: 'r1',
    douar_id: 'd1',
    moqaddem_id: 'm1',
    water_source: 'well',
    problem_type: 'no_water',
    problem_started_on: '2026-01-05',
    duration_days: 10,
    interruption_frequency: 'daily',
    has_alternative_source: true,
    alternative_distance_km: 3.5,
    severity_reported: 'high',
    water_quality_risk: false,
    affected_families: 5,
    affected_people: 20,
    observations: 'تلوث واضح في الماء',
    lat: null,
    lon: null,
    location_accuracy_m: null,
    collected_at: '2026-01-06T10:00:00Z',
    synced_at: '2026-01-06T10:05:00Z',
    status: 'validated',
    version: 2,
    score: 85,
    media: [],
    priority: {
      score: 85,
      breakdown: [
        {
          criterion: 'severity',
          value: 'high',
          weight: 0.3,
          points: 25.5,
          reason_key: 'priority.severity',
          reason_params: {},
          reason: 'درجة خطورة مرتفعة',
        },
      ],
      computed_at: '2026-01-06T12:00:00Z',
    },
    validations: [],
    ...overrides,
  }
}

function renderPage(reportId = 'r1') {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/reports/${reportId}`]}>
        <AuthProvider>
          <Routes>
            <Route path="/reports/:reportId" element={<ReportDetailPage />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ReportDetailPage', () => {
  beforeEach(() => {
    mockedApiFetch.mockReset()
    void i18n.changeLanguage('ar')
  })

  it('renders the douar name, priority breakdown reason, and empty states', async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path.startsWith('/reports/')) return Promise.resolve(detail())
      if (path.startsWith('/douars')) return Promise.resolve(DOUAR_LIST)
      return Promise.reject(new Error(`unexpected path: ${path}`))
    })

    renderPage()

    await waitFor(() => expect(screen.getByText('دوار الأمل')).toBeInTheDocument())
    expect(screen.getByText('85')).toBeInTheDocument()
    expect(screen.getByText('درجة خطورة مرتفعة')).toBeInTheDocument()
    expect(screen.getByText('لا توجد وسائط مرفقة')).toBeInTheDocument()
    expect(screen.getByText('لا يوجد سجل تحقق بعد')).toBeInTheDocument()
  })

  it('shows the no-priority message when the report has not been scored yet', async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path.startsWith('/reports/')) return Promise.resolve(detail({ priority: null }))
      if (path.startsWith('/douars')) return Promise.resolve(DOUAR_LIST)
      return Promise.reject(new Error(`unexpected path: ${path}`))
    })

    renderPage()

    await waitFor(() => expect(screen.getByText('لم يتم احتساب الأولوية بعد')).toBeInTheDocument())
  })

  it('shows a retry affordance on failure', async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path.startsWith('/reports/')) return Promise.reject(new Error('network down'))
      if (path.startsWith('/douars')) return Promise.resolve(DOUAR_LIST)
      return Promise.reject(new Error(`unexpected path: ${path}`))
    })

    renderPage()

    await waitFor(() => expect(screen.getByText('تعذر تحميل تفاصيل البلاغ')).toBeInTheDocument())
    expect(screen.getByRole('button', { name: 'إعادة المحاولة' })).toBeInTheDocument()
  })
})

const EXPERT_ME = {
  id: 'u2',
  full_name: 'Expert Demo',
  email: 'expert@w4f.ma',
  role: 'expert',
  preferred_language: 'ar',
  territories: [],
}

describe('ReportDetailPage — expert validation form', () => {
  beforeEach(() => {
    mockedApiFetch.mockReset()
    void i18n.changeLanguage('ar')
    localStorage.clear()
    localStorage.setItem('w4f_access_token', 'expert-token')
    localStorage.setItem('w4f_refresh_token', 'expert-refresh')
  })

  it('shows the form for an expert on a non-terminal report, and hides it after a terminal status', async () => {
    mockedApiFetch.mockImplementation((path: string, options?: { method?: string }) => {
      if (path === '/auth/me') return Promise.resolve(EXPERT_ME)
      if (path.startsWith('/douars')) return Promise.resolve(DOUAR_LIST)
      if (path === '/reports/r1' && (!options?.method || options.method === 'GET')) {
        return Promise.resolve(detail({ status: 'submitted' }))
      }
      return Promise.reject(new Error(`unexpected request: ${options?.method ?? 'GET'} ${path}`))
    })

    renderPage()

    await waitFor(() => expect(screen.getByText('إضافة تحقق')).toBeInTheDocument())
  })

  it('hides the form once the report is in a terminal status', async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path === '/auth/me') return Promise.resolve(EXPERT_ME)
      if (path.startsWith('/douars')) return Promise.resolve(DOUAR_LIST)
      if (path === '/reports/r1') return Promise.resolve(detail({ status: 'rejected' }))
      return Promise.reject(new Error(`unexpected path: ${path}`))
    })

    renderPage()

    await waitFor(() => expect(screen.getByText('دوار الأمل')).toBeInTheDocument())
    expect(screen.queryByText('إضافة تحقق')).not.toBeInTheDocument()
  })

  it('submits a decision and refetches the report, picking up the server-assigned new status', async () => {
    mockedApiFetch.mockImplementation((path: string, options?: { method?: string; body?: unknown }) => {
      if (path === '/auth/me') return Promise.resolve(EXPERT_ME)
      if (path.startsWith('/douars')) return Promise.resolve(DOUAR_LIST)
      if (path === '/reports/r1/validations' && options?.method === 'POST') {
        return Promise.resolve({ id: 'v1', report_id: 'r1', new_report_status: 'validated', ...(options.body as object) })
      }
      if (path === '/reports/r1') return Promise.resolve(detail({ status: 'submitted' }))
      return Promise.reject(new Error(`unexpected request: ${options?.method ?? 'GET'} ${path}`))
    })
    const user = userEvent.setup()

    renderPage()
    await waitFor(() => expect(screen.getByText('إضافة تحقق')).toBeInTheDocument())

    await user.selectOptions(screen.getByLabelText('القرار'), 'validated')
    await user.click(screen.getByRole('button', { name: 'إرسال' }))

    await waitFor(() => expect(screen.getByText('تم تسجيل التحقق بنجاح')).toBeInTheDocument())
    expect(mockedApiFetch).toHaveBeenCalledWith(
      '/reports/r1/validations',
      expect.objectContaining({ method: 'POST' }),
    )
  })
})
