<template>
  <div class="register-container">
    <div class="register-card">
      <div class="login-title">新規登録</div>
      <form class="login-form" @submit.prevent="onSubmit">
        <div class="field">
          <label>電話番号</label>
          <input v-model="phone" type="tel" required @blur="formatPhone" />
        </div>
        <div class="field">
          <label>表示名</label>
          <input v-model="displayName" type="text" />
        </div>
        <div class="field">
          <label>パスワード</label>
          <div class="password-field">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              required
            />
            <button
              type="button"
              class="toggle-password-btn"
              @click="togglePassword"
              :aria-label="showPassword ? 'パスワードを隠す' : 'パスワードを表示'"
            >
              <svg
                v-if="!showPassword"
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
              >
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
              <svg
                v-else
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
              >
                <path
                  d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"
                ></path>
                <line x1="1" y1="1" x2="23" y2="23"></line>
              </svg>
            </button>
          </div>
        </div>
        <button class="login-btn" :disabled="loading">登録</button>
        <p v-if="message" class="success">{{ message }}</p>
        <p v-if="error" class="error">{{ error }}</p>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { apiFetch, setUserRole } from '../api'
import './login.css'

const phone = ref('')
const displayName = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')
const message = ref('')
const showPassword = ref(false)

function togglePassword() {
  showPassword.value = !showPassword.value
}

function normalizeJpPhone(raw) {
  if (!raw) return ''
  const digits = (raw + '').replace(/\D/g, '')
  if (digits.startsWith('81')) return '0' + digits.slice(2)
  if (digits.startsWith('0')) return digits
  return digits
}

function isValidJpPhone(raw) {
  const d = normalizeJpPhone(raw)
  return d.length === 10 || d.length === 11
}

function formatPhone() {
  const d = normalizeJpPhone(phone.value)
  phone.value = d
}

async function onSubmit() {
  error.value = ''
  message.value = ''
  loading.value = true
  try {
    if (!isValidJpPhone(phone.value)) {
      throw new Error('日本の電話番号の形式が正しくありません')
    }
    const res = await apiFetch('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ phone: normalizeJpPhone(phone.value), password: password.value, displayName: displayName.value }),
    })
    message.value = res.message || '登録受付：審査中です'
    if (res?.user?.role) {
      setUserRole(res.user.role)
    }
    showPassword.value = false
    window.dispatchEvent(new CustomEvent('app-barrage', {
      detail: {
        text: '登録手続きが完了しました。審査結果をお待ちください。',
        type: 'success',
        duration: 5000,
      },
    }))
  } catch (e) {
    const msg = e.message || ''
    if (msg.includes('審査中')) {
      // 交互作用由前端展示为提示
      message.value = 'この電話番号は現在審査中です'
    } else {
      error.value = msg
    }
    window.dispatchEvent(new CustomEvent('app-barrage', {
      detail: {
        text: msg || '登録に失敗しました。',
        type: msg ? 'warning' : 'error',
      },
    }))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.password-field {
  display: flex;
  align-items: center;
  gap: 10px;
}

.password-field input {
  flex: 1;
  height: 44px;
  padding: 0 14px;
  border-radius: 10px;
  border: 1px solid #d1d5db;
  background: #fff;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.password-field input:focus {
  border-color: #2563eb;
  box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.12);
  outline: none;
}

.toggle-password-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 10px;
  border: 1px solid #d1d5db;
  background: #f3f4f6;
  color: #4b5563;
  cursor: pointer;
  transition: all 0.2s ease;
}

.toggle-password-btn:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.toggle-password-btn svg {
  stroke-width: 2;
}

.register-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7ff 0%, #edf2ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
}

.register-card {
  width: 100%;
  max-width: 520px;
  padding: 48px 56px;
  background: #ffffff;
  border-radius: 28px;
  box-shadow: 0 35px 60px -25px rgba(15, 23, 42, 0.35);
  border: 1px solid rgba(148, 163, 184, 0.2);
}
</style> 