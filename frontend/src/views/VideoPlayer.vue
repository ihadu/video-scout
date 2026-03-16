<template>
  <div class="video-player" v-if="videoInfo">
    <div class="player-header">
      <button class="back-btn" @click="goBack">← 返回</button>
      <button 
        class="favorite-btn" 
        :class="{ 'favorited': isFavorited }"
        @click="toggleFavorite"
      >
        {{ isFavorited ? '★ 已收藏' : '☆ 收藏' }}
      </button>
    </div>
    
    <!-- 支持浏览器播放 -->
    <div v-if="videoInfo.browser_supported" class="player-section">
      <div class="player-container">
        <video 
          ref="videoPlayer"
          :src="`/api/play/${videoId}`"
          controls
          autoplay
          class="video-element"
          @timeupdate="handleTimeUpdate"
          @loadedmetadata="handleVideoLoaded"
        >
          您的浏览器不支持视频播放
        </video>
      </div>
    </div>
    
    <!-- 不支持浏览器播放 -->
    <div v-else class="unsupported-format">
      <div class="unsupported-icon">⚠️</div>
      <h3>此格式不支持浏览器播放</h3>
      <p>格式：.{{ videoInfo.format }}</p>
      <p class="hint">浏览器原生不支持 {{ videoInfo.format.toUpperCase() }} 格式</p>
      <a :href="downloadUrl" :download="videoInfo.file_name" class="btn-download">
        💾 下载视频
      </a>
    </div>
    
    <div class="video-details">
      <h2>{{ videoInfo.file_name }}</h2>
      <div class="video-meta">
        <span v-if="videoInfo.width && videoInfo.height">
          📏 {{ videoInfo.width }}x{{ videoInfo.height }}
        </span>
        <span>⏱️ {{ formatDuration(videoInfo.duration) }}</span>
        <span>💾 {{ formatFileSize(videoInfo.file_size) }}</span>
        <span v-if="videoInfo.format">📁 .{{ videoInfo.format }}</span>
        <span v-if="videoInfo.codec">🎬 {{ videoInfo.codec }}</span>
      </div>
      <div class="video-info">
        <div class="video-path">
          <span>📂 {{ videoInfo.file_path }}</span>
        </div>
        <div class="video-date" v-if="videoInfo.created_at">
          <span>📅 添加时间：{{ formatDate(videoInfo.created_at) }}</span>
        </div>
      </div>
      <!-- 删除按钮 -->
      <div class="video-actions">
        <button @click="deleteVideoFile" class="btn-delete">
          ⚠️ 删除源文件
        </button>
      </div>
    </div>
  </div>
  
  <div class="error-state" v-else-if="!loading">
    <p>视频不存在或无法加载</p>
    <router-link to="/" class="btn-primary">返回视频库</router-link>
  </div>
  
  <div class="loading" v-if="loading">
    <div class="spinner"></div>
    <p>加载中...</p>
  </div>
  
  <!-- 继续观看对话框 -->
  <div class="continue-dialog" v-if="showContinueDialog && lastProgress > 0">
    <div class="dialog-content">
      <h3>📺 继续观看？</h3>
      <p>上次看到：{{ formatDuration(lastProgress) }} / {{ formatDuration(videoInfo.duration) }}</p>
      <div class="dialog-buttons">
        <button class="btn-cancel" @click="closeDialog">从头开始</button>
        <button class="btn-continue" @click="continueWatching">继续观看</button>
      </div>
    </div>
  </div>
</template>

<script>
import { videoApi, favoriteApi, historyApi } from '../api'
import axios from 'axios'

export default {
  name: 'VideoPlayer',
  data() {
    return {
      videoId: null,  // 保存 videoId 到 data 中
      videoInfo: null,
      loading: true,
      isFavorited: false,
      progressTimer: null,  // 进度保存定时器
      lastProgress: 0,  // 上次观看进度
      showContinueDialog: false  // 显示继续观看对话框
    }
  },
  computed: {
    downloadUrl() {
      // 返回视频文件的下载链接
      return `/api/play/${this.videoId}`
    }
  },
  mounted() {
    this.videoId = this.$route.params.id
    this.loadVideoInfo()
    this.checkFavoriteStatus()
    this.checkWatchHistory()
  },
  beforeUnmount() {
    // 离开页面时保存进度
    this.saveProgress()
    if (this.progressTimer) {
      clearTimeout(this.progressTimer)
    }
  },
  methods: {
    async loadVideoInfo() {
      try {
        // 使用新的 API 获取播放信息
        const res = await axios.get(`/api/play/info/${this.videoId}`)
        this.videoInfo = res.data
      } catch (error) {
        console.error('加载视频失败:', error)
        window.showToast('加载视频失败：' + (error.response?.data?.detail || error.message), 'error')
      } finally {
        this.loading = false
      }
    },
    
    async checkWatchHistory() {
      try {
        const res = await historyApi.getHistory(1)
        const histories = res.data
        // 查找当前视频的历史记录
        const history = histories.find(h => h.video_id === this.videoId)
        if (history && history.progress > 0 && history.progress < this.videoInfo?.duration * 0.9) {
          // 有进度且未看完（超过 90% 不提示）
          this.lastProgress = history.progress
          this.showContinueDialog = true
        }
      } catch (error) {
        console.error('检查观看历史失败:', error)
      }
    },
    
    continueWatching() {
      this.showContinueDialog = false
      const video = this.$refs.videoPlayer
      if (video) {
        video.currentTime = this.lastProgress
        video.play()
        window.showToast(`从 ${this.formatDuration(this.lastProgress)} 继续观看`, 'info')
      }
    },
    
    closeDialog() {
      this.showContinueDialog = false
    },
    
    handleVideoLoaded() {
      // 视频元数据加载完成
      if (this.showContinueDialog && this.lastProgress > 0) {
        // 对话框已处理，不需要额外操作
      }
    },
    
    async checkFavoriteStatus() {
      try {
        const res = await favoriteApi.checkStatus(this.videoId)
        this.isFavorited = res.data.is_favorited
      } catch (error) {
        console.error('检查收藏状态失败:', error)
      }
    },
    
    async toggleFavorite() {
      try {
        if (this.isFavorited) {
          await favoriteApi.removeFavorite(this.videoId)
          this.isFavorited = false
          window.showToast('已取消收藏', 'info')
        } else {
          await favoriteApi.addFavorite(this.videoId)
          this.isFavorited = true
          window.showToast('已添加到收藏', 'success')
        }
      } catch (error) {
        window.showToast(error.response?.data?.detail || '操作失败', 'error')
      }
    },
    
    handleTimeUpdate() {
      // 每 5 秒保存一次进度
      if (this.progressTimer) {
        clearTimeout(this.progressTimer)
      }
      this.progressTimer = setTimeout(() => {
        this.saveProgress()
      }, 5000)
    },
    
    async saveProgress() {
      const video = this.$refs.videoPlayer
      if (!video || !this.videoId || !this.videoInfo) return
      
      const currentTime = video.currentTime
      try {
        await historyApi.updateProgress(this.videoId, currentTime)
      } catch (error) {
        console.error('保存进度失败:', error)
      }
    },
    
    goBack() {
      this.$router.go(-1)
    },
    
    formatDuration(seconds) {
      if (!seconds || seconds < 0) return '00:00'
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    },
    
    formatFileSize(bytes) {
      if (!bytes) return '0 B'
      const kb = bytes / 1024
      const mb = kb / 1024
      const gb = mb / 1024
      
      if (gb > 1) return `${gb.toFixed(1)} GB`
      if (mb > 1) return `${mb.toFixed(1)} MB`
      if (kb > 1) return `${kb.toFixed(1)} KB`
      return `${bytes} B`
    },
    
    formatDate(dateStr) {
      if (!dateStr) return '-'
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN')
    },
    
    async deleteVideoFile() {
      // 二次确认
      const confirmMsg = `⚠️ 警告：此操作将永久删除视频文件！\n\n文件：${this.videoInfo.file_name}\n路径：${this.videoInfo.file_path}\n\n删除后无法恢复，确定要继续？`
      if (!confirm(confirmMsg)) return
      
      // 三次确认（输入文件名）
      const fileName = prompt(`请输入文件名 "${this.videoInfo.file_name}" 以确认删除：`)
      if (fileName !== this.videoInfo.file_name) {
        window.showToast('文件名不匹配，操作已取消', 'info')
        return
      }
      
      try {
        const res = await axios.delete(`/api/play/file/${this.videoId}`)
        window.showToast(res.data.message || '删除成功', 'success')
        
        // 返回视频库
        setTimeout(() => {
          this.$router.push('/')
        }, 1000)
      } catch (error) {
        window.showToast(error.response?.data?.detail || '删除失败', 'error')
      }
    }
  }
}
</script>

<style scoped>
.video-player {
  max-width: 1200px;
  margin: 0 auto;
}

.player-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.back-btn {
  padding: 0.75rem 1.5rem;
  background-color: #16213e;
  color: #eee;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.favorite-btn {
  padding: 0.75rem 1.5rem;
  background-color: #16213e;
  color: #eee;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.favorite-btn:hover {
  background-color: #0f3460;
}

.favorite-btn.favorited {
  background-color: #e94560;
  color: white;
}

.favorite-btn.favorited:hover {
  background-color: #ff6b6b;
}

.back-btn:hover {
  background-color: #e94560;
}

.player-section {
  margin-bottom: 2rem;
}

.player-container {
  background-color: #000;
  border-radius: 12px;
  overflow: hidden;
}

.video-element {
  width: 100%;
  max-height: 80vh;
  display: block;
}

.unsupported-format {
  background-color: #16213e;
  padding: 4rem 2rem;
  border-radius: 12px;
  text-align: center;
  margin-bottom: 2rem;
}

.unsupported-icon {
  font-size: 5rem;
  margin-bottom: 1rem;
}

.unsupported-format h3 {
  color: #e94560;
  margin-bottom: 1rem;
}

.unsupported-format p {
  color: #aaa;
  margin: 0.5rem 0;
}

.hint {
  font-size: 0.9rem;
  color: #888;
  margin: 1rem 0;
}

.btn-download {
  display: inline-block;
  padding: 1rem 2rem;
  background-color: #4caf50;
  color: white;
  text-decoration: none;
  border-radius: 8px;
  margin-top: 1rem;
  font-size: 1.1rem;
  transition: background-color 0.3s;
}

.btn-download:hover {
  background-color: #45a049;
}

.video-details {
  background-color: #16213e;
  padding: 1.5rem;
  border-radius: 12px;
}

.video-details h2 {
  margin-bottom: 1rem;
  font-size: 1.3rem;
}

.video-meta {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
  color: #aaa;
}

.video-info {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #0f3460;
}

.video-path {
  font-size: 0.9rem;
  color: #888;
  word-break: break-all;
  margin-bottom: 0.5rem;
}

.video-date {
  font-size: 0.85rem;
  color: #666;
}

.video-actions {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 2px dashed #e94560;
}

.btn-delete {
  padding: 1rem 2rem;
  background-color: #c62828;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 auto;
}

.btn-delete:hover {
  background-color: #ff5252;
  transform: scale(1.05);
}

.error-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #888;
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

/* 继续观看对话框 */
.continue-dialog {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.dialog-content {
  background-color: #16213e;
  padding: 2rem;
  border-radius: 12px;
  text-align: center;
  max-width: 400px;
  width: 90%;
}

.dialog-content h3 {
  color: #e94560;
  margin-bottom: 1rem;
  font-size: 1.5rem;
}

.dialog-content p {
  color: #eee;
  margin-bottom: 2rem;
  font-size: 1rem;
}

.dialog-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.dialog-buttons button {
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s;
}

.btn-cancel {
  background-color: #0f3460;
  color: #eee;
}

.btn-cancel:hover {
  background-color: #16213e;
}

.btn-continue {
  background-color: #e94560;
  color: white;
}

.btn-continue:hover {
  background-color: #ff6b6b;
}

@media (max-width: 768px) {
  .video-meta {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .dialog-buttons {
    flex-direction: column;
  }
  
  .dialog-buttons button {
    width: 100%;
  }
}
</style>
