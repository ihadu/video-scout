<template>
  <div class="video-player" v-if="videoInfo">
    <button class="back-btn" @click="goBack">← 返回</button>
    
    <!-- 支持浏览器播放 -->
    <div v-if="videoInfo.browser_supported" class="player-section">
      <div class="player-container">
        <video 
          ref="videoPlayer"
          :src="`/api/play/${videoId}`"
          controls
          autoplay
          class="video-element"
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
</template>

<script>
import { videoApi } from '../api'
import axios from 'axios'

export default {
  name: 'VideoPlayer',
  data() {
    return {
      videoInfo: null,
      loading: true
    }
  },
  computed: {
    videoId() {
      return this.$route.params.id
    },
    downloadUrl() {
      // 返回视频文件的下载链接
      return `/api/play/${this.videoId}`
    }
  },
  mounted() {
    this.loadVideoInfo()
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
    }
  }
}
</script>

<style scoped>
.video-player {
  max-width: 1200px;
  margin: 0 auto;
}

.back-btn {
  padding: 0.75rem 1.5rem;
  background-color: #16213e;
  color: #eee;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 1rem;
  transition: background-color 0.3s;
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

@media (max-width: 768px) {
  .video-meta {
    flex-direction: column;
    gap: 0.5rem;
  }
}
</style>
