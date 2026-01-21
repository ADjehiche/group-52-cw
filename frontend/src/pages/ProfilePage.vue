<template>
  <div class="auth-shell">
    <div class="auth-card">
      <div class="auth-header">
        <h1 class="auth-title">Profile</h1>
        <p class="auth-subtitle">Manage your details and profile image.</p>
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
            <h2 class="section-title">Profile image</h2>
          </div>

          <div class="image-row">
            <div class="avatar">
              <img
                v-if="currentImageSrc"
                :src="currentImageSrc"
                alt="Profile"
                class="avatar-img"
              />
              <span v-else class="auth-muted small">No image</span>
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
                {{ uploading ? "Uploading..." : "Upload image" }}
              </button>
            </div>
          </div>
        </div>

        <!-- Details -->
        <div class="section">
          <div class="section-head">
            <h2 class="section-title">Details</h2>
          </div>

          <div class="field">
            <label class="auth-label">Username</label>
            <input class="auth-input" type="text" :value="profile?.username" disabled />
          </div>

          <div class="field">
            <label class="auth-label">Email</label>
            <input
              class="auth-input"
              type="email"
              v-model="form.email"
              :class="{ 'auth-input--invalid': !!errors.email }"
            />
            <div v-if="errors.email" class="auth-error">{{ errors.email }}</div>
          </div>

          <div class="field">
            <label class="auth-label">Date of birth</label>
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

          <button
            class="btn-primary"
            type="button"
            :disabled="saving"
            @click="saveProfile"
          >
            {{ saving ? "Saving..." : "Save changes" }}
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
/* Page background like your login/signup */
.auth-shell {
  min-height: calc(100vh - 60px);
  display: grid;
  place-items: center;
  padding: 48px 16px;
  background:
    radial-gradient(1200px 600px at 20% 10%, rgba(255, 164, 0, 0.12), transparent 55%),
    radial-gradient(900px 500px at 80% 20%, rgba(255, 164, 0, 0.10), transparent 60%),
    linear-gradient(180deg, #0b1220 0%, #070b14 100%);
}

.auth-card {
  width: 100%;
  max-width: 760px;
  background: rgba(17, 24, 39, 0.86);
  border: 1px solid rgba(255, 164, 0, 0.18);
  border-radius: 18px;
  padding: 28px;
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.55),
    0 0 0 1px rgba(255, 164, 0, 0.08) inset;
  backdrop-filter: blur(10px);
}

.auth-header {
  margin-bottom: 18px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.auth-title {
  margin: 0;
  font-size: 36px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: #f3f4f6;
}

.auth-subtitle {
  margin: 8px 0 0;
  color: rgba(243, 244, 246, 0.65);
  font-size: 14px;
}

.auth-muted {
  color: rgba(243, 244, 246, 0.65);
}

.section {
  margin-top: 18px;
  padding: 16px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.section-head {
  margin-bottom: 12px;
}

.section-title {
  margin: 0;
  font-size: 14px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(243, 244, 246, 0.72);
}

.image-row {
  display: grid;
  grid-template-columns: 96px 1fr;
  gap: 14px;
  align-items: center;
}

@media (max-width: 560px) {
  .image-row {
    grid-template-columns: 1fr;
  }
}

.avatar {
  width: 96px;
  height: 96px;
  border-radius: 14px;
  overflow: hidden;
  display: grid;
  place-items: center;
  background: rgba(2, 6, 23, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.10);
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-controls {
  display: grid;
  gap: 10px;
}

.field {
  margin-top: 12px;
  display: grid;
  gap: 8px;
}

.auth-label {
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(243, 244, 246, 0.70);
}

.auth-input {
  width: 100%;
  padding: 12px 12px;
  border-radius: 12px;
  background: rgba(2, 6, 23, 0.40);
  border: 1px solid rgba(255, 255, 255, 0.10);
  color: #f3f4f6;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.auth-input:focus {
  border-color: rgba(255, 164, 0, 0.55);
  box-shadow: 0 0 0 4px rgba(255, 164, 0, 0.12);
}

.auth-input:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.auth-input--invalid {
  border-color: rgba(239, 68, 68, 0.7);
}

.btn-primary {
  margin-top: 6px;
  width: 100%;
  border: none;
  border-radius: 12px;
  padding: 12px 14px;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #0b1220;
  background: linear-gradient(180deg, #ffb020 0%, #f59e0b 100%);
  box-shadow: 0 10px 28px rgba(245, 158, 11, 0.22);
  cursor: pointer;
  transition: transform 0.08s ease, filter 0.15s ease, opacity 0.15s ease;
}

.btn-primary:hover {
  filter: brightness(1.02);
}

.btn-primary:active {
  transform: translateY(1px);
}

.btn-primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.auth-error {
  font-size: 12px;
  color: rgba(248, 113, 113, 0.95);
}

.auth-alert {
  padding: 10px 12px;
  border-radius: 12px;
  margin-bottom: 12px;
  border: 1px solid transparent;
  font-size: 14px;
}

.auth-alert--error {
  background: rgba(239, 68, 68, 0.10);
  border-color: rgba(239, 68, 68, 0.25);
  color: rgba(248, 113, 113, 0.95);
}

.auth-alert--success {
  background: rgba(34, 197, 94, 0.10);
  border-color: rgba(34, 197, 94, 0.25);
  color: rgba(134, 239, 172, 0.95);
}
</style>
