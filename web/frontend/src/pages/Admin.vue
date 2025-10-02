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

    <div class="card" style="padding:12px">
      <table style="width:100%; border-collapse: collapse;">
        <thead>
          <tr style="text-align:left; border-bottom: 1px solid var(--border)">
            <th style="padding:8px">ID</th>
            <th style="padding:8px">メール</th>
            <th style="padding:8px">表示名</th>
            <th style="padding:8px">ポイント</th>
            <th style="padding:8px; width:220px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id" style="border-bottom: 1px solid var(--border)">
            <td style="padding:8px">{{ u.id }}</td>
            <td style="padding:8px">{{ u.email }}</td>
            <td style="padding:8px">{{ u.displayName }}</td>
            <td style="padding:8px"><strong>{{ u.points }}</strong></td>
            <td style="padding:8px">
              <input v-model.number="rowDelta[u.id]" type="number" placeholder="±ポイント" style="width:100px; margin-right:8px" />
              <button @click="adjustRow(u)" :disabled="loading">反映</button>
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { apiFetch } from '../api'

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

async function adjustRow(u) {
  error.value = ''
  message.value = ''
  const delta = Number(rowDelta[u.id] || 0)
  if (!delta) return
  loading.value = true
  try {
    const res = await apiFetch('/admin/points/adjust', {
      method: 'POST',
      headers: { 'X-ADMIN-KEY': adminKey.value },
      body: JSON.stringify({ userId: u.id, delta, reason: '管理調整' }),
    })
    message.value = `ID ${u.id} 残高: ${res.balance}`
    await fetchUsers()
    rowDelta[u.id] = 0
  } catch (e) {
    error.value = e.message
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