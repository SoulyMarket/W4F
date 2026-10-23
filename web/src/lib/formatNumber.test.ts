import { describe, expect, it } from 'vitest'
import { formatPoints } from './formatNumber'

describe('formatPoints', () => {
  it('cleans up floating-point artifacts from the scoring service', () => {
    expect(formatPoints(0.44999999999999996)).toBe('0.45')
  })

  it('does not add trailing zeros to a whole number', () => {
    expect(formatPoints(15)).toBe('15')
  })

  it('rounds to two decimal places by default', () => {
    expect(formatPoints(11.2537)).toBe('11.25')
  })
})
