// Example of how to use Vue Router

import { createRouter, createWebHistory } from 'vue-router'
import { pinia } from "@/pinia";
import { useAuthStore } from "@/stores/auth";

// 1. Define route components.
// These can be imported from other files
import MainPage from '../pages/MainPage.vue';
import OtherPage from '../pages/OtherPage.vue';
import NewItemPage from "../pages/NewItemPage.vue";


let base = (import.meta.env.MODE == 'development') ? import.meta.env.BASE_URL : ''

// 2. Define some routes
// Each route should map to a component.
// We'll talk about nested routes later.
const router = createRouter({
    history: createWebHistory(base),
    routes: [
        { path: '/', name: 'Main Page', component: MainPage, meta: { requiresAuth: false } },
        { path: '/other/', name: 'Other Page', component: OtherPage, meta: { requiresAuth: false } },
        { path: "/items/new/", name: "New Item", component: NewItemPage, meta: { requiresAuth: true } },
    ]
})

router.beforeEach(async (to, _from, next) => {
  const requiresAuth = to.meta.requiresAuth === true;
  if (!requiresAuth) return next();

  const auth = useAuthStore(pinia);
  await auth.ensureChecked();

  if (auth.isAuthenticated) return next();

  const nextUrl = encodeURIComponent(to.fullPath);
  window.location.href = `/accounts/login/?next=${nextUrl}`;
  return next(false);
});


export default router
