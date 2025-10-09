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
              <label for="cardholder">カード名義人 (ローマ字)</label>
              <input
                id="cardholder"
                v-model="cardState.form.holder"
                type="text"
                autocomplete="cc-name"
                placeholder="TARO YAMADA"
                :disabled="cardState.loading"
                required
              />
            </div>
            <div class="field-row">
              <label for="card-number">
                カード番号
                <span v-if="cardState.cardType" class="card-type-badge">{{ cardState.cardType }}</span>
              </label>
              <input
                id="card-number"
                v-model="cardState.form.number"
                type="text"
                autocomplete="cc-number"
                inputmode="numeric"
                placeholder="1234 5678 9012 3456"
                :disabled="cardState.loading"
                maxlength="19"
                required
              />
            </div>
            <div class="field-grid">
              <div class="field-row">
                <label for="card-exp">有効期限</label>
                <input
                  id="card-exp"
                  v-model="cardState.form.exp"
                  type="text"
                  autocomplete="cc-exp"
                  placeholder="MM/YY"
                  :disabled="cardState.loading"
                  maxlength="5"
                  required
                />
              </div>
              <div class="field-row">
                <label for="card-cvc">セキュリティコード</label>
                <input
                  id="card-cvc"
                  v-model="cardState.form.cvc"
                  type="password"
                  autocomplete="cc-csc"
                  placeholder="***"
                  :disabled="cardState.loading"
                  maxlength="4"
                  required
                />
              </div>
            </div>
            <div class="field-row">
              <label for="card-zip">ご請求先郵便番号</label>
              <input
                id="card-zip"
                v-model="cardState.form.zip"
                type="text"
                inputmode="numeric"
                placeholder="1000001"
                :disabled="cardState.loading"
                maxlength="7"
                required
              />
            </div>
            <div class="agreement">
              <label>
                <input type="checkbox" v-model="cardState.form.consent" :disabled="cardState.loading" />
                登録内容が実際の決済に利用されない疑似機能であることに同意します。
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
import { computed, ref, onMounted, watch } from 'vue'
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
  cardType: '',
  form: {
    holder: '',
    number: '',
    exp: '',
    cvc: '',
    zip: '',
    consent: false,
  },
})

const cardStatusLabel = computed(() => {
  if (cardState.value.status === 'bound') return '登録済み'
  if (cardState.value.status === 'pending') return '審査中'
  return '未登録'
})

function detectCardType(number) {
  const digits = number.replace(/\D/g, '')
  if (/^4/.test(digits)) return 'Visa'
  if (/^5[1-5]/.test(digits)) return 'MasterCard'
  if (/^3[47]/.test(digits)) return 'Amex'
  if (/^35/.test(digits)) return 'JCB'
  return ''
}

function sanitizeCardNumber(value) {
  return value.replace(/[^0-9]/g, '').slice(0, 16)
}

function formatCardNumber(value) {
  const digits = sanitizeCardNumber(value)
  return digits.replace(/(\d{4})(?=\d)/g, '$1 ').trim()
}

function sanitizeNumeric(value) {
  return value.replace(/\D/g, '')
}

function luhnCheck(cardNumber) {
  const digits = cardNumber.replace(/\D/g, '')
  let sum = 0
  let isEven = false
  for (let i = digits.length - 1; i >= 0; i--) {
    let digit = parseInt(digits[i], 10)
    if (isEven) {
      digit *= 2
      if (digit > 9) digit -= 9
    }
    sum += digit
    isEven = !isEven
  }
  return sum % 10 === 0
}

function sanitizeExp(value) {
  return value
    .replace(/[^0-9]/g, '')
    .slice(0, 4)
    .replace(/(\d{2})(\d{1,2})?/, (match, mm, yy = '') => (yy ? `${mm}/${yy}` : mm))
}

function openCardModal() {
  showCardModal.value = true
}

function closeCardModal() {
  showCardModal.value = false
}

function resetCardForm() {
  cardState.value.form = {
    holder: '',
    number: '',
    exp: '',
    cvc: '',
    zip: '',
    consent: false,
  }
  cardState.value.error = ''
  cardState.value.success = ''
}

function validateCardForm() {
  const { holder, number, exp, cvc, zip, consent } = cardState.value.form
  
  if (!consent) {
    return '同意にチェックを入れてください。'
  }
  
  const trimmedHolder = holder.trim()
  if (!trimmedHolder) {
    return 'カード名義人を入力してください。'
  }
  if (!/^[A-Za-z\s]+$/.test(trimmedHolder)) {
    return 'カード名義人はローマ字で入力してください。'
  }
  if (trimmedHolder.length < 3) {
    return 'カード名義人が短すぎます。'
  }
  
  const cardDigits = sanitizeCardNumber(number)
  if (cardDigits.length < 13) {
    return 'カード番号は13桁以上で入力してください。'
  }
  if (cardDigits.length > 16) {
    return 'カード番号は16桁以内で入力してください。'
  }
  
  // Luhn check for card validation
  if (!luhnCheck(cardDigits)) {
    return 'カード番号が正しくありません。入力内容をご確認ください。'
  }
  
  if (!/^(0[1-9]|1[0-2])\/(\d{2})$/.test(exp)) {
    return '有効期限はMM/YY形式で入力してください（例：12/25）。'
  }
  const [mm, yy] = exp.split('/')
  const expMonth = Number(mm)
  const expYear = 2000 + Number(yy)
  if (expMonth < 1 || expMonth > 12) {
    return '有効期限の月は01〜12で入力してください。'
  }
  
  const now = new Date()
  const currentYear = now.getFullYear()
  const currentMonth = now.getMonth() + 1
  if (expYear < currentYear || (expYear === currentYear && expMonth < currentMonth)) {
    return '有効期限が切れています。'
  }
  if (expYear > currentYear + 20) {
    return '有効期限が正しくありません。'
  }
  
  if (!/^\d{3,4}$/.test(cvc)) {
    return 'セキュリティコードは3桁または4桁の数字で入力してください。'
  }
  
  const zipDigits = sanitizeNumeric(zip)
  if (zipDigits.length !== 7) {
    return '郵便番号は7桁の数字で入力してください（例：1000001）。'
  }
  
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
    const last4 = sanitizeCardNumber(cardState.value.form.number).slice(-4)
    const cardTypeText = cardState.value.cardType ? ` (${cardState.value.cardType})` : ''
    const maskedNumber = `**** **** **** ${last4}`
    cardState.value.success = `${maskedNumber}${cardTypeText} を登録しました（デモ）。実際の決済処理には利用されません。`
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

watch(
  () => cardState.value.form.number,
  (value) => {
    const formatted = formatCardNumber(value)
    if (formatted !== value) {
      cardState.value.form.number = formatted
    }
    cardState.value.cardType = detectCardType(value)
  }
)

watch(
  () => cardState.value.form.exp,
  (value) => {
    const formatted = sanitizeExp(value)
    if (formatted !== value) {
      cardState.value.form.exp = formatted
    }
  }
)

watch(
  () => cardState.value.form.cvc,
  (value) => {
    const sanitized = sanitizeNumeric(value).slice(0, 4)
    if (sanitized !== value) {
      cardState.value.form.cvc = sanitized
    }
  }
)

watch(
  () => cardState.value.form.zip,
  (value) => {
    const sanitized = sanitizeNumeric(value).slice(0, 7)
    if (sanitized !== value) {
      cardState.value.form.zip = sanitized
    }
  }
)

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