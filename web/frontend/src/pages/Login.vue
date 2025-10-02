<template>
  <div>
    <div class="login-banner"></div>
    <div class="login-wrap">
      <div class="login-card">
        <div class="login-title">ログイン</div>
        <form class="login-form" @submit.prevent="onSubmit">
          <div class="field">
            <label>メール/ユーザー名</label>
            <input v-model="email" type="text" required />
          </div>
          <div class="field">
            <label>パスワード</label>
            <input v-model="password" type="password" required />
          </div>
          <button class="login-btn" :disabled="loading">ログイン</button>
          <p v-if="error" class="error">{{ error }}</p>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { apiFetch, setAuthToken } from '../api'
import './login.css'

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    const res = await apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: email.value, password: password.value }),
    })
    setAuthToken(res.token)
    location.hash = '#/user'
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script> 