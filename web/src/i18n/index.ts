import i18next from 'i18next'
import { initReactI18next } from 'react-i18next'
import { setApiLanguage } from '../lib/api'
import ar from './ar.json'
import fr from './fr.json'

export const SUPPORTED_LANGUAGES = ['ar', 'fr'] as const
export type SupportedLanguage = (typeof SUPPORTED_LANGUAGES)[number]

const LANGUAGE_STORAGE_KEY = 'w4f_language'

function isSupportedLanguage(value: string | null): value is SupportedLanguage {
  return SUPPORTED_LANGUAGES.includes(value as SupportedLanguage)
}

// Section 2.1: "Default locale: ar" — a stored user choice (switched in
// this session or a previous one) wins, otherwise Arabic, never the
// browser's own language. `preferred_language` from `/auth/me` overrides
// this once login completes (see AuthProvider).
const storedLanguage = localStorage.getItem(LANGUAGE_STORAGE_KEY)
const initialLanguage: SupportedLanguage = isSupportedLanguage(storedLanguage) ? storedLanguage : 'ar'

export function dirFor(lang: SupportedLanguage): 'rtl' | 'ltr' {
  return lang === 'ar' ? 'rtl' : 'ltr'
}

export function applyDocumentDirection(lang: SupportedLanguage) {
  document.documentElement.lang = lang
  document.documentElement.dir = dirFor(lang)
}

export async function setLanguage(lang: SupportedLanguage) {
  localStorage.setItem(LANGUAGE_STORAGE_KEY, lang)
  await i18next.changeLanguage(lang)
  applyDocumentDirection(lang)
  setApiLanguage(lang)
}

applyDocumentDirection(initialLanguage)
setApiLanguage(initialLanguage)

void i18next.use(initReactI18next).init({
  lng: initialLanguage,
  fallbackLng: 'ar',
  resources: {
    ar: { translation: ar },
    fr: { translation: fr },
  },
  interpolation: { escapeValue: false },
})

export default i18next
