import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import i18n from '../../i18n'
import { apiFetch } from '../../lib/api'
import { ScoringWeightsPage } from './ScoringWeightsPage'
import type { RecomputeResultDto, ScoringConfigDto } from './scoringApi'

vi.mock('../../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../../lib/api')>('../../lib/api')
  return { ...actual, apiFetch: vi.fn() }
})

const mockedApiFetch = vi.mocked(apiFetch)

const CONFIG: ScoringConfigDto = {
  id: 'c1',
  weights: {
    people_affected: 25,
    duration: 15,
    frequency: 10,
    no_alternative: 15,
    distance: 10,
    severity: 15,
    water_quality_risk: 10,
  },
  is_active: true,
  created_by: 'u1',
  created_at: '2026-01-01T00:00:00Z',
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <ScoringWeightsPage />
    </QueryClientProvider>,
  )
}

describe('ScoringWeightsPage', () => {
  beforeEach(() => {
    mockedApiFetch.mockReset()
    void i18n.changeLanguage('ar')
  })

  it('shows the active weights and disables Save until something changes', async () => {
    mockedApiFetch.mockResolvedValue(CONFIG)

    renderPage()

    await waitFor(() => expect(screen.getAllByText('25').length).toBeGreaterThan(0))
    expect(screen.getByRole('button', { name: 'حفظ وإعادة الاحتساب' })).toBeDisabled()
  })

  it('saves the edited weights and shows the recompute count', async () => {
    mockedApiFetch.mockImplementation((path: string, options?: { method?: string }) => {
      if (path === '/scoring-config' && (!options?.method || options.method === 'GET')) {
        return Promise.resolve(CONFIG)
      }
      if (path === '/scoring-config' && options?.method === 'PUT') {
        const result: RecomputeResultDto = {
          config: { ...CONFIG, weights: { ...CONFIG.weights, people_affected: 40 } },
          reports_recomputed: 7,
        }
        return Promise.resolve(result)
      }
      return Promise.reject(new Error(`unexpected request: ${options?.method ?? 'GET'} ${path}`))
    })
    const userEventInstance = userEvent.setup()

    renderPage()
    await waitFor(() => expect(screen.getAllByText('25').length).toBeGreaterThan(0))

    const peopleAffectedSlider = screen.getByLabelText('عدد الأشخاص المتضررين')
    fireEvent.change(peopleAffectedSlider, { target: { value: '40' } })

    const saveButton = screen.getByRole('button', { name: 'حفظ وإعادة الاحتساب' })
    expect(saveButton).not.toBeDisabled()
    await userEventInstance.click(saveButton)

    await waitFor(() => expect(screen.getByText('تم الحفظ — أُعيد احتساب 7 بلاغ')).toBeInTheDocument())
  })
})
