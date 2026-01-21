<template>
    <div class="d-flex flex-column min-vh-100">
        <main class="container pt-4 flex-grow-1">
            <div>
                <router-link
                    class=""
                    :to="{name: 'Main Page'}"
                >
                    {{ $t('nav.mainPage') }}
                </router-link>
                |
                <router-link
                    class=""
                    :to="{name: 'Other Page'}"
                >
                    {{ $t('nav.otherPage') }}
                </router-link>
                |
                <router-link
                    class=""
                    :to="{name: 'New Item'}"
                >
                    {{ $t('nav.newItem') }}
                </router-link>
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
            </div>
            <RouterView class="flex-shrink-0" />
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
  setup() {
    const auth = useAuthStore();
    const loggingOut = ref(false);

    // hydrate once on app load
    auth.ensureChecked();

    const authChecked = computed(() => auth.checked);
    const isAuthed = computed(() => auth.isAuthenticated);

    const logout = async () => {
      loggingOut.value = true;
      await auth.logout();
      window.location.href = "/accounts/login/";
    };

    return { auth, loggingOut, authChecked, isAuthed, logout };
  },
});
</script>


<style scoped>
</style>
