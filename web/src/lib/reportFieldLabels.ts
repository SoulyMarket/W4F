import type { TFunction } from 'i18next'

// Same raw-value lookup pattern as statusLabels.ts, and the same Arabic/
// French wording as the Android app's ReportEnumLabels.kt (copied from
// android/app/src/main/res/values{,-fr}/strings.xml) — one set of correct
// translations for these enums, not two that can drift apart.
export function waterSourceLabel(t: TFunction, value: string): string {
  return t(`field.water_source.${value}`, { defaultValue: value })
}

export function problemTypeLabel(t: TFunction, value: string): string {
  return t(`field.problem_type.${value}`, { defaultValue: value })
}

export function frequencyLabel(t: TFunction, value: string): string {
  return t(`field.frequency.${value}`, { defaultValue: value })
}

export function severityLabel(t: TFunction, value: string): string {
  return t(`field.severity.${value}`, { defaultValue: value })
}
