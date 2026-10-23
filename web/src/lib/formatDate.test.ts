import { describe, expect, it } from 'vitest'
import { formatDate } from './formatDate'

describe('formatDate', () => {
  it('formats as dd/MM/yyyy with Western digits regardless of locale', () => {
    expect(formatDate('2026-03-05T14:30:00Z')).toBe('05/03/2026')
  })

  it('pads single-digit day and month', () => {
    expect(formatDate('2026-01-09')).toBe('09/01/2026')
  })

  it('does not shift a date-only value across local timezones', () => {
    // A naive `new Date('2026-01-09').getDate()` reads back 8 in any
    // timezone behind UTC (the string parses as UTC midnight) — this
    // must stay 09 everywhere, independent of where the test runs.
    expect(formatDate('2026-01-09')).toBe('09/01/2026')
    expect(formatDate('2026-12-31')).toBe('31/12/2026')
  })
})
