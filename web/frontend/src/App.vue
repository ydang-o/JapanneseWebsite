<template>
  <div class="container">
    <header class="header">
      <nav class="nav">
        <router-link class="brand" to="/">代購サイト</router-link>
        <div class="links">
          <router-link to="/" class="link">ホーム</router-link>
          <router-link to="/login" class="link">ログイン</router-link>
          <router-link to="/register" class="link">新規登録</router-link>
          <router-link to="/user" class="link">マイページ</router-link>
          <router-link to="/admin" class="link">管理</router-link>
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
</script>

<style scoped>
.container { max-width: 960px; margin: 0 auto; padding: 16px; }
.header { padding: 12px 0; }
.nav { display: flex; justify-content: space-between; align-items: center; }
.brand { font-weight: 700; color: #222; text-decoration: none; }
.links { display: flex; gap: 12px; }
.link { color: #333; text-decoration: none; }
.link:hover { text-decoration: underline; }
.main { padding: 16px 0; }
.footer { color: #666; font-size: 12px; padding-top: 16px; border-top: 1px solid #eee; }
</style> 