import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(router)
app.mount('#app')

// 创建全局 Toast 实例
window.showToast = function(message, type = 'info', duration = 3000) {
  // 创建 Toast 元素
  const toast = document.createElement('div')
  toast.className = `toast toast-${type}`
  
  const icons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  }
  
  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <span class="toast-message">${message}</span>
  `
  
  document.body.appendChild(toast)
  
  // 添加样式
  const style = document.createElement('style')
  style.textContent = `
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
      animation: toastIn 0.3s ease;
    }
    .toast-success { background: linear-gradient(135deg, #4caf50 0%, #45a049 100%); }
    .toast-error { background: linear-gradient(135deg, #f44336 0%, #da190b 100%); }
    .toast-warning { background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%); }
    .toast-info { background: linear-gradient(135deg, #2196f3 0%, #1976d2 100%); }
    .toast-icon { font-size: 16px; }
    @keyframes toastIn {
      from { opacity: 0; transform: translateX(-50%) translateY(-20px); }
      to { opacity: 1; transform: translateX(-50%) translateY(0); }
    }
  `
  document.head.appendChild(style)
  
  // 自动移除
  setTimeout(() => {
    toast.style.animation = 'toastIn 0.3s ease reverse'
    setTimeout(() => toast.remove(), 300)
  }, duration)
}
