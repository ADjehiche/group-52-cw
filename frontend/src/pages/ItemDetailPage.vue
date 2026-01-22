<template>
  <section class="item-detail-page">
    <header class="mb-3">
      <p class="eyebrow">{{ $t('pages.itemDetail.eyebrow') }}</p>
      <h1 class="h3 mb-1">{{ item?.title || $t('pages.itemDetail.loading') }}</h1>
    </header>

    <div v-if="loading" class="text-muted">{{ $t('pages.itemDetail.loadingText') }}</div>
    <div v-else-if="error" class="text-danger">{{ error }}</div>
    <div v-else-if="item" class="item-grid">
      <!-- Left Column: Image -->
      <div class="image-column">
        <div class="image-wrapper">
          <img 
            v-if="item.images && item.images.length > 0" 
            :src="currentImage" 
            :alt="item.title" 
            class="item-image"
          />
          <div v-else class="no-image-placeholder">
            <span>{{ $t('pages.itemDetail.noImage') || 'No Image Available' }}</span>
          </div>
        </div>

        <!-- Thumbnails -->
        <div v-if="item.images && item.images.length > 1" class="thumbnails">
          <button 
            v-for="(img, idx) in item.images" 
            :key="img.id"
            class="thumbnail-btn"
            :class="{ active: currentImageIndex === idx }"
            @click="currentImageIndex = idx"
            :aria-label="'View image ' + (idx + 1)"
          >
            <img :src="img.url" class="thumbnail-img" alt="" />
          </button>
        </div>
      </div>

      <!-- Right Column: Details & Bidding -->

      <div class="details-column card p-4">
        <!-- Seller Info -->
        <div class="seller-info mb-3">
          <div class="seller-avatar">
            <img v-if="item.owner_avatar_url" :src="item.owner_avatar_url" alt="Seller" />
            <div v-else class="avatar-placeholder">{{ item.owner_username?.charAt(0).toUpperCase() }}</div>
          </div>
          <div class="seller-details">
            <span class="seller-label">Seller</span>
            <strong class="seller-name">{{ item.owner_username }}</strong>
          </div>
          <button 
            v-if="isAuthenticated && currentUserId !== item.owner_id"
            class="btn btn-sm follow-btn" 
            :class="item.is_following_owner ? 'btn-outline-secondary' : 'btn-primary'"
            @click="toggleFollow"
            :disabled="followLoading"
          >
            {{ item.is_following_owner ? $t('pages.itemDetail.unfollow') : $t('pages.itemDetail.follow') }}
          </button>
        </div>

        <p class="description mb-4">{{ item.description || "No description provided." }}</p>

        <dl class="details-list mb-4">
          <div class="detail-row">
            <dt>{{ $t('pages.itemDetail.startingPrice') }}</dt>
            <dd>£{{ item.starting_price }}</dd>
          </div>

          <div class="detail-row">
            <dt>{{ $t('pages.itemDetail.highestBid') }}</dt>
            <dd>
              <span v-if="item.highest_bid?.amount" class="highlight-bid">£{{ item.highest_bid.amount }}</span>
              <span v-else class="text-muted">{{ $t('pages.itemDetail.noBids') }}</span>
            </dd>
          </div>

          <div class="detail-row">
            <dt>{{ $t('pages.itemDetail.timeRemaining') }}</dt>
            <dd :class="{'text-danger': remainingSeconds < 3600}">{{ formatTimeRemaining(remainingSeconds) }}</dd>
          </div>

          <div class="detail-row">
            <dt>{{ $t('pages.itemDetail.endsAt') }}</dt>
            <dd>{{ formatDate(item.ends_at) }}</dd>
          </div>
        </dl>

        <div class="bidding-section">
          <template v-if="!isAuthenticated">
            <a class="btn btn-primary w-100" href="/accounts/login/">{{ $t('pages.itemDetail.loginToBid') }}</a>
          </template>
          <template v-else-if="isOwner">
            <div class="owner-controls">
              <div class="alert alert-info">
                {{ $t('pages.itemDetail.selfBidRestriction') }}
              </div>
              <button class="btn btn-danger w-100 mt-2" @click="deleteListing">
                {{ $t('pages.itemDetail.deleteButton') }}
              </button>
            </div>
          </template>
          <template v-else>
            <div v-if="remainingSeconds <= 0" class="alert alert-warning">
              {{ $t('pages.itemDetail.ended') }}
            </div>
            <form v-else @submit.prevent="submitBid" class="bid-form">
              <label class="form-label small mb-1">Place your bid</label>
              <div class="input-group mb-2">
                <span class="currency-symbol">£</span>
                <input 
                  type="number" 
                  v-model="bidAmount" 
                  step="0.01" 
                  min="0.01"
                  class="form-control"
                  placeholder="Amount"
                  :disabled="placingBid"
                  required
                >
                <button class="btn btn-primary" type="submit" :disabled="placingBid">
                  {{ placingBid ? '...' : 'Bid' }}
                </button>
              </div>
              <div v-if="bidError" class="text-danger mt-2 small">{{ bidError }}</div>
              <div v-if="bidSuccess" class="text-success mt-2 small">{{ bidSuccess }}</div>
            </form>
          </template>
        </div>
      </div>
    </div>

    <section id="qa" class="mt-4">
      <h2 class="h5">{{ $t('pages.itemDetail.qaHeading') }}</h2>
      
      <div v-if="isAuthenticated" class="mb-4">
        <form @submit.prevent="submitQuestion" class="qa-form">
          <textarea 
            v-model="newQuestion" 
            class="form-control" 
            rows="3" 
            :placeholder="$t('pages.itemDetail.questionPlaceholder')"
            :disabled="postingQuestion"
            required
          ></textarea>
          <div class="d-flex justify-content-end mt-2">
            <button class="btn btn-secondary btn-sm" type="submit" :disabled="postingQuestion || !newQuestion.trim()">
              {{ postingQuestion ? $t('pages.itemDetail.posting') : $t('pages.itemDetail.postQuestion') }}
            </button>
          </div>
          <div v-if="questionError" class="text-danger mt-2 small">{{ questionError }}</div>
        </form>
      </div>

      <div v-if="questions.length === 0" class="text-muted">
        No questions yet.
      </div>
      
      <div v-else class="qa-list">
        <div v-for="q in questions" :key="q.id" class="qa-item card">
          <div class="qa-header">
            <div class="qa-author-info">
              <div class="qa-avatar">
                <img v-if="q.author_avatar_url" :src="q.author_avatar_url" alt="" />
                <div v-else class="avatar-placeholder small">{{ q.author.charAt(0).toUpperCase() }}</div>
              </div>
              <strong class="author">{{ q.author }}</strong>
            </div>
            <span class="date">{{ formatDate(q.created_at) }}</span>
          </div>
          <p class="qa-content">{{ q.content }}</p>
          
          <div v-if="q.answer" class="qa-answer">
            <div class="answer-header">
              <strong>Seller Answer</strong>
              <span class="date">{{ formatDate(q.answer.created_at) }}</span>
            </div>
            <p>{{ q.answer.content }}</p>
          </div>
          
           <div v-else-if="isOwner" class="qa-reply mt-3">
             <button v-if="replyingToId !== q.id" @click="startReply(q.id)" class="btn btn-sm btn-outline-primary">
               {{ $t('pages.itemDetail.replyButton') }}
             </button>
             <form v-else @submit.prevent="submitAnswer(q.id)" class="reply-form">
               <textarea
                 v-model="replyContent"
                 class="form-control mb-2"
                 rows="2"
                 :placeholder="$t('pages.itemDetail.replyPlaceholder')"
                 :disabled="submittingAnswer"
                 required
               ></textarea>
               <div class="d-flex gap-2">
                 <button type="submit" class="btn btn-sm btn-primary" :disabled="submittingAnswer || !replyContent.trim()">
                   {{ submittingAnswer ? $t('pages.itemDetail.sending') : $t('pages.itemDetail.sendAnswer') }}
                 </button>
                 <button type="button" class="btn btn-sm btn-outline-secondary" @click="cancelReply" :disabled="submittingAnswer">
                   {{ $t('pages.itemDetail.cancel') }}
                 </button>
               </div>
               <div v-if="answerError" class="text-danger mt-2 small">{{ answerError }}</div>
             </form>
          </div>
        </div>
      </div>
    </section>
  </section>
</template>

<script lang="ts">
import { defineComponent } from "vue";
import { fetchItemDetail, ItemDetail, Question, placeBid, fetchItemQuestions, postQuestion, postAnswer, followUser, unfollowUser, deleteItem } from "../api";
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
      currentUserId: null as number | null,
      // Image Gallery
      currentImageIndex: 0,
      
      // Bidding
      bidAmount: "",
      placingBid: false,
      bidError: "",
      bidSuccess: "",
      // Q&A
      questions: [] as Question[],
      newQuestion: "",
      postingQuestion: false,
      questionError: "",
      
      // Answering
      replyingToId: null as number | null,
      replyContent: "",
      submittingAnswer: false,
      answerError: "",
      
      // Following
      followLoading: false,
    };
  },
  async created() {
    await this.load();
    await this.loadQuestions();
  },
  watch: {
    "$route.params.id": {
      immediate: false,
      async handler() {
        await this.load();
        await this.loadQuestions();
      },
    },
  },
  beforeUnmount() {
    this.stopTick();
  },
  computed: {
    isOwner(): boolean {
      return !!(this.item && this.currentUserId && this.item.owner_id === this.currentUserId);
    },
    currentImage(): string {
       if (!this.item || !this.item.images || this.item.images.length === 0) return "";
       return this.item.images[this.currentImageIndex]?.url || this.item.images[0].url;
    }
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
      this.currentImageIndex = 0; // Reset gallery on load
      try {
        const status = await fetchAuthStatus();
        this.isAuthenticated = status.authenticated;
        if (status.authenticated && status.user) {
            this.currentUserId = status.user.id;
        } else {
            this.currentUserId = null;
        }
      } catch {
        this.isAuthenticated = false;
        this.currentUserId = null;
      }
      const id = Number((this as any).$route.params.id);
      if (!Number.isInteger(id) || id <= 0) {
        this.error = this.$t('pages.itemDetail.errorInvalidId');
        this.loading = false;
        return;
      }
      try {
        this.item = await fetchItemDetail(id);
        this.remainingSeconds = this.item.time_remaining_seconds ?? 0;
        this.startTick();
      } catch (err: unknown) {
        this.error = err instanceof Error ? err.message : this.$t('pages.itemDetail.errorLoadFailed');
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
    async submitBid() {
      if (!this.item || !this.bidAmount) return;
      this.placingBid = true;
      this.bidError = "";
      this.bidSuccess = "";

      try {
        await placeBid(this.item.id, this.bidAmount);
        this.bidSuccess = this.$t('pages.itemDetail.bidSuccess');
        this.bidAmount = "";
        await this.load(); // Reload to see new highest bid
      } catch (err: any) {
         if (err instanceof Error) {
             this.bidError = err.message;
         } else if (err && typeof err === 'object') {
             const structured = err.errors || err;
             if (structured.amount) this.bidError = structured.amount;
             else if (structured.detail) this.bidError = structured.detail;
             else this.bidError = JSON.stringify(structured);
         } else {
             this.bidError = this.$t('pages.itemDetail.bidFailed');
         }
      } finally {
        this.placingBid = false;
      }
    },
    async loadQuestions() {
      if (!this.item) return;
      try {
        const res = await fetchItemQuestions(this.item.id);
        this.questions = res.questions;
      } catch (err) {
        console.error("Failed to load questions", err);
      }
    },
    async submitQuestion() {
      if (!this.item || !this.newQuestion.trim()) return;
      this.postingQuestion = true;
      this.questionError = "";
      
      try {
        const q = await postQuestion(this.item.id, this.newQuestion);
        this.questions.unshift(q); // Add to top
        this.newQuestion = "";
      } catch (err: any) {
          if (err instanceof Error) {
              this.questionError = err.message;
          } else if (err && typeof err === 'object') {
              const structured = err.errors || err;
              if (structured.content) this.questionError = structured.content;
              else if (structured.detail) this.questionError = structured.detail;
              else this.questionError = JSON.stringify(structured);
          } else {
              this.questionError = this.$t('pages.itemDetail.questionFailed');
          }
      } finally {
        this.postingQuestion = false;
      }
    },
    startReply(questionId: number) {
      this.replyingToId = questionId;
      this.replyContent = "";
      this.answerError = "";
    },
    cancelReply() {
      this.replyingToId = null;
      this.replyContent = "";
      this.answerError = "";
    },
    async submitAnswer(questionId: number) {
      if (!this.replyContent.trim()) return;
      this.submittingAnswer = true;
      this.answerError = "";
      
      try {
        const answer = await postAnswer(questionId, this.replyContent);
        // Update local state
        const qIndex = this.questions.findIndex(q => q.id === questionId);
        if (qIndex !== -1) {
            this.questions[qIndex].answer = answer;
        }
        this.cancelReply();
      } catch (err: any) {
          if (err instanceof Error) {
              this.answerError = err.message;
          } else if (err && typeof err === 'object') {
              const structured = err.errors || err;
              if (structured.content) this.answerError = structured.content;
              else if (structured.detail) this.answerError = structured.detail;
              else this.answerError = JSON.stringify(structured);
          } else {
              this.answerError = this.$t('pages.itemDetail.answerFailed');
          }
      } finally {
        this.submittingAnswer = false;
      }
    },
    async toggleFollow() {
      if (!this.item) return;
      this.followLoading = true;
      try {
        if (this.item.is_following_owner) {
          await unfollowUser(this.item.owner_id);
          this.item.is_following_owner = false;
        } else {
          await followUser(this.item.owner_id);
          this.item.is_following_owner = true;
        }
      } catch (e) {
        console.error("Failed to toggle follow", e);
      } finally {
        this.followLoading = false;
      }
    },
    async deleteListing() {
      if (!this.item || !confirm(this.$t('pages.itemDetail.deleteConfirm'))) return;
      try {
        await deleteItem(this.item.id);
        window.location.href = "/";
      } catch (err: any) {
        this.error = err.detail || "Failed to delete item.";
      }
    },
  },
});
</script>



<style scoped>
.item-detail-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.item-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2.5rem;
  align-items: start;
}

/* Image Column */
.image-column {
  /* Sticky image on scroll if details are long */
  position: sticky;
  top: 100px; 
}

.image-wrapper {
  border-radius: 12px;
  overflow: hidden;
  box-shadow: var(--shadow-md);
  aspect-ratio: 4/3;
  background: var(--bg-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1rem;
}

.item-image {
  width: 100%;
  height: 100%;
  object-fit: contain; /* Changed from cover to contain to prevent stretching */
  background: black; /* Or any muted background for letterboxing */
}

/* Thumbnails */
.thumbnails {
  display: flex;
  gap: 0.5rem;
  overflow-x: auto;
  padding-bottom: 0.5rem;
}

.thumbnail-btn {
  border: 2px solid transparent;
  border-radius: 8px;
  padding: 0;
  cursor: pointer;
  width: 80px;
  height: 60px;
  flex-shrink: 0;
  overflow: hidden;
  background: var(--bg-muted);
  transition: all 0.2s ease;
}

.thumbnail-btn:hover {
  transform: translateY(-2px);
}

.thumbnail-btn.active {
  border-color: var(--accent-coral);
  box-shadow: 0 0 0 2px rgba(255, 107, 107, 0.2);
}

.thumbnail-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.no-image-placeholder {
  color: var(--text-muted);
  font-weight: 500;
}

/* Details Column */
.details-column {
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: 16px;
  padding: 2rem;
  box-shadow: var(--shadow-sm);
}

.description {
  font-size: 1.1rem;
  color: var(--text-primary);
  line-height: 1.6;
}

.details-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1.5rem 0;
  border-top: 1px solid var(--border-light);
  border-bottom: 1px solid var(--border-light);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-row dt {
  font-weight: 600;
  color: var(--text-secondary);
}

.detail-row dd {
  margin: 0;
  font-weight: 500;
  color: var(--text-primary);
  text-align: right;
}

.highlight-bid {
  font-weight: 700;
  color: var(--accent-coral);
  font-size: 1.1rem;
}

/* Bidding Form */
.bidding-section {
  padding-top: 1rem;
}

.input-group {
  display: flex;
  gap: 0.5rem;
}

.currency-symbol {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  background: var(--bg-muted);
  border: 1px solid var(--border-light);
  border-radius: 8px;
  font-weight: 600;
  color: var(--text-secondary);
}

.form-control {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1px solid var(--border-light);
  border-radius: 8px;
  font-size: 1rem;
}

/* QA Sections */
#qa {
  margin-top: 4rem;
  max-width: 800px; /* Keep QA readable width */
}

/* Responsive */
@media (max-width: 768px) {
  .item-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
  
  .image-column {
    position: static;
  }
}

/* Utility / Typography */
.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--accent-amber);
  font-size: 0.875rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.h3 {
  font-size: 2rem;
  font-weight: 800;
  line-height: 1.2;
  color: var(--text-primary);
}

.text-muted { color: var(--text-muted); }
.text-danger { color: #d32f2f; }
.text-success { color: #388e3c; }

.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
  border: none;
  text-align: center;
  text-decoration: none;
  display: inline-block;
}

.btn-primary {
  background: var(--gradient-warm);
  color: white;
  box-shadow: var(--shadow-sm);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.btn-primary:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.qa-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.qa-item {
  background: var(--bg-card);
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid var(--border-light);
  box-shadow: var(--shadow-sm);
}

.qa-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  font-size: 0.9rem;
}

.qa-answer {
  margin-top: 1.25rem;
  padding: 1.25rem;
  background: var(--bg-muted);
  border-radius: 8px;
  border-left: 3px solid var(--accent-sage);
}


</style>

<style scoped>
/* QA Answer Header specific override to ensure gap */
.answer-header {
  display: flex !important;
  justify-content: space-between !important;
  align-items: center !important;
  gap: 1rem !important;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: var(--accent-sage);
}

.btn-outline-primary {
  background: transparent;
  border: 1px solid var(--accent-coral);
  color: var(--accent-coral);
}

.btn-outline-primary:hover {
  background: var(--accent-coral);
  color: white;
}
</style>

<style scoped>
/* QA Avatar Styles */
.qa-author-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.qa-avatar, .seller-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  background: var(--bg-muted);
  flex-shrink: 0;
  display: grid;
  place-items: center;
}

.qa-avatar img, .seller-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-placeholder {
  font-weight: 700;
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.seller-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-light);
}

.seller-avatar {
  width: 48px;
  height: 48px;
}

.seller-details {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.seller-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  color: var(--text-muted);
  font-weight: 600;
  letter-spacing: 0.05em;
}

.seller-name {
  font-size: 1.1rem;
  color: var(--text-primary);
}

.follow-btn {
  border-radius: 20px;
  padding: 0.3rem 0.8rem;
}
</style>

