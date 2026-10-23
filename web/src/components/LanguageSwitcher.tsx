import { useTranslation } from 'react-i18next'
import { setLanguage, SUPPORTED_LANGUAGES, type SupportedLanguage } from '../i18n'

const LABELS: Record<SupportedLanguage, string> = {
  ar: 'العربية',
  fr: 'Français',
}

export function LanguageSwitcher() {
  const { t, i18n } = useTranslation()
  const current = i18n.language as SupportedLanguage

  return (
    <label className="flex items-center gap-2 text-sm text-muted-foreground">
      <span className="sr-only">{t('common.language')}</span>
      <select
        value={current}
        onChange={(event) => void setLanguage(event.target.value as SupportedLanguage)}
        className="cursor-pointer rounded-md border border-border bg-background px-2 py-1.5 text-sm text-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-ring"
      >
        {SUPPORTED_LANGUAGES.map((lang) => (
          <option key={lang} value={lang}>
            {LABELS[lang]}
          </option>
        ))}
      </select>
    </label>
  )
}
