<template>
  <div>
    <div class="login-banner"></div>
    <div class="login-wrap">
      <div class="login-card">
        <div class="login-title">ログイン</div>
        <p v-if="prompt==='login-required'" class="info">ログインが必要です。続行するにはログインしてください。</p>
        <p v-if="prompt==='admin-required'" class="info">管理者権限が必要です。管理者でログインしてください。</p>
        <form class="login-form" @submit.prevent="onSubmit">
          <div class="field">
            <label>電話番号/ユーザー名</label>
            <input v-model="identifier" type="tel" required @blur="formatPhone" />
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
import { ref, onMounted } from 'vue'
import { apiFetch, setAuthToken } from '../api'
import './login.css'

const identifier = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const prompt = ref('')
const redirectPath = ref('')

onMounted(() => {
  try {
    prompt.value = localStorage.getItem('authPrompt') || ''
    redirectPath.value = localStorage.getItem('redirectPath') || ''
    localStorage.removeItem('authPrompt')
  } catch {}
})

function normalizeJpPhone(raw) {
  if (!raw) return ''
  const digits = (raw + '').replace(/\D/g, '')
  if (digits.startsWith('81')) return '0' + digits.slice(2)
  if (digits.startsWith('0')) return digits
  return raw // allow username admin
}

function isLikelyPhone(raw) {
  const d = (raw + '').replace(/\D/g, '')
  if (d.startsWith('81')) return (('0' + d.slice(2)).length === 10 || ('0' + d.slice(2)).length === 11)
  if (d.startsWith('0')) return (d.length === 10 || d.length === 11)
  return false
}

function formatPhone() {
  if (isLikelyPhone(identifier.value)) {
    identifier.value = normalizeJpPhone(identifier.value)
  }
}

async function importRsaPublicKey(pem) {
  // Remove PEM header/footer
  const b64 = pem.replace(/-----BEGIN PUBLIC KEY-----/, '').replace(/-----END PUBLIC KEY-----/, '').replace(/\s+/g, '')
  const raw = Uint8Array.from(atob(b64), c => c.charCodeAt(0)).buffer
  return await window.crypto.subtle.importKey(
    'spki',
    raw,
    { name: 'RSA-OAEP', hash: 'SHA-256' },
    false,
    ['encrypt']
  )
}

async function rsaEncrypt(publicKey, dataBytes) {
  const cipher = await window.crypto.subtle.encrypt({ name: 'RSA-OAEP' }, publicKey, dataBytes)
  return btoa(String.fromCharCode(...new Uint8Array(cipher)))
}

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    // 1) fetch pubkey
    const pub = await apiFetch('/auth/pubkey')
    const key = await importRsaPublicKey(pub.pem)
    // 2) build plaintext
    const id = isLikelyPhone(identifier.value) ? normalizeJpPhone(identifier.value) : identifier.value
    const body = JSON.stringify({ phone: id, password: password.value, ts: Date.now() })
    const enc = await rsaEncrypt(key, new TextEncoder().encode(body))
    // 3) send encrypted payload
    const res = await apiFetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ enc }),
    })
    setAuthToken(res.token)
    try { localStorage.setItem('userRole', res?.user?.role || '') } catch {}
    setTimeout(() => { /* simple client-side TTL awareness */ }, res.ttlMs || 0)
    const back = redirectPath.value || '#/user'
    location.hash = back.startsWith('#') ? back : `#${back}`
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.info { color: #1f2328; background: #f3f4f6; border:1px solid var(--border); padding:8px 12px; border-radius:8px; margin-bottom:8px }
</style> 