<template>
  <div class="discover-page" @touchstart="onTouchStart" @touchend="onTouchEnd">
    <!-- 顶部栏 -->
    <div class="top-bar">
      <button @click="goBack" class="back-btn">← 返回</button>
      <span class="title">发现</span>
      <button @click="showFilterDialog = true" class="filter-btn">⚙️</button>
    </div>
    
    <!-- 视频容器 -->
    <div class="video-container">
      <div 
        class="video-wrapper"
        :style="{ transform: `translateY(-${currentIndex * 100}%)`, transition: isAnimating ? 'transform 0.3s ease-out' : 'none' }"
      >
        <div 
          v-for="(video, videoIdx) in videos" 
          :key="video.id" 
          class="video-item"
        >
          <!-- 视频播放器 -->
          <video
            ref="videoRefs"
            :src="`/api/play/${video.id}`"
            class="video-player"
            :class="{ playing: currentVideoIndex === videoIdx && isPlaying }"
            @click="togglePlay"
            @loadedmetadata="onVideoLoaded(videoIdx, $event)"
            @timeupdate="onTimeUpdate(videoIdx)"
            @ended="onVideoEnded(videoIdx)"
            preload="auto"
            playsinline
          />
          
          <!-- 视频信息 -->
          <div class="video-info">
            <div class="video-tags">
              <span v-if="video.categories && video.categories.length" class="category-chip">
                📁 {{ video.categories.map(c => c.name).join(' • ') }}
              </span>
              <span v-if="video.tags && video.tags.length" class="tag-chip">
                🏷️ {{ video.tags.map(t => t.name).join(' • ') }}
              </span>
            </div>
            <div class="video-title">{{ video.file_name }}</div>
            <div class="video-duration">
              ⏱️ {{ formatDuration(currentVideoIndex === videoIdx ? currentTime : video.duration) }} / {{ formatDuration(video.duration) }}
            </div>
          </div>
          
          <!-- 操作栏 -->
          <div class="action-bar">
            <button @click="toggleFavorite(video)" class="action-btn">
              <span :class="{ 'active': video.isFavorite }">❤️</span>
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 右侧工具栏 -->
    <div class="right-toolbar">
      <button @click="showCategoryDialog = true" class="toolbar-btn" title="添加分类">
        📁
      </button>
      <button @click="showTagDialog = true" class="toolbar-btn" title="添加标签">
        🏷️
      </button>
      <button @click="skipVideo" class="toolbar-btn" title="跳过">
        ⏭️
      </button>
    </div>
    
    <!-- 分类选择对话框 -->
    <div class="dialog-overlay" v-if="showCategoryDialog">
      <div class="dialog-content">
        <h3>选择分类</h3>
        <div class="category-grid">
          <button
            v-for="cat in categories"
            :key="cat.id"
            class="category-card"
            :class="{ selected: currentVideoCategories.includes(cat.id) }"
            @click="toggleCategory(cat.id)"
          >
            {{ cat.name }}
          </button>
        </div>
        <div class="dialog-actions">
          <button @click="showCategoryDialog = false" class="btn-cancel">完成</button>
        </div>
      </div>
    </div>
    
    <!-- 标签选择对话框 -->
    <div class="dialog-overlay" v-if="showTagDialog">
      <div class="dialog-content">
        <h3>选择标签</h3>
        <div class="tag-grid">
          <button
            v-for="tag in tags"
            :key="tag.id"
            class="tag-card"
            :class="{ selected: currentVideoTags.includes(tag.id) }"
            :style="{ borderColor: tag.color }"
            @click="toggleTag(tag.id)"
          >
            {{ tag.name }}
          </button>
        </div>
        <div class="dialog-actions">
          <button @click="showTagDialog = false" class="btn-cancel">完成</button>
        </div>
      </div>
    </div>
    
    <!-- 时长筛选对话框 -->
    <div class="dialog-overlay" v-if="showFilterDialog">
      <div class="dialog-content">
        <h3>最大时长</h3>
        <div class="filter-options">
          <button
            v-for="option in durationOptions"
            :key="option.value"
            class="filter-option"
            :class="{ active: maxDuration === option.value }"
            @click="maxDuration = option.value"
          >
            {{ option.label }}
          </button>
        </div>
        <div class="dialog-actions">
          <button @click="showFilterDialog = false" class="btn-cancel">确定</button>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div class="empty-state" v-if="videos.length === 0 && !loading">
      <div class="empty-icon">🎬</div>
      <p>暂无符合条件的视频</p>
      <p class="empty-hint">尝试调整时长筛选条件</p>
    </div>
    
    <!-- 加载状态 -->
    <div class="loading-state" v-if="loading">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>
    
    <!-- 底部导航 -->
    <BottomNavigation />
  </div>
</template>

<script>
import BottomNavigation from '../components/BottomNavigation.vue'
import { videoApi, categoryApi, tagApi } from '../api'

export default {
  name: 'Discover',
  components: { BottomNavigation },
  data() {
    return {
      videos: [],
      currentIndex: 0,
      currentVideoIndex: -1,
      isPlaying: false,
      currentTime: 0,
      maxDuration: 600,
      loading: false,
      touchStartY: 0,
      touchEndY: 0,
      isAnimating: false,
      showCategoryDialog: false,
      showTagDialog: false,
      showFilterDialog: false,
      categories: [],
      tags: [],
      currentVideoCategories: [],
      currentVideoTags: [],
      durationOptions: [
        { value: 60, label: '< 1 分钟' },
        { value: 300, label: '< 5 分钟' },
        { value: 600, label: '< 10 分钟' },
        { value: 1800, label: '< 30 分钟' },
        { value: 0, label: '全部' }
      ]
    }
  },
  mounted() {
    this.init()
  },
  methods: {
    async init() {
      await Promise.all([
        this.loadCategories(),
        this.loadTags()
      ])
      await this.loadVideos()
    },
    
    onTouchStart(e) {
      this.touchStartY = e.touches[0].clientY
    },
    
    onTouchEnd(e) {
      this.touchEndY = e.changedTouches[0].clientY
      this.handleSwipe()
    },
    
    handleSwipe() {
      const diff = this.touchStartY - this.touchEndY
      const threshold = window.innerHeight * 0.3
      
      if (Math.abs(diff) > threshold) {
        if (diff > 0) {
          this.nextVideo()
        } else {
          this.prevVideo()
        }
      }
    },
    
    async nextVideo() {
      if (this.currentIndex < this.videos.length - 1) {
        this.isAnimating = true
        this.pauseCurrentVideo()
        this.currentIndex++
        setTimeout(() => {
          this.isAnimating = false
          this.autoplayCurrent()
        }, 300)
      } else {
        await this.loadMoreVideos()
      }
    },
    
    prevVideo() {
      if (this.currentIndex > 0) {
        this.isAnimating = true
        this.pauseCurrentVideo()
        this.currentIndex--
        setTimeout(() => {
          this.isAnimating = false
          this.autoplayCurrent()
        }, 300)
      }
    },
    
    skipVideo() {
      this.nextVideo()
    },
    
    async loadVideos() {
      this.loading = true
      try {
        const params = {
          page: 1,
          page_size: 20,
          sort: 'modified_at',
          order: 'desc'
        }
        
        if (this.maxDuration > 0) {
          params.max_duration = this.maxDuration
        }
        
        const res = await videoApi.listVideos(params)
        this.videos = this.shuffleArray(res.data.videos).map(v => ({
          ...v,
          isFavorite: false,
          categories: [],
          tags: []
        }))
        
        if (this.videos.length > 0) {
          await this.loadVideoMetadata(0)
          setTimeout(() => this.autoplayCurrent(), 500)
        }
      } catch (err) {
        console.error('加载视频失败:', err)
        window.showToast('加载视频失败', 'error')
      } finally {
        this.loading = false
      }
    },
    
    async loadMoreVideos() {
      try {
        const params = {
          page: 1,
          page_size: 20,
          sort: 'modified_at'
        }
        
        if (this.maxDuration > 0) {
          params.max_duration = this.maxDuration
        }
        
        const res = await videoApi.listVideos(params)
        const newVideos = this.shuffleArray(res.data.videos).map(v => ({
          ...v,
          isFavorite: false,
          categories: [],
          tags: []
        }))
        
        this.videos = [...this.videos, ...newVideos]
        this.nextVideo()
      } catch (err) {
        console.error('加载更多失败:', err)
        window.showToast('没有更多视频了', 'warning')
      }
    },
    
    shuffleArray(arr) {
      const result = arr.slice()
      for (let i = result.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
        const temp = result[i]
        result[i] = result[j]
        result[j] = temp
      }
      return result
    },
    
    async loadVideoMetadata(videoIdx) {
      const video = this.videos[videoIdx]
      if (!video) return
      
      try {
        const catRes = await videoApi.getVideoCategories(video.id)
        const tagRes = await videoApi.getVideoTags(video.id)
        
        this.videos[videoIdx] = {
          ...video,
          categories: catRes.data.categories || [],
          tags: tagRes.data.tags || []
        }
        
        if (videoIdx === this.currentIndex) {
          this.currentVideoCategories = (catRes.data.categories || []).map(c => c.id)
          this.currentVideoTags = (tagRes.data.tags || []).map(t => t.id)
        }
      } catch (err) {
        console.error('加载视频元数据失败:', videoIdx, err)
      }
    },
    
    autoplayCurrent() {
      this.currentVideoIndex = this.currentIndex
      this.isPlaying = true
      this.$nextTick(() => {
        const videoEl = this.$refs.videoRefs && this.$refs.videoRefs[this.currentIndex]
        if (videoEl) {
          videoEl.play().catch(e => console.log('自动播放失败:', e))
        }
      })
    },
    
    pauseCurrentVideo() {
      this.isPlaying = false
      const videoEl = this.$refs.videoRefs && this.$refs.videoRefs[this.currentIndex]
      if (videoEl) {
        videoEl.pause()
      }
    },
    
    togglePlay() {
      const videoEl = this.$refs.videoRefs && this.$refs.videoRefs[this.currentIndex]
      if (videoEl) {
        if (this.isPlaying) {
          videoEl.pause()
        } else {
          videoEl.play()
        }
        this.isPlaying = !this.isPlaying
      }
    },
    
    onVideoLoaded(videoIdx, event) {
      console.log('视频', videoIdx, '加载完成', event.target.duration)
    },
    
    onTimeUpdate(videoIdx) {
      if (videoIdx === this.currentIndex) {
        const videoEl = this.$refs.videoRefs && this.$refs.videoRefs[this.currentIndex]
        if (videoEl) {
          this.currentTime = videoEl.currentTime
        }
      }
    },
    
    onVideoEnded(videoIdx) {
      if (videoIdx === this.currentIndex) {
        this.nextVideo()
      }
    },
    
    async loadCategories() {
      try {
        const res = await categoryApi.listCategories()
        this.categories = res.data.filter(cat => cat.parent_id === null)
      } catch (err) {
        console.error('加载分类失败:', err)
      }
    },
    
    async loadTags() {
      try {
        const res = await tagApi.listTags()
        this.tags = res.data
      } catch (err) {
        console.error('加载标签失败:', err)
      }
    },
    
    async toggleCategory(categoryId) {
      const video = this.videos[this.currentIndex]
      if (!video) return
      
      const catIdx = this.currentVideoCategories.indexOf(categoryId)
      if (catIdx > -1) {
        this.currentVideoCategories.splice(catIdx, 1)
        try {
          await videoApi.removeVideoCategory(video.id, categoryId)
        } catch (err) {
          console.error('移除分类失败:', err)
        }
      } else {
        this.currentVideoCategories.push(categoryId)
        try {
          await videoApi.addVideoCategory(video.id, categoryId)
          window.showToast('已添加分类', 'success')
        } catch (err) {
          console.error('添加分类失败:', err)
          window.showToast('添加失败', 'error')
        }
      }
      
      await this.loadVideoMetadata(this.currentIndex)
    },
    
    async toggleTag(tagId) {
      const video = this.videos[this.currentIndex]
      if (!video) return
      
      const tagIdx = this.currentVideoTags.indexOf(tagId)
      if (tagIdx > -1) {
        this.currentVideoTags.splice(tagIdx, 1)
        try {
          await videoApi.removeVideoTag(video.id, tagId)
        } catch (err) {
          console.error('移除标签失败:', err)
        }
      } else {
        this.currentVideoTags.push(tagId)
        try {
          await videoApi.addVideoTag(video.id, tagId)
          window.showToast('已添加标签', 'success')
        } catch (err) {
          console.error('添加标签失败:', err)
          window.showToast('添加失败', 'error')
        }
      }
      
      await this.loadVideoMetadata(this.currentIndex)
    },
    
    toggleFavorite(video) {
      video.isFavorite = !video.isFavorite
      const msg = video.isFavorite ? '已收藏' : '已取消收藏'
      window.showToast(msg, 'success')
    },
    
    goBack() {
      this.$router.push('/videos')
    },
    
    formatDuration(seconds) {
      if (!seconds || seconds < 0) return '00:00'
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
  },
  watch: {
    maxDuration() {
      this.currentIndex = 0
      this.loadVideos()
    }
  }
}
</script>

<style scoped>
.discover-page {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #000;
  overflow: hidden;
  z-index: 2000;
}

.top-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: linear-gradient(to bottom, rgba(0,0,0,0.7), transparent);
  z-index: 10;
}

.back-btn,
.filter-btn {
  background: rgba(0, 0, 0, 0.5);
  border: none;
  color: #fff;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
}

.title {
  color: #fff;
  font-size: 1.2rem;
  font-weight: 600;
}

.video-container {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.video-wrapper {
  width: 100%;
  height: 100%;
}

.video-item {
  width: 100%;
  height: 100%;
  position: relative;
}

.video-player {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.video-player.playing {
  display: block;
}

.video-player:not(.playing) {
  display: none;
}

.video-info {
  position: absolute;
  bottom: 80px;
  left: 0;
  right: 0;
  padding: 1rem;
  background: linear-gradient(to top, rgba(0,0,0,0.8), transparent);
  color: #fff;
}

.video-tags {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}

.category-chip,
.tag-chip {
  padding: 0.25rem 0.75rem;
  background-color: rgba(233, 69, 96, 0.8);
  border-radius: 12px;
  font-size: 0.85rem;
}

.video-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.video-duration {
  font-size: 0.9rem;
  color: #ccc;
}

.action-bar {
  position: absolute;
  bottom: 60px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.action-btn {
  background: none;
  border: none;
  color: #fff;
  font-size: 2rem;
  cursor: pointer;
  opacity: 0.8;
  transition: opacity 0.3s;
}

.action-btn:hover {
  opacity: 1;
}

.action-btn span.active {
  animation: heartbeat 0.5s;
}

@keyframes heartbeat {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.3); }
}

.right-toolbar {
  position: absolute;
  right: 1rem;
  bottom: 100px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  z-index: 10;
}

.toolbar-btn {
  width: 50px;
  height: 50px;
  background: rgba(0, 0, 0, 0.6);
  border: none;
  border-radius: 50%;
  color: #fff;
  font-size: 1.5rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background-color 0.3s;
}

.toolbar-btn:hover {
  background: rgba(233, 69, 96, 0.8);
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 3000;
}

.dialog-content {
  background-color: #16213e;
  padding: 2rem;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow-y: auto;
}

.dialog-content h3 {
  margin: 0 0 1.5rem 0;
  color: #fff;
}

.category-grid,
.tag-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}

.category-card,
.tag-card {
  padding: 0.75rem 0.5rem;
  background-color: #0f3460;
  border: 2px solid transparent;
  border-radius: 8px;
  color: #eee;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.3s;
  min-height: 50px;
}

.category-card:hover,
.tag-card:hover {
  background-color: #1a2744;
}

.category-card.selected,
.tag-card.selected {
  background-color: rgba(233, 69, 96, 0.15);
  border-color: #e94560;
  color: #e94560;
}

.filter-options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-option {
  padding: 1rem;
  background-color: #0f3460;
  border: 2px solid transparent;
  border-radius: 8px;
  color: #eee;
  cursor: pointer;
  font-size: 1rem;
  text-align: left;
  transition: all 0.3s;
}

.filter-option:hover {
  background-color: #1a2744;
}

.filter-option.active {
  background-color: rgba(233, 69, 96, 0.15);
  border-color: #e94560;
  color: #e94560;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.btn-cancel {
  padding: 0.75rem 2rem;
  background-color: #e94560;
  border: none;
  border-radius: 8px;
  color: #fff;
  cursor: pointer;
  font-size: 1rem;
}

.empty-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
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

.loading-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  color: #888;
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

@media (min-width: 769px) {
  .right-toolbar {
    right: 2rem;
  }
}
</style>
