<template>
  <div :class="['container', { 'container--auth': isAuthPage }]">
    <header :class="['header', { 'header--fluid': hasFluidHeader }]">
      <nav class="nav">
        <router-link class="brand" to="/">
          <img src="/logo.png" alt="logo" class="logo" />
          <div class="brand-text">日本の通販商品・ オ-クションの入れサポ-ト・賺入サポ-トサ-ビス</div>
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
    <main :class="['main', { 'main--auth': isAuthPage }]">
      <router-view />
    </main>
    <footer class="footer">© 2025 日本の通販商品・ オ-クションの入れサポ-ト・賺入サポ-トサ-ビス</footer>
    <BarrageOverlay />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { getAuthToken, setAuthToken, setUserRole } from './api'
import BarrageOverlay from './components/BarrageOverlay.vue'

const token = ref(getAuthToken())
const userRole = ref('')
const isLoggedIn = computed(() => !!token.value)
const route = useRoute()
const AUTH_ROUTES = new Set(['/login', '/register'])
const FLUID_HEADER_ROUTES = new Set(['/login', '/register', '/'])
const isAuthPage = computed(() => AUTH_ROUTES.has(route.path))
const hasFluidHeader = computed(() => FLUID_HEADER_ROUTES.has(route.path))

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
.container { max-width: 1200px; margin: 0 auto; padding: 16px 24px; min-height: 100vh; display: flex; flex-direction: column; }
.container--auth { max-width: none; padding: 0; }
.header { padding: 20px 0; border-bottom: 1px solid var(--border); }
.header--fluid {
  width: 100vw;
  margin-left: calc(50% - 50vw);
  margin-right: calc(50% - 50vw);
  padding-left: max(24px, calc((100vw - 1200px) / 2));
  padding-right: max(24px, calc((100vw - 1200px) / 2));
  background: #f8fbff;
  box-sizing: border-box;
}
.nav { display: flex; flex-wrap: wrap; align-items: center; gap: 12px 32px; }
.brand { display:flex; align-items:center; gap: 12px; font-weight: 700; color: var(--text); text-decoration: none; flex: 1 1 360px; }
.logo { width: 32px; height: 32px; object-fit: contain; }
.brand-text { font-size: 16px; line-height: 1.4; letter-spacing: 0.02em; }
.links { display: flex; flex: 1 1 auto; flex-wrap: wrap; gap: 16px 24px; justify-content: flex-end; }
.link { color: var(--text); text-decoration: none; opacity: 0.9; font-size: 15px; }
.link:hover { text-decoration: underline; opacity: 1; }
.main { padding: 24px 0; flex: 1; }
.main--auth { padding: 0; display: flex; flex: 1; justify-content: center; align-items: center; }
.main--auth > * { width: 100%; }
.container--auth .header { padding: 20px 24px; }
.container--auth .main { flex: 1; }
.container--auth .footer { padding: 16px 24px; }
.footer { color: var(--muted); font-size: 12px; padding-top: 16px; border-top: 1px solid var(--border); }
@media (max-width: 600px) {
  .container { padding: 12px 16px; }
  .brand { flex: 1 1 100%; }
  .links { width: 100%; justify-content: flex-start; }
}
@media (max-width: 600px) {
  .container--auth .header { padding: 20px 16px; }
  .container--auth .footer { padding: 16px; }
  .header--fluid { padding-left: 16px; padding-right: 16px; }
}
</style>