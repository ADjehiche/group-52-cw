<template>
    <main class="container pt-4">
        <div>
            <router-link
                class=""
                :to="{name: 'Main Page'}"
            >
                Main Page
            </router-link>
            |
            <router-link
                class=""
                :to="{name: 'Other Page'}"
            >
                Other Page
            </router-link>
            |
            <router-link
                class=""
                :to="{name: 'New Item'}"
            >
                New Item
            </router-link>
            <template v-if="authChecked">
                |
                <button
                    v-if="isAuthed"
                    class="btn btn-link p-0 align-baseline"
                    type="button"
                    @click="logout"
                    :disabled="loggingOut"
                >
                    {{ loggingOut ? "Logging out..." : "Logout" }}
                </button>
                <span v-else>
                    |
                    <a class="text-decoration-none" href="/accounts/login/">Login</a>
                    |
                    <a class="text-decoration-none" href="/accounts/signup/">Sign up</a>
                </span>
            </template>
        </div>
        <RouterView class="flex-shrink-0" />
    </main>
</template>


<script lang="ts">
import { defineComponent } from "vue";
import { RouterView } from "vue-router";
import { apiFetch } from "@/http";
import { fetchAuthStatus } from "@/auth";

export default defineComponent({
    components: { RouterView },
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
