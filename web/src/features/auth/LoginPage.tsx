import { motion, useReducedMotion } from 'framer-motion'
import { useState, type FormEvent } from 'react'
import { useTranslation } from 'react-i18next'
import { Navigate } from 'react-router-dom'
import { Button } from '../../components/Button'
import { inputClass, labelClass } from '../../components/formStyles'
import { LanguageSwitcher } from '../../components/LanguageSwitcher'
import { ApiError } from '../../lib/api'
import { useAuth } from './AuthContext'

export function LoginPage() {
  const { t } = useTranslation()
  const { status, login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const prefersReducedMotion = useReducedMotion()

  if (status === 'authenticated') return <Navigate to="/" replace />

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('common.error_generic'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <div className="flex justify-end p-4">
        <LanguageSwitcher />
      </div>
      <div className="flex flex-1 items-center justify-center px-4">
        <motion.div
          initial={prefersReducedMotion ? undefined : { opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: 'easeOut' }}
          className="w-full max-w-sm rounded-xl border border-border bg-white/60 p-8 shadow-md dark:bg-white/5"
        >
          <h1 className="mb-1 text-xl font-semibold text-foreground">{t('app.name')}</h1>
          <h2 className="mb-6 text-sm text-muted-foreground">{t('login.title')}</h2>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {error && (
              <motion.p
                initial={prefersReducedMotion ? undefined : { opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                role="alert"
                className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
              >
                {error}
              </motion.p>
            )}

            <div className="flex flex-col gap-1.5">
              <label htmlFor="email" className={labelClass}>
                {t('login.email_label')}
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className={`${inputClass} h-11 text-base`}
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor="password" className={labelClass}>
                {t('login.password_label')}
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className={`${inputClass} h-11 text-base`}
              />
            </div>

            <Button type="submit" isLoading={isSubmitting} className="mt-2 h-11 w-full text-base">
              {isSubmitting ? t('login.submitting') : t('login.submit')}
            </Button>
          </form>
        </motion.div>
      </div>
    </div>
  )
}
