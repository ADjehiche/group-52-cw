<template>
  <div class="container py-4" style="max-width: 720px;">
    <h1 class="h3 mb-4">Profile</h1>

    <div v-if="loading" class="text-muted">Loading...</div>

    <div v-else>
      <div v-if="globalError" class="alert alert-danger" role="alert">
        {{ globalError }}
      </div>
      <div v-if="successMsg" class="alert alert-success" role="alert">
        {{ successMsg }}
      </div>

      <!-- Image -->
      <div class="card mb-4">
        <div class="card-body">
          <h2 class="h5 mb-3">Profile image</h2>

          <div class="d-flex align-items-center gap-3 flex-wrap">
            <div
              class="border rounded d-flex align-items-center justify-content-center"
              style="width: 96px; height: 96px; overflow: hidden;"
            >
              <img
                v-if="currentImageSrc"
                :src="currentImageSrc"
                alt="Profile"
                style="width: 100%; height: 100%; object-fit: cover;"
              />
              <span v-else class="text-muted small">No image</span>
            </div>

            <div class="flex-grow-1">
              <input
                class="form-control"
                type="file"
                accept="image/*"
                @change="onFileChange"
              />
              <div v-if="errors.profile_image" class="text-danger small mt-1">
                {{ errors.profile_image }}
              </div>

              <button
                class="btn btn-primary mt-2"
                type="button"
                :disabled="uploading || !imageFile"
                @click="uploadImage"
              >
                {{ uploading ? "Uploading..." : "Upload image" }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Details -->
      <div class="card">
        <div class="card-body">
          <h2 class="h5 mb-3">Details</h2>

          <div class="mb-3">
            <label class="form-label">Username</label>
            <input class="form-control" type="text" :value="profile?.username" disabled />
          </div>

          <div class="mb-3">
            <label class="form-label">Email</label>
            <input
              class="form-control"
              type="email"
              v-model="form.email"
              :class="{ 'is-invalid': !!errors.email }"
            />
            <div v-if="errors.email" class="invalid-feedback">{{ errors.email }}</div>
          </div>

          <div class="mb-3">
            <label class="form-label">Date of birth</label>
            <input
              class="form-control"
              type="date"
              v-model="form.date_of_birth"
              :class="{ 'is-invalid': !!errors.date_of_birth }"
            />
            <div v-if="errors.date_of_birth" class="invalid-feedback">
              {{ errors.date_of_birth }}
            </div>
          </div>

          <button
            class="btn btn-success"
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
