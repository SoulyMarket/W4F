import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import i18n from '../../i18n'
import { apiFetch } from '../../lib/api'
import { ReportsListPage } from './ReportsListPage'
import type { ReportDto, ReportListDto } from './reportsApi'

vi.mock('../../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../../lib/api')>('../../lib/api')
  return { ...actual, apiFetch: vi.fn() }
})

const mockedApiFetch = vi.mocked(apiFetch)

function report(overrides: Partial<ReportDto> = {}): ReportDto {
  return {
    id: 'r1',
    douar_id: 'd1',
    moqaddem_id: 'm1',
    water_source: 'well',
    problem_type: 'no_water',
    problem_started_on: '2026-01-05',
    duration_days: 10,
    interruption_frequency: 'daily',
    has_alternative_source: false,
    alternative_distance_km: null,
    severity_reported: 'high',
    water_quality_risk: false,
    affected_families: 5,
    affected_people: 20,
    observations: null,
    lat: null,
    lon: null,
    location_accuracy_m: null,
    collected_at: '2026-01-06T10:00:00Z',
    synced_at: '2026-01-06T10:05:00Z',
    status: 'submitted',
    version: 1,
    score: 72,
    ...overrides,
  }
}

const REPORT_LIST: ReportListDto = { items: [report()], total: 1, page: 1, page_size: 20 }
const DOUAR_LIST = { items: [{ id: 'd1', name_ar: 'دوار الأمل', name_fr: 'Douar Al Amal', commune_id: 'c1', lat: null, lon: null, population: null, families_count: null, notes: null }], total: 1, page: 1, page_size: 100 }

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ReportsListPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ReportsListPage', () => {
  beforeEach(() => {
    mockedApiFetch.mockReset()
    void i18n.changeLanguage('ar')
    mockedApiFetch.mockImplementation((path: string) => {
      if (path.startsWith('/reports')) return Promise.resolve(REPORT_LIST)
      if (path.startsWith('/douars')) return Promise.resolve(DOUAR_LIST)
      return Promise.reject(new Error(`unexpected path: ${path}`))
    })
  })

  it('resolves the douar name and shows the row once both requests settle', async () => {
    renderPage()

    await waitFor(() => expect(screen.getByText('دوار الأمل')).toBeInTheDocument())
    expect(screen.getByText('72')).toBeInTheDocument()
  })

  it('shows the empty-state message when there are no matching reports', async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path.startsWith('/reports')) return Promise.resolve({ items: [], total: 0, page: 1, page_size: 20 })
      if (path.startsWith('/douars')) return Promise.resolve(DOUAR_LIST)
      return Promise.reject(new Error(`unexpected path: ${path}`))
    })

    renderPage()

    await waitFor(() => expect(screen.getByText('لا توجد بلاغات مطابقة')).toBeInTheDocument())
  })
})
