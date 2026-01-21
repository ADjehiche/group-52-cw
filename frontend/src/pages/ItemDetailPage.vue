<template>
  <section class="page">
    <header class="mb-3">
      <p class="eyebrow">Item</p>
      <h1 class="h3 mb-1">{{ item?.title || "Loading item..." }}</h1>
      <p v-if="item" class="text-muted mb-0">ID {{ item.id }}</p>
    </header>

    <div v-if="loading" class="text-muted">Loading item…</div>
    <div v-else-if="error" class="text-danger">{{ error }}</div>
    <div v-else-if="item" class="card p-3">
      <div v-if="item.images.length" class="image-grid">
        <img
          v-for="image in item.images"
          :key="image.id"
          :src="image.url"
          :alt="`Image ${image.order + 1}`"
          class="item-image"
        />
      </div>

      <p class="mb-2">{{ item.description || "No description provided." }}</p>

      <dl class="row mb-2">
        <dt class="col-sm-4">Starting price</dt>
        <dd class="col-sm-8">£{{ item.starting_price }}</dd>

        <dt class="col-sm-4">Ends at</dt>
        <dd class="col-sm-8">{{ formatDate(item.ends_at) }}</dd>
      </dl>

      <div class="d-flex gap-2 align-items-center">
        <a v-if="!isAuthenticated" class="btn btn-primary" href="/accounts/login/">Login to bid</a>
        <button v-else class="btn btn-primary" type="button" disabled>Bid feature coming soon</button>
        <a class="btn btn-outline-secondary" href="#qa">Go to Q&A</a>
      </div>
    </div>

    <section id="qa" class="mt-4">
      <h2 class="h5">Q&A</h2>
      <p class="text-muted">Public questions and answers will appear here (coming soon).</p>
    </section>
  </section>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { fetchAuthStatus } from "../auth";
import { apiFetch } from "../http";

type ItemImage = {
  id: number;
  url: string;
  order: number;
};

type ItemDetail = {
  id: number;
  title: string;
  description: string;
  starting_price: string;
  ends_at: string;
  owner_id: number;
  images: ItemImage[];
};

export default defineComponent({
  name: "ItemDetailPage",
  data() {
    return {
      item: null as ItemDetail | null,
      loading: true,
      error: "",
      isAuthenticated: false,
    };
  },
  async created() {
    await this.load();
  },
  watch: {
    "$route.params.id": {
      immediate: false,
      async handler() {
        await this.load();
      },
    },
  },
  methods: {
    async load() {
      this.loading = true;
      this.error = "";
      try {
        const status = await fetchAuthStatus();
        this.isAuthenticated = status.authenticated;
      } catch {
        this.isAuthenticated = false;
      }

      const id = Number(this.$route.params.id);
      if (!Number.isInteger(id) || id <= 0) {
        this.error = "Invalid item id.";
        this.loading = false;
        return;
      }

      try {
        this.item = await apiFetch<ItemDetail>(`/api/items/${id}/`);
      } catch (err: unknown) {
        this.error = err instanceof Error ? err.message : "Failed to load item.";
      } finally {
        this.loading = false;
      }
    },
    formatDate(value: string) {
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return value;
      return date.toLocaleString();
    },
  },
});
</script>

<style scoped>
.page {
  display: grid;
  gap: 1rem;
  padding: 1rem 0;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #6c757d;
  font-size: 0.9rem;
}

.image-grid {
  display: grid;
  gap: 0.75rem;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  margin-bottom: 1rem;
}

.item-image {
  width: 100%;
  height: 160px;
  object-fit: cover;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}
</style>
