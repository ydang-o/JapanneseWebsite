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
import { ref, onMounted, computed } from 'vue'

const userRole = ref('')
const isLoggedIn = computed(() => !!(localStorage.getItem('token') || ''))

function logout() {
  try { localStorage.removeItem('token'); localStorage.removeItem('userRole') } catch {}
  userRole.value = ''
  location.hash = '#/login'
}

onMounted(() => {
  try {
    const cached = localStorage.getItem('userRole') || ''
    if (cached) userRole.value = cached
  } catch {}
})
</script>

<style scoped>
.container { max-width: 960px; margin: 0 auto; padding: 16px; }
.header { padding: 12px 0; }
.nav { display: flex; justify-content: space-between; align-items: center; }
.brand { display:flex; align-items:center; font-weight: 700; color: #222; text-decoration: none; }
.logo { width: 28px; height: 28px; object-fit: contain; }
.links { display: flex; gap: 12px; }
.link { color: #333; text-decoration: none; }
.link:hover { text-decoration: underline; }
.main { padding: 16px 0; }
.footer { color: #666; font-size: 12px; padding-top: 16px; border-top: 1px solid #eee; }
</style> 