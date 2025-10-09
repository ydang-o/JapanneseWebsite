<template>
  <transition name="fade">
    <div v-if="visible" class="notice" :class="typeClass" role="alert">
      <div class="notice-content">
        <div class="notice-header">
          <span class="notice-title">{{ title }}</span>
          <button class="notice-close" @click="$emit('close')">×</button>
        </div>
        <p v-if="description" class="notice-description">{{ description }}</p>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  type: { type: String, default: 'info' },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
})

defineEmits(['close'])

const typeClass = computed(() => {
  switch (props.type) {
    case 'success':
      return 'notice-success'
    case 'warning':
      return 'notice-warning'
    case 'error':
      return 'notice-error'
    default:
      return 'notice-info'
  }
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.notice {
  border-radius: 10px;
  border: 1px solid transparent;
  padding: 16px 18px;
  margin-bottom: 16px;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.12);
  background: #fff;
}

.notice-content {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.notice-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.notice-title {
  font-size: 15px;
}

.notice-description {
  margin: 0;
  color: #4b5563;
  font-size: 14px;
  line-height: 1.5;
}

.notice-close {
  background: transparent;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: inherit;
  padding: 0 4px;
}

.notice-info {
  border-color: rgba(59, 130, 246, 0.4);
  background: rgba(59, 130, 246, 0.08);
  color: #1d4ed8;
}

.notice-success {
  border-color: rgba(16, 185, 129, 0.4);
  background: rgba(16, 185, 129, 0.08);
  color: #047857;
}

.notice-warning {
  border-color: rgba(234, 179, 8, 0.4);
  background: rgba(234, 179, 8, 0.08);
  color: #b45309;
}

.notice-error {
  border-color: rgba(248, 113, 113, 0.4);
  background: rgba(248, 113, 113, 0.08);
  color: #b91c1c;
}
</style>

