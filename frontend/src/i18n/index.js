import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import translations from './translations';

// Get stored language from localStorage or default to German
const storedLang = typeof window !== 'undefined' ? localStorage.getItem('casedesk_language') : null;
const defaultLang = storedLang || 'de';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: translations.en },
      de: { translation: translations.de }
    },
    lng: defaultLang,
    fallbackLng: 'de', // Fallback to German
    interpolation: {
      escapeValue: false
    }
  });

// Listen for language changes and store in localStorage
i18n.on('languageChanged', (lng) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('casedesk_language', lng);
  }
});

export default i18n;
