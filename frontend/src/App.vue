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
import { defineComponent } from "vue";
import { RouterView } from "vue-router";
import Footer from "./components/Footer.vue";
import { apiFetch } from "@/http";
import { fetchAuthStatus } from "@/auth";

export default defineComponent({
    components: { RouterView, Footer },
    data() {
        return {
            loggingOut: false,
            authChecked: false,
            isAuthed: false,
        };
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
                await apiFetch("/api/logout/", {
                    method: "POST",
                });
            } catch (err) {
                // Ignore errors; still redirect to login.
            } finally {
                window.location.href = "/accounts/login/";
            }
        },
    },
});

</script>

<style scoped>
</style>
