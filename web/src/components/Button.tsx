import { motion, useReducedMotion, type HTMLMotionProps } from 'framer-motion'
import { forwardRef, type ReactNode } from 'react'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'destructive' | 'destructive-ghost'
export type ButtonSize = 'sm' | 'md'

const VARIANT_CLASSES: Record<ButtonVariant, string> = {
  primary:
    'bg-primary text-on-primary hover:opacity-90 focus-visible:ring-ring disabled:opacity-60',
  secondary:
    'border border-border bg-background text-foreground hover:bg-muted focus-visible:ring-ring disabled:opacity-60',
  ghost: 'text-foreground hover:bg-muted focus-visible:ring-ring disabled:opacity-50',
  destructive:
    'bg-destructive text-white hover:opacity-90 focus-visible:ring-destructive disabled:opacity-60',
  'destructive-ghost': 'text-destructive hover:bg-destructive/10 focus-visible:ring-destructive disabled:opacity-50',
}

const SIZE_CLASSES: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-xs',
  md: 'h-10 px-4 text-sm',
}

interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'ref' | 'children'> {
  variant?: ButtonVariant
  size?: ButtonSize
  /** Shows a spinner and disables the button, for an in-flight mutation. */
  isLoading?: boolean
  children?: ReactNode
}

// One button for the whole app — every screen built in step 3.1-3.6 hand
// -styled its own <button> with a slightly different class list (noticed
// after a round of manual testing: hover opacity here, bg-muted there,
// no two forms quite matching). The press/hover motion follows the
// ui-ux-pro-max guidance pulled for this project (active:scale-95-style
// press feedback, 150ms ease) — done through framer-motion instead of a
// CSS :active rule so it also responds to prefers-reduced-motion via
// useReducedMotion() (a CSS transition can't query that the same way
// without a separate media-query block).
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = 'primary', size = 'md', isLoading, disabled, className = '', children, ...props }, ref) => {
    const prefersReducedMotion = useReducedMotion()
    const isDisabled = disabled || isLoading

    return (
      <motion.button
        ref={ref}
        disabled={isDisabled}
        whileHover={!isDisabled && !prefersReducedMotion ? { scale: 1.02 } : undefined}
        whileTap={!isDisabled && !prefersReducedMotion ? { scale: 0.96 } : undefined}
        transition={{ duration: 0.15, ease: 'easeOut' }}
        className={`inline-flex cursor-pointer items-center justify-center gap-2 rounded-md font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed ${VARIANT_CLASSES[variant]} ${SIZE_CLASSES[size]} ${className}`}
        {...props}
      >
        {isLoading && (
          <span
            aria-hidden="true"
            className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent"
          />
        )}
        {children}
      </motion.button>
    )
  },
)
Button.displayName = 'Button'
