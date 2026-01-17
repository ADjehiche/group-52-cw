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

export default defineComponent({
    components: { RouterView, Footer },
});

</script>

<style scoped>
</style>

