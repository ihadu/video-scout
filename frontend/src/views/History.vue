<template>
  <div class="history">
    <div class="page-header">
      <h1>📺 观看历史</h1>
      <button class="btn-clear" @click="clearHistory">🗑️ 清空历史</button>
    </div>
    
    <!-- 视频列表 -->
    <div class="history-list" v-if="histories.length > 0">
      <div 
        v-for="item in histories" 
        :key="item.id"
        class="history-item"
        @click="playVideo(item.video_id)"
      >
        <div class="history-thumbnail">
          <img 
            :src="`/api/play/thumbnail/${item.video_id}`" 
            :alt="item.file_name"
            @error="handleImageError"
          />
          <div class="history-duration">{{ formatDuration(item.duration) }}</div>
        </div>
        <div class="history-info">
          <h3>{{ item.file_name }}</h3>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: progressPercentage(item) + '%' }"
            ></div>
          </div>
          <div class="history-meta">
            <span>进度：{{ formatDuration(item.progress) }} / {{ formatDuration(item.duration) }}</span>
            <span>{{ formatDate(item.watched_at) }}</span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div class="empty-state" v-else-if="!loading">
      <div class="empty-icon">📺</div>
      <p>暂无观看历史</p>
      <p class="empty-hint">观看视频后会自动记录</p>
      <router-link to="/" class="btn-primary">去浏览视频</router-link>
    </div>
    
    <!-- 加载状态 -->
    <div class="loading" v-if="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>
  </div>
</template>

<script>
import { historyApi } from '../api'

export default {
  name: 'History',
  data() {
    return {
      histories: [],
      loading: false
    }
  },
  mounted() {
    this.loadHistory()
  },
  methods: {
    async loadHistory() {
      this.loading = true
      try {
        const res = await historyApi.getHistory(50)
        this.histories = res.data
      } catch (error) {
        console.error('加载历史失败:', error)
        window.showToast('加载历史失败：' + (error.response?.data?.detail || error.message), 'error')
      } finally {
        this.loading = false
      }
    },
    
    async clearHistory() {
      if (!confirm('确定要清空所有观看历史吗？')) return
      
      try {
        await historyApi.clearHistory()
        window.showToast('观看历史已清空', 'success')
        this.loadHistory()
      } catch (error) {
        window.showToast('清空失败：' + (error.response?.data?.detail || error.message), 'error')
      }
    },
    
    playVideo(id) {
      this.$router.push(`/play/${id}`)
    },
    
    formatDuration(seconds) {
      if (!seconds || seconds < 0) return '00:00'
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    },
    
    progressPercentage(item) {
      if (!item.duration || item.duration === 0) return 0
      return Math.min((item.progress / item.duration) * 100, 100)
    },
    
    formatDate(dateStr) {
      if (!dateStr) return '-'
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN')
    },
    
    handleImageError(e) {
      e.target.src = '/placeholder-video.jpg'
    }
  }
}
</script>

<style scoped>
.history {
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-header h1 {
  color: #e94560;
}

.btn-clear {
  padding: 0.5rem 1rem;
  background-color: #16213e;
  color: #eee;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-clear:hover {
  background-color: #e94560;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.history-item {
  display: flex;
  gap: 1rem;
  background-color: #16213e;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
}

.history-item:hover {
  transform: translateX(5px);
  box-shadow: 0 5px 20px rgba(233, 69, 96, 0.2);
}

.history-thumbnail {
  position: relative;
  width: 200px;
  height: 112px;
  background-color: #0f3460;
  flex-shrink: 0;
}

.history-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.history-duration {
  position: absolute;
  bottom: 6px;
  right: 6px;
  padding: 0.2rem 0.4rem;
  background-color: rgba(0, 0, 0, 0.8);
  border-radius: 4px;
  font-size: 0.75rem;
  color: white;
}

.history-info {
  flex: 1;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.history-info h3 {
  font-size: 1rem;
  margin-bottom: 0.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.progress-bar {
  height: 6px;
  background-color: #0f3460;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #e94560 0%, #ff6b6b 100%);
  border-radius: 3px;
  transition: width 0.3s;
}

.history-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: #888;
}

.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #888;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-hint {
  margin: 1rem 0;
  font-size: 0.9rem;
}

.btn-primary {
  display: inline-block;
  padding: 0.75rem 2rem;
  background-color: #e94560;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  margin-top: 1rem;
  transition: background-color 0.3s;
}

.btn-primary:hover {
  background-color: #ff6b6b;
}

.loading {
  text-align: center;
  padding: 4rem;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid #16213e;
  border-top-color: #e94560;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .history-item {
    flex-direction: column;
  }
  
  .history-thumbnail {
    width: 100%;
    height: 180px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 1rem;
  }
  
  .btn-clear {
    width: 100%;
  }
}
</style>
