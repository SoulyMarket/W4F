const DATE_ONLY_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/

// Section 2.1: "Digits: use Western digits (0-9)... Dates in dd/MM/yyyy."
// in both languages — Intl.DateTimeFormat with an 'ar' locale would
// render Arabic-Indic digits unless numberingSystem is pinned, so this
// formats by hand instead of trusting locale defaults either way.
//
// A plain `YYYY-MM-DD` (a `date` field, e.g. `problem_started_on`) is
// read out digit-by-digit rather than going through `Date` + local-time
// getters: `new Date('2026-01-09')` parses as UTC midnight, and in any
// timezone behind UTC that rolls back to the previous local day — the
// report would show one day earlier than what was actually entered. A
// full timestamp (e.g. `collected_at`) has no such ambiguity and SHOULD
// convert to the viewer's local time, so only the date-only case is
// special-cased.
export function formatDate(isoDateOrDateTime: string): string {
  const dateOnlyMatch = DATE_ONLY_PATTERN.exec(isoDateOrDateTime)
  if (dateOnlyMatch) {
    const [, year, month, day] = dateOnlyMatch
    return `${day}/${month}/${year}`
  }

  const date = new Date(isoDateOrDateTime)
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()
  return `${day}/${month}/${year}`
}
