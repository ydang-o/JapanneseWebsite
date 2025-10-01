<template>
  <div class="card">
    <h2>ホーム</h2>
    <p>Mercari の商品を参照できます。</p>
    <div class="row">
      <input v-model="path" placeholder="/search?keyword=..." />
      <button @click="go" :disabled="loading">表示</button>
    </div>
    <p class="muted">例: /search?keyword=iphone</p>
    <iframe v-if="src" :src="src" style="width:100%; height:70vh; border:1px solid #eee; border-radius:8px;"></iframe>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const path = ref('/search?keyword=iphone')
const src = ref('')
const loading = ref(false)

function go() {
  loading.value = true
  src.value = `/api/home/proxy?path=${encodeURIComponent(path.value)}`
  setTimeout(() => { loading.value = false }, 300)
}

</script>

<style scoped>
.muted { color: #777; font-size: 12px; }
</style> 