<template>
  <section class="page">
    <header class="header">
      <div>
        <p class="eyebrow">{{ $t('pages.main.eyebrow') }}</p>
        <h1 class="title">{{ $t('pages.main.heading') }}</h1>
        <p class="subtitle">{{ $t('pages.main.subtitle') }}</p>
      </div>
    </header>

    <div class="search-card">
      <label class="search-label" for="search">{{ $t('pages.main.searchLabel') }}</label>
      <div class="search-row">
        <input
          id="search"
          v-model="query"
          @input="onQueryInput"
          type="search"
          :placeholder="$t('pages.main.searchPlaceholder')"
        />
        <div class="controls">
          <label class="sort-label" for="sort">{{ $t('pages.main.sortLabel') }}</label>
          <select id="sort" v-model="sort" @change="onSortChange">
            <option value="ending-soon">{{ $t('pages.main.sortEndingSoon') }}</option>
            <option value="relevance">{{ $t('pages.main.sortRelevance') }}</option>
            <option value="newest">{{ $t('pages.main.sortNewest') }}</option>
            <option value="price-asc">{{ $t('pages.main.sortPriceLow') }}</option>
            <option value="price-desc">{{ $t('pages.main.sortPriceHigh') }}</option>
            <option value="price-desc">{{ $t('pages.main.sortPriceHigh') }}</option>
          </select>
          
          <div v-if="currentUserId" class="my-listings-toggle">
            <input 
              type="checkbox" 
              id="my-listings" 
              v-model="onlyMyItems" 
              @change="fetchItems"
            >
            <label for="my-listings">Show My Listings Only</label>
          </div>
        </div>
        <button type="button" class="ghost" @click="clearQuery" v-if="query">{{ $t('pages.main.clear') }}</button>
      </div>
    </div>

    <div class="status" v-if="error">
      <span class="error">{{ error }}</span>
    </div>
    <div class="status" v-else-if="loading">
      <span>{{ $t('pages.main.loading') }}</span>
    </div>

    <div v-else>
      <ul class="items" v-if="items.length">
        <li v-for="item in items" :key="item.id" class="item-card">
          <router-link
            class="card-link"
            :to="{ name: 'Item Detail', params: { id: item.id } }"
          >
            <div class="card-image-wrapper">
              <img 
                v-if="item.images && item.images.length > 0" 
                :src="item.images[0].url" 
                :alt="item.title" 
                class="card-preview-image"
              />
              <div v-else class="card-no-image">
                <span>No Image</span>
              </div>
            </div>
            <div class="card-content">
              <div class="item-head">
                <h3 class="item-title">{{ item.title }}</h3>
                <span class="price">£{{ item.starting_price }}</span>
              </div>
              <p class="description">{{ item.description || 'No description provided.' }}</p>
              <div class="meta">
                <span>{{ $t('pages.main.ends') }}: {{ formatDate(item.ends_at) }}</span>
              </div>
            </div>
          </router-link>
        </li>
      </ul>
      <p v-else class="empty">{{ $t('pages.main.noItems') }}</p>
    </div>
  </section>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { fetchAuthStatus } from "../auth";

type Item = {
  id: number;
  title: string;
  description: string;
  starting_price: string;
  images: { url: string }[];
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
      onlyMyItems: false,
      currentUserId: null as number | null,
    };
  },
  async created() {
    try {
      const status = await fetchAuthStatus();
      if (status.authenticated && status.user) {
        this.currentUserId = status.user.id;
      }
    } catch {
      // ignore
    }
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
      if (this.onlyMyItems && this.currentUserId) {
        params.append("user_id", String(this.currentUserId));
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
  padding: 0;
}

.header .eyebrow {
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin: 0;
  color: var(--accent-amber);
  font-weight: 600;
}

.header .title {
  margin: 0.5rem 0;
  font-size: 2.25rem;
  color: var(--text-primary);
  font-weight: 700;
}

.header .subtitle {
  margin: 0;
  color: var(--text-secondary);
  font-size: 1.05rem;
}

.search-card {
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  background: var(--bg-card);
  display: grid;
  gap: 0.5rem;
  box-shadow: var(--shadow-sm);
}

.search-label {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 1rem;
}

.search-row {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 0.75rem;
  align-items: end;
}

.search-row input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 2px solid var(--border-medium);
  border-radius: 10px;
  font-size: 1rem;
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: all 0.2s ease;
}

.search-row input:focus {
  outline: none;
  border-color: var(--accent-coral);
  box-shadow: 0 0 0 3px rgba(255, 107, 107, 0.1);
}

.controls {
  display: grid;
  gap: 0.25rem;
  min-width: 180px;
}

.sort-label {
  font-size: 0.9rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.controls select {
  padding: 0.65rem 0.75rem;
  border: 2px solid var(--border-medium);
  border-radius: 10px;
  background: var(--bg-secondary);
  font-size: 0.95rem;
  color: var(--text-primary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.controls select:focus {
  outline: none;
  border-color: var(--accent-coral);
}

.my-listings-toggle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: var(--text-primary);
  font-weight: 500;
  padding: 0.65rem 0.75rem;
  background: var(--bg-secondary);
  border-radius: 10px;
  border: 2px solid var(--border-medium);
}

.my-listings-toggle input {
  accent-color: var(--accent-coral);
  width: 1.25em;
  height: 1.25em;
  cursor: pointer;
}

.my-listings-toggle label {
  cursor: pointer;
}

.search-row button.ghost {
  border: 2px solid var(--accent-sage);
  background: transparent;
  color: var(--accent-sage);
  border-radius: 10px;
  padding: 0.65rem 1.25rem;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s ease;
}

.search-row button.ghost:hover {
  background: var(--accent-sage);
  color: white;
  transform: translateY(-1px);
}

.hint {
  font-size: 0.875rem;
  color: var(--text-muted);
  margin: 0;
  font-style: italic;
}

.status {
  color: var(--text-primary);
  font-size: 1rem;
  padding: 1rem;
  text-align: center;
}

.error {
  color: #d32f2f;
  font-weight: 500;
}

.items {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 1rem;
}

.item-card {
  border: 1px solid var(--border-light);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  background: var(--bg-card);
  box-shadow: var(--shadow-sm);
  transition: all 0.25s ease;
}

.item-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--accent-coral);
}

.card-link {
  color: inherit;
  text-decoration: none;
  display: flex;
  gap: 1.5rem;
  align-items: start;
}

.card-image-wrapper {
  width: 120px;
  height: 120px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-muted);
  border: 1px solid var(--border-light);
  display: grid;
  place-items: center;
}

.card-preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-no-image {
  color: var(--text-muted);
  font-size: 0.75rem;
  font-weight: 500;
}

.card-content {
  flex: 1;
  min-width: 0;
}

.card-link:hover .item-title {
  color: var(--accent-coral);
}

.item-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.item-title {
  margin: 0;
  font-size: 1.3rem;
  color: var(--text-primary);
  font-weight: 600;
  transition: color 0.2s ease;
}

.price {
  font-weight: 700;
  color: var(--accent-coral);
  font-size: 1.1rem;
  white-space: nowrap;
}

.description {
  margin: 0.25rem 0 0.75rem;
  color: var(--text-secondary);
  line-height: 1.5;
}

.meta {
  display: flex;
  gap: 0.5rem;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.dot {
  font-weight: bold;
}

.empty {
  color: var(--text-secondary);
  margin: 0;
  text-align: center;
  padding: 2rem;
  font-size: 1.05rem;
}

@media (max-width: 640px) {
  .header .title {
    font-size: 1.75rem;
  }
  
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
  
  .item-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>

