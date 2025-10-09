<template>
  <div class="card">
    <h2>マイページ</h2>
    <div v-if="notLoggedIn" style="padding:8px 0">
      <p>このページを見るにはログインが必要です。</p>
      <button @click="goLogin">ログインへ</button>
    </div>
    <div v-else>
      <div v-if="isLoading">読み込み中...</div>
      <div v-else>
        <div class="profile-section">
          <p>アカウント: {{ data?.email }}</p>
          <p>表示名: {{ data?.displayName }}</p>
          <p>ポイント残高: <strong>{{ points.balance }}</strong></p>
          <button class="refresh-button" @click="refresh" :disabled="isRefreshing">
            {{ isRefreshing ? '更新中...' : '最新情報を取得' }}
          </button>
        </div>

        <h3>履歴</h3>
        <ul v-if="hasTransactions" class="transaction-list">
          <li v-for="tx in formattedTransactions" :key="tx.id" class="transaction-item">
            <div class="transaction-header">
              <span class="transaction-date">{{ tx.formattedDate }}</span>
              <span :class="['transaction-delta', { positive: tx.delta > 0, negative: tx.delta < 0 }]">
                {{ tx.formattedDelta }}
              </span>
            </div>
            <span class="transaction-reason">{{ tx.reason }}</span>
          </li>
        </ul>
        <p v-else class="empty-state">まだポイント履歴がありません。</p>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { apiFetch, getAuthToken } from '../api'

const data = ref(null)
const points = ref({ balance: 0, transactions: [] })
const error = ref('')
const notLoggedIn = ref(false)
const isLoading = ref(true)
const isRefreshing = ref(false)

function goLogin() { location.hash = '#/login' }

function formatDateTime(isoString) {
  if (!isoString) return ''
  try {
    return new Date(isoString).toLocaleString('ja-JP', { timeZone: 'Asia/Tokyo' })
  } catch (err) {
    return isoString
  }
}

const formattedTransactions = computed(() =>
  (points.value?.transactions ?? []).map((tx) => ({
    ...tx,
    formattedDate: formatDateTime(tx.createdAt),
    formattedDelta: `${tx.delta > 0 ? '+' : ''}${tx.delta}`,
  }))
)

const hasTransactions = computed(() => formattedTransactions.value.length > 0)

async function loadUserPoints(options = { silent: false }) {
  const token = getAuthToken()
  if (!token) {
    notLoggedIn.value = true
    isLoading.value = false
    return
  }

  if (options.silent) {
    isRefreshing.value = true
  } else {
    isLoading.value = true
  }

  error.value = ''

  try {
    const [profile, pointInfo] = await Promise.all([
      apiFetch('/user/me'),
      apiFetch('/user/points'),
    ])
    data.value = profile
    points.value = pointInfo
  } catch (e) {
    const message = e?.message || ''
    if (message.toLowerCase().includes('認証') || message.includes('401')) {
      notLoggedIn.value = true
      error.value = ''
      data.value = null
      points.value = { balance: 0, transactions: [] }
    } else {
      error.value = message || 'データの取得に失敗しました'
    }
  } finally {
    isLoading.value = false
    isRefreshing.value = false
  }
}

function refresh() {
  loadUserPoints({ silent: true })
}

onMounted(() => {
  loadUserPoints()
})
</script> 

<style scoped>
.profile-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.refresh-button {
  align-self: flex-start;
  padding: 8px 16px;
  background: #ff0211;
  border: none;
  color: #fff;
  border-radius: 6px;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.refresh-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.transaction-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.transaction-item {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.transaction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.transaction-delta {
  font-size: 1rem;
}

.transaction-delta.positive {
  color: #0f9d58;
}

.transaction-delta.negative {
  color: #d93025;
}

.transaction-reason {
  color: #666;
  font-size: 0.9rem;
}

.empty-state {
  color: #666;
}

.error {
  color: #d93025;
  margin-top: 12px;
}
</style>