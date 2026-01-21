<template>
  <div class="app-shell d-flex flex-column min-vh-100">
    <header class="py-3">
      <nav class="container">
        <router-link :to="{ name: 'Main Page' }">{{ $t('nav.mainPage') }}</router-link>
        |
        <router-link :to="{ name: 'Other Page' }">{{ $t('nav.otherPage') }}</router-link>
        |
        <router-link :to="{ name: 'New Item' }">{{ $t('nav.newItem') }}</router-link>
        |
        <router-link :to="{ name: 'Profile' }">{{ $t('nav.profile') }}</router-link>

        <template v-if="authChecked">
          <span class="mx-1">|</span>
          <template v-if="isAuthed">
            <button
              class="btn btn-link p-0 align-baseline"
              type="button"
              @click="logout"
              :disabled="loggingOut"
            >
              {{ loggingOut ? $t('nav.loggingOut') : $t('nav.logout') }}
            </button>
          </template>
          <template v-else>
            <a class="text-decoration-none" href="/accounts/login/">{{ $t('nav.login') }}</a>
            <span class="mx-1">|</span>
            <a class="text-decoration-none" href="/accounts/signup/">{{ $t('nav.signup') }}</a>
          </template>
        </template>
      </nav>
    </header>

    <!-- RouterView is now full-width/full-height area -->
    <main class="flex-grow-1 d-flex">
      <RouterView class="flex-grow-1" />
    </main>

    <Footer />
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { RouterView } from "vue-router";
import Footer from "./components/Footer.vue";
import { apiFetch } from "@/http";
import { fetchAuthStatus } from "@/auth";

export default defineComponent({
  components: { RouterView, Footer },
  data() {
    return { loggingOut: false, authChecked: false, isAuthed: false };
  },
  async created() {
    const status = await fetchAuthStatus();
    this.isAuthed = status.authenticated;
    this.authChecked = true;
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

<!-- IMPORTANT: NOT scoped -->
<style>
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
