// Every form field across the app (login, validation, project creation,
// status updates, user creation, filters) had hand-copied its own input/
// select/textarea class string with small drift between them (h-10 vs
// h-11, some missing the focus ring). One shared string instead.
export const inputClass =
  'h-10 w-full rounded-md border border-border bg-background px-3 text-sm text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-ring'

export const selectClass = `${inputClass} cursor-pointer`

export const textareaClass =
  'w-full rounded-md border border-border bg-background px-3 py-2 text-sm text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-ring'

export const labelClass = 'text-sm font-medium text-foreground'
