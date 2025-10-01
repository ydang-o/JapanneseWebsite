<template>
  <div class="card">
    <h2>新規登録</h2>
    <form class="form" @submit.prevent="onSubmit">
      <div>
        <label>メールアドレス</label>
        <input v-model="email" type="email" required />
      </div>
      <div>
        <label>表示名</label>
        <input v-model="displayName" type="text" />
      </div>
      <div>
        <label>パスワード</label>
        <input v-model="password" type="password" required />
      </div>
      <button :disabled="loading">登録</button>
      <p v-if="message" class="success">{{ message }}</p>
      <p v-if="error" class="error">{{ error }}</p>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { apiFetch } from '../api'

const email = ref('')
const displayName = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const message = ref('')

async function onSubmit() {
  error.value = ''
  message.value = ''
  loading.value = true
  try {
    const res = await apiFetch('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email: email.value, password: password.value, displayName: displayName.value }),
    })
    message.value = res.message || '登録完了'
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script> 