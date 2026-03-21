<template>
  <div class="discover-page">
    <!-- 顶部栏 -->
    <div class="top-bar">
      <button @click="goBack" class="back-btn">← 返回</button>
      
      <!-- 模式切换器 -->
      <div class="mode-switcher">
        <button 
          :class="{ active: currentMode === 'organize' }"
          @click="switchMode('organize')"
        >
          🔧 整理
        </button>
        <button 
          :class="{ active: currentMode === 'recommend' }"
          @click="switchMode('recommend')"
        >
          🎯 推荐
        </button>
      </div>
      
      <button @click="showFilterDialog = true" class="filter-btn">⚙️</button>
    </div>
    
    <!-- 模式信息栏 -->
    <div class="mode-info">
      <span v-if="currentMode === 'organize'">
        📊 整理进度：{{ markingProgress }}% ({{ markedVideos }}/{{ totalVideos }} 已标记)
      </span>
      <span v-else>
        🎯 为你推荐最爱视频
      </span>
    </div>
    
    <!-- 视频容器 -->
    <div
      class="video-container"
      :class="{ 'has-dialog': showCategoryDialog || showTagDialog || showRatingDialog || showFilterDialog }"
      @touchstart="onTouchStart"
      @touchend="onTouchEnd"
    >
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
            @error="onVideoError(videoIdx, video.id, $event)"
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
          
        </div>
      </div>
    </div>
    
    <!-- 右侧工具栏 - 对话框打开时隐藏 -->
    <div class="right-toolbar" v-if="!showCategoryDialog && !showTagDialog && !showRatingDialog && !showFilterDialog">
      <button @click="showCategoryDialog = true" class="toolbar-btn" title="添加分类">
        📁
      </button>
      <button @click="showTagDialog = true" class="toolbar-btn" title="添加标签">
        🏷️
      </button>
      <button @click="showRatingDialog = true" class="toolbar-btn" title="评分">
        ⭐
      </button>
      <button @click="toggleFavorite" class="toolbar-btn" :class="{ 'favorite-active': videos[currentIndex]?.isFavorite }" title="收藏">
        ❤️
      </button>
      <button @click="skipVideo" class="toolbar-btn" title="跳过">
        ⏭️
      </button>
    </div>
    
    <!-- 分类选择对话框 - 底部固定 -->
    <div class="dialog-overlay bottom-sheet" v-if="showCategoryDialog">
      <div class="dialog-content">
        <div class="dialog-header">
          <h3>选择分类</h3>
          <button class="close-btn" @click="showCategoryDialog = false">×</button>
        </div>
        <div class="search-input-wrapper">
          <input
            v-model="searchCategoryQuery"
            type="text"
            placeholder="搜索分类..."
            class="search-input"
          />
        </div>
        <div class="category-grid">
          <button
            v-for="cat in filteredCategories"
            :key="cat.id"
            class="category-card"
            :class="{ selected: currentVideoCategories.includes(cat.id) }"
            @click="toggleCategory(cat.id)"
          >
            {{ cat.icon || '📁' }} {{ cat.name }}
          </button>
        </div>
      </div>
    </div>

    <!-- 标签选择对话框 - 底部固定 -->
    <div class="dialog-overlay bottom-sheet" v-if="showTagDialog">
      <div class="dialog-content">
        <div class="dialog-header">
          <h3>选择标签</h3>
          <button class="close-btn" @click="showTagDialog = false">×</button>
        </div>
        <div class="search-input-wrapper">
          <input
            v-model="searchTagQuery"
            type="text"
            placeholder="搜索标签..."
            class="search-input"
          />
        </div>
        <div class="tag-grid">
          <button
            v-for="tag in filteredTags"
            :key="tag.id"
            class="tag-card"
            :class="{ selected: currentVideoTags.includes(tag.id) }"
            :style="{ borderColor: tag.color }"
            @click="toggleTag(tag.id)"
          >
            {{ tag.name }}
          </button>
        </div>
      </div>
    </div>

    <!-- 评分对话框 - 底部固定 -->
    <div class="dialog-overlay bottom-sheet" v-if="showRatingDialog">
      <div class="dialog-content rating-dialog">
        <div class="dialog-header">
          <h3>给这个视频打分</h3>
          <button class="close-btn" @click="showRatingDialog = false">×</button>
        </div>
        <div class="rating-stars">
          <span
            v-for="star in 5"
            :key="star"
            class="star"
            :class="{ active: star <= currentRating }"
            @click="setRating(star)"
          >⭐</span>
        </div>
        <div class="rating-hint">
          <span v-if="currentRating === 0">未评分</span>
          <span v-else-if="currentRating === 1">一般</span>
          <span v-else-if="currentRating === 2">还行</span>
          <span v-else-if="currentRating === 3">喜欢</span>
          <span v-else-if="currentRating === 4">很喜欢</span>
          <span v-else-if="currentRating === 5">最爱</span>
        </div>
        <div class="dialog-actions">
          <button @click="clearRating" class="btn-clear" v-if="currentRating > 0">清除评分</button>
        </div>
      </div>
    </div>

    <!-- 时长筛选对话框 - 底部固定 -->
    <div class="dialog-overlay bottom-sheet" v-if="showFilterDialog">
      <div class="dialog-content">
        <div class="dialog-header">
          <h3>最大时长</h3>
          <button class="close-btn" @click="showFilterDialog = false">×</button>
        </div>
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
import { videoApi, categoryApi, tagApi, discoverApi, ratingApi, favoriteApi, videoCategoryApi, videoTagApi } from '../api'

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
      currentMode: 'organize',
      markingProgress: 0,
      markedVideos: 0,
      totalVideos: 0,
      showCategoryDialog: false,
      showTagDialog: false,
      showRatingDialog: false,
      showFilterDialog: false,
      categories: [],
      tags: [],
      currentVideoCategories: [],
      currentVideoTags: [],
      currentRating: 0,
      searchCategoryQuery: '',
      searchTagQuery: '',
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
  computed: {
    filteredCategories() {
      let result = this.searchCategoryQuery
        ? this.categories.filter(cat => cat.name.toLowerCase().includes(this.searchCategoryQuery.toLowerCase()))
        : this.categories

      // 将已选中的分类排在前面
      return result.sort((a, b) => {
        const aSelected = this.currentVideoCategories.includes(a.id)
        const bSelected = this.currentVideoCategories.includes(b.id)
        if (aSelected && !bSelected) return -1
        if (!aSelected && bSelected) return 1
        return 0
      })
    },
    filteredTags() {
      let result = this.searchTagQuery
        ? this.tags.filter(tag => tag.name.toLowerCase().includes(this.searchTagQuery.toLowerCase()))
        : this.tags

      // 将已选中的标签排在前面
      return result.sort((a, b) => {
        const aSelected = this.currentVideoTags.includes(a.id)
        const bSelected = this.currentVideoTags.includes(b.id)
        if (aSelected && !bSelected) return -1
        if (!aSelected && bSelected) return 1
        return 0
      })
    }
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
        // 预加载下一个视频的元数据
        if (this.currentIndex + 1 < this.videos.length) {
          this.loadVideoMetadata(this.currentIndex + 1)
        }
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
        // 预加载上一个视频的元数据
        if (this.currentIndex - 1 >= 0) {
          this.loadVideoMetadata(this.currentIndex - 1)
        }
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
          limit: 20,
          max_duration: this.maxDuration > 0 ? this.maxDuration : 0,
          mode: this.currentMode
        }
        
        const res = await discoverApi.recommend(params)
        
        this.markingProgress = res.data.metadata.marking_progress || 0
        this.totalVideos = res.data.metadata.total_videos || 0
        this.markedVideos = res.data.metadata.marked_videos || 0
        
        this.videos = res.data.videos.map(v => ({
          ...v,
          isFavorite: false,
          categories: [],
          tags: []
        }))
        
        if (this.videos.length > 0) {
          // 批量预加载前 5 个视频的元数据
          const preloadCount = Math.min(5, this.videos.length)
          for (let i = 0; i < preloadCount; i++) {
            this.loadVideoMetadata(i)
          }
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
          limit: 20,
          max_duration: this.maxDuration > 0 ? this.maxDuration : 0,
          mode: this.currentMode
        }
        
        const res = await discoverApi.recommend(params)
        const newVideos = res.data.videos.map(v => ({
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
        // 并行请求分类、标签和收藏状态
        const [catRes, tagRes, favRes] = await Promise.all([
          videoApi.getVideoCategories(video.id),
          videoApi.getVideoTags(video.id),
          favoriteApi.checkStatus(video.id).catch(() => ({ data: { is_favorited: false } }))
        ])

        // 直接修改属性以保留响应式
        this.videos[videoIdx].categories = catRes.data.categories || []
        this.videos[videoIdx].tags = tagRes.data.tags || []
        this.videos[videoIdx].isFavorite = favRes.data?.is_favorited || false

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
      // 视频播放完后自动循环播放当前视频
      if (videoIdx === this.currentIndex) {
        console.log('视频播放结束，循环播放')
        const videoEl = this.$refs.videoRefs && this.$refs.videoRefs[this.currentIndex]
        if (videoEl) {
          videoEl.currentTime = 0
          videoEl.play().catch(e => {
            console.log('循环播放失败:', e)
            this.isPlaying = false
          })
        }
      }
    },

    async onVideoError(videoIdx, videoId, event) {
      // 视频加载错误处理
      const videoEl = event.target
      if (videoEl && videoEl.networkState === 4) {
        // NETWORK_NO_SOURCE - 资源不存在
        console.error(`视频 ${videoId} 加载失败：文件不存在`)
        window.showToast('视频文件不存在，请检查外接硬盘是否已挂载', 'error')

        // 自动跳过当前视频
        if (videoIdx === this.currentIndex) {
          this.isPlaying = false
          setTimeout(() => {
            this.nextVideo()
          }, 1500)
        }
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
          await videoCategoryApi.removeCategory(video.id, categoryId)
          window.showToast('已移除分类', 'success')
        } catch (err) {
          console.error('移除分类失败:', err)
          window.showToast('移除失败', 'error')
        }
      } else {
        this.currentVideoCategories.push(categoryId)
        try {
          await videoCategoryApi.addCategories(video.id, [categoryId])
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
          await videoTagApi.removeTag(video.id, tagId)
          window.showToast('已移除标签', 'success')
        } catch (err) {
          console.error('移除标签失败:', err)
          window.showToast('移除失败', 'error')
        }
      } else {
        this.currentVideoTags.push(tagId)
        try {
          await videoTagApi.addTags(video.id, [tagId])
          window.showToast('已添加标签', 'success')
        } catch (err) {
          console.error('添加标签失败:', err)
          window.showToast('添加失败', 'error')
        }
      }

      await this.loadVideoMetadata(this.currentIndex)
    },
    
    async toggleFavorite() {
      const video = this.videos[this.currentIndex]
      if (!video) return

      try {
        if (video.isFavorite) {
          // 取消收藏
          await favoriteApi.removeFavorite(video.id)
          this.videos[this.currentIndex].isFavorite = false
          window.showToast('已取消收藏', 'success')
        } else {
          // 添加收藏
          await favoriteApi.addFavorite(video.id)
          this.videos[this.currentIndex].isFavorite = true
          window.showToast('已收藏', 'success')
        }
      } catch (err) {
        console.error('收藏操作失败:', err)
        window.showToast('操作失败', 'error')
      }
    },
    
    switchMode(mode) {
      this.currentMode = mode
      this.currentIndex = 0
      this.loadVideos()
    },
    
    async setRating(star) {
      const video = this.videos[this.currentIndex]
      if (!video) return
      
      try {
        await ratingApi.updateRating(video.id, star)
        this.currentRating = star
        this.showRatingDialog = false
        window.showToast(`已评分：${star}星`, 'success')
        this.loadVideos()
      } catch (err) {
        console.error('评分失败:', err)
        window.showToast('评分失败', 'error')
      }
    },
    
    async clearRating() {
      const video = this.videos[this.currentIndex]
      if (!video) return
      
      try {
        await ratingApi.updateRating(video.id, 0)
        this.currentRating = 0
        this.showRatingDialog = false
        window.showToast('已清除评分', 'success')
        this.loadVideos()
      } catch (err) {
        console.error('清除评分失败:', err)
        window.showToast('清除评分失败', 'error')
      }
    },
    
    async loadCurrentVideoRating() {
      const video = this.videos[this.currentIndex]
      if (!video) return
      
      try {
        const res = await ratingApi.getRating(video.id)
        this.currentRating = res.data.rating || 0
      } catch (err) {
        console.error('加载评分失败:', err)
        this.currentRating = 0
      }
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
    },
    showRatingDialog(val) {
      if (val) {
        this.loadCurrentVideoRating()
      }
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

/* 顶部栏 */
.top-bar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: linear-gradient(to bottom, rgba(0,0,0,0.8), transparent);
  z-index: 100;
}

.mode-switcher {
  display: flex;
  background-color: rgba(0, 0, 0, 0.6);
  border-radius: 8px;
  padding: 0.25rem;
}

.mode-switcher button {
  padding: 0.5rem 1rem;
  background: transparent;
  border: none;
  color: #888;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s;
}

.mode-switcher button.active {
  background-color: #e94560;
  color: #fff;
  font-weight: 600;
}

/* 模式信息栏 */
.mode-info {
  position: absolute;
  top: 55px;
  left: 0;
  right: 0;
  padding: 0.5rem 1rem;
  background: linear-gradient(to bottom, rgba(0,0,0,0.7), transparent);
  color: #fff;
  font-size: 0.85rem;
  text-align: center;
  z-index: 100;
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

/* 视频容器 - 关键布局 */
.video-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  margin-top: 60px;  /* 为顶部栏留出空间 */
  margin-bottom: 60px;  /* 为底部导航留出空间 */
  overflow: hidden;
  z-index: 1;
  transition: margin-bottom 0.3s ease;
}

/* 模态框打开时，视频容器缩小 */
.video-container.has-dialog {
  margin-bottom: calc(60px + 65vh);
}

.video-wrapper {
  width: 100%;
  height: 100%;
}

.video-item {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;  /* 确保视频不会溢出 */
}

/* 视频播放器 */
.video-player {
  width: 100%;
  height: 100%;
  object-fit: contain;
  position: relative;
  z-index: 1;
  pointer-events: auto;  /* 允许视频接收点击事件 */
}

/* 视频始终显示，不根据播放状态隐藏 */

/* 视频信息 */
.video-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 1rem;
  background: linear-gradient(to top, rgba(0,0,0,0.9), transparent);
  color: #fff;
  z-index: 10;
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

/* 收藏按钮动画 */
.toolbar-btn.favorite-active {
  animation: heartbeat 0.5s ease-in-out;
  will-change: transform;
}

@keyframes heartbeat {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.3); }
}

/* 右侧工具栏 */
.right-toolbar {
  position: fixed;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  flex-direction: column;
  gap: 1rem;
  z-index: 10002;
  pointer-events: none;  /* 让工具栏本身不拦截点击，但按钮可以 */
}

.toolbar-btn {
  pointer-events: auto;  /* 按钮恢复点击 */
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
  transition: all 0.3s;
  transform-origin: center;  /* 确保缩放原点正确 */
}

.toolbar-btn:hover {
  background: rgba(233, 69, 96, 0.8);
}

.toolbar-btn.favorite-active {
  color: #e94560;
  background: rgba(233, 69, 96, 0.3);
}

/* 对话框 - 底部固定 */
.dialog-overlay.bottom-sheet {
  position: fixed;
  top: auto;
  bottom: 0;
  left: 0;
  right: 0;
  height: 65vh;
  background-color: transparent;
  display: block;
  z-index: 10001;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}

.dialog-content {
  background-color: #16213e;
  height: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 16px 16px 0 0;
  overflow: hidden;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border-bottom: 1px solid #30363d;
  position: sticky;
  top: 0;
  background-color: #16213e;
}

.dialog-header h3 {
  margin: 0;
  color: #fff;
  font-size: 1.1rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #8b949e;
  padding: 0.25rem 0.5rem;
}

/* 搜索输入框 */
.search-input-wrapper {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #30363d;
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem;
  background-color: #0d1117;
  border: 1px solid #30363d;
  border-radius: 8px;
  color: #fff;
  font-size: 0.95rem;
  outline: none;
  transition: border-color 0.3s;
}

.search-input:focus {
  border-color: #e94560;
}

.search-input::placeholder {
  color: #6e7681;
}

/* 修复底部导航栏 z-index */
:deep(.bottom-navigation) {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 3000;
}

.dialog-content h3 {
  margin: 0 0 1.5rem 0;
  color: #fff;
}

.rating-dialog {
  text-align: center;
}

/* 分类和标签网格 */
.category-grid,
.tag-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  padding: 1rem;
  overflow-y: auto;
}

/* 桌面端更多列 */
@media (min-width: 769px) {
  .category-grid,
  .tag-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

.rating-stars {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin: 2rem 0;
  font-size: 3rem;
  padding: 0 1rem;
}

.star {
  cursor: pointer;
  color: #444;
  transition: color 0.3s;
}

.star.active,
.star:hover {
  color: #ffd700;
}

.rating-hint {
  color: #888;
  font-size: 1rem;
  margin-bottom: 2rem;
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
  display: flex;
  align-items: center;
  gap: 0.5rem;
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
  padding: 1rem;
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
  justify-content: center;
  padding: 1rem;
  gap: 1rem;
}

.btn-clear {
  padding: 0.75rem 2rem;
  background-color: #444;
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

/* 桌面端优化 */
@media (min-width: 769px) {
  .right-toolbar {
    right: 2rem;
  }
}
</style>
