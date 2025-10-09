<template>
  <div class="container">
    <header class="header">
      <nav class="nav">
        <router-link class="brand" to="/">
          <img src="/logo.png" alt="logo" class="logo" />
          <span style="margin-left:8px">代購サイト</span>
        </router-link>
        <div class="links">
          <router-link to="/" class="link">ホーム</router-link>
          <router-link to="/login" class="link">ログイン</router-link>
          <router-link to="/register" class="link">新規登録</router-link>
          <router-link to="/user" class="link">マイページ</router-link>
          <router-link v-if="userRole==='admin'" to="/admin" class="link">管理</router-link>
          <a v-if="isLoggedIn" class="link" href="#" @click.prevent="logout">ログアウト</a>
        </div>
      </nav>
    </header>
    <main class="main">
      <router-view />
    </main>
    <footer class="footer">© 2025 代購サイト</footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { getAuthToken, setAuthToken, setUserRole } from './api'

const token = ref(getAuthToken())
const userRole = ref('')
const isLoggedIn = computed(() => !!token.value)

function updateAuthState() {
  token.value = getAuthToken()
  try {
    userRole.value = localStorage.getItem('userRole') || ''
  } catch {
    userRole.value = ''
  }
}

function logout() {
  setAuthToken('')
  setUserRole('')
  updateAuthState()
  location.hash = '#/login'
}

onMounted(() => {
  updateAuthState()
  window.addEventListener('storage', updateAuthState)
  window.addEventListener('auth-state-changed', updateAuthState)
})

onBeforeUnmount(() => {
  window.removeEventListener('storage', updateAuthState)
  window.removeEventListener('auth-state-changed', updateAuthState)
})
</script>

<style scoped>
.container { max-width: 960px; margin: 0 auto; padding: 16px; }
.header { padding: 12px 0; }
.nav { display: flex; justify-content: space-between; align-items: center; }
.brand { display:flex; align-items:center; font-weight: 700; color: var(--text); text-decoration: none; }
.logo { width: 28px; height: 28px; object-fit: contain; }
.links { display: flex; gap: 12px; }
.link { color: var(--text); text-decoration: none; opacity: 0.9; }
.link:hover { text-decoration: underline; opacity: 1; }
.main { padding: 16px 0; }
.footer { color: var(--muted); font-size: 12px; padding-top: 16px; border-top: 1px solid var(--border); }
</style> 