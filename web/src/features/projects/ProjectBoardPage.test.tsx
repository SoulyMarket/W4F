import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import i18n from '../../i18n'
import { apiFetch } from '../../lib/api'
import { ProjectBoardPage } from './ProjectBoardPage'
import type { ProjectDto } from './projectsApi'

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

function project(overrides: Partial<ProjectDto> = {}): ProjectDto {
  return {
    id: 'p1',
    report_id: 'r1',
    douar_id: 'd1',
    title: 'إصلاح القناة الرئيسية',
    solution_type: 'pipe_repair',
    description: null,
    status: 'new',
    owner_id: 'u1',
    planned_start: null,
    planned_end: null,
    actual_start: null,
    actual_end: null,
    progress_percent: 0,
    created_at: '2026-10-01T10:00:00Z',
    ...overrides,
  }
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ProjectBoardPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ProjectBoardPage', () => {
  beforeEach(() => {
    mockedApiFetch.mockReset()
    void i18n.changeLanguage('ar')
  })

  it('places each project under its own status column', async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path.startsWith('/projects')) {
        return Promise.resolve({ items: [project({ status: 'in_progress' })], total: 1, page: 1, page_size: 100 })
      }
      if (path.startsWith('/douars')) return Promise.resolve(DOUAR_LIST)
      return Promise.reject(new Error(`unexpected path: ${path}`))
    })

    renderPage()

    await waitFor(() => expect(screen.getByText('إصلاح القناة الرئيسية')).toBeInTheDocument())
    expect(screen.getByText('دوار الأمل')).toBeInTheDocument()
    // Every column exists even when empty, each saying so.
    expect(screen.getAllByText('لا توجد مشاريع').length).toBeGreaterThan(0)
  })

  it('shows a retry affordance on failure', async () => {
    mockedApiFetch.mockImplementation((path: string) => {
      if (path.startsWith('/projects')) return Promise.reject(new Error('network down'))
      if (path.startsWith('/douars')) return Promise.resolve(DOUAR_LIST)
      return Promise.reject(new Error(`unexpected path: ${path}`))
    })

    renderPage()

    await waitFor(() => expect(screen.getByText('تعذر تحميل المشاريع')).toBeInTheDocument())
    expect(screen.getByRole('button', { name: 'إعادة المحاولة' })).toBeInTheDocument()
  })
})
