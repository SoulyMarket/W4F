import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '../../lib/api'

export interface DouarMapFeatureProperties {
  id: string
  name_ar: string
  name_fr: string
  latest_score: number | null
  report_count: number
  project_status: string | null
}

export interface DouarMapFeature {
  type: 'Feature'
  geometry: { type: 'Point'; coordinates: [number, number] }
  properties: DouarMapFeatureProperties
}

export interface DouarMapGeoJson {
  type: 'FeatureCollection'
  features: DouarMapFeature[]
}

export function useDashboardMap() {
  return useQuery({
    queryKey: ['dashboard', 'map'],
    queryFn: () => apiFetch<DouarMapGeoJson>('/dashboard/map'),
  })
}

// In progress toward or at completion — anything past validation that
// isn't cancelled, mirroring the Android app's own PROJECT_UNDERWAY
// classification (`MapViewModel.kt`) so "colored by priority" means the
// same thing on both clients.
const PROJECT_UNDERWAY_STATUSES = new Set(['in_study', 'approved', 'in_preparation', 'in_progress', 'completed'])

export type MarkerPriorityLevel = 'no_reports' | 'low' | 'medium' | 'high' | 'project_underway'

// Section 5: "map (colored by priority)". A project already underway
// outranks the raw score in the legend — once work has started, the
// color should say so, not keep flashing red as if nothing had happened
// yet. Thresholds mirror the dashboard's own `_PRIORITY_DOUAR_THRESHOLD`
// (70) for "high"; "medium" is this prototype's own reasonable midpoint,
// not a value the backend enforces anywhere.
export function markerPriorityLevel(properties: DouarMapFeatureProperties): MarkerPriorityLevel {
  if (properties.project_status && PROJECT_UNDERWAY_STATUSES.has(properties.project_status)) {
    return 'project_underway'
  }
  if (properties.latest_score === null) return 'no_reports'
  if (properties.latest_score >= 70) return 'high'
  if (properties.latest_score >= 40) return 'medium'
  return 'low'
}

export const MARKER_COLOR_BY_LEVEL: Record<MarkerPriorityLevel, string> = {
  no_reports: '#9E9E9E',
  low: '#2563EB',
  medium: '#F59E0B',
  high: '#DC2626',
  project_underway: '#16A34A',
}
