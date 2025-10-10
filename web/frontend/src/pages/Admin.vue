<template>
  <div class="card">
    <h2>管理</h2>
    <div class="form" style="margin-bottom:16px">
      <div>
        <label>管理キー (X-ADMIN-KEY)</label>
        <input v-model="adminKey" placeholder="change-admin-key" />
      </div>
      <div class="row">
        <button @click="initDb" :disabled="loading" style="background:#666">DB 初期化</button>
        <button @click="reload" :disabled="loading">一覧を更新</button>
      </div>
      <p v-if="message" class="success">{{ message }}</p>
      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <AdminNotice
      :visible="notice.visible"
      :type="notice.type"
      :title="notice.title"
      :description="notice.description"
      @close="notice.visible = false"
    />

    <div class="card" style="padding:12px; margin-bottom:16px">
      <h3>管理者登録（バックエンド作成）</h3>
      <div class="row">
        <input v-model="createPhone" type="tel" placeholder="電話番号 (例: 09012345678)" style="max-width:220px" />
        <input v-model="createName" type="text" placeholder="表示名" style="max-width:200px" />
        <button @click="createUser" :disabled="loading">作成</button>
      </div>
    </div>

    <div class="card" style="padding:12px">
      <table style="width:100%; border-collapse: collapse;">
        <thead>
          <tr style="text-align:left; border-bottom: 1px solid var(--border)">
            <th style="padding:8px">ID</th>
            <th style="padding:8px">電話</th>
            <th style="padding:8px">表示名</th>
            <th style="padding:8px">ポイント</th>
            <th style="padding:8px">ステータス</th>
            <th style="padding:8px; width:380px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" style="border-bottom: 1px solid var(--border)">
            <td style="padding:8px">{{ u.id }}</td>
            <td style="padding:8px">{{ u.email }}</td>
            <td style="padding:8px">{{ u.displayName }}</td>
            <td style="padding:8px"><strong>{{ u.points }}</strong></td>
            <td style="padding:8px">{{ statusLabel(u.status) }}</td>
            <td style="padding:8px">
              <div class="adjust-group">
                <input
                  v-model.number="rowDelta[u.id]"
                  type="number"
                  placeholder="±ポイント"
                  class="small-input"
                />
                <input
                  v-model="rowReason[u.id]"
                  type="text"
                  placeholder="理由 (例: キャンペーン追加)"
                  class="reason-input"
                />
              </div>
              <div class="action-group">
                <button @click="adjustRow(u)" :disabled="loading" class="secondary">反映</button>
                <button @click="approve(u)" :disabled="loading" class="primary">承認</button>
                <button @click="reject(u)" :disabled="loading" class="danger">却下</button>
                <button @click="openResetModal(u)" :disabled="loading" class="warning">PWリセット</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="row" style="justify-content:flex-end; margin-top:12px">
        <button @click="prevPage" :disabled="page<=1">前へ</button>
        <span style="padding:0 8px">{{ page }} / {{ totalPages }}</span>
        <button @click="nextPage" :disabled="page>=totalPages">次へ</button>
      </div>
    </div>

    <transition name="fade">
      <div
        v-if="resetModal.visible"
        class="modal-overlay"
        @click.self="closeResetModal"
      >
        <div class="modal-card">
          <h4>パスワードをリセット</h4>
          <p class="modal-text">
            ID {{ resetModal.user?.id }} / {{ resetModal.user?.displayName }} のパスワードを初期化します。<br />
            確認のため管理者パスワードを入力してください。
          </p>
          <input
            v-model="resetModal.password"
            type="password"
            class="modal-input"
            placeholder="管理者パスワード"
            :disabled="loading"
          />
          <div class="modal-actions">
            <button class="warning" @click="submitResetPassword" :disabled="loading">
              リセット実行
            </button>
            <button class="secondary" @click="closeResetModal" :disabled="loading">
              キャンセル
            </button>
          </div>
          <p class="modal-note">リセット後の初期パスワードは「123456」です。</p>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { apiFetch } from '../api'
import AdminNotice from './components/AdminNotice.vue'

const adminKey = ref('change-admin-key')
const loading = ref(false)
const error = ref('')
const message = ref('')
const users = ref([])
const page = ref(1)
const pageSize = ref(20)
const total = ref(0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const rowDelta = reactive({})
const rowReason = reactive({})
const createPhone = ref('')
const createName = ref('')
const notice = reactive({
  visible: false,
  type: 'info',
  title: '',
  description: '',
})
const resetModal = reactive({
  visible: false,
  user: null,
  password: '',
})

function showNotice(options) {
  notice.visible = true
  notice.type = options.type || 'info'
  notice.title = options.title || ''
  notice.description = options.description || ''
}

function hideNotice() {
  notice.visible = false
}

function statusLabel(status) {
  if (status === 'approved') return '承認済み'
  if (status === 'rejected') return '却下'
  if (status === 'pending') return '審査中'
  return status
}

async function fetchUsers() {
  loading.value = true
  error.value = ''
  try {
    const data = await apiFetch(`/admin/users?page=${page.value}&pageSize=${pageSize.value}`, {
      headers: { 'X-ADMIN-KEY': adminKey.value },
    })
    users.value = data.items
    total.value = data.total
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function createUser() {
  loading.value = true
  error.value = ''
  message.value = ''
  try {
    const res = await apiFetch('/admin/users/create', {
      method: 'POST',
      headers: { 'X-ADMIN-KEY': adminKey.value },
      body: JSON.stringify({ phone: createPhone.value, displayName: createName.value }),
    })
    message.value = res.message
    createPhone.value = ''
    createName.value = ''
    await fetchUsers()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function approve(u) {
  loading.value = true
  error.value = ''
  message.value = ''
  try {
    const res = await apiFetch('/admin/users/approve', {
      method: 'POST',
      headers: { 'X-ADMIN-KEY': adminKey.value },
      body: JSON.stringify({ userId: u.id }),
    })
    message.value = res.message
    await fetchUsers()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function reject(u) {
  loading.value = true
  error.value = ''
  message.value = ''
  try {
    const res = await apiFetch('/admin/users/reject', {
      method: 'POST',
      headers: { 'X-ADMIN-KEY': adminKey.value },
      body: JSON.stringify({ userId: u.id }),
    })
    message.value = res.message
    await fetchUsers()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function openResetModal(u) {
  resetModal.visible = true
  resetModal.user = u
  resetModal.password = ''
}

function closeResetModal() {
  resetModal.visible = false
  resetModal.user = null
  resetModal.password = ''
}

async function submitResetPassword() {
  const target = resetModal.user
  if (!target) return

  const adminPw = resetModal.password.trim()
  if (!adminPw) {
    showNotice({
      type: 'warning',
      title: '管理者パスワードが必要です',
      description: 'パスワードリセットを実行する前に管理者パスワードを入力してください。',
    })
    return
  }

  loading.value = true
  error.value = ''
  message.value = ''
  hideNotice()
  try {
    const res = await apiFetch('/admin/users/reset-password', {
      method: 'POST',
      headers: { 'X-ADMIN-KEY': adminKey.value },
      body: JSON.stringify({ userId: target.id, adminPassword: adminPw }),
    })
    message.value = res.message
    showNotice({
      type: 'success',
      title: 'パスワードをリセットしました',
      description: `ID ${target.id} の初期パスワードは「123456」です。`,
    })
    closeResetModal()
  } catch (e) {
    error.value = e.message
    showNotice({
      type: 'error',
      title: 'リセットに失敗しました',
      description: e.message,
    })
  } finally {
    loading.value = false
  }
}

async function adjustRow(u) {
  error.value = ''
  message.value = ''
  const delta = Number(rowDelta[u.id] || 0)
  const reason = (rowReason[u.id] || '').trim()

  if (!delta) {
    showNotice({
      type: 'warning',
      title: 'ポイント数を入力してください',
      description: '正負どちらでも構いませんが、0は設定できません。',
    })
    return
  }

  if (!reason) {
    showNotice({
      type: 'warning',
      title: '理由を入力してください',
      description: '操作履歴を明確にするため、理由を必ず記録してください。',
    })
    return
  }

  const confirmMessage = `ID ${u.id} (${u.displayName}) のポイントを ${delta > 0 ? '+' : ''}${delta} 変更します。\n理由: ${reason}\nよろしいですか？`
  if (!window.confirm(confirmMessage)) {
    showNotice({
      type: 'info',
      title: '処理をキャンセルしました',
      description: '変更は送信されていません。',
    })
    return
  }

  loading.value = true
  hideNotice()
  try {
    const res = await apiFetch('/admin/points/adjust', {
      method: 'POST',
      headers: { 'X-ADMIN-KEY': adminKey.value },
      body: JSON.stringify({ userId: u.id, delta, reason }),
    })
    message.value = `ID ${u.id} 残高: ${res.balance}`
    showNotice({
      type: 'success',
      title: 'ポイントを更新しました',
      description: `${u.displayName} の残高は ${res.balance} になりました。`,
    })
    await fetchUsers()
    rowDelta[u.id] = 0
    rowReason[u.id] = ''
  } catch (e) {
    error.value = e.message
    showNotice({
      type: 'error',
      title: 'ポイント更新に失敗しました',
      description: e.message,
    })
  } finally {
    loading.value = false
  }
}

async function initDb() {
  error.value = ''
  message.value = ''
  loading.value = true
  try {
    const res = await apiFetch('/admin/init-db', {
      method: 'POST',
      headers: { 'X-ADMIN-KEY': adminKey.value },
    })
    message.value = res.message
    await fetchUsers()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

function prevPage() { if (page.value > 1) { page.value--; fetchUsers() } }
function nextPage() { if (page.value < totalPages.value) { page.value++; fetchUsers() } }
function reload() { fetchUsers() }

onMounted(fetchUsers)
</script>

<style scoped>
.adjust-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 8px;
}

.action-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.small-input {
  width: 120px;
}

.reason-input {
  width: 100%;
  max-width: 240px;
}

.secondary {
  background: #f3f4f6;
  color: #1f2328;
}

.primary {
  background: #2563eb;
  color: #fff;
}

.danger {
  background: #dc2626;
  color: #fff;
}

.warning {
  background: #f59e0b;
  color: #1f2328;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  z-index: 1000;
}

.modal-card {
  background: #fff;
  width: 100%;
  max-width: 360px;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.2);
}

.modal-text {
  font-size: 14px;
  line-height: 1.6;
  color: #374151;
  margin-top: 12px;
}

.modal-input {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px 12px;
  margin-top: 16px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 20px;
}

.modal-note {
  margin-top: 16px;
  font-size: 12px;
  color: var(--muted);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style> 