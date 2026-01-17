import { createI18n } from 'vue-i18n';
import { messages, defaultLocale, supportedLocales } from '../locales';
import { getInitialLocale } from '../utils/locale';

const i18n = createI18n({
  legacy: false, // Use Composition API mode
  locale: getInitialLocale(supportedLocales, defaultLocale),
  fallbackLocale: defaultLocale,
  messages,
  globalInjection: true, // Makes $t available in templates
});

export default i18n;
