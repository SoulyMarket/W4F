// The priority breakdown's `points` is a float built from several
// weighted multiplications server-side (section 5's scoring service) —
// real floating-point artifacts like 0.44999999999999996 reach the API
// response as-is. Rounding is display-only (never sent back anywhere),
// so it's safe to clean up here rather than showing raw IEEE-754 noise
// to a reviewer.
export function formatPoints(value: number, maxFractionDigits = 2): string {
  return Number(value.toFixed(maxFractionDigits)).toString()
}
