<template>
  <div class="new-item-page">
    <div class="content-wrapper">
      <div class="brand">
        <h1>{{ $t('pages.newItem.title') }}</h1>
        <p class="description">
          {{ $t('pages.newItem.subtitle') }}
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
          <label for="title">{{ $t('pages.newItem.titleLabel') }}</label>
          <input
            id="title"
            v-model.trim="form.title"
            type="text"
            required
            maxlength="120"
            :placeholder="$t('pages.newItem.titlePlaceholder')"
          />
          <div v-if="errors.title" class="error-text">
            {{ errors.title }}
          </div>
        </div>

        <!-- Description -->
        <div>
          <label for="description">{{ $t('pages.newItem.descriptionLabel') }}</label>
          <textarea
            id="description"
            v-model.trim="form.description"
            rows="5"
            :placeholder="$t('pages.newItem.descriptionPlaceholder')"
          ></textarea>
          <div v-if="errors.description" class="error-text">
            {{ errors.description }}
          </div>
        </div>

        <div class="form-row">
          <!-- Starting price -->
          <div class="form-col">
            <label for="starting_price">{{ $t('pages.newItem.startingPriceLabel') }}</label>
            <input
              id="starting_price"
              v-model.trim="form.starting_price"
              type="text"
              :placeholder="$t('pages.newItem.pricePlaceholder')"
            />
            <div v-if="errors.starting_price" class="error-text">
              {{ errors.starting_price }}
            </div>
          </div>

          <!-- End date/time -->
          <div class="form-col">
            <label for="ends_at">{{ $t('pages.newItem.endsAtLabel') }}</label>
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
          <label>{{ $t('pages.newItem.imagesLabel') }}</label>
          <div
            class="upload-zone"
            :class="{ 'drag-over': isDragging, 'has-image': images.length }"
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
            
            <div v-if="!images.length" class="upload-placeholder">
              <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                <circle cx="8.5" cy="8.5" r="1.5"></circle>
                <polyline points="21 15 16 10 5 21"></polyline>
              </svg>
              <p>{{ $t('pages.newItem.uploadPrompt') }}</p>
              <span class="upload-hint">{{ $t('pages.newItem.uploadHint') }}</span>
            </div>
            
            <div v-else class="image-preview-container">
              <div class="image-preview-grid">
                <div
                  v-for="(image, index) in images"
                  :key="image.id"
                  class="image-preview-item"
                >
                  <img :src="image.preview" alt="Preview" class="image-preview" />
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
              <span class="upload-hint">{{ images.length }} / 8 {{ $t('pages.newItem.imagesSelected') }}</span>
            </div>
          </div>
          <div v-if="errors.image || errors.images" class="error-text">
            {{ errors.image || errors.images }}
          </div>
        </div>

        <button type="submit" :disabled="submitting">
          {{ submitting ? $t('pages.newItem.creating') : $t('pages.newItem.createItem') }}
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

    type ImageEntry = {
    id: number;
    file: File;
    preview: string;
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
        images: [] as ImageEntry[],
        nextImageId: 1,
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
          const newErrors: string[] = [];
          let skipped = 0;

          for (const file of incoming) {
            if (this.images.length >= maxImages) {
              newErrors.push(this.$t('pages.newItem.errorMaxImages'));
              skipped += 1;
              continue;
            }

            if (!file.type.startsWith("image/")) {
              newErrors.push(`${file.name}: ${this.$t('pages.newItem.errorImageOnly')}`);
              skipped += 1;
              continue;
            }

            if (file.size > 10 * 1024 * 1024) {
              newErrors.push(`${file.name}: ${this.$t('pages.newItem.errorImageSize')}`);
              skipped += 1;
              continue;
            }

            const entry: ImageEntry = {
              id: this.nextImageId,
              file,
              preview: "",
            };
            this.nextImageId += 1;
            this.images.push(entry);

            const reader = new FileReader();
            reader.onload = (e) => {
              entry.preview = (e.target?.result as string) || "";
            };
            reader.readAsDataURL(file);
          }

          if (newErrors.length) {
            const summary = skipped === 1 ? this.$t('pages.newItem.errorSkippedOne') : (this.$t as any)('pages.newItem.errorSkippedMany', { count: skipped });
            this.errors.images = `${summary} ${newErrors.join(" ")}`.trim();
          } else {
            this.errors.images = "";
          }
        },

        removeImage(index: number) {
          this.images.splice(index, 1);
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
            
            if (this.images.length) {
              this.images.forEach((image) => formData.append("images", image.file));
            }

            const resp = await apiFetch("/api/items/", {
            method: "POST",
            body: formData,
            });

            const data = await resp.json().catch(() => ({}));

            if (resp.status === 201) {
            this.successMessage = this.$t('pages.newItem.success');
            this.form = {
                title: "",
                description: "",
                starting_price: "",
                ends_at: "",
            };
            this.images = [];
            this.nextImageId = 1;
            this.errors = {};
            return;
            }

            if (resp.status === 401) {
            this.generalError = this.$t('pages.newItem.errorLoginRequired');
            return;
            }

            if (data && data.errors) {
            this.errors = data.errors as FieldErrors;
            return;
            }

            this.generalError = this.$t('pages.newItem.errorGeneric');
        } catch {
            this.generalError = this.$t('pages.newItem.errorNetwork');
        } finally {
            this.submitting = false;
        }
        },
    },
    });
</script>

<style scoped>
.new-item-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.content-wrapper {
  max-width: 740px;
  margin: 0 auto;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 16px;
  padding: 48px 40px;
  box-shadow: var(--shadow-md);
}

h1 {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.5px;
  margin-bottom: 8px;
  color: var(--text-primary);
}

p.description {
  color: var(--text-secondary);
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
  color: var(--text-primary);
  letter-spacing: 0.3px;
  text-transform: uppercase;
  font-size: 12px;
}

input,
textarea {
  width: 100%;
  border: 2px solid var(--border-medium);
  background: var(--bg-secondary);
  border-radius: 10px;
  padding: 13px 16px;
  font-size: 15px;
  color: var(--text-primary);
  font-family: inherit;
  transition: all 0.2s ease;
}

input::placeholder,
textarea::placeholder {
  color: var(--text-muted);
}

input:focus,
textarea:focus {
  outline: none;
  border-color: var(--accent-coral);
  background: var(--bg-card);
  box-shadow: 0 0 0 3px rgba(255, 107, 107, 0.1);
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
  background: var(--gradient-warm);
  color: white;
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
  box-shadow: var(--shadow-sm);
}

button[type="submit"]:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
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
  background: rgba(211, 47, 47, 0.1);
  color: #d32f2f;
  border: 2px solid rgba(211, 47, 47, 0.2);
  font-size: 14px;
  line-height: 1.5;
}

.alert-success {
  background: rgba(46, 125, 50, 0.1);
  color: #2e7d32;
  border: 2px solid rgba(46, 125, 50, 0.3);
}

.error-text {
  font-size: 13px;
  color: #d32f2f;
  margin-top: 6px;
  line-height: 1.4;
}

/* Upload zone styles */
.upload-zone {
  border: 2px dashed var(--border-medium);
  border-radius: 12px;
  padding: 24px;
  min-height: 200px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--bg-secondary);
}

.upload-zone.drag-over {
  border-color: var(--accent-coral);
  background: rgba(255, 107, 107, 0.05);
  transform: scale(1.01);
}

.upload-zone.has-image {
  border-style: solid;
  border-color: var(--border-light);
  cursor: default;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--text-secondary);
  padding: 24px;
}

.upload-placeholder svg {
  opacity: 0.6;
  color: var(--accent-coral);
}

.upload-placeholder p {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.upload-hint {
  font-size: 13px;
  color: var(--text-muted);
  margin-top: 8px;
  text-align: center;
  display: block;
}

.image-preview-container {
  position: relative;
  width: 100%;
  min-height: 200px;
}

.image-preview-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 12px;
  margin-bottom: 12px;
}

.image-preview-item {
  position: relative;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--border-light);
  background: var(--bg-primary);
  padding: 6px;
  aspect-ratio: 1;
}

.image-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 6px;
}

.remove-image {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(211, 47, 47, 0.95);
  border: none;
  border-radius: 6px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
  color: white;
  z-index: 2;
}

.remove-image:hover {
  background: #d32f2f;
  transform: scale(1.1);
}

.remove-image svg {
  stroke-width: 3;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .auth-shell {
    padding: 36px 28px;
  }
  
  h1 {
    font-size: 24px;
  }
  
  .image-preview-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 8px;
  }
}

</style>
