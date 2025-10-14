<template>
  <div class="mercari-home">
    <main class="main-content">
      <section class="hero">
        <div class="hero-content">
          <h1 class="hero-title">日本最大のフリマサービス</h1>
          <p class="hero-subtitle">誰でも安心して簡単に売り買いが楽しめる</p>
          <div class="search-container">
            <form class="search-box" @submit.prevent="searchMercari">
              <input
                type="search"
                placeholder="キーワードを入力"
                class="search-input"
                v-model="searchQuery"
                ref="searchInput"
              />
              <button class="search-btn" type="submit">
                検索
              </button>
            </form>
          </div>
          <p v-if="searchError" class="error">{{ searchError }}</p>
        </div>
      </section>

      <section class="featured-products">
        <div class="section-title-row">
          <h2 class="section-title">最新の人気商品</h2>
          <div class="filter-controls">
            <div class="filter-checkboxes">
              <label
                v-for="filter in FILTERS"
                :key="filter.key"
                class="filter-checkbox"
              >
                <input
                  type="checkbox"
                  :value="filter.key"
                  :checked="isFilterSelected(filter.key)"
                  @change="toggleFilter(filter.key)"
                />
                <span>{{ filter.label }}</span>
              </label>
            </div>
            <button class="section-action" type="button" @click="refreshItems" :disabled="isLoading">
              {{ isLoading ? '読み込み中...' : '更新' }}
            </button>
          </div>
        </div>
        <div class="product-grid" v-if="items.length">
          <article
            class="product-card"
            v-for="product in items"
            :key="product.id"
            @click="openProduct(product)"
          >
            <div class="product-image">
              <img :src="product.image" :alt="product.imageAlt" loading="lazy" />
            </div>
            <div class="product-info">
              <h3 class="product-name">{{ product.title }}</h3>
              <p class="product-price">{{ product.priceText }}</p>
              <div class="product-meta">
                <span class="product-status" v-if="product.statusLabel">{{ product.statusLabel }}</span>
                <span class="product-location" v-if="product.location">{{ product.location }}</span>
              </div>
            </div>
          </article>
        </div>
        <p v-else class="empty-message">商品を読み込めませんでした。</p>
      </section>
    </main>

    <footer class="footer">
      <div class="footer-content">
        <p>&copy; 2025 日本の通販商品・ オ-クションの入れサポ-ト・賺入サポ-トサ-ビス</p>
      </div>
    </footer>

    <transition name="modal">
      <div v-if="selectedProduct" class="modal" @click.self="closeProductModal">
        <div class="modal-content">
          <button class="modal-close" type="button" @click="closeProductModal">×</button>
          <div class="modal-body">
            <div class="modal-image">
              <img :src="selectedProduct.image" :alt="selectedProduct.imageAlt" />
            </div>
            <div class="modal-info">
              <h3>{{ selectedProduct.title }}</h3>
              <p class="modal-price">{{ selectedProduct.priceText }}</p>
              <ul class="modal-meta">
                <li v-if="selectedProduct.location">発送地: {{ selectedProduct.location }}</li>
                <li v-if="selectedProduct.statusLabel">状態: {{ selectedProduct.statusLabel }}</li>
              </ul>
              <a :href="selectedProduct.href" class="modal-action" target="_blank" rel="noopener">Mercariで見る</a>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import fallbackItems from '@/data/mercari_items.json'

const DISPLAY_COUNT = 21
const FILTERS = [
  { key: 'all', label: '全て', brand: null, limit: DISPLAY_COUNT },
  { key: 'chanel', label: 'CHANEL', brand: 'Chanel', limit: 21 },
  { key: 'louis-vuitton', label: 'Louis Vuitton', brand: 'Louis Vuitton', limit: 21 },
  { key: 'hermes', label: 'Hermès', brand: 'Hermes', limit: 21 },
  { key: 'gucci', label: 'Gucci', brand: 'Gucci', limit: 21 },
]

const searchQuery = ref('')
const searchError = ref('')
const isLoading = ref(false)
const items = ref([])
const selectedProduct = ref(null)
const searchInput = ref(null)
const activeFilters = ref(['all'])
const filterCache = ref({})
const searchKey = ref(null)
const keyLoading = ref(false)

function isFilterSelected(key) {
  return activeFilters.value.includes(key)
}

function toggleFilter(key) {
  if (key === 'all') {
    activeFilters.value = ['all']
    refreshItems()
    return
  }

  const next = new Set(activeFilters.value)
  if (next.has(key)) {
    next.delete(key)
  } else {
    next.add(key)
    next.delete('all')
  }

  if (!next.size) {
    next.add('all')
  }

  activeFilters.value = Array.from(next)
  refreshItems()
}

function pickRandomItems(list, count) {
  if (!Array.isArray(list) || list.length <= count) {
    return list
  }
  const shuffled = [...list]
  for (let i = shuffled.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
  }
  return shuffled.slice(0, count)
}

async function refreshItems() {
  isLoading.value = true
  searchError.value = ''

  try {
    const datasets = await Promise.all(
      activeFilters.value.map(async (key) => {
        const filter = FILTERS.find((f) => f.key === key)
        if (!filter) return []

        if (filter.key !== 'all' && filterCache.value[filter.key]) {
          return filterCache.value[filter.key]
        }

        const params = new URLSearchParams()
        if (filter.brand) params.set('brand', filter.brand)
        params.set('limit', String(filter.limit || DISPLAY_COUNT))

        try {
          const resp = await fetch(`/api/home/items?${params.toString()}`)
          if (!resp.ok) {
            throw new Error(`${filter.label} の商品取得に失敗しました`)
          }
          const data = await resp.json()
          const transformed = transformItems(data.items || [])

          if (filter.key !== 'all') {
            filterCache.value[filter.key] = transformed
          }
          return transformed
        } catch (err) {
          console.warn(`[Filter:${filter.label}]`, err)
          return []
        }
      })
    )

    const merged = datasets.flat().filter(Boolean)

    items.value = pickRandomItems(dedupeItems(merged), DISPLAY_COUNT)

    if (!items.value.length) {
      const fallbackTransformed = dedupeItems(transformItems(fallbackItems))
      items.value = pickRandomItems(fallbackTransformed, DISPLAY_COUNT)
    }
  } catch (err) {
    console.error('[Refresh] Error:', err)
    const fallbackTransformed = dedupeItems(transformItems(fallbackItems))
    items.value = pickRandomItems(fallbackTransformed, DISPLAY_COUNT)
  } finally {
    isLoading.value = false
  }
}

function searchMercari() {
  ;(async () => {
    const keyword = searchQuery.value.trim()
    if (!keyword) {
      searchError.value = 'キーワードを入力してください。'
      return
    }

    if (!window.crypto?.subtle) {
      searchError.value = 'このブラウザは検索暗号化に対応していません。'
      return
    }

    try {
      isLoading.value = true
      searchError.value = ''

      const key = await ensureSearchKey()
      if (!key) {
        throw new Error('暗号鍵を取得できませんでした。')
      }

      const payload = {
        keyword,
        ts: Date.now(),
        nonce: crypto.randomUUID(),
      }
      const encoder = new TextEncoder()
      const encoded = encoder.encode(JSON.stringify(payload))
      const encrypted = await crypto.subtle.encrypt({ name: 'RSA-OAEP' }, key, encoded)
      const encryptedBytes = new Uint8Array(encrypted)
      const t_s = arrayBufferToBase64Url(encryptedBytes)

      const params = new URLSearchParams({ t_s })
      const resp = await fetch(`/api/home/search?${params.toString()}`)
      if (!resp.ok) {
        const errBody = await resp.json().catch(() => ({}))
        const msg = errBody.error || '検索に失敗しました。'
        throw new Error(msg)
      }
      const data = await resp.json()
      const transformed = transformItems(data.items || [])
      items.value = transformed.length ? transformed : []
      if (!transformed.length) {
        searchError.value = '該当する商品が見つかりませんでした。'
      }
    } catch (error) {
      console.error('[Search] Failed:', error)
      searchError.value = error?.message || '検索に失敗しました。'
    } finally {
      isLoading.value = false
    }
  })()
}

function openProduct(product) {
  selectedProduct.value = product
}

function closeProductModal() {
  selectedProduct.value = null
}

function transformItems(rawItems = []) {
  return rawItems.map((item) => {
    const image = item.image?.src || item.image
    const href = item.link || item.href || ''
    
    // 构建完整的 Mercari 商品 URL
    let absoluteHref = ''
    if (href.startsWith('http')) {
      // 已经是完整 URL
      absoluteHref = href
    } else if (href.startsWith('/item/')) {
      // 相对路径，构建完整的 Mercari URL
      absoluteHref = `https://jp.mercari.com${href}`
    } else if (item.id) {
      // 使用商品 ID 构建 URL
      absoluteHref = `https://jp.mercari.com/item/${item.id}`
    } else {
      absoluteHref = 'https://jp.mercari.com'
    }
    
    return {
      id: item.id || item.m_item_id || item.title,
      title: item.title || item.image?.title || '商品',
      priceText: item.priceText || item.price || (item.price && !String(item.price).includes('円') ? `${item.price}円` : ''),
      statusLabel: item.statusLabel || item.status,
      location: item.location || item.shippingFrom || '',
      href: absoluteHref,
      image,
      imageAlt: item.image?.alt || item.image?.title || item.title || '商品',
    }
  })
}

function dedupeItems(rawItems = []) {
  const seen = new Map()
  rawItems.forEach((item) => {
    if (!item) return
    const key = item.id || item.href || item.title
    if (!key) return
    if (!seen.has(key)) {
      seen.set(key, item)
    }
  })
  return Array.from(seen.values())
}

onMounted(() => {
  refreshItems()
  if (searchInput.value) searchInput.value.focus()
})

async function ensureSearchKey() {
  if (searchKey.value || keyLoading.value) {
    return searchKey.value
  }
  try {
    keyLoading.value = true
    const resp = await fetch('/api/login/pubkey')
    if (!resp.ok) {
      throw new Error('公開鍵の取得に失敗しました。')
    }
    const body = await resp.json()
    const pem = body?.pem
    if (!pem) {
      throw new Error('公開鍵が無効です。')
    }
    const binaryDer = pemToArrayBuffer(pem)
    const imported = await crypto.subtle.importKey(
      'spki',
      binaryDer,
      {
        name: 'RSA-OAEP',
        hash: 'SHA-256',
      },
      false,
      ['encrypt']
    )
    searchKey.value = imported
    return imported
  } catch (error) {
    console.error('[Search] Failed to ensure key:', error)
    searchError.value = error?.message || '検索暗号化の初期化に失敗しました。'
    return null
  } finally {
    keyLoading.value = false
  }
}

function pemToArrayBuffer(pem) {
  const base64 = pem
    .replace('-----BEGIN PUBLIC KEY-----', '')
    .replace('-----END PUBLIC KEY-----', '')
    .replace(/\s+/g, '')
  const raw = atob(base64)
  const buffer = new ArrayBuffer(raw.length)
  const view = new Uint8Array(buffer)
  for (let i = 0; i < raw.length; i += 1) {
    view[i] = raw.charCodeAt(i)
  }
  return buffer
}

function arrayBufferToBase64Url(buffer) {
  let binary = ''
  const bytes = new Uint8Array(buffer)
  const len = bytes.byteLength
  for (let i = 0; i < len; i += 1) {
    binary += String.fromCharCode(bytes[i])
  }
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '')
}
</script>

<style scoped>
.mercari-home {
  min-height: 100vh;
  background: var(--bg);
}

.hero {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-hover) 100%);
  color: #fff;
  padding: 60px 0;
  text-align: center;
  margin-bottom: 40px;
  border-radius: 12px;
  margin-top: 20px;
}

.search-box {
  display: flex;
  background: var(--card);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.1);
}

.search-input {
  flex: 1;
  padding: 16px 20px;
  border: none;
  font-size: 16px;
  color: var(--text);
}

.search-btn {
  background: var(--primary);
  color: #fff;
  border: none;
  padding: 16px 32px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}

.section-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.filter-checkboxes {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.filter-checkbox {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid rgba(233, 84, 32, 0.26);
  color: var(--text);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
  background: rgba(233, 84, 32, 0.05);
}

.filter-checkbox input {
  accent-color: var(--primary);
}

.filter-checkbox:hover,
.filter-checkbox input:checked + span {
  border-color: var(--primary);
  background: rgba(233, 84, 32, 0.1);
}

@media (max-width: 640px) {
  .section-title-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .filter-controls {
    width: 100%;
    justify-content: flex-start;
  }

  .filter-checkboxes {
    width: 100%;
  }
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 24px;
}

.product-card {
  background: var(--card);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.1);
  cursor: pointer;
}

.product-price {
  color: var(--primary);
  font-weight: 700;
}

.product-location {
  color: var(--muted);
}

.footer {
  background: var(--card);
  color: var(--muted);
  padding: 40px 0;
  text-align: center;
  border-top: 1px solid var(--border);
  margin-top: 60px;
}

.modal {
  position: fixed;
  inset: 0;
  background: rgba(31, 35, 40, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 16px;
  z-index: 130;
}

.modal-content {
  width: min(920px, 100%);
  background: var(--card);
  border-radius: 18px;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-close {
  position: absolute;
  top: 12px;
  right: 16px;
  border: none;
  background: transparent;
  font-size: 1.5rem;
  cursor: pointer;
  color: var(--muted);
}

.modal-action {
  border: none;
  background: var(--primary);
  color: #fff;
  padding: 12px 18px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  justify-content: center;
  align-items: center;
  text-decoration: none;
}

.error {
  color: #d93025;
  margin-top: 12px;
  font-weight: 500;
  text-align: center;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
}

.hero-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 16px;
}

.hero-subtitle {
  font-size: 1.25rem;
  margin-bottom: 32px;
  opacity: 0.95;
}

.search-container {
  max-width: 600px;
  margin: 0 auto;
}

.search-input:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(233, 84, 32, 0.1);
}

.search-btn:hover:not(:disabled) {
  background: var(--primary-hover);
}

.search-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.featured-products {
  margin-top: 40px;
  margin-bottom: 60px;
}

.products-layout {
  display: grid;
  grid-template-columns: 2fr minmax(300px, 1fr);
  gap: 32px;
  align-items: start;
}

.brand-sidebar {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.section-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 24px;
}

.section-action:hover:not(:disabled) {
  text-decoration: underline;
}

.section-action:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.product-image {
  width: 100%;
  aspect-ratio: 1;
  overflow: hidden;
  background: var(--bg);
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.product-card:hover .product-image img {
  transform: scale(1.05);
}

.product-info {
  padding: 16px;
}

.product-name {
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 8px;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}

.product-meta {
  display: flex;
  gap: 8px;
  font-size: 0.875rem;
  margin-top: 8px;
}

.product-status {
  color: var(--muted);
}

.empty-message {
  text-align: center;
  color: var(--muted);
  padding: 60px 20px;
  font-size: 1.125rem;
}

.brand-feature {
  background: var(--card);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(229, 231, 235, 0.7);
  box-shadow: 0 18px 32px -24px rgba(15, 23, 42, 0.18);
}

.brand-description {
  color: var(--muted);
  margin-bottom: 16px;
}

.brand {
  display: flex;
  align-items: center;
  text-decoration: none;
  color: var(--text);
  font-weight: 700;
  font-size: 1.125rem;
}

.logo {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.modal-body {
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 40px;
}

.modal-image {
  width: 100%;
  max-height: 400px;
  overflow: hidden;
  border-radius: 12px;
}

.modal-image img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.modal-info {
  display: flex;
  flex-direction: column;
    gap: 16px;
  }
  
.modal-info h3 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text);
}

.modal-price {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--primary);
}

.modal-meta {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
    flex-direction: column;
  gap: 8px;
  color: var(--muted);
}

.modal-meta li {
  padding: 8px 0;
  border-bottom: 1px solid var(--border);
}

.modal-action:hover {
  background: var(--primary-hover);
}

.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

@media (min-width: 768px) {
  .modal-body {
    flex-direction: row;
  }
  
  .modal-image {
    flex: 0 0 50%;
  }
  
  .modal-info {
    flex: 1;
  }
}
</style> 