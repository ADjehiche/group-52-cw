const LOCALE_STORAGE_KEY = 'locale';

/**
 * Get the stored locale from localStorage
 */
export function getStoredLocale(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(LOCALE_STORAGE_KEY);
}

/**
 * Save locale to localStorage
 */
export function setStoredLocale(locale: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(LOCALE_STORAGE_KEY, locale);
}

/**
 * Get browser's preferred language
 * Returns the first two characters of the browser language (e.g., 'en' from 'en-US')
 */
export function getBrowserLocale(): string {
  if (typeof window === 'undefined') return 'en';
  
  const browserLang = navigator.language || 'en';
  return browserLang.substring(0, 2);
}

/**
 * Get the initial locale to use
 * Priority: localStorage > browser language > default
 */
export function getInitialLocale(supportedLocales: string[], defaultLocale: string): string {
  // Check localStorage first
  const storedLocale = getStoredLocale();
  if (storedLocale && supportedLocales.includes(storedLocale)) {
    return storedLocale;
  }

  // Check browser language
  const browserLocale = getBrowserLocale();
  if (supportedLocales.includes(browserLocale)) {
    return browserLocale;
  }

  // Fall back to default
  return defaultLocale;
}
