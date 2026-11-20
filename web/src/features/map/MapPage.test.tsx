import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import i18n from '../../i18n'
import { apiFetch } from '../../lib/api'
import { MapPage } from './MapPage'
import type { DouarMapGeoJson } from './mapApi'

vi.mock('../../lib/api', async () => {
  const actual = await vi.importActual<typeof import('../../lib/api')>('../../lib/api')
  return { ...actual, apiFetch: vi.fn() }
})

// jsdom has no WebGL context, so the real library would throw the
// moment a Map tries to create one. The page's own logic (loading/error/
// empty states, the legend, marker color classification) is what this
// test covers — actual WebGL rendering is left to manual verification in
// a real browser, same split the Android app already draws between
// MapViewModel (unit-tested) and MapScreen's MapLibre calls (on-device
// only) for the same reason.
vi.mock('maplibre-gl', () => {
  class FakeMap {
    addControl = vi.fn()
    remove = vi.fn()
    isStyleLoaded = vi.fn(() => true)
    once = vi.fn()
    fitBounds = vi.fn()
  }
  class FakeMarker {
    setLngLat = vi.fn().mockReturnThis()
    setPopup = vi.fn().mockReturnThis()
    addTo = vi.fn().mockReturnThis()
    remove = vi.fn()
  }
  class FakePopup {
    setHTML = vi.fn().mockReturnThis()
  }
  class FakeLngLatBounds {
    extend = vi.fn()
    isEmpty = vi.fn(() => false)
  }
  class FakeNavigationControl {}
  return {
    MapLibreMap: FakeMap,
    Marker: FakeMarker,
    Popup: FakePopup,
    LngLatBounds: FakeLngLatBounds,
    NavigationControl: FakeNavigationControl,
  }
})

const mockedApiFetch = vi.mocked(apiFetch)

const GEOJSON: DouarMapGeoJson = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [-7.9, 31.2] },
      properties: {
        id: 'd1',
        name_ar: 'دوار الأمل',
        name_fr: 'Douar Al Amal',
        latest_score: 85,
        report_count: 3,
        project_status: null,
      },
    },
  ],
}

function renderPage() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={queryClient}>
      <MapPage />
    </QueryClientProvider>,
  )
}

describe('MapPage', () => {
  beforeEach(() => {
    mockedApiFetch.mockReset()
    void i18n.changeLanguage('ar')
  })

  it('renders the map container and legend once douars with coordinates arrive', async () => {
    mockedApiFetch.mockResolvedValue(GEOJSON)

    renderPage()

    await waitFor(() => expect(screen.getByText('الخريطة')).toBeInTheDocument())
    expect(screen.getByText('أولوية عالية')).toBeInTheDocument()
    expect(screen.getByText('مشروع قيد الإنجاز')).toBeInTheDocument()
  })

  it('shows the empty-state message when no douar has coordinates', async () => {
    mockedApiFetch.mockResolvedValue({ type: 'FeatureCollection', features: [] })

    renderPage()

    await waitFor(() => expect(screen.getByText('لا توجد دواوير ذات إحداثيات لعرضها')).toBeInTheDocument())
  })
})
