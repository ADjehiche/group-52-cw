<template>
  <footer class="footer mt-auto py-3 bg-light border-top">
    <div class="container">
      <div class="row align-items-center">
        <div class="col-md-6 text-center text-md-start">
          <span class="text-muted">© 2026 Your App</span>
        </div>
        <div class="col-md-6 text-center text-md-end">
          <div class="d-inline-flex align-items-center">
            <label class="me-2 text-muted">{{ $t('footer.language') }}:</label>
            <div class="btn-group btn-group-sm" role="group" aria-label="Language selector">
              <button
                v-for="locale in availableLocales"
                :key="locale.code"
                type="button"
                class="btn"
                :class="currentLocale === locale.code ? 'btn-primary' : 'btn-outline-primary'"
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
  margin-top: 2rem;
}

.btn-group-sm .btn {
  min-width: 70px;
}
</style>
