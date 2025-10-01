<template>
  <div class="card">
    <h2>管理</h2>
    <div class="form">
      <div>
        <label>管理キー (X-ADMIN-KEY)</label>
        <input v-model="adminKey" placeholder="change-admin-key" />
      </div>
      <div>
        <label>ユーザーID</label>
        <input v-model.number="userId" type="number" />
      </div>
      <div>
        <label>ポイント増減 (delta)</label>
        <input v-model.number="delta" type="number" />
      </div>
      <div>
        <label>理由</label>
        <input v-model="reason" />
      </div>
      <div class="row">
        <button @click="adjust" :disabled="loading">更新</button>
        <button @click="initDb" :disabled="loading" style="background:#666">DB 初期化</button>
      </div>
      <p v-if="message" class="success">{{ message }}</p>
      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { apiFetch } from '../api'

const adminKey = ref('change-admin-key')
const userId = ref(1)
const delta = ref(10)
const reason = ref('調整')
const loading = ref(false)
const error = ref('')
const message = ref('')

async function adjust() {
  error.value = ''
  message.value = ''
  loading.value = true
  try {
    const res = await apiFetch('/admin/points/adjust', {
      method: 'POST',
      headers: { 'X-ADMIN-KEY': adminKey.value },
      body: JSON.stringify({ userId: userId.value, delta: delta.value, reason: reason.value }),
    })
    message.value = `残高: ${res.balance}`
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
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script> 