<template>
  <transition name="toast">
    <div v-if="visible" :class="['toast', type]">
      <span class="toast-icon">{{ icon }}</span>
      <span class="toast-message">{{ message }}</span>
    </div>
  </transition>
</template>

<script>
export default {
  name: 'Toast',
  data() {
    return {
      visible: false,
      message: '',
      type: 'info',
      timer: null
    }
  },
  computed: {
    icon() {
      const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
      }
      return icons[this.type] || icons.info
    }
  },
  methods: {
    show(message, type = 'info', duration = 3000) {
      this.message = message
      this.type = type
      this.visible = true
      
      if (this.timer) {
        clearTimeout(this.timer)
      }
      
      this.timer = setTimeout(() => {
        this.visible = false
      }, duration)
    },
    
    success(message, duration = 3000) {
      this.show(message, 'success', duration)
    },
    
    error(message, duration = 4000) {
      this.show(message, 'error', duration)
    },
    
    warning(message, duration = 3000) {
      this.show(message, 'warning', duration)
    },
    
    info(message, duration = 2000) {
      this.show(message, 'info', duration)
    }
  }
}
</script>

<style scoped>
.toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 8px;
  color: white;
  font-size: 14px;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  min-width: 200px;
  max-width: 90%;
}

.toast.success {
  background: linear-gradient(135deg, #4caf50 0%, #45a049 100%);
}

.toast.error {
  background: linear-gradient(135deg, #f44336 0%, #da190b 100%);
}

.toast.warning {
  background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
}

.toast.info {
  background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%);
}

.toast-icon {
  font-size: 16px;
}

.toast-message {
  word-break: break-word;
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}
</style>
