import type { TFunction } from 'i18next'

// Raw values are the backend's own StrEnum values (section 4,
// `backend/app/models/enums.py`), never translated server-side — mirrors
// the Android app's `ReportEnumLabels.kt` lookup-table pattern so a
// future screen can't drift between a parallel TS enum and the backend's.
export const REPORT_STATUSES = [
  'submitted',
  'under_review',
  'recheck_requested',
  'validated',
  'rejected',
  'converted_to_project',
] as const
export type ReportStatus = (typeof REPORT_STATUSES)[number]

export const PROJECT_STATUSES = [
  'new',
  'in_study',
  'approved',
  'in_preparation',
  'in_progress',
  'completed',
  'cancelled',
] as const
export type ProjectStatus = (typeof PROJECT_STATUSES)[number]

export function reportStatusLabel(t: TFunction, status: string): string {
  return t(`status.report.${status}`, { defaultValue: status })
}

export function projectStatusLabel(t: TFunction, status: string): string {
  return t(`status.project.${status}`, { defaultValue: status })
}
