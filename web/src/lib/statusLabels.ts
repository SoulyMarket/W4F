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

// Mirrors the backend's own PROJECT_STATUS_TRANSITIONS
// (`backend/app/models/enums.py`) — any non-terminal status may also move
// to `cancelled`; `completed`/`cancelled` are terminal. Kept here so the
// status-change form only ever offers a transition the server will
// actually accept, rather than letting a manager submit one that 409s.
export const PROJECT_STATUS_TRANSITIONS: Record<ProjectStatus, readonly ProjectStatus[]> = {
  new: ['in_study', 'cancelled'],
  in_study: ['approved', 'cancelled'],
  approved: ['in_preparation', 'cancelled'],
  in_preparation: ['in_progress', 'cancelled'],
  in_progress: ['completed', 'cancelled'],
  completed: [],
  cancelled: [],
}

export const VALIDATION_DECISIONS = ['validated', 'recheck_requested', 'modified', 'rejected'] as const
export type ValidationDecision = (typeof VALIDATION_DECISIONS)[number]

export function validationDecisionLabel(t: TFunction, decision: string): string {
  return t(`status.validation_decision.${decision}`, { defaultValue: decision })
}

export const AUDIT_ACTIONS = [
  'create',
  'update',
  'delete',
  'login',
  'login_failed',
  'logout',
  'status_change',
  'export',
] as const

export function auditActionLabel(t: TFunction, action: string): string {
  return t(`audit_action.${action}`, { defaultValue: action })
}
