<template>
  <div class="card">
    <h2>マイページ</h2>
    <div v-if="!data">読み込み中...</div>
    <div v-else>
      <p>メール: {{ data.email }}</p>
      <p>表示名: {{ data.displayName }}</p>
      <p>ポイント残高: <strong>{{ points?.balance ?? 0 }}</strong></p>
      <h3>履歴</h3>
      <ul>
        <li v-for="t in points?.transactions || []" :key="t.id">{{ t.createdAt }}: {{ t.delta }} ({{ t.reason }})</li>
      </ul>
    </div>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiFetch } from '../api'

const data = ref(null)
const points = ref(null)
const error = ref('')

onMounted(async () => {
  try {
    data.value = await apiFetch('/user/me')
    points.value = await apiFetch('/user/points')
  } catch (e) {
    error.value = e.message
  }
})
</script> 