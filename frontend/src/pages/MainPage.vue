<template>
  <section class="page">
    <header class="header">
      <div>
        <p class="eyebrow">Marketplace</p>
        <h1 class="title">Browse items</h1>
        <p class="subtitle">Search by title or description. Only active listings are shown.</p>
      </div>
    </header>

    <div class="search-card">
      <label class="search-label" for="search">Keyword</label>
      <div class="search-row">
        <input
          id="search"
          v-model="query"
          @input="onQueryInput"
          type="search"
          placeholder="e.g. camera, phone"
        />
        <div class="controls">
          <label class="sort-label" for="sort">Sort by</label>
          <select id="sort" v-model="sort" @change="onSortChange">
            <option value="ending-soon">Ending soon (default)</option>
            <option value="relevance">Relevance (when searching)</option>
            <option value="newest">Newest</option>
            <option value="price-asc">Price: low to high</option>
            <option value="price-desc">Price: high to low</option>
          </select>
        </div>
        <button type="button" class="ghost" @click="clearQuery" v-if="query">Clear</button>
      </div>
      <p class="hint">Search happens automatically with a short delay.</p>
    </div>

    <div class="status" v-if="error">
      <span class="error">{{ error }}</span>
    </div>
    <div class="status" v-else-if="loading">
      <span>Loading items…</span>
    </div>

    <div v-else>
      <ul class="items" v-if="items.length">
        <li v-for="item in items" :key="item.id" class="item-card">
          <router-link
            class="card-link"
            :to="{ name: 'Item Detail', params: { id: item.id } }"
          >
            <div class="item-head">
              <h3 class="item-title">{{ item.title }}</h3>
              <span class="price">£{{ item.starting_price }}</span>
            </div>
            <p class="description">{{ item.description || 'No description provided.' }}</p>
            <div class="meta">
              <span>Ends: {{ formatDate(item.ends_at) }}</span>
              <span class="dot" aria-hidden="true">•</span>
              <span>ID {{ item.id }}</span>
            </div>
          </router-link>
        </li>
      </ul>
      <p v-else class="empty">No items found.</p>
    </div>
  </section>
</template>

<script lang="ts">
import { defineComponent } from "vue";

type Item = {
  id: number;
  title: string;
  description: string;
  starting_price: string;
  image_url: string;
  ends_at: string;
  owner_id: number;
};

export default defineComponent({
  name: "MainPage",
  data() {
    return {
      query: "",
      items: [] as Item[],
      loading: true,
      error: "",
      debounceHandle: null as number | null,
      sort: "ending-soon",
    };
  },
  mounted() {
    this.fetchItems();
  },
  beforeUnmount() {
    if (this.debounceHandle) {
      clearTimeout(this.debounceHandle);
      this.debounceHandle = null;
    }
  },
  methods: {
    onQueryInput() {
      if (this.debounceHandle) {
        clearTimeout(this.debounceHandle);
      }
      this.debounceHandle = window.setTimeout(() => {
        this.fetchItems();
      }, 300);
    },
    onSortChange() {
      this.fetchItems();
    },
    clearQuery() {
      this.query = "";
      this.fetchItems();
    },
    async fetchItems() {
      this.loading = true;
      this.error = "";
      const params = new URLSearchParams();
      if (this.query) {
        params.append("q", this.query);
      }
      if (this.sort) {
        params.append("sort", this.sort);
      }
      const queryString = params.toString();
      try {
        const response = await fetch(`/api/items/${queryString ? `?${queryString}` : ""}` , {
          credentials: "include",
        });
        if (!response.ok) {
          throw new Error(`Request failed (${response.status})`);
        }
        const payload = await response.json();
        this.items = payload.items || [];
      } catch (err: unknown) {
        this.error = err instanceof Error ? err.message : "Failed to load items.";
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
  gap: 1.5rem;
  padding: 1rem 0;
}

.header .eyebrow {
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin: 0;
  color: #5a5a5a;
}

.header .title {
  margin: 0.15rem 0;
  font-size: 2rem;
}

.header .subtitle {
  margin: 0;
  color: #666;
}

.search-card {
  border: 1px solid #e4e4e4;
  border-radius: 12px;
  padding: 1rem 1.25rem;
  background: #fafafa;
  display: grid;
  gap: 0.25rem;
}

.search-label {
  font-weight: 600;
  color: #444;
}

.search-row {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 0.75rem;
  align-items: end;
}

.search-row input {
  flex: 1;
  padding: 0.65rem 0.75rem;
  border: 1px solid #d1d1d1;
  border-radius: 10px;
  font-size: 1rem;
}

.controls {
  display: grid;
  gap: 0.25rem;
  min-width: 180px;
}

.sort-label {
  font-size: 0.9rem;
  color: #555;
}

.controls select {
  padding: 0.5rem 0.6rem;
  border: 1px solid #d1d1d1;
  border-radius: 10px;
  background: white;
  font-size: 0.95rem;
}

.search-row button.ghost {
  border: 1px solid #d1d1d1;
  background: white;
  border-radius: 10px;
  padding: 0.55rem 0.9rem;
  cursor: pointer;
}

.hint {
  font-size: 0.9rem;
  color: #666;
  margin: 0;
}

.status {
  color: #333;
  font-size: 0.95rem;
}

.error {
  color: #b00020;
}

.items {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 0.75rem;
}

.item-card {
  border: 1px solid #e6e6e6;
  border-radius: 12px;
  padding: 1rem 1.25rem;
  background: #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.03);
}

.card-link {
  color: inherit;
  text-decoration: none;
  display: block;
}

.card-link:hover .item-title {
  text-decoration: underline;
}

.item-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.35rem;
}

.item-title {
  margin: 0;
  font-size: 1.2rem;
}

.price {
  font-weight: 700;
}

.description {
  margin: 0.15rem 0 0.5rem;
  color: #555;
}

.meta {
  display: flex;
  gap: 0.35rem;
  color: #777;
  font-size: 0.95rem;
}

.dot {
  font-weight: bold;
}

.empty {
  color: #666;
  margin: 0;
}

@media (max-width: 640px) {
  .search-row {
    grid-template-columns: 1fr;
  }

  .search-row button.ghost {
    width: 100%;
    text-align: center;
  }

  .controls {
    width: 100%;
  }
}
</style>
