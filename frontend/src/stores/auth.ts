// frontend/src/stores/auth.ts
import { defineStore } from "pinia";
import { fetchAuthStatus, type AuthStatus } from "@/auth";
import { apiFetch } from "@/http";

type User = NonNullable<AuthStatus["user"]>;

let inFlight: Promise<void> | null = null;

export const useAuthStore = defineStore("auth", {
  state: () => ({
    user: null as User | null,
    checked: false,
    loading: false,
  }),

  getters: {
    isAuthenticated: (s) => !!s.user,
  },

  actions: {
    async refresh(force = false) {
      this.loading = true;
      try {
        const status = await fetchAuthStatus(force);
        this.user = status.authenticated ? (status.user as User) : null;
      } finally {
        this.checked = true;
        this.loading = false;
      }
    },

    async ensureChecked() {
      if (this.checked) return;
      if (inFlight) return inFlight;

      inFlight = this.refresh(false).finally(() => {
        inFlight = null;
      });

      return inFlight;
    },

    async logout() {
      try {
        await apiFetch("/api/logout/", { method: "POST" });
      } catch {
        // ignore
      } finally {
        // Also clear the store state
        this.user = null;
        this.checked = true;
        // Optional: force fresh status next time
        await fetchAuthStatus(true).catch(() => {});
      }
    },
  },
});
