<template>
  <div class="favorites">
    <h1>⭐ 我的收藏</h1>
    
    <!-- 视频网格 -->
    <div class="video-grid" v-if="favorites.length > 0">
      <div 
        v-for="video in favorites" 
        :key="video.video_id" 
        class="video-card"
        @click="playVideo(video.video_id)"
      >
        <div class="video-thumbnail">
          <img 
            :src="`/api/play/thumbnail/${video.video_id}`" 
            :alt="video.file_name"
            @error="handleImageError"
          />
          <div class="video-overlay">
            <span class="play-icon">▶</span>
          </div>
          <div class="video-duration">{{ formatDuration(video.duration) }}</div>
        </div>
        <div class="video-info">
          <h3>{{ video.file_name }}</h3>
          <div class="video-meta">
            <span v-if="video.width && video.height">
              {{ video.width }}x{{ video.height }}
            </span>
            <span>{{ formatFileSize(video.file_size) }}</span>
          </div>
          <button class="unfavorite-btn" @click.stop="removeFavorite(video.video_id)">
            ✖ 取消收藏
          </button>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div class="empty-state" v-else-if="!loading">
      <div class="empty-icon">⭐</div>
      <p>暂无收藏</p>
      <p class="empty-hint">在视频详情页点击"收藏"按钮</p>
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
import { favoriteApi } from '../api'

export default {
  name: 'Favorites',
  data() {
    return {
      favorites: [],
      loading: false
    }
  },
  mounted() {
    this.loadFavorites()
  },
  methods: {
    async loadFavorites() {
      this.loading = true
      try {
        const res = await favoriteApi.getFavorites()
        this.favorites = res.data
      } catch (error) {
        console.error('加载收藏失败:', error)
        window.showToast('加载收藏失败：' + (error.response?.data?.detail || error.message), 'error')
      } finally {
        this.loading = false
      }
    },
    
    async removeFavorite(videoId) {
      try {
        await favoriteApi.removeFavorite(videoId)
        window.showToast('已取消收藏', 'success')
        this.loadFavorites()
      } catch (error) {
        window.showToast('取消收藏失败：' + (error.response?.data?.detail || error.message), 'error')
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
    
    handleImageError(e) {
      e.target.src = '/placeholder-video.jpg'
    }
  }
}
</script>

<style scoped>
.favorites {
  max-width: 1400px;
  margin: 0 auto;
}

.favorites h1 {
  margin-bottom: 2rem;
  color: #e94560;
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.video-card {
  background-color: #16213e;
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
}

.video-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(233, 69, 96, 0.3);
}

.video-thumbnail {
  position: relative;
  width: 100%;
  padding-top: 56.25%;
  background-color: #0f3460;
}

.video-thumbnail img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(0, 0, 0, 0.5);
  opacity: 0;
  transition: opacity 0.3s;
}

.video-card:hover .video-overlay {
  opacity: 1;
}

.play-icon {
  font-size: 3rem;
  color: white;
}

.video-duration {
  position: absolute;
  bottom: 8px;
  right: 8px;
  padding: 0.25rem 0.5rem;
  background-color: rgba(0, 0, 0, 0.8);
  border-radius: 4px;
  font-size: 0.8rem;
  color: white;
}

.video-info {
  padding: 1rem;
}

.video-info h3 {
  font-size: 1rem;
  margin-bottom: 0.5rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-meta {
  display: flex;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: #888;
  margin-bottom: 0.75rem;
}

.unfavorite-btn {
  width: 100%;
  padding: 0.5rem;
  background-color: #0f3460;
  color: #eee;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: background-color 0.3s;
}

.unfavorite-btn:hover {
  background-color: #e94560;
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
  .video-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }
  
  .empty-state {
    padding: 2rem 1rem;
  }
  
  .empty-icon {
    font-size: 3rem;
  }
}
</style>
