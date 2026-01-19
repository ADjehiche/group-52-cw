<template>
  <div class="new-item-page">
    <div class="auth-shell">
      <div class="brand">
        <h1>Create new item</h1>
        <p class="description">
          List your item for auction and start receiving bids.
        </p>
      </div>

      <!-- Success message -->
      <div v-if="successMessage" class="alert alert-success">
        {{ successMessage }}
      </div>

      <!-- General error message -->
      <div v-if="generalError" class="alert">
        {{ generalError }}
      </div>

      <form @submit.prevent="submit">
        <!-- Title -->
        <div>
          <label for="title">Title</label>
          <input
            id="title"
            v-model.trim="form.title"
            type="text"
            required
            maxlength="120"
            placeholder="e.g. Wooden desk"
          />
          <div v-if="errors.title" class="error-text">
            {{ errors.title }}
          </div>
        </div>

        <!-- Description -->
        <div>
          <label for="description">Description</label>
          <textarea
            id="description"
            v-model.trim="form.description"
            rows="5"
            placeholder="Describe the condition, size, etc."
          ></textarea>
          <div v-if="errors.description" class="error-text">
            {{ errors.description }}
          </div>
        </div>

        <div class="form-row">
          <!-- Starting price -->
          <div class="form-col">
            <label for="starting_price">Starting price</label>
            <input
              id="starting_price"
              v-model.trim="form.starting_price"
              type="text"
              placeholder="e.g. 100.00"
            />
            <div v-if="errors.starting_price" class="error-text">
              {{ errors.starting_price }}
            </div>
          </div>

          <!-- End date/time -->
          <div class="form-col">
            <label for="ends_at">End date/time</label>
            <input
              id="ends_at"
              v-model="form.ends_at"
              type="datetime-local"
              required
            />
            <div v-if="errors.ends_at" class="error-text">
              {{ errors.ends_at }}
            </div>
          </div>
        </div>

        <!-- Multiple Image Upload (Drag & Drop) -->
        <div>
          <label>Images (up to 8)</label>
          <div
            class="upload-zone"
            :class="{ 'drag-over': isDragging, 'has-image': imagePreviews.length }"
            @drop.prevent="handleDrop"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @click="triggerFileInput"
          >
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              multiple
              @change="handleFileSelect"
              style="display: none"
            />
            
            <div v-if="!imagePreviews.length" class="upload-placeholder">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <circle cx="8.5" cy="8.5" r="1.5"></circle>
                <polyline points="21 15 16 10 5 21"></polyline>
              </svg>
              <p>Click to upload or drag and drop</p>
              <span class="upload-hint">PNG, JPG, GIF up to 10MB each (max 8)</span>
            </div>
            
            <div v-else class="image-preview-container">
              <div class="image-preview-grid">
                <div
                  v-for="(preview, index) in imagePreviews"
                  :key="preview + index"
                  class="image-preview-item"
                >
                  <img :src="preview" alt="Preview" class="image-preview" />
                  <button
                    type="button"
                    class="remove-image"
                    @click.stop="removeImage(index)"
                    title="Remove image"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <line x1="18" y1="6" x2="6" y2="18"></line>
                      <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                  </button>
                </div>
              </div>
              <span class="upload-hint">{{ imagePreviews.length }} / 8 selected</span>
            </div>
          </div>
          <div v-if="errors.image || errors.images" class="error-text">
            {{ errors.image || errors.images }}
          </div>
        </div>

        <button type="submit" :disabled="submitting">
          {{ submitting ? "Creating..." : "Create item" }}
        </button>
      </form>
    </div>
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
    };

    export default defineComponent({
    name: "NewItemPage",
    data() {
        return {
        submitting: false,
        successMessage: "",
        generalError: "",
        errors: {} as Record<string, string>,
        isDragging: false,
        imageFiles: [] as File[],
        imagePreviews: [] as string[],
        form: {
            title: "",
            description: "",
            starting_price: "",  
            ends_at: "",       
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
        } else {
          const endsAt = new Date(this.form.ends_at);
          if (endsAt <= new Date()) {
          this.errors.ends_at = "End date/time must be in the future.";
          }
        }

        return Object.keys(this.errors).length === 0;
        },

        triggerFileInput() {
            const input = this.$refs.fileInput as HTMLInputElement;
            input?.click();
        },

        handleFileSelect(event: Event) {
            const target = event.target as HTMLInputElement;
          const files = target.files;
          if (files && files.length) {
            this.addImages(files);
          }
          if (target) target.value = "";
        },

        handleDrop(event: DragEvent) {
            this.isDragging = false;
          const files = event.dataTransfer?.files;
          if (files && files.length) {
            this.addImages(files);
          }
        },

        addImages(files: FileList | File[]) {
          const maxImages = 8;
          const incoming = Array.from(files);

          for (const file of incoming) {
            if (this.imageFiles.length >= maxImages) {
              this.errors.images = "Maximum 8 images allowed.";
              break;
            }

            if (!file.type.startsWith("image/")) {
              this.errors.images = "Only image files are allowed.";
              continue;
            }

            if (file.size > 10 * 1024 * 1024) {
              this.errors.images = "Each image must be less than 10MB.";
              continue;
            }

            this.imageFiles.push(file);
            this.errors.images = "";

            const reader = new FileReader();
            reader.onload = (e) => {
              this.imagePreviews.push(e.target?.result as string);
            };
            reader.readAsDataURL(file);
          }
        },

        removeImage(index: number) {
          this.imageFiles.splice(index, 1);
          this.imagePreviews.splice(index, 1);
          this.errors.images = "";
        },

        async submit() {
        if (!this.validateClient()) return;

        this.submitting = true;
        this.generalError = "";
        this.successMessage = "";

        try {
            // Use FormData for file upload
            const formData = new FormData();
            formData.append("title", this.form.title.trim());
            formData.append("description", this.form.description.trim());
            formData.append("starting_price", this.form.starting_price.trim());
            formData.append("ends_at", this.form.ends_at);
            
            if (this.imageFiles.length) {
              this.imageFiles.forEach((file) => formData.append("images", file));
            }

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
            };
            this.imageFiles = [];
            this.imagePreviews = [];
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

<style scoped>
/* Import sophisticated font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

.new-item-page {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  min-height: 100vh;
  width: 100vw;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: linear-gradient(135deg, #1a1f2e 0%, #0f1419 100%);
  color: #ffffff;
  overflow-x: hidden;
  overflow-y: auto;
  z-index: 9999;
}

.new-item-page::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: 
    radial-gradient(circle at 20% 30%, rgba(245, 158, 11, 0.08) 0%, transparent 50%),
    radial-gradient(circle at 80% 70%, rgba(245, 158, 11, 0.05) 0%, transparent 50%);
  pointer-events: none;
}

.auth-shell {
  width: min(740px, 100%);
  background: #1a1f2e;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 48px 40px;
  position: relative;
  z-index: 1;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
}

.auth-shell::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, transparent, #f59e0b, transparent);
  border-radius: 16px 16px 0 0;
}

h1 {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.5px;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #ffffff 0%, #e5e7eb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

p.description {
  color: #8b95a8;
  line-height: 1.6;
  margin-bottom: 32px;
  font-size: 15px;
}

form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #ffffff;
  letter-spacing: 0.3px;
  text-transform: uppercase;
  font-size: 12px;
}

input,
textarea {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  padding: 13px 16px;
  font-size: 15px;
  color: #ffffff;
  font-family: inherit;
  transition: all 0.2s ease;
}

input::placeholder,
textarea::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

input:focus,
textarea:focus {
  outline: none;
  border-color: #f59e0b;
  background: rgba(255, 255, 255, 0.05);
  box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.2);
}

textarea {
  resize: vertical;
  min-height: 120px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.form-col {
  display: flex;
  flex-direction: column;
}

button[type="submit"] {
  margin-top: 8px;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: #0f1419;
  border: none;
  border-radius: 10px;
  padding: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  letter-spacing: 0.3px;
  text-transform: uppercase;
  font-size: 14px;
  box-shadow: 0 4px 16px rgba(245, 158, 11, 0.2);
}

button[type="submit"]:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(245, 158, 11, 0.2);
}

button[type="submit"]:active:not(:disabled) {
  transform: translateY(0);
}

button[type="submit"]:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.alert {
  margin: 0 0 20px;
  padding: 12px 14px;
  width: 100%;
  border-radius: 12px;
  background: rgba(239, 68, 68, 0.08);
  color: #fecdd3;
  border: 1px solid rgba(239, 68, 68, 0.25);
  font-size: 14px;
  line-height: 1.5;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25);
}

.alert-success {
  background: rgba(16, 185, 129, 0.08);
  color: #a7f3d0;
  border: 1px solid rgba(16, 185, 129, 0.25);
}

.error-text {
  font-size: 13px;
  color: #fca5a5;
  margin-top: 6px;
  line-height: 1.4;
}

/* Multi-image grid styles */
.images-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.image-slot {
  aspect-ratio: 1;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  background: rgba(255, 255, 255, 0.02);
  border: 2px solid rgba(255, 255, 255, 0.1);
  transition: all 0.2s ease;
}

.image-slot.has-image {
  border-color: rgba(245, 158, 11, 0.3);
}

.image-slot.upload-slot {
  border-style: dashed;
  border-color: rgba(255, 255, 255, 0.2);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.image-slot.upload-slot:hover {
  border-color: rgba(245, 158, 11, 0.6);
  background: rgba(255, 255, 255, 0.04);
  transform: scale(1.02);
}

.image-slot.upload-slot.drag-over {
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
  transform: scale(1.05);
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: #8b95a8;
  padding: 12px;
}

.upload-placeholder svg {
  opacity: 0.6;
  color: #f59e0b;
}

.upload-placeholder p {
  margin: 0;
  font-size: 13px;
  font-weight: 500;
  color: #ffffff;
}

.upload-hint {
  font-size: 11px;
  color: #8b95a8;
}

.image-preview-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 200px;
}

.image-preview-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
}

.image-preview-item {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  padding: 6px;
}

.image-preview {
  width: 100%;
  height: 100%;
  object-fit: contain;
  border-radius: 12px;
  max-height: 400px;
}

.remove-image {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(239, 68, 68, 0.9);
  border: none;
  border-radius: 6px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #ffffff;
  backdrop-filter: blur(8px);
  z-index: 2;
}

.remove-image:hover {
  background: rgba(239, 68, 68, 1);
  transform: scale(1.1);
}

.remove-image svg {
  stroke-width: 3;
}

.image-number {
  position: absolute;
  bottom: 6px;
  left: 6px;
  background: rgba(0, 0, 0, 0.7);
  color: #ffffff;
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 11px;
  font-weight: 600;
  backdrop-filter: blur(4px);
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .images-grid {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  }
}

@media (max-width: 480px) {
  .auth-shell {
    padding: 36px 28px;
  }
  
  h1 {
    font-size: 24px;
  }
  
  .images-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 8px;
  }
}

</style>
