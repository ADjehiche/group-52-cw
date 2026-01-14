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

      <!-- Image URL -->
      <div class="mb-3">
        <label class="form-label">Image URL (optional)</label>
        <input
          v-model.trim="form.image_url"
          class="form-control"
          :class="{ 'is-invalid': !!errors.image_url }"
          type="url"
          placeholder="https://..."
        />
        <div v-if="errors.image_url" class="invalid-feedback">
          {{ errors.image_url }}
        </div>
      </div>

      <button class="btn btn-primary" type="submit" :disabled="submitting">
        {{ submitting ? "Creating..." : "Create item" }}
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
    image_url: string;
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
            image_url: "",       
        } as NewItemForm,
        };
    },
    methods: {
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
        }

        return Object.keys(this.errors).length === 0;
        },

        async submit() {
        if (!this.validateClient()) return;

        this.submitting = true;
        this.generalError = "";
        this.successMessage = "";

        try {
            const payload = {
            title: this.form.title.trim(),
            description: this.form.description.trim(),
            starting_price: this.form.starting_price.trim(),
            ends_at: this.form.ends_at,
            image_url: this.form.image_url.trim(),
            };

            const resp = await apiFetch("/api/items/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
            });

            const data = await resp.json().catch(() => ({}));

            if (resp.status === 201) {
            this.successMessage = "Item created successfully.";
            this.form = {
                title: "",
                description: "",
                starting_price: "",
                ends_at: "",
                image_url: "",
            };
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
