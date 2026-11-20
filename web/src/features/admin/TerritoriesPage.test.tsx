import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import i18n from '../../i18n'
import { apiFetch } from '../../lib/api'
import { TerritoriesPage } from './TerritoriesPage'
import type { TerritoryDto } from './territoriesApi'

vi.mock('../../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../../lib/api')>('../../lib/api')
  return { ...actual, apiFetch: vi.fn() }
})

const mockedApiFetch = vi.mocked(apiFetch)

const PROVINCE: TerritoryDto = { id: 'p1', name_ar: 'الحوز', name_fr: 'Al Haouz', level: 'province', parent_id: null }
const COMMUNE: TerritoryDto = {
  id: 'c1',
  name_ar: 'أيت أورير',
  name_fr: 'Ait Ourir',
  level: 'commune',
  parent_id: 'p1',
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <TerritoriesPage />
    </QueryClientProvider>,
  )
}

describe('TerritoriesPage', () => {
  beforeEach(() => {
    mockedApiFetch.mockReset()
    void i18n.changeLanguage('ar')
  })

  it('lists territories with their resolved parent name', async () => {
    mockedApiFetch.mockResolvedValue([PROVINCE, COMMUNE])

    renderPage()

    // "Al Haouz" appears twice by design: once as the province's own row,
    // once as the commune row's resolved parent name (not a raw id).
    await waitFor(() => expect(screen.getAllByText('Al Haouz').length).toBe(2))
    expect(screen.getByText('Ait Ourir')).toBeInTheDocument()
    expect(screen.getByText('بدون (مستوى جذري)')).toBeInTheDocument()
  })

  it('shows the empty-state message when there are no territories yet', async () => {
    mockedApiFetch.mockResolvedValue([])

    renderPage()

    await waitFor(() => expect(screen.getByText('لا توجد ترابات بعد')).toBeInTheDocument())
  })

  it('creates a new province through the create form', async () => {
    mockedApiFetch.mockImplementation((path: string, options?: { method?: string }) => {
      if (path === '/territories' && (!options?.method || options.method === 'GET')) {
        return Promise.resolve([PROVINCE])
      }
      if (path === '/territories' && options?.method === 'POST') {
        return Promise.resolve({ id: 'p2', name_ar: 'جديد', name_fr: 'New Province', level: 'province', parent_id: null })
      }
      return Promise.reject(new Error(`unexpected request: ${options?.method ?? 'GET'} ${path}`))
    })
    const userEventInstance = userEvent.setup()

    renderPage()
    await waitFor(() => expect(screen.getByText('Al Haouz')).toBeInTheDocument())

    await userEventInstance.click(screen.getByText('ترابة جديدة'))
    await userEventInstance.type(screen.getByLabelText('الاسم (عربي)'), 'جديد')
    await userEventInstance.type(screen.getByLabelText('الاسم (فرنسي)'), 'New Province')
    await userEventInstance.selectOptions(screen.getByLabelText('المستوى'), 'province')
    await userEventInstance.click(screen.getByRole('button', { name: 'إنشاء' }))

    await waitFor(() =>
      expect(mockedApiFetch).toHaveBeenCalledWith(
        '/territories',
        expect.objectContaining({
          method: 'POST',
          body: { name_ar: 'جديد', name_fr: 'New Province', level: 'province', parent_id: null },
        }),
      ),
    )
  })
})
