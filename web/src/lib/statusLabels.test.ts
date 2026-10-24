import { describe, expect, it } from 'vitest'
import i18n from '../i18n'
import {
  PROJECT_STATUS_TRANSITIONS,
  PROJECT_STATUSES,
  projectStatusLabel,
  REPORT_STATUSES,
  reportStatusLabel,
  VALIDATION_DECISIONS,
  validationDecisionLabel,
} from './statusLabels'

describe('statusLabels', () => {
  it('resolves every known report status to a non-empty, non-raw label in both languages', () => {
    for (const lang of ['ar', 'fr'] as const) {
      void i18n.changeLanguage(lang)
      for (const status of REPORT_STATUSES) {
        const label = reportStatusLabel(i18n.t.bind(i18n), status)
        expect(label).not.toBe(status)
        expect(label.length).toBeGreaterThan(0)
      }
    }
  })

  it('resolves every known project status to a non-empty, non-raw label in both languages', () => {
    for (const lang of ['ar', 'fr'] as const) {
      void i18n.changeLanguage(lang)
      for (const status of PROJECT_STATUSES) {
        const label = projectStatusLabel(i18n.t.bind(i18n), status)
        expect(label).not.toBe(status)
        expect(label.length).toBeGreaterThan(0)
      }
    }
  })

  it('resolves every known validation decision to a non-raw label in both languages', () => {
    for (const lang of ['ar', 'fr'] as const) {
      void i18n.changeLanguage(lang)
      for (const decision of VALIDATION_DECISIONS) {
        const label = validationDecisionLabel(i18n.t.bind(i18n), decision)
        expect(label).not.toBe(decision)
        expect(label.length).toBeGreaterThan(0)
      }
    }
  })

  it('falls back to the raw value for an unrecognized status rather than guessing', () => {
    void i18n.changeLanguage('ar')
    expect(reportStatusLabel(i18n.t.bind(i18n), 'some_future_status')).toBe('some_future_status')
  })

  it('mirrors the backend state machine: completed/cancelled are terminal, every other status can reach cancelled', () => {
    expect(PROJECT_STATUS_TRANSITIONS.completed).toEqual([])
    expect(PROJECT_STATUS_TRANSITIONS.cancelled).toEqual([])
    for (const status of PROJECT_STATUSES) {
      if (status === 'completed' || status === 'cancelled') continue
      expect(PROJECT_STATUS_TRANSITIONS[status]).toContain('cancelled')
    }
  })
})
