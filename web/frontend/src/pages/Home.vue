<template>
  <div class="mercari-home">
    <!-- Header Navigation -->
    <header class="header">
      <div class="nav-container">
        <div class="logo">
          <svg viewBox="0 0 182 49" width="120" height="32" xmlns="http://www.w3.org/2000/svg">
            <title>メルカリ</title>
            <g>
              <path fill="#ff0211" fill-rule="evenodd" d="M42.65,14.15l0,21a3.55,3.55,0,0,1-2,3.17l-17.8,8.59a3.54,3.54,0,0,1-3.08,0L9.25,41.82a3.55,3.55,0,0,1-2-3.17l0-21a3.55,3.55,0,0,1,2-3.17L27.05,8.59a3.54,3.54,0,0,1,3.08,0L47.93,11a3.55,3.55,0,0,1,2,3.17Z"/>
              <text x="60" y="25" font-family="Arial, sans-serif" font-size="18" font-weight="bold" fill="#ff0211">メルカリ</text>
            </g>
          </svg>
        </div>
        <nav class="nav-links">
          <a href="#/" class="nav-link">ホーム</a>
          <a v-if="isAdmin" href="#/admin" class="nav-link">管理</a>
          <a v-if="isLoggedIn" href="#/user" class="nav-link">マイページ</a>
          <a v-if="!isLoggedIn" href="#/login" class="nav-link">ログイン</a>
          <a v-if="!isLoggedIn" href="#/register" class="nav-link">新規登録</a>
          <button v-if="isLoggedIn" class="nav-link nav-button" @click="logout">ログアウト</button>
        </nav>
      </div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Hero Section -->
      <section class="hero">
        <div class="hero-content">
          <h1 class="hero-title">日本最大のフリマサービス</h1>
          <p class="hero-subtitle">誰でも安心して簡単に売り買いが楽しめる</p>
          
          <!-- Search Bar -->
          <div class="search-container">
            <div class="search-box">
              <input type="text" placeholder="何をお探しですか？" class="search-input" />
              <button class="search-btn">検索</button>
            </div>
          </div>
        </div>
      </section>

      <!-- Categories Section -->
      <section class="categories">
        <h2 class="section-title">カテゴリから探す</h2>
        <div class="category-grid">
          <div class="category-item" v-for="category in categories" :key="category.id">
            <div class="category-icon">
              <img :src="category.icon" :alt="category.name" />
            </div>
            <span class="category-name">{{ category.name }}</span>
          </div>
        </div>
      </section>

      <!-- Featured Products -->
      <section class="featured-products">
        <h2 class="section-title">おすすめ商品</h2>
        <div class="product-grid">
          <a
            class="product-card"
            v-for="product in featuredProducts"
            :key="product.id"
            :href="product.href"
            target="_blank"
            rel="noopener noreferrer"
          >
            <div class="product-image">
              <img :src="product.image" :alt="product.imageAlt" loading="lazy" />
            </div>
            <div class="product-info">
              <h3 class="product-name">{{ product.title }}</h3>
              <p class="product-price">{{ product.priceText }}</p>
              <div class="product-meta">
                <span class="product-status" v-if="product.statusLabel">{{ product.statusLabel }}</span>
                <span class="product-discount" v-if="product.discount">{{ product.discount }}</span>
              </div>
            </div>
          </a>
        </div>
      </section>

      <!-- Banner Section -->
      <section class="banner">
        <div class="banner-content">
          <h3>スマホでかんたん出品</h3>
          <p>写真を撮るだけ！かんたん出品でお得に売買</p>
          <button class="cta-button">今すぐ始める</button>
        </div>
      </section>
    </main>

    <!-- Footer -->
    <footer class="footer">
      <div class="footer-content">
        <p>&copy; 2024 メルカリ - 日本最大のフリマサービス</p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import mercariItems from '@/data/mercariItems.json'
import { getAuthToken, setAuthToken } from '@/api'

// 模拟分类数据
const categories = ref([
  { id: 1, name: 'レディース', icon: 'https://placehold.co/60x60/FF0211/FFFFFF?text=L' },
  { id: 2, name: 'メンズ', icon: 'https://placehold.co/60x60/FF0211/FFFFFF?text=M' },
  { id: 3, name: 'ベビー・キッズ', icon: 'https://placehold.co/60x60/FF0211/FFFFFF?text=BK' },
  { id: 4, name: 'インテリア・住まい', icon: 'https://placehold.co/60x60/FF0211/FFFFFF?text=IS' },
  { id: 5, name: 'キッチン・食器', icon: 'https://placehold.co/60x60/FF0211/FFFFFF?text=K' },
  { id: 6, name: '本・音楽・ゲーム', icon: 'https://placehold.co/60x60/FF0211/FFFFFF?text=BG' },
  { id: 7, name: 'おもちゃ・ホビー', icon: 'https://placehold.co/60x60/FF0211/FFFFFF?text=H' },
  { id: 8, name: 'コスメ・香水・美容', icon: 'https://placehold.co/60x60/FF0211/FFFFFF?text=C' }
])

const featuredProducts = ref(
  mercariItems.map((item) => ({
    ...item,
    statusLabel: item.status === 'on_sale' ? '販売中' : item.status
  }))
)

const isLoggedIn = ref(Boolean(getAuthToken()))
const userRole = ref('')
const isAdmin = computed(() => isLoggedIn.value && userRole.value === 'admin')

function updateLoginState() {
  isLoggedIn.value = Boolean(getAuthToken())
  try {
    userRole.value = localStorage.getItem('userRole') || ''
  } catch {
    userRole.value = ''
  }
}

function handleStorage(event) {
  if (!event.key || event.key === 'token' || event.key === 'userRole') {
    updateLoginState()
  }
}

function logout() {
  setAuthToken('')
  try {
    localStorage.removeItem('userRole')
    localStorage.removeItem('redirectPath')
    localStorage.removeItem('authPrompt')
  } catch {}
  updateLoginState()
  location.hash = '#/login'
}

onMounted(() => {
  updateLoginState()
  window.addEventListener('storage', handleStorage)
})

onBeforeUnmount(() => {
  window.removeEventListener('storage', handleStorage)
})
</script>

<style scoped>
.mercari-home {
  min-height: 100vh;
  background: #f5f5f5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans JP', 'Hiragino Kaku Gothic ProN', 'Yu Gothic', 'Meiryo', sans-serif;
}

/* Header Styles */
.header {
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 64px;
}

.logo {
  display: flex;
  align-items: center;
}

.nav-links {
  display: flex;
  gap: 24px;
}

.nav-link {
  color: #333;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s;
}

.nav-link:hover {
  color: #ff0211;
}

.nav-button {
  background: transparent;
  border: none;
  padding: 0;
  font: inherit;
  cursor: pointer;
}

/* Main Content */
.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

/* Hero Section */
.hero {
  background: linear-gradient(135deg, #ff0211 0%, #ff4d6d 100%);
  color: white;
  padding: 60px 0;
  text-align: center;
  margin-bottom: 40px;
  border-radius: 12px;
  margin-top: 20px;
}

.hero-title {
  font-size: 2.5rem;
  font-weight: bold;
  margin-bottom: 16px;
}

.hero-subtitle {
  font-size: 1.2rem;
  margin-bottom: 32px;
  opacity: 0.9;
}

.search-container {
  max-width: 600px;
  margin: 0 auto;
}

.search-box {
  display: flex;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.search-input {
  flex: 1;
  padding: 16px 20px;
  border: none;
  font-size: 16px;
  color: #333;
}

.search-input:focus {
  outline: none;
}

.search-btn {
  background: #ff0211;
  color: white;
  border: none;
  padding: 16px 32px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}

.search-btn:hover {
  background: #d4000f;
}

/* Categories Section */
.categories {
  margin-bottom: 60px;
}

.section-title {
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 24px;
  color: #333;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 20px;
}

.category-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.2s;
  cursor: pointer;
}

.category-item:hover {
  transform: translateY(-2px);
}

.category-icon {
  width: 60px;
  height: 60px;
  margin-bottom: 12px;
}

.category-icon img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
}

.category-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  text-align: center;
}

/* Featured Products */
.featured-products {
  margin-bottom: 60px;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.product-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: transform 0.2s;
  cursor: pointer;
}

.product-card:hover {
  transform: translateY(-4px);
}

.product-image {
  width: 100%;
  height: 200px;
  overflow: hidden;
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.product-info {
  padding: 16px;
}

.product-name {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-price {
  font-size: 18px;
  font-weight: bold;
  color: #ff0211;
  margin-bottom: 8px;
}

.product-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #666;
}

/* Banner Section */
.banner {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px;
  border-radius: 12px;
  text-align: center;
  margin-bottom: 40px;
}

.banner-content h3 {
  font-size: 1.8rem;
  font-weight: bold;
  margin-bottom: 12px;
}

.banner-content p {
  font-size: 1.1rem;
  margin-bottom: 24px;
  opacity: 0.9;
}

.cta-button {
  background: white;
  color: #667eea;
  border: none;
  padding: 16px 32px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.cta-button:hover {
  transform: translateY(-2px);
}

/* Footer */
.footer {
  background: #333;
  color: white;
  padding: 40px 0;
  text-align: center;
  margin-top: 60px;
}

.footer-content p {
  margin: 0;
  opacity: 0.8;
}

/* Responsive Design */
@media (max-width: 768px) {
  .nav-container {
    padding: 0 16px;
    height: 56px;
  }
  
  .nav-links {
    gap: 16px;
  }
  
  .nav-link {
    font-size: 14px;
  }
  
  .hero {
    padding: 40px 20px;
  }
  
  .hero-title {
    font-size: 2rem;
  }
  
  .hero-subtitle {
    font-size: 1rem;
  }
  
  .search-box {
    flex-direction: column;
  }
  
  .search-btn {
    border-radius: 0 0 8px 8px;
  }
  
  .category-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }
  
  .category-item {
    padding: 12px;
  }
  
  .category-icon {
    width: 40px;
    height: 40px;
  }
  
  .category-name {
    font-size: 12px;
  }
  
  .product-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .banner {
    padding: 30px 20px;
  }
  
  .banner-content h3 {
    font-size: 1.5rem;
  }
}
</style> 