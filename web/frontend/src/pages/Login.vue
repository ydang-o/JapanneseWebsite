<template>
  <div class="card">
    <h2>ログイン</h2>
    <div v-if="showEmbed" class="embed">
      <iframe :src="embedSrc" style="width:100%; height:60vh; border:1px solid #eee; border-radius:8px;"></iframe>
    </div>
    <form class="form" @submit.prevent="onSubmit">
      <div>
        <label>メール/ユーザー名</label>
        <input v-model="email" type="text" required />
      </div>
      <div>
        <label>パスワード</label>
        <input v-model="password" type="password" required />
      </div>
      <button :disabled="loading">ログイン</button>
      <p v-if="error" class="error">{{ error }}</p>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiFetch, setAuthToken, getAuthToken } from '../api'

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const showEmbed = ref(false)
const embedSrc = ref('')

onMounted(async () => {
  const token = getAuthToken()
  if (token) {
    try {
      const me = await apiFetch('/user/me')
      goByRole(me?.role)
    } catch {
      // token invalid, ignore
    }
    showEmbed.value = true
    embedSrc.value = `/api/home/proxy?path=${encodeURIComponent('/')}`
  }
})

function goByRole(role) {
  if (role === 'admin') location.hash = '#/admin'
  else if (role === 'user') location.hash = '#/user'
}

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    const res = await apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email: email.value, password: password.value }),
    })
    setAuthToken(res.token)
    showEmbed.value = true
    embedSrc.value = `/api/home/proxy?path=${encodeURIComponent('/')}`
    goByRole(res?.user?.role)
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script> 