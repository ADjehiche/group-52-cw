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
      <p class="mb-2">{{ item.description || "No description provided." }}</p>

      <dl class="row mb-2">
        <dt class="col-sm-4">Starting price</dt>
        <dd class="col-sm-8">£{{ item.starting_price }}</dd>

        <dt class="col-sm-4">Highest bid</dt>
        <dd class="col-sm-8">
          <span v-if="item.highest_bid?.amount">£{{ item.highest_bid.amount }}</span>
          <span v-else class="text-muted">No bids yet</span>
        </dd>

        <dt class="col-sm-4">Time remaining</dt>
        <dd class="col-sm-8">{{ formatTimeRemaining(remainingSeconds) }}</dd>

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
import { fetchItemDetail, ItemDetail } from "../api";
import { fetchAuthStatus } from "../auth";

export default defineComponent({
  name: "ItemDetailPage",
  data() {
    return {
      item: null as ItemDetail | null,
      loading: true,
      error: "",
      remainingSeconds: 0,
      tickHandle: null as number | null,
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
  beforeUnmount() {
    this.stopTick();
  },
  methods: {
    stopTick() {
      if (this.tickHandle) {
        clearInterval(this.tickHandle);
        this.tickHandle = null;
      }
    },
    startTick() {
      this.stopTick();
      this.tickHandle = window.setInterval(() => {
        if (this.remainingSeconds > 0) {
          this.remainingSeconds -= 1;
        } else {
          this.stopTick();
        }
      }, 1000);
    },
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
        this.item = await fetchItemDetail(id);
        this.remainingSeconds = this.item.time_remaining_seconds ?? 0;
        this.startTick();
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
    formatTimeRemaining(seconds: number) {
      const clamped = Math.max(0, Math.floor(seconds));
      if (clamped <= 0) return "Ended";
      const hrs = Math.floor(clamped / 3600);
      const mins = Math.floor((clamped % 3600) / 60);
      const secs = clamped % 60;
      const parts = [] as string[];
      if (hrs) parts.push(`${hrs}h`);
      if (hrs || mins) {
        parts.push(`${mins.toString().padStart(hrs ? 2 : 1, "0")}m`);
        parts.push(`${secs.toString().padStart(2, "0")}s`);
      } else {
        parts.push(`${secs}s`);
      }
      return parts.join(" ") || "<1s";
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
</style>
