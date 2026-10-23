import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import i18n from '../../i18n'
import { apiFetch } from '../../lib/api'
import { DashboardPage } from './DashboardPage'
import type { DashboardSummaryDto } from './dashboardApi'

vi.mock('../../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../../lib/api')>('../../lib/api')
  return { ...actual, apiFetch: vi.fn() }
})

const mockedApiFetch = vi.mocked(apiFetch)

const SUMMARY: DashboardSummaryDto = {
  total_douars: 12,
  reports_by_status: { submitted: 3, validated: 2 },
  priority_douars: [{ id: 'd1', name_ar: 'دوار الأمل', name_fr: 'Douar Al Amal', score: 85, report_count: 4 }],
  projects_by_status: { new: 1 },
  recurring_problem_douars: [],
}

function renderWithClient() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <DashboardPage />
    </QueryClientProvider>,
  )
}

describe('DashboardPage', () => {
  beforeEach(() => {
    mockedApiFetch.mockReset()
    void i18n.changeLanguage('ar')
  })

  it('renders KPI counts and priority douars from the summary response', async () => {
    mockedApiFetch.mockResolvedValue(SUMMARY)

    renderWithClient()

    await waitFor(() => expect(screen.getByText('12')).toBeInTheDocument())
    expect(screen.getByText('دوار الأمل')).toBeInTheDocument()
  })

  it('shows the empty-state message when a douar list has no entries', async () => {
    mockedApiFetch.mockResolvedValue(SUMMARY)

    renderWithClient()

    await waitFor(() => expect(screen.getByText('لا توجد دواوير بمشاكل متكررة حاليًا')).toBeInTheDocument())
  })

  it('shows a retry affordance on failure', async () => {
    mockedApiFetch.mockRejectedValue(new Error('network down'))

    renderWithClient()

    await waitFor(() => expect(screen.getByText('تعذر تحميل لوحة القيادة')).toBeInTheDocument())
    expect(screen.getByRole('button', { name: 'إعادة المحاولة' })).toBeInTheDocument()
  })
})
