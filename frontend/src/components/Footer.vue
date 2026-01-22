<template>
  <footer class="footer">
    <div class="footer-container">
      <div class="footer-content">
        <div class="footer-left">
          <span class="copyright">© 2026 Cbay 🏛️</span>
        </div>
        <div class="footer-right">
          <div class="language-selector">
            <label class="lang-label">{{ $t('footer.language') }}:</label>
            <div class="lang-buttons">
              <button
                v-for="locale in availableLocales"
                :key="locale.code"
                type="button"
                class="lang-btn"
                :class="{ active: currentLocale === locale.code }"
                @click="changeLocale(locale.code)"
              >
                {{ locale.label }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </footer>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { useI18n } from 'vue-i18n';
import { setStoredLocale } from '../utils/locale';

export default defineComponent({
  name: 'Footer',
  setup() {
    const { locale } = useI18n();

    const availableLocales = [
      { code: 'en', label: 'English' },
      { code: 'es', label: 'Español' }
    ];

    const changeLocale = (newLocale: string) => {
      locale.value = newLocale;
      setStoredLocale(newLocale);
    };

    return {
      currentLocale: locale,
      availableLocales,
      changeLocale
    };
  }
});
</script>

<style scoped>
.footer {
  margin-top: auto;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-light);
  box-shadow: 0 -1px 3px rgba(0, 0, 0, 0.05);
}

.footer-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1.5rem 2rem;
}

.footer-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.copyright {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.language-selector {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.lang-label {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin: 0;
}

.lang-buttons {
  display: flex;
  gap: 0.5rem;
}

.lang-btn {
  padding: 0.4rem 1rem;
  border: 2px solid var(--border-medium);
  background: var(--bg-primary);
  color: var(--text-secondary);
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.85rem;
  min-width: 70px;
}

.lang-btn:hover {
  border-color: var(--accent-coral);
  color: var(--accent-coral);
  background: var(--bg-hover);
}

.lang-btn.active {
  background: var(--accent-coral);
  border-color: var(--accent-coral);
  color: white;
}

@media (max-width: 768px) {
  .footer-content {
    flex-direction: column;
    text-align: center;
  }
  
  .language-selector {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>

