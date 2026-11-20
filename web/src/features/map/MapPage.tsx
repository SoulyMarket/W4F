// No default export — this package is ESM-only with named exports
// (confirmed against node_modules/maplibre-gl/dist/maplibre-gl.d.ts
// before use, same "verify an unfamiliar library's actual API" pass as
// framer-motion in step 3.7). `MapLibreMap` is the package's own alias
// for `Map`, used here instead to avoid shadowing the built-in `Map`.
import { MapTrifoldIcon } from '@phosphor-icons/react'
import { LngLatBounds, MapLibreMap, Marker, NavigationControl, Popup } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Button } from '../../components/Button'
import { EmptyState } from '../../components/EmptyState'
import { Skeleton } from '../../components/Skeleton'
import type { SupportedLanguage } from '../../i18n'
import { ApiError } from '../../lib/api'
import {
  MARKER_COLOR_BY_LEVEL,
  markerPriorityLevel,
  useDashboardMap,
  type DouarMapFeature,
} from './mapApi'

// A free, no-API-key-required public MapLibre demo style — same choice
// and same reasoning as the Android app's own MapScreen.kt (this
// prototype has no tile-hosting contract of its own).
const BASE_STYLE_URL = 'https://demotiles.maplibre.org/style.json'

export function MapPage() {
  const { t, i18n } = useTranslation()
  const lang = i18n.language as SupportedLanguage
  const { data, isPending, isError, error, refetch } = useDashboardMap()

  if (isPending) {
    return (
      <div className="flex flex-col gap-4" aria-hidden="true">
        <Skeleton className="h-8 w-32" />
        <Skeleton className="h-[60vh] min-h-[320px] w-full" />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex flex-col items-start gap-2">
        <p className="text-destructive">{error instanceof ApiError ? error.message : t('map.loading_error')}</p>
        <Button variant="secondary" onClick={() => void refetch()}>
          {t('common.retry')}
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold tracking-tight text-foreground font-heading">{t('map.title')}</h1>
      {data.features.length === 0 ? (
        <EmptyState icon={MapTrifoldIcon} message={t('map.empty')} />
      ) : (
        <>
          <div className="h-[60vh] min-h-[320px] overflow-hidden rounded-xl border border-border/70 shadow-soft">
            <MapLibreView features={data.features} lang={lang} />
          </div>
          <MapLegend />
        </>
      )}
    </div>
  )
}

function MapLibreView({ features, lang }: { features: DouarMapFeature[]; lang: SupportedLanguage }) {
  const { t } = useTranslation()
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<MapLibreMap | null>(null)
  const markersRef = useRef<Marker[]>([])

  // Map instance: created once per mount, destroyed on unmount — not
  // re-created when `features` changes (see the effect below), since
  // tearing down and rebuilding the whole WebGL context on every
  // react-query refetch would reset the user's pan/zoom for no reason.
  useEffect(() => {
    if (!containerRef.current) return
    const map = new MapLibreMap({
      container: containerRef.current,
      style: BASE_STYLE_URL,
      center: [-7.9, 31.2],
      zoom: 8,
    })
    map.addControl(new NavigationControl(), 'top-right')
    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  // Markers rebuilt whenever the data or language changes (popup text is
  // localized) — cheap relative to the map instance itself, and simpler
  // than diffing marker-by-marker for this prototype's douar count.
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    function renderMarkers() {
      if (!map) return
      for (const marker of markersRef.current) marker.remove()
      markersRef.current = []

      const bounds = new LngLatBounds()
      for (const feature of features) {
        const [lon, lat] = feature.geometry.coordinates
        bounds.extend([lon, lat])
        const level = markerPriorityLevel(feature.properties)
        const name = lang === 'ar' ? feature.properties.name_ar : feature.properties.name_fr
        const scoreLine =
          feature.properties.latest_score === null
            ? t('map.marker_no_score')
            : t('map.marker_score', { score: feature.properties.latest_score })
        const popup = new Popup({ offset: 20, closeButton: false }).setHTML(
          `<strong>${escapeHtml(name)}</strong><br/>${escapeHtml(scoreLine)}<br/>${escapeHtml(
            t('map.marker_reports', { count: feature.properties.report_count }),
          )}`,
        )
        const marker = new Marker({ color: MARKER_COLOR_BY_LEVEL[level] })
          .setLngLat([lon, lat])
          .setPopup(popup)
          .addTo(map)
        markersRef.current.push(marker)
      }

      if (!bounds.isEmpty()) {
        map.fitBounds(bounds, { padding: 48, maxZoom: 13, duration: 0 })
      }
    }

    if (map.isStyleLoaded()) {
      renderMarkers()
    } else {
      map.once('load', renderMarkers)
    }

    return () => {
      for (const marker of markersRef.current) marker.remove()
      markersRef.current = []
    }
  }, [features, lang, t])

  return <div ref={containerRef} className="h-full w-full" />
}

// The popup's own HTML is built from douar names and formatted numbers
// only — no user-authored free text reaches this template — but escaping
// unconditionally costs nothing and means that stays true even if a
// future field (e.g. a douar's `notes`) gets added to the popup later.
function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => {
    switch (char) {
      case '&':
        return '&amp;'
      case '<':
        return '&lt;'
      case '>':
        return '&gt;'
      case '"':
        return '&quot;'
      default:
        return '&#39;'
    }
  })
}

function MapLegend() {
  const { t } = useTranslation()
  const entries: Array<[string, string]> = [
    [MARKER_COLOR_BY_LEVEL.no_reports, t('map.legend_no_reports')],
    [MARKER_COLOR_BY_LEVEL.low, t('map.legend_low')],
    [MARKER_COLOR_BY_LEVEL.medium, t('map.legend_medium')],
    [MARKER_COLOR_BY_LEVEL.high, t('map.legend_high')],
    [MARKER_COLOR_BY_LEVEL.project_underway, t('map.legend_project_underway')],
  ]
  return (
    <div className="flex flex-wrap gap-4">
      {entries.map(([color, label]) => (
        <div key={label} className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="h-3 w-3 shrink-0 rounded-full" style={{ backgroundColor: color }} />
          {label}
        </div>
      ))}
    </div>
  )
}
