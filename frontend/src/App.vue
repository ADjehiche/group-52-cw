<template>
  <div class="app-shell d-flex flex-column min-vh-100">
    <header class="py-3">
      <nav class="container">
        <router-link :to="{ name: 'Main Page' }">{{ $t('nav.mainPage') }}</router-link>
        |
        <router-link :to="{ name: 'Other Page' }">{{ $t('nav.otherPage') }}</router-link>

        <!-- Auth-dependent links -->
        <template v-if="authChecked && isAuthed">
          <span class="mx-1">|</span>

          <router-link :to="{ name: 'New Item' }">{{ $t('nav.newItem') }}</router-link>
          <span class="mx-1">|</span>

          <router-link :to="{ name: 'Profile' }">{{ $t('nav.profile') }}</router-link>
          <span class="mx-1">|</span>

          <button
            class="btn btn-link p-0 align-baseline"
            type="button"
            @click="logout"
            :disabled="loggingOut"
          >
            {{ loggingOut ? $t('nav.loggingOut') : $t('nav.logout') }}
          </button>
        </template>

        <!-- Auth checked but not authed -->
        <template v-else-if="authChecked">
          <span class="mx-1">|</span>
          <a class="text-decoration-none" href="/accounts/login/">{{ $t('nav.login') }}</a>
          <span class="mx-1">|</span>
          <a class="text-decoration-none" href="/accounts/signup/">{{ $t('nav.signup') }}</a>
        </template>
      </nav>
    </header>

    <main class="flex-grow-1 d-flex">
      <RouterView class="flex-grow-1" />
    </main>

    <Footer />
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, ref } from "vue";
import { RouterView } from "vue-router";
import Footer from "./components/Footer.vue";
import { useAuthStore } from "@/stores/auth";

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
html, body, #app {
  height: 100%;
}

body {
  margin: 0;
  color: #f3f4f6;
  background:
    radial-gradient(1200px 600px at 20% 10%, rgba(255, 164, 0, 0.12), transparent 55%),
    radial-gradient(900px 500px at 80% 20%, rgba(255, 164, 0, 0.10), transparent 60%),
    linear-gradient(180deg, #0b1220 0%, #070b14 100%);
}

.app-shell a {
  color: rgba(243, 244, 246, 0.85);
  text-decoration: none;
}
.app-shell a.router-link-active {
  text-decoration: underline;
}
</style>
