<template>
  <div>
    <div class="login-banner"></div>
    <div class="login-wrap">
      <div class="login-card">
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
            <input v-model="password" type="password" required />
          </div>
          <button class="login-btn" :disabled="loading">登録</button>
          <p v-if="message" class="success">{{ message }}</p>
          <p v-if="error" class="error">{{ error }}</p>
        </form>
      </div>
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
  } catch (e) {
    const msg = e.message || ''
    if (msg.includes('審査中')) {
      // 交互作用由前端展示为提示
      message.value = 'この電話番号は現在審査中です'
    } else {
      error.value = msg
    }
  } finally {
    loading.value = false
  }
}
</script> 