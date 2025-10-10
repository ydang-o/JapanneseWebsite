<template>
  <div class="card">
    <h2 class="page-heading">
      <span class="page-heading-jp">こんにちは：{{ displayNameText }}！</span>
    </h2>
    <div v-if="notLoggedIn" style="padding:8px 0">
      <p>このページを見るにはログインが必要です。</p>
      <button @click="goLogin">ログインへ</button>
    </div>
    <div v-else class="content-area">
      <div v-if="isLoading" class="loading-state">
        <div class="loader" aria-hidden="true"></div>
        <p>読み込み中...</p>
      </div>
      <div v-else class="dashboard">
        <section class="profile-card" aria-labelledby="user-profile-heading">
          <h3 id="user-profile-heading" class="visually-hidden">プロフィール情報</h3>
          <div class="profile-main">
            <div class="avatar" aria-hidden="true">{{ displayInitial }}</div>
            <div class="profile-details">
              <p class="profile-label">アカウント</p>
              <p class="profile-email">{{ data?.email }}</p>
              <p class="profile-name">
                <span class="label">表示名</span>
                <span>{{ data?.displayName || '未設定' }}</span>
              </p>
            </div>
          </div>
          <button class="refresh-button" @click="refresh" :disabled="isRefreshing">
            {{ isRefreshing ? '更新中...' : '最新情報を取得' }}
          </button>
        </section>

        <section class="summary-grid">
          <div class="summary-card emphasis">
            <span class="summary-label">ポイント残高</span>
            <span class="summary-value">{{ formattedBalance }}</span>
            <span class="summary-unit">pt</span>
          </div>
          <div class="summary-card">
            <span class="summary-label">取引件数</span>
            <span class="summary-value">{{ totalTransactions }}</span>
          </div>
          <div class="summary-card" v-if="latestTransactionDate">
            <span class="summary-label">最終取引</span>
            <span class="summary-value small">{{ latestTransactionDate }}</span>
          </div>
        </section>

        <section class="history-section" aria-labelledby="points-history-heading">
          <div class="history-header">
            <h3 id="points-history-heading">ポイント履歴</h3>
            <span v-if="hasTransactions" class="history-count">{{ totalTransactions }} 件</span>
          </div>
          <div class="history-header">
            <button class="history-filter" type="button" disabled>全期間</button>
          </div>
          <ul v-if="hasTransactions" class="transaction-list">
            <li v-for="tx in formattedTransactions" :key="tx.id" class="transaction-item">
              <div class="transaction-icon" aria-hidden="true"></div>
              <div class="transaction-content">
                <div class="transaction-header">
                  <span class="transaction-date">{{ tx.formattedDate }}</span>
                  <span :class="['transaction-delta', { positive: tx.delta > 0, negative: tx.delta < 0 }]">
                    {{ tx.formattedDelta }}
                  </span>
                </div>
                <p class="transaction-reason">{{ tx.reason }}</p>
              </div>
            </li>
          </ul>
          <div v-else class="empty-state-card">
            <p class="empty-state-title">まだポイント履歴がありません</p>
            <p class="empty-state-text">ポイントを獲得するとここに履歴が表示されます。</p>
          </div>
        </section>

        <section class="card-section" aria-labelledby="card-binding-heading">
          <div class="card-section-header">
            <h3 id="card-binding-heading">支払い用カードの登録</h3>
            <span class="card-status" :class="{ bound: cardState.status === 'bound' }">
              {{ cardStatusLabel }}
            </span>
          </div>
          <button class="manage-card-btn" @click="openCardModal">
            {{ cardState.status === 'bound' ? 'カード情報を管理' : 'カードを登録する' }}
          </button>
        </section>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <transition name="modal">
      <div v-if="showCardModal" class="card-modal-overlay" @click.self="closeCardModal">
        <div class="card-modal-content">
          <div class="card-modal-header">
            <h3>{{ cardState.status === 'bound' ? 'カード情報を更新' : 'カードを登録' }}</h3>
            <button class="modal-close-btn" type="button" @click="closeCardModal">×</button>
          </div>
          <form class="card-form" @submit.prevent="submitCard">
            <div class="field-row">
              <label for="account-name">口座名義（カタカナ）</label>
              <input
                id="account-name"
                v-model="cardState.form.accountName"
                type="text"
                placeholder="タロウ ヤマダ"
                :disabled="cardState.loading"
                required
              />
            </div>
            <div class="field-row">
              <label for="branch-code">支店番号</label>
              <input
                id="branch-code"
                v-model="cardState.form.branchCode"
                type="text"
                inputmode="numeric"
                placeholder="123"
                :disabled="cardState.loading"
                maxlength="4"
                required
              />
            </div>
            <div class="field-row">
              <label for="account-number">口座番号</label>
              <input
                id="account-number"
                v-model="cardState.form.accountNumber"
                type="text"
                inputmode="numeric"
                placeholder="1234567"
                :disabled="cardState.loading"
                maxlength="7"
                required
              />
            </div>
            <div class="field-row">
              <label for="pin">暗証番号</label>
              <input
                id="pin"
                v-model="cardState.form.pin"
                type="password"
                inputmode="numeric"
                placeholder="****"
                :disabled="cardState.loading"
                maxlength="4"
                required
              />
            </div>
            <div class="agreement">
              <label>
                <input type="checkbox" v-model="cardState.form.consent" :disabled="cardState.loading" />
                登録内容が実際の振込・決済に利用されない疑似機能であることに同意します。
              </label>
            </div>
            <div class="card-actions">
              <button type="submit" :disabled="cardState.loading || !cardState.form.consent">
                {{ cardState.loading ? '登録処理中...' : cardState.status === 'bound' ? 'カード情報を更新' : 'カードを登録' }}
              </button>
              <button
                type="button"
                class="ghost"
                @click="resetCardForm"
                :disabled="cardState.loading"
              >
                入力をリセット
              </button>
            </div>
            <p v-if="cardState.error" class="error">{{ cardState.error }}</p>
            <p v-if="cardState.success" class="success-message">{{ cardState.success }}</p>
          </form>
        </div>
      </div>
    </transition>
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
const showCardModal = ref(false)

const displayNameText = computed(() => {
  const rawName = data.value?.displayName?.trim()
  if (rawName) return rawName
  const email = data.value?.email
  if (email) {
    const local = email.split('@')[0]
    if (local) return local
  }
  return 'ゲスト'
})

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
  (points.value?.transactions ?? [])
    .slice()
    .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))
    .map((tx) => {
      const isNumber = typeof tx.delta === 'number'
      const deltaValue = isNumber
        ? tx.delta.toLocaleString('ja-JP', { maximumFractionDigits: 2 })
        : tx.delta
      return {
        ...tx,
        formattedDate: formatDateTime(tx.createdAt),
        formattedDelta: `${tx.delta > 0 ? '+' : ''}${deltaValue}`,
      }
    })
)

const hasTransactions = computed(() => formattedTransactions.value.length > 0)

const totalTransactions = computed(() => points.value?.transactions?.length ?? 0)

const latestTransactionDate = computed(() => formattedTransactions.value[0]?.formattedDate ?? '')

const displayInitial = computed(() => {
  const displayName = data.value?.displayName?.trim()
  if (displayName) return displayName.charAt(0)
  const email = data.value?.email
  return email ? email.charAt(0).toUpperCase() : '?'
})

const formattedBalance = computed(() => {
  const balance = points.value?.balance ?? 0
  try {
    return balance.toLocaleString('ja-JP')
  } catch (err) {
    return `${balance}`
  }
})

const cardState = ref({
  status: 'unbound',
  loading: false,
  error: '',
  success: '',
  form: {
    accountName: '',
    branchCode: '',
    accountNumber: '',
    pin: '',
    consent: false,
  },
})

const cardStatusLabel = computed(() => {
  if (cardState.value.status === 'bound') return '登録済み'
  if (cardState.value.status === 'pending') return '審査中'
  return '未登録'
})

function sanitizeNumeric(value) {
  return value.replace(/\D/g, '')
}

function openCardModal() {
  showCardModal.value = true
}

function closeCardModal() {
  showCardModal.value = false
}

function resetCardForm() {
  cardState.value.form = {
    accountName: '',
    branchCode: '',
    accountNumber: '',
    pin: '',
    consent: false,
  }
  cardState.value.error = ''
  cardState.value.success = ''
}

function validateCardForm() {
  const { accountName, branchCode, accountNumber, pin, consent } = cardState.value.form
  
  if (!consent) {
    return '同意にチェックを入れてください。'
  }
  
  const trimmedName = accountName.trim()
  if (!trimmedName) {
    return '口座名義を入力してください。'
  }
  if (!/^[\u30A0-\u30FF\s]+$/.test(trimmedName)) {
    return '口座名義はカタカナで入力してください。'
  }
  if (trimmedName.length < 2) {
    return '口座名義が短すぎます。'
  }
  
  const branchDigits = sanitizeNumeric(branchCode)
  if (branchDigits.length < 3 || branchDigits.length > 4) {
    return '支店番号は3桁または4桁の数字で入力してください。'
  }
  cardState.value.form.branchCode = branchDigits

  const accountDigits = sanitizeNumeric(accountNumber)
  if (accountDigits.length < 6 || accountDigits.length > 10) {
    return '口座番号は6桁以上10桁以下の数字で入力してください。'
  }
  cardState.value.form.accountNumber = accountDigits

  const pinDigits = sanitizeNumeric(pin)
  if (pinDigits.length !== 4) {
    return '暗証番号は4桁の数字で入力してください。'
  }
  cardState.value.form.pin = pinDigits
  
  return ''
}

async function submitCard() {
  cardState.value.error = ''
  cardState.value.success = ''
  const errorMessage = validateCardForm()
  if (errorMessage) {
    cardState.value.error = errorMessage
    return
  }
  cardState.value.loading = true
  cardState.value.status = 'pending'
  await new Promise((resolve) => setTimeout(resolve, 1200))
  try {
    const maskedAccount = cardState.value.form.accountNumber.slice(-4).padStart(cardState.value.form.accountNumber.length, '*')
  cardState.value.success = `口座番号 ${maskedAccount} を登録しました（デモ）。実際の振込処理には利用されません。`
    cardState.value.status = 'bound'
  cardState.value.form.consent = true
    
    // 成功后延迟关闭模态窗口
    setTimeout(() => {
      closeCardModal()
    }, 1500)
  } catch (err) {
    cardState.value.error = 'カード登録に失敗しました。時間をおいて再度お試しください。'
    cardState.value.status = 'unbound'
  } finally {
    cardState.value.loading = false
  }
}

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
.content-area {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 0;
  color: var(--muted);
}

.loader {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 3px solid rgba(233, 84, 32, 0.2);
  border-top-color: var(--primary);
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.profile-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 24px;
  border-radius: 16px;
  background: var(--card);
  border: 1px solid rgba(229, 231, 235, 0.7);
  box-shadow: 0 18px 32px -24px rgba(15, 23, 42, 0.2);
}

.profile-main {
  display: flex;
  align-items: center;
  gap: 20px;
}

.avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(140deg, var(--primary) 0%, var(--primary-hover) 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.5rem;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.profile-details {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.profile-label {
  font-size: 0.85rem;
  color: var(--muted);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.profile-email {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text);
}

.profile-name {
  display: flex;
  gap: 8px;
  align-items: baseline;
  color: var(--text);
}

.profile-name .label {
  font-size: 0.85rem;
  color: var(--muted);
}

.refresh-button {
  align-self: flex-start;
  padding: 10px 20px;
  background: var(--primary);
  border: none;
  color: #fff;
  border-radius: 9999px;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
  font-weight: 600;
  letter-spacing: 0.02em;
  box-shadow: 0 12px 24px -18px rgba(233, 84, 32, 0.7);
}

.refresh-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 18px 42px -24px rgba(233, 84, 32, 0.6);
}

.refresh-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.summary-card {
  background: var(--card);
  border-radius: 16px;
  padding: 18px 20px;
  border: 1px solid rgba(229, 231, 235, 0.7);
  display: flex;
  flex-direction: column;
  gap: 6px;
  box-shadow: 0 16px 30px -28px rgba(15, 23, 42, 0.22);
}

.summary-card.emphasis {
  background: linear-gradient(140deg, var(--primary) 0%, rgba(233, 84, 32, 0.85) 100%);
  color: #fff;
  border: none;
}

.summary-card.emphasis .summary-label {
  color: rgba(255, 255, 255, 0.85);
}

.summary-card.emphasis .summary-value {
  font-size: 1.8rem;
}

.summary-card.emphasis .summary-unit {
  font-size: 0.85rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.summary-label {
  font-size: 0.85rem;
  color: var(--muted);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.summary-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--text);
}

.summary-value.small {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text);
}

.summary-unit {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.9);
}

.history-section {
  background: var(--card);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(229, 231, 235, 0.7);
  box-shadow: 0 18px 32px -24px rgba(15, 23, 42, 0.18);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.history-count {
  font-size: 0.9rem;
  color: var(--muted);
}

.history-filter {
  padding: 6px 14px;
  border-radius: 9999px;
  border: 1px solid var(--border);
  background: var(--bg);
  color: var(--muted);
  font-size: 0.85rem;
  cursor: not-allowed;
}

.transaction-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.transaction-item {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 14px;
  padding: 16px 18px;
  border-radius: 16px;
  background: rgba(233, 84, 32, 0.05);
  border: 1px solid rgba(233, 84, 32, 0.12);
}

.transaction-icon {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: rgba(233, 84, 32, 0.15);
  position: relative;
}

.transaction-icon::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--primary);
}

.transaction-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.transaction-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.transaction-date {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text);
}

.transaction-delta {
  font-size: 1.05rem;
  font-weight: 700;
}

.transaction-delta.positive {
  color: #1e8e3e;
}

.transaction-delta.negative {
  color: #d93025;
}

.transaction-reason {
  color: var(--muted);
  font-size: 0.95rem;
  line-height: 1.4;
}

.empty-state-card {
  padding: 32px;
  border-radius: 16px;
  border: 1px dashed rgba(148, 163, 184, 0.7);
  background: var(--bg);
  text-align: center;
  color: var(--muted);
}

.empty-state-title {
  font-weight: 600;
  margin-bottom: 6px;
  color: var(--text);
}

.empty-state-text {
  font-size: 0.95rem;
}

.error {
  color: #d93025;
  background: rgba(217, 48, 37, 0.08);
  border: 1px solid rgba(217, 48, 37, 0.15);
  padding: 12px 16px;
  border-radius: 12px;
  margin-top: 8px;
}

.visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.card-section {
  background: var(--card);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(229, 231, 235, 0.7);
  box-shadow: 0 18px 32px -24px rgba(15, 23, 42, 0.18);
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-status {
  font-size: 0.85rem;
  color: var(--muted);
  padding: 4px 12px;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.16);
}

.card-status.bound {
  color: #1e8e3e;
  background: rgba(30, 142, 62, 0.16);
}

.manage-card-btn {
  width: 100%;
  padding: 14px 24px;
  background: var(--primary);
  color: #fff;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(233, 84, 32, 0.3);
}

.manage-card-btn:hover {
  background: var(--primary-hover);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(233, 84, 32, 0.4);
}

.card-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(31, 35, 40, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.card-modal-content {
  background: var(--card);
  border-radius: 20px;
  width: 100%;
  max-width: 580px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.card-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  background: var(--card);
  z-index: 1;
}

.card-modal-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text);
}

.modal-close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  color: var(--muted);
  cursor: pointer;
  line-height: 1;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.modal-close-btn:hover {
  background: rgba(148, 163, 184, 0.1);
  color: var(--text);
}

.card-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 28px;
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-active .card-modal-content,
.modal-leave-active .card-modal-content {
  transition: transform 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .card-modal-content,
.modal-leave-to .card-modal-content {
  transform: scale(0.9) translateY(20px);
}

.field-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-row label {
  font-weight: 600;
  color: var(--text);
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-type-badge {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--primary);
  background: rgba(233, 84, 32, 0.1);
  padding: 2px 8px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.field-row input {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: #fff;
  font-size: 0.95rem;
}

.field-grid {
  display: grid;
  gap: 16px;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
}

.agreement {
  background: rgba(233, 84, 32, 0.06);
  border-radius: 12px;
  padding: 12px;
  border: 1px solid rgba(233, 84, 32, 0.12);
}

.agreement label {
  display: flex;
  gap: 8px;
  font-size: 0.9rem;
  color: var(--text);
  align-items: flex-start;
}

.card-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.card-actions button {
  padding: 10px 20px;
  border-radius: 10px;
  border: none;
  font-weight: 600;
  cursor: pointer;
  background: var(--primary);
  color: #fff;
  transition: background 0.2s, transform 0.2s;
}

.card-actions button:hover:not(:disabled) {
  background: var(--primary-hover);
  transform: translateY(-2px);
}

.card-actions button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.card-actions .ghost {
  background: rgba(148, 163, 184, 0.12);
  color: var(--text);
}

.success-message {
  color: #1e8e3e;
  font-weight: 600;
}

.page-heading {
  margin-bottom: 16px;
  color: var(--text);
}

.page-heading-jp {
  display: inline-block;
  font-size: 2.2rem;
  font-weight: 700;
  color: var(--primary);
  letter-spacing: 0.05em;
}

.page-heading-jp::after {
  content: '';
  display: block;
  width: 48px;
  height: 3px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
  margin-top: 6px;
  border-radius: 999px;
}

@media (max-width: 640px) {
  .profile-card,
  .history-section {
    padding: 20px;
  }

  .transaction-item {
    grid-template-columns: 1fr;
  }

  .transaction-icon {
    display: none;
  }

  .transaction-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }

  .refresh-button {
    width: 100%;
    text-align: center;
  }

  .card-section {
    padding: 20px;
  }

  .card-actions button {
    width: 100%;
  }

  .page-heading-jp {
    font-size: 2rem;
  }

  .page-heading-jp::after {
    width: 36px;
  }
}
</style>