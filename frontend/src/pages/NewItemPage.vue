<template>
  <div class="container py-4" style="max-width: 720px">
    <h2 class="mb-4">Create new item</h2>

    <!-- Success / error messages -->
    <div v-if="successMessage" class="alert alert-success" role="alert">
      {{ successMessage }}
    </div>

    <div v-if="generalError" class="alert alert-danger" role="alert">
      {{ generalError }}
    </div>

    <form @submit.prevent="submit">
      <!-- Image uploads -->
      <div class="mb-3">
        <label class="form-label">Images (up to 8)</label>
        <input
          ref="imageInput"
          class="form-control"
          :class="{ 'is-invalid': !!errors.images }"
          type="file"
          accept="image/*"
          multiple
          @change="onImagesSelected"
        />
        <div class="d-flex gap-2 mt-2 align-items-center">
          <span class="text-muted small">
            {{ form.image_files.length }} / 8 selected
          </span>
          <button
            v-if="form.image_files.length"
            class="btn btn-outline-danger btn-sm"
            type="button"
            @click="clearImages"
          >
            Clear
          </button>
        </div>
        <div v-if="errors.images" class="invalid-feedback d-block">
          {{ errors.images }}
        </div>
      </div>

      <!-- Title -->
      <div class="mb-3">
        <label class="form-label">Title</label>
        <input
          v-model.trim="form.title"
          class="form-control"
          :class="{ 'is-invalid': !!errors.title }"
          type="text"
          required
          maxlength="120"
          placeholder="e.g. Wooden desk"
        />
        <div v-if="errors.title" class="invalid-feedback">
          {{ errors.title }}
        </div>
      </div>

      <!-- Description -->
      <div class="mb-3">
        <label class="form-label">Description</label>
        <textarea
          v-model.trim="form.description"
          class="form-control"
          rows="5"
          :class="{ 'is-invalid': !!errors.description }"
          placeholder="Describe the condition, size, etc."
        ></textarea>
        <div v-if="errors.description" class="invalid-feedback">
          {{ errors.description }}
        </div>
      </div>

      <div class="row">
        <!-- Starting price -->
        <div class="col-md-6 mb-3">
          <label class="form-label">Starting price</label>
          <input
            v-model.trim="form.starting_price"
            type="text"
            class="form-control"
            :class="{ 'is-invalid': !!errors.starting_price }"
            placeholder="e.g. 100.00"
          />
          <div v-if="errors.starting_price" class="invalid-feedback">
            {{ errors.starting_price }}
          </div>
        </div>

        <!-- End date/time -->
        <div class="col-md-6 mb-3">
          <label class="form-label">End date/time</label>
          <input
            v-model="form.ends_at"
            class="form-control"
            :class="{ 'is-invalid': !!errors.ends_at }"
            type="datetime-local"
            required
          />
          <div v-if="errors.ends_at" class="invalid-feedback">
            {{ errors.ends_at }}
          </div>
        </div>
      </div>

      <button class="btn btn-primary" type="submit" :disabled="submitting">
        {{ submitting ? "Creating..." : "Create listing" }}
      </button>
    </form>
  </div>
</template>

<script lang="ts">
    import { defineComponent } from "vue";
    import { apiFetch } from "@/http";

    type FieldErrors = Record<string, string>;

    type NewItemForm = {
    title: string;
    description: string;
    starting_price: string;
    ends_at: string; // datetime-local string
    image_files: File[];
    };

    export default defineComponent({
    name: "NewItemPage",
    data() {
        return {
        submitting: false,
        successMessage: "",
        generalError: "",
        errors: {} as Record<string, string>,
        form: {
            title: "",
            description: "",
            starting_price: "",  
            ends_at: "",         
            image_files: [],
        } as NewItemForm,
        };
    },
    methods: {
        onImagesSelected(event: Event) {
          const input = event.target as HTMLInputElement;
          const files = input.files ? Array.from(input.files) : [];
          this.form.image_files = files.slice(0, 8);
          if (files.length > 8) {
            this.errors.images = "You can upload up to 8 images.";
          }
        },
        clearImages() {
          this.form.image_files = [];
          this.errors.images = "";
          const input = this.$refs.imageInput as HTMLInputElement | undefined;
          if (input) {
            input.value = "";
          }
        },
        validateClient(): boolean {
        this.errors = {};
        this.generalError = "";
        this.successMessage = "";

        if (!this.form.title.trim()) {
            this.errors.title = "Title is required.";
        }

        if (!this.form.starting_price.trim()) {
            this.errors.starting_price = "Starting price is required.";
        } else {
            const n = Number(this.form.starting_price);
            if (Number.isNaN(n)) {
            this.errors.starting_price = "Starting price must be a valid number.";
            } else if (n < 0) {
            this.errors.starting_price = "Starting price must be 0 or more.";
            }
        }

        if (!this.form.ends_at) {
          this.errors.ends_at = "End date/time is required.";
        } else {
          const endsAt = new Date(this.form.ends_at);
          if (endsAt <= new Date()) {
          this.errors.ends_at = "End date/time must be in the future.";
          }
        }

        if (this.form.image_files.length > 8) {
          this.errors.images = "You can upload up to 8 images.";
        }

        return Object.keys(this.errors).length === 0;
        },

        async submit() {
        if (!this.validateClient()) return;

        this.submitting = true;
        this.generalError = "";
        this.successMessage = "";

        try {
            const formData = new FormData();
            formData.append("title", this.form.title.trim());
            formData.append("description", this.form.description.trim());
            formData.append("starting_price", this.form.starting_price.trim());
            formData.append("ends_at", this.form.ends_at);
            this.form.image_files.forEach((file) => {
              formData.append("images", file);
            });

            const resp = await apiFetch("/api/items/", {
            method: "POST",
            body: formData,
            });

            const data = await resp.json().catch(() => ({}));

            if (resp.status === 201) {
            this.successMessage = "Item created successfully.";
            this.form = {
                title: "",
                description: "",
                starting_price: "",
                ends_at: "",
              image_files: [],
            };
            this.clearImages();
            this.errors = {};
            return;
            }

            if (resp.status === 401) {
            this.generalError = "You must be logged in to create items.";
            return;
            }

            if (data && data.errors) {
            this.errors = data.errors as FieldErrors;
            return;
            }

            this.generalError = "Something went wrong. Please try again.";
        } catch {
            this.generalError = "Network error. Is the backend running?";
        } finally {
            this.submitting = false;
        }
        },
    },
    });
</script>

<style scoped></style>
