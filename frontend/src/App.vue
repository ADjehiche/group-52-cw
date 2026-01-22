<template>
  <div class="app-shell">
    <header class="header">
      <nav class="nav-container">
        <div class="nav-brand">
          <router-link :to="{ name: 'Main Page' }" class="brand-link">
            {{ $t('nav.mainPage') }}
          </router-link>
        </div>
        
        <div class="nav-links">
          <!-- Auth-dependent links -->
          <template v-if="authChecked && isAuthed">
            <router-link :to="{ name: 'New Item' }" class="nav-link">
              {{ $t('nav.newItem') }}
            </router-link>

            <router-link :to="{ name: 'Profile' }" class="nav-link">
              {{ $t('nav.profile') }}
            </router-link>

            <button
              class="btn-logout"
              type="button"
              @click="logout"
              :disabled="loggingOut"
            >
              {{ loggingOut ? $t('nav.loggingOut') : $t('nav.logout') }}
            </button>
          </template>

          <!-- Auth checked but not authed -->
          <template v-else-if="authChecked">
            <a class="nav-link" href="/accounts/login/">{{ $t('nav.login') }}</a>
            <a class="nav-link btn-signup" href="/accounts/signup/">{{ $t('nav.signup') }}</a>
          </template>
        </div>
      </nav>
    </header>

    <main class="main-content">
      <RouterView />
    </main>

    <Footer />
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { RouterView } from "vue-router";
import Footer from "./components/Footer.vue";
import { fetchAuthStatus } from "@/auth";
import { apiFetch } from "@/http";

export default defineComponent({
  components: { RouterView, Footer },
  data() {
    return { loggingOut: false, authChecked: false, isAuthed: false };
  },
   async created() {
     try {
       const status = await fetchAuthStatus();
       this.isAuthed = status.authenticated;
     } catch (error) {
       this.isAuthed = false;
     } finally {
       this.authChecked = true;
     }
   },
  methods: {
    async logout() {
      this.loggingOut = true;
      try {
        await apiFetch("/api/logout/", { method: "POST" });
      } finally {
        window.location.href = "/accounts/login/";
      }
    },
  },
});
</script>


<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--gradient-bg);
}

/* Header Styling */
.header {
  background: var(--bg-secondary);
  box-shadow: var(--shadow-sm);
  border-bottom: 1px solid var(--border-light);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
}

.nav-brand .brand-link {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--accent-coral);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.nav-brand .brand-link:hover {
  color: var(--accent-coral-hover);
  transform: translateY(-1px);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.nav-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.nav-link:hover {
  color: var(--accent-coral);
  background: var(--bg-hover);
}

.nav-link.router-link-active {
  color: var(--accent-coral);
  background: var(--bg-hover);
}

.btn-signup {
  background: var(--gradient-warm);
  color: white;
  font-weight: 600;
}

.btn-signup:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  color: white;
}

.btn-logout {
  background: transparent;
  border: 2px solid var(--accent-sage);
  color: var(--accent-sage);
  font-weight: 600;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.95rem;
}

.btn-logout:hover:not(:disabled) {
  background: var(--accent-sage);
  color: white;
  transform: translateY(-1px);
}

.btn-logout:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Main Content */
.main-content {
  flex: 1;
  padding: 2rem 1rem;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
}

/* Responsive Design */
@media (max-width: 768px) {
  .nav-container {
    flex-direction: column;
    padding: 1rem;
  }
  
  .nav-links {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .main-content {
    padding: 1rem 0.5rem;
  }
}
</style>

