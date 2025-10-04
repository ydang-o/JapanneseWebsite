<template>
  <div class="card">
    <h2>マイページ</h2>
    <div v-if="notLoggedIn" style="padding:8px 0">
      <p>このページを見るにはログインが必要です。</p>
      <button @click="goLogin">ログインへ</button>
    </div>
    <div v-else>
      <div v-if="!data">読み込み中...</div>
      <div v-else>
        <p>アカウント: {{ data.email }}</p>
        <p>表示名: {{ data.displayName }}</p>
        <p>ポイント残高: <strong>{{ points?.balance ?? 0 }}</strong></p>
        <h3>履歴</h3>
        <ul>
          <li v-for="t in points?.transactions || []" :key="t.id">{{ t.createdAt }}: {{ t.delta }} ({{ t.reason }})</li>
        </ul>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiFetch, getAuthToken } from '../api'

const data = ref(null)
const points = ref(null)
const error = ref('')
const notLoggedIn = ref(false)

function goLogin() { location.hash = '#/login' }

onMounted(async () => {
  const token = getAuthToken()
  if (!token) {
    notLoggedIn.value = true
    return
  }
  try {
    data.value = await apiFetch('/user/me')
    points.value = await apiFetch('/user/points')
  } catch (e) {
    if ((e.message || '').toLowerCase().includes('認証') || (e.message || '').includes('401')) {
      notLoggedIn.value = true
      error.value = ''
    } else {
      error.value = e.message
    }
  }
})
</script> 