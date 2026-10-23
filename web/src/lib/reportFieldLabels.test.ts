import { describe, expect, it } from 'vitest'
import i18n from '../i18n'
import {
  frequencyLabel,
  problemTypeLabel,
  severityLabel,
  waterSourceLabel,
} from './reportFieldLabels'

const WATER_SOURCES = ['network', 'well', 'spring', 'tank_truck', 'river', 'other']
const PROBLEM_TYPES = [
  'no_water',
  'intermittent',
  'low_pressure',
  'contamination',
  'broken_pump',
  'broken_pipe',
  'dry_source',
  'other',
]
const FREQUENCIES = ['permanent', 'daily', 'weekly', 'monthly', 'rare']
const SEVERITIES = ['low', 'medium', 'high', 'critical']

describe('reportFieldLabels', () => {
  it('resolves every known value to a non-raw label in both languages', () => {
    for (const lang of ['ar', 'fr'] as const) {
      void i18n.changeLanguage(lang)
      const t = i18n.t.bind(i18n)
      for (const value of WATER_SOURCES) expect(waterSourceLabel(t, value)).not.toBe(value)
      for (const value of PROBLEM_TYPES) expect(problemTypeLabel(t, value)).not.toBe(value)
      for (const value of FREQUENCIES) expect(frequencyLabel(t, value)).not.toBe(value)
      for (const value of SEVERITIES) expect(severityLabel(t, value)).not.toBe(value)
    }
  })

  it('falls back to the raw value for an unrecognized value', () => {
    void i18n.changeLanguage('ar')
    const t = i18n.t.bind(i18n)
    expect(waterSourceLabel(t, 'solar_pump')).toBe('solar_pump')
  })
})
