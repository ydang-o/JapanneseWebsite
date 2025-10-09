<template>
  <div class="login-container">
    <div class="login-content">
      <div class="login-header">
        <h1 class="login-title">ログイン</h1>
        <router-link to="/register" class="register-link">会員登録はこちら</router-link>
      </div>

      <p v-if="prompt==='login-required'" class="info-message">ログインが必要です。続行するにはログインしてください。</p>
      <p v-if="prompt==='admin-required'" class="info-message">管理者権限が必要です。管理者でログインしてください。</p>

      <form class="login-form" @submit.prevent="onSubmit">
        <div class="form-group">
          <label for="identifier" class="form-label">電話番号（メールアドレスも可）</label>
          <input 
            id="identifier"
            v-model="identifier" 
            type="text" 
            class="form-input"
            placeholder="09000012345"
            required 
            @blur="formatPhone" 
          />
        </div>

        <div class="form-group">
          <label for="password" class="form-label">パスワード</label>
          <div class="password-wrapper">
            <input 
              id="password"
              v-model="password" 
              :type="showPassword ? 'text' : 'password'" 
              class="form-input"
              required 
            />
            <button 
              type="button" 
              class="toggle-password" 
              @click="showPassword = !showPassword"
              :aria-label="showPassword ? 'パスワードを隠す' : 'パスワードを表示'"
            >
              <svg v-if="!showPassword" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
              <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                <line x1="1" y1="1" x2="23" y2="23"></line>
              </svg>
            </button>
          </div>
        </div>

        <button class="submit-btn" type="submit" :disabled="loading">
          {{ loading ? '処理中...' : 'ログイン' }}
        </button>

        <p v-if="error" class="error-message">{{ error }}</p>
      </form>

      <div class="login-footer">
        <p class="terms-text">
          <router-link to="/terms" class="terms-link">利用規約</router-link>および<router-link to="/privacy" class="terms-link">プライバシーポリシー</router-link>に同意の上、ログインへお進みください。<br>
          このサイトはreCAPTCHAで保護されており、Googleの<router-link to="/privacy" class="terms-link">プライバシーポリシー</router-link>と<router-link to="/terms" class="terms-link">利用規約</router-link>が適用されます。
        </p>
        <router-link to="/forgot-password" class="forgot-link">
          ログインできない方はこちら
          <span class="arrow">›</span>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiFetch, setAuthToken, setUserRole } from '../api'
import './login.css'

const identifier = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const prompt = ref('')
const redirectPath = ref('')
const showPassword = ref(false)

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
  if (!pem || typeof pem !== 'string') {
    throw new Error('公開鍵を取得できませんでした。再度お試しください。')
  }
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
    const pem = pub?.pem
    const key = await importRsaPublicKey(pem)
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
    setUserRole(res?.user?.role || '')
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
.login-container {
  min-height: 100vh;
  background: #2c2c2c;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-content {
  width: 100%;
  max-width: 720px;
  padding: 40px;
}

.login-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.login-title {
  font-size: 2rem;
  font-weight: 700;
  color: #ffffff;
  margin: 0;
}

.register-link {
  color: #4a9eff;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
}

.register-link:hover {
  text-decoration: underline;
}

.info-message {
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid rgba(255, 193, 7, 0.3);
  color: #ffc107;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 24px;
  font-size: 0.875rem;
}

.login-form {
  margin-bottom: 32px;
}

.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  color: #ffffff;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 14px 16px;
  background: #3a3a3a;
  border: 1px solid #4a4a4a;
  border-radius: 8px;
  color: #ffffff;
  font-size: 1rem;
  transition: all 0.2s;
  box-sizing: border-box;
}

.form-input::placeholder {
  color: #888;
}

.form-input:focus {
  outline: none;
  border-color: #4a9eff;
  background: #404040;
}

.password-wrapper {
  position: relative;
}

.password-wrapper .form-input {
  padding-right: 48px;
}

.toggle-password {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
}

.toggle-password:hover {
  color: #ffffff;
}

.toggle-password svg {
  stroke-width: 2;
}

.submit-btn {
  width: 100%;
  padding: 16px;
  background: #e65550;
  border: none;
  border-radius: 8px;
  color: #ffffff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
  margin-top: 8px;
}

.submit-btn:hover:not(:disabled) {
  background: #d44a45;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  color: #ff6b6b;
  background: rgba(255, 107, 107, 0.1);
  border: 1px solid rgba(255, 107, 107, 0.3);
  padding: 12px 16px;
  border-radius: 8px;
  margin-top: 16px;
  font-size: 0.875rem;
}

.login-footer {
  border-top: 1px solid #4a4a4a;
  padding-top: 24px;
}

.terms-text {
  color: #999;
  font-size: 0.75rem;
  line-height: 1.6;
  margin-bottom: 20px;
}

.terms-link {
  color: #4a9eff;
  text-decoration: none;
}

.terms-link:hover {
  text-decoration: underline;
}

.forgot-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #4a9eff;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
}

.forgot-link:hover {
  text-decoration: underline;
}

.forgot-link .arrow {
  font-size: 1.25rem;
  transition: transform 0.2s;
}

.forgot-link:hover .arrow {
  transform: translateX(4px);
}

@media (max-width: 768px) {
  .login-content {
    padding: 24px;
  }

  .login-title {
    font-size: 1.5rem;
  }

  .login-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style> 