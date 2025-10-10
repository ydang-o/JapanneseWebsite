<template>
  <div class="barrage-container" aria-live="polite" aria-atomic="true">
    <transition-group name="barrage" tag="div" class="barrage-inner">
      <div
        v-for="item in messages"
        :key="item.id"
        class="barrage-item"
        :class="item.type"
      >
        {{ item.text }}
      </div>
    </transition-group>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'

const messages = ref([])
let counter = 0

function pushMessage(detail) {
  if (!detail || !detail.text) return
  const id = `${Date.now()}-${counter++}`
  const type = detail.type || 'info'
  messages.value.push({ id, text: detail.text, type })
  setTimeout(() => {
    messages.value = messages.value.filter((msg) => msg.id !== id)
  }, detail.duration ?? 4000)
}

function handleEvent(evt) {
  pushMessage(evt.detail || {})
}

onMounted(() => {
  window.addEventListener('app-barrage', handleEvent)
})

onBeforeUnmount(() => {
  window.removeEventListener('app-barrage', handleEvent)
})
</script>

<style scoped>
.barrage-container {
  pointer-events: none;
  position: fixed;
  top: 72px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2000;
  width: 100%;
  max-width: 560px;
  padding: 0 16px;
}

.barrage-inner {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.barrage-item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10px 16px;
  border-radius: 999px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  background: rgba(55, 65, 81, 0.85);
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.25);
  animation: barrage-slide 4s linear forwards;
}

.barrage-item.info {
  background: rgba(59, 130, 246, 0.86);
}

.barrage-item.success {
  background: rgba(16, 185, 129, 0.88);
}

.barrage-item.error {
  background: rgba(248, 113, 113, 0.9);
}

.barrage-item.warning {
  background: rgba(251, 191, 36, 0.92);
  color: #1f2937;
}

@keyframes barrage-slide {
  0% {
    transform: translateX(40%);
    opacity: 0;
  }
  10% {
    transform: translateX(0%);
    opacity: 1;
  }
  90% {
    transform: translateX(-10%);
    opacity: 1;
  }
  100% {
    transform: translateX(-20%);
    opacity: 0;
  }
}

.barrage-enter-from,
.barrage-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

.barrage-enter-active,
.barrage-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

@media (max-width: 600px) {
  .barrage-container {
    top: 64px;
    max-width: 100%;
  }
}
</style>

