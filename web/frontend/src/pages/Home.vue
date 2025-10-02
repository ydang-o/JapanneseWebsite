<template>
  <div class="card">
    <h2>ホーム</h2>
    <p>Mercari の商品を参照できます。</p>
    <iframe v-if="src" :src="src" style="width:100%; height:70vh; border:1px solid #eee; border-radius:8px;"></iframe>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const src = ref('')

onMounted(() => {
  src.value = `/api/home/proxy?path=${encodeURIComponent('/')}`
})
</script>

<style scoped>
.muted { color: #777; font-size: 12px; }
</style> 