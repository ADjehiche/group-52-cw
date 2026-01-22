<template>
  <div class="auth-shell">
    <div class="auth-card">
      <div class="auth-header">
        <h1 class="auth-title">{{ $t('pages.profile.title') }}</h1>
        <p class="auth-subtitle">{{ $t('pages.profile.subtitle') }}</p>
      </div>

      <div v-if="loading" class="auth-muted">Loading...</div>

      <div v-else>
        <div v-if="globalError" class="auth-alert auth-alert--error" role="alert">
          {{ globalError }}
        </div>
        <div v-if="successMsg" class="auth-alert auth-alert--success" role="alert">
          {{ successMsg }}
        </div>

        <!-- Image -->
        <div class="section">
          <div class="section-head">
            <h2 class="section-title">{{ $t('pages.profile.profileImage') }}</h2>
          </div>

          <div class="image-row">
            <div class="avatar">
              <img
                v-if="currentImageSrc"
                :src="currentImageSrc"
                alt="Profile"
                class="avatar-img"
              />
              <span v-else class="auth-muted small">{{ $t('pages.profile.noImage') }}</span>
            </div>

            <div class="image-controls">
              <input
                class="auth-input"
                type="file"
                accept="image/*"
                @change="onFileChange"
              />

              <div v-if="errors.profile_image" class="auth-error">
                {{ errors.profile_image }}
              </div>

              <button
                class="btn-primary"
                type="button"
                :disabled="uploading || !imageFile"
                @click="uploadImage"
              >
                {{ uploading ? $t('pages.profile.uploading') : $t('pages.profile.uploadImage') }}
              </button>
            </div>
          </div>
        </div>

        <!-- Details -->
        <div class="section">
          <div class="section-head">
            <h2 class="section-title">{{ $t('pages.profile.details') }}</h2>
          </div>

          <div class="field">
            <label class="auth-label">{{ $t('pages.profile.username') }}</label>
            <input class="auth-input" type="text" :value="profile?.username" disabled />
          </div>

          <div class="field">
            <label class="auth-label">{{ $t('pages.profile.email') }}</label>
            <input
              class="auth-input"
              type="email"
              v-model="form.email"
              :class="{ 'auth-input--invalid': !!errors.email }"
            />
            <div v-if="errors.email" class="auth-error">{{ errors.email }}</div>
          </div>

          <div class="field">
            <label class="auth-label">{{ $t('pages.profile.dateOfBirth') }}</label>
            <input
              class="auth-input"
              type="date"
              v-model="form.date_of_birth"
              :class="{ 'auth-input--invalid': !!errors.date_of_birth }"
            />
            <div v-if="errors.date_of_birth" class="auth-error">
              {{ errors.date_of_birth }}
            </div>
          </div>

          <!-- Follower Stats -->
          <div class="field">
            <label class="auth-label">Social Stats</label>
            <div class="stats-row">
              <div class="stat-item">
                <span class="stat-number">{{ followerStats.follower_count }}</span>
                <span class="stat-label">Followers</span>
              </div>
              <div class="stat-item">
                <span class="stat-number">{{ followerStats.following_count }}</span>
                <span class="stat-label">Following</span>
              </div>
            </div>
          </div>

          <button
            class="btn-primary"
            type="button"
            :disabled="saving"
            @click="saveProfile"
          >
            {{ saving ? $t('pages.profile.saving') : $t('pages.profile.saveChanges') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { apiFetch } from "@/http";

type FieldErrors = Record<string, string>;

type UserProfile = {
  id: number;
  username: string;
  email: string;
  date_of_birth: string | null;
  profile_image_url: string | null;
};

export default defineComponent({
  name: "ProfilePage",
  data() {
    return {
      loading: true,
      saving: false,
      uploading: false,
      globalError: "" as string,
      successMsg: "" as string,
      errors: {} as FieldErrors,

      profile: null as UserProfile | null,
      form: {
        email: "",
        date_of_birth: "", // YYYY-MM-DD or ""
      },

      imageFile: null as File | null,
      imagePreviewUrl: "" as string, // object URL
      
      followerStats: {
        follower_count: 0,
        following_count: 0,
      },
    };
  },

  computed: {
    currentImageSrc(): string {
      if (this.imagePreviewUrl) return this.imagePreviewUrl;
      return this.profile?.profile_image_url || "";
    },
  },

  async created() {
    await this.loadProfile();
    await this.loadFollowerStats();
  },

  beforeUnmount() {
    if (this.imagePreviewUrl) URL.revokeObjectURL(this.imagePreviewUrl);
  },

  methods: {
    async loadProfile() {
      this.loading = true;
      this.globalError = "";
      this.successMsg = "";
      this.errors = {};

      try {
        const resp = await apiFetch("/api/profile/");
        if (resp.status === 401) {
          window.location.href = "/accounts/login/";
          return;
        }
        if (!resp.ok) {
          this.globalError = "Failed to load profile.";
          return;
        }

        const data = (await resp.json()) as UserProfile;
        this.profile = data;
        this.form.email = data.email || "";
        this.form.date_of_birth = data.date_of_birth || "";
      } catch (e) {
        this.globalError = "Network error while loading profile.";
      } finally {
        this.loading = false;
      }
    },

    async loadFollowerStats() {
      try {
        const resp = await apiFetch("/api/follower-stats/");
        if (resp.ok) {
          const data = await resp.json();
          this.followerStats = {
            follower_count: data.follower_count || 0,
            following_count: data.following_count || 0,
          };
        }
      } catch (e) {
        // Silently fail - stats are not critical
        console.error("Failed to load follower stats", e);
      }
    },

    async saveProfile() {
      this.saving = true;
      this.globalError = "";
      this.successMsg = "";
      this.errors = {};

      try {
        const resp = await apiFetch("/api/profile/", {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: this.form.email,
            date_of_birth: this.form.date_of_birth, // "" clears it
          }),
        });

        const data = (await resp.json()) as any;

        if (!resp.ok) {
          this.errors = (data?.errors || {}) as FieldErrors;
          if (!Object.keys(this.errors).length) {
            this.globalError = "Could not save changes.";
          }
          return;
        }

        this.profile = data as UserProfile;
        this.form.email = this.profile.email || "";
        this.form.date_of_birth = this.profile.date_of_birth || "";
        this.successMsg = "Saved!";
      } catch (e) {
        this.globalError = "Network error while saving.";
      } finally {
        this.saving = false;
      }
    },

    onFileChange(evt: Event) {
      this.errors = { ...this.errors };
      delete this.errors.profile_image;

      const input = evt.target as HTMLInputElement;
      const file = input.files?.[0] || null;

      this.imageFile = file;

      if (this.imagePreviewUrl) {
        URL.revokeObjectURL(this.imagePreviewUrl);
        this.imagePreviewUrl = "";
      }

      if (file) {
        this.imagePreviewUrl = URL.createObjectURL(file);
      }
    },

    async uploadImage() {
      if (!this.imageFile) return;

      this.uploading = true;
      this.globalError = "";
      this.successMsg = "";
      this.errors = {};

      try {
        const fd = new FormData();
        fd.append("profile_image", this.imageFile);

        const resp = await apiFetch("/api/profile/image/", {
          method: "POST",
          body: fd,
        });

        const data = (await resp.json()) as any;

        if (!resp.ok) {
          this.errors = (data?.errors || {}) as FieldErrors;
          if (!Object.keys(this.errors).length) {
            this.globalError = "Could not upload image.";
          }
          return;
        }

        this.profile = data as UserProfile;

        // reset file + preview (we now show server URL)
        this.imageFile = null;
        if (this.imagePreviewUrl) {
          URL.revokeObjectURL(this.imagePreviewUrl);
          this.imagePreviewUrl = "";
        }

        this.successMsg = "Image updated!";
      } catch (e) {
        this.globalError = "Network error while uploading image.";
      } finally {
        this.uploading = false;
      }
    },
  },
});
</script>

<style scoped>
/* Light theme for Profile Page */
.auth-shell {
  min-height: calc(100vh - 60px);
  display: grid;
  place-items: center;
  padding: 48px 16px;
  background: var(--gradient-bg);
}

.auth-card {
  width: 100%;
  max-width: 760px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: var(--shadow-lg);
}

.auth-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid var(--border-light);
}

.auth-title {
  margin: 0;
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
}

.auth-subtitle {
  margin: 0.5rem 0 0;
  color: var(--text-secondary);
  font-size: 1rem;
}

.auth-muted {
  color: var(--text-muted);
}

.section {
  margin-top: 1.5rem;
  padding: 1.25rem;
  border-radius: 12px;
  background: var(--bg-primary);
  border: 1px solid var(--border-light);
}

.section-head {
  margin-bottom: 1rem;
}

.section-title {
  margin: 0;
  font-size: 0.875rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent-amber);
  font-weight: 600;
}

.image-row {
  display: grid;
  grid-template-columns: 96px 1fr;
  gap: 1rem;
  align-items: center;
}

@media (max-width: 560px) {
  .image-row {
    grid-template-columns: 1fr;
  }
  
  .auth-title {
    font-size: 1.5rem;
  }
}

.avatar {
  width: 96px;
  height: 96px;
  border-radius: 12px;
  overflow: hidden;
  display: grid;
  place-items: center;
  background: var(--bg-secondary);
  border: 2px solid var(--border-medium);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-controls {
  display: grid;
  gap: 0.75rem;
}

.field {
  margin-top: 1rem;
  display: grid;
  gap: 0.5rem;
}

.stats-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 0.5rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  background: var(--bg-secondary);
  border: 2px solid var(--border-medium);
  border-radius: 10px;
  transition: all 0.2s ease;
}

.stat-item:hover {
  border-color: var(--accent-coral);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.stat-number {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--accent-coral);
  line-height: 1;
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
}

.auth-label {
  font-size: 0.875rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--text-secondary);
  font-weight: 600;
}

.auth-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  background: var(--bg-secondary);
  border: 2px solid var(--border-medium);
  color: var(--text-primary);
  outline: none;
  transition: all 0.2s ease;
  font-size: 1rem;
}

.auth-input:focus {
  border-color: var(--accent-coral);
  box-shadow: 0 0 0 3px rgba(255, 107, 107, 0.1);
}

.auth-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  background: var(--bg-primary);
}

.auth-input--invalid {
  border-color: #d32f2f;
}

.btn-primary {
  margin-top: 0.5rem;
  width: 100%;
  border: none;
  border-radius: 10px;
  padding: 0.75rem 1rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: white;
  background: var(--gradient-warm);
  box-shadow: var(--shadow-md);
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 1rem;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.auth-error {
  font-size: 0.875rem;
  color: #d32f2f;
  margin-top: 0.25rem;
}

.auth-alert {
  padding: 0.75rem 1rem;
  border-radius: 10px;
  margin-bottom: 1rem;
  border: 2px solid transparent;
  font-size: 0.95rem;
  font-weight: 500;
}

.auth-alert--error {
  background: rgba(211, 47, 47, 0.1);
  border-color: rgba(211, 47, 47, 0.3);
  color: #d32f2f;
}

.auth-alert--success {
  background: rgba(46, 125, 50, 0.1);
  border-color: rgba(46, 125, 50, 0.3);
  color: #2e7d32;
}

.small {
  font-size: 0.875rem;
}
</style>

