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
          v-for="(video, index) in videos" 
          :key="video.id" 
          class="video-item"
        >
          <!-- 视频播放器 -->
          <video
            ref="videoRefs"
            :src="`/api/play/${video.id}`"
            class="video-player"
            :class="{ playing: currentVideoIndex === index && isPlaying }"
            @click="togglePlay"
            @loadedmetadata="onVideoLoaded(index, $event)"
            @timeupdate="onTimeUpdate(index)"
            @ended="onVideoEnded(index)"
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
              ⏱️ {{ formatDuration(currentVideoIndex === index ? currentTime : video.duration) }} / {{ formatDuration(video.duration) }}
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
      maxDuration: 600, // 默认 10 分钟
      loading: false,
      touchStartY: 0,
      touchEndY: 0,
      isAnimating: false,
      // 对话框
      showCategoryDialog: false,
      showTagDialog: false,
      showFilterDialog: false,
      // 分类和标签
      categories: [],
      tags: [],
      currentVideoCategories: [],
      currentVideoTags: [],
      // 时长选项
      durationOptions: [
        { value: 60, label: '< 1 分钟' },
        { value: 300, label: '< 5 分钟' },
        { value: 600, label: '< 10 分钟' },
        { value: 1800, label: '< 30 分钟' },
        { value: 0, label: '全部' }
      ]
    }
  },
  computed: {
    currentVideo() {
      return this.videos[this.currentIndex] || null
    }
  },
  mounted() {
    this.loadCategories()
    this.loadTags()
    this.loadVideos()
  },
  methods: {
    // 触摸事件
    onTouchStart(e) {
      this.touchStartY = e.touches[0].clientY
    },
    onTouchEnd(e) {
      this.touchEndY = e.changedTouches[0].clientY
      this.handleSwipe()
    },
    
    // 处理滑动
    handleSwipe() {
      const diff = this.touchStartY - this.touchEndY
      const threshold = window.innerHeight * 0.3
      
      if (Math.abs(diff) > threshold) {
        if (diff > 0) {
          // 上滑 - 下一个
          this.nextVideo()
        } else {
          // 下滑 - 上一个
          this.prevVideo()
        }
      }
    },
    
    // 下一个视频
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
        // 加载更多
        await this.loadMoreVideos()
      }
    },
    
    // 上一个视频
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
    
    // 跳过视频
    skipVideo() {
      this.nextVideo()
    },
    
    // 加载视频列表
    async loadVideos() {
      this.loading = true
      try {
        const params = {
          page: 1,
          page_size: 20,
          sort: 'created_at',
          order: 'desc'
        }
        
        if (this.maxDuration > 0) {
          params.max_duration = this.maxDuration
        }
        
        // 随机排序：使用修改时间作为随机种子
        params.sort = 'modified_at'
        
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
      } catch (error) {
        console.error('加载视频失败:', error)
        window.showToast('加载视频失败', 'error')
      } finally {
        this.loading = false
      }
    },
    
    // 加载更多视频
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
      } catch (error) {
        console.error('加载更多失败:', error)
        window.showToast('没有更多视频了', 'warning')
      }
    },
    
    // 随机打乱数组
    shuffleArray(array) {
      const shuffled = [...array]
      for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]]
      }
      return shuffled
    },
    
    // 加载视频元数据（分类、标签）
    async loadVideoMetadata(index) {
      const video = this.videos[index]
      if (!video) return
      
      try {
        // 并行加载分类和标签
        const catPromise = videoApi.getVideoCategories(video.id).catch(err => {
          console.warn('加载分类失败:', video.id, err)
          return { data: { categories: [] } }
        })
        const tagPromise = videoApi.getVideoTags(video.id).catch(err => {
          console.warn('加载标签失败:', video.id, err)
          return { data: { tags: [] } }
        })
        
        const [catRes, tagRes] = await Promise.all([catPromise, tagPromise])
        
        this.videos[index] = {
          ...video,
          categories: catRes.data.categories || [],
          tags: tagRes.data.tags || []
        }
        
        // 只在当前视频时更新 currentVideoCategories/Tags
        if (index === this.currentIndex) {
          this.currentVideoCategories = (catRes.data.categories || []).map(c => c.id)
          this.currentVideoTags = (tagRes.data.tags || []).map(t => t.id)
        }
      } catch (error) {
        console.error('加载视频元数据失败:', index, error)
        // 确保至少有一个空数组
        this.videos[index] = {
          ...video,
          categories: this.videos[index]?.categories || [],
          tags: this.videos[index]?.tags || []
        }
      }
    },
    
    // 自动播放当前视频
    autoplayCurrent() {
      this.currentVideoIndex = this.currentIndex
      this.isPlaying = true
      this.$nextTick(() => {
        const video = this.$refs.videoRefs && this.$refs.videoRefs[this.currentIndex]
        if (video) {
          video.play().catch(err => console.log('自动播放失败:', err))
        }
      })
    },
    
    // 暂停当前视频
    pauseCurrentVideo() {
      this.isPlaying = false
      const video = this.$refs.videoRefs && this.$refs.videoRefs[this.currentIndex]
      if (video) {
        video.pause()
      }
    },
    
    // 切换播放/暂停
    togglePlay() {
      const video = this.$refs.videoRefs && this.$refs.videoRefs[this.currentIndex]
      if (video) {
        if (this.isPlaying) {
          video.pause()
        } else {
          video.play()
        }
        this.isPlaying = !this.isPlaying
      }
    },
    
    // 视频加载完成
    onVideoLoaded(index, event) {
      console.log(`视频 ${index} 加载完成`, event.target.duration)
    },
    
    // 时间更新
    onTimeUpdate(index) {
      if (index === this.currentIndex) {
        const video = this.$refs.videoRefs && this.$refs.videoRefs[this.currentIndex]
        if (video) {
          this.currentTime = video.currentTime
        }
      }
    },
    
    // 视频播放结束
    onVideoEnded(index) {
      if (index === this.currentIndex) {
        this.nextVideo()
      }
    },
    
    // 加载分类
    async loadCategories() {
      try {
        const res = await categoryApi.listCategories()
        this.categories = res.data.filter(cat => cat.parent_id === null)
      } catch (error) {
        console.error('加载分类失败:', error)
      }
    },
    
    // 加载标签
    async loadTags() {
      try {
        const res = await tagApi.listTags()
        this.tags = res.data
      } catch (error) {
        console.error('加载标签失败:', error)
      }
    },
    
    // 切换分类
    async toggleCategory(categoryId) {
      const video = this.videos[this.currentIndex]
      if (!video) return
      
      const index = this.currentVideoCategories.indexOf(categoryId)
      if (index > -1) {
        // 移除
        this.currentVideoCategories.splice(index, 1)
        try {
          await videoApi.removeVideoCategory(video.id, categoryId)
        } catch (error) {
          console.error('移除分类失败:', error)
        }
      } else {
        // 添加
        this.currentVideoCategories.push(categoryId)
        try {
          await videoApi.addVideoCategory(video.id, categoryId)
          window.showToast('已添加分类', 'success')
        } catch (error) {
          console.error('添加分类失败:', error)
          window.showToast('添加失败', 'error')
        }
      }
      
      // 更新视频数据
      await this.loadVideoMetadata(this.currentIndex)
    },
    
    // 切换标签
    async toggleTag(tagId) {
      const video = this.videos[this.currentIndex]
      if (!video) return
      
      const index = this.currentVideoTags.indexOf(tagId)
      if (index > -1) {
        // 移除
        this.currentVideoTags.splice(index, 1)
        try {
          await videoApi.removeVideoTag(video.id, tagId)
        } catch (error) {
          console.error('移除标签失败:', error)
        }
      } else {
        // 添加
        this.currentVideoTags.push(tagId)
        try {
          await videoApi.addVideoTag(video.id, tagId)
          window.showToast('已添加标签', 'success')
        } catch (error) {
          console.error('添加标签失败:', error)
          window.showToast('添加失败', 'error')
        }
      }
      
      // 更新视频数据
      await this.loadVideoMetadata(this.currentIndex)
    },
    
    // 切换收藏
    toggleFavorite(video) {
      video.isFavorite = !video.isFavorite
      const msg = video.isFavorite ? '已收藏' : '已取消收藏'
      window.showToast(msg, 'success')
    },
    
    // 返回
    goBack() {
      this.$router.push('/videos')
    },
    
    // 格式化时长
    formatDuration(seconds) {
      if (!seconds || seconds < 0) return '00:00'
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
  },
  watch: {
    maxDuration() {
      // 时长变化时重新加载视频
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

/* 顶部栏 */
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

/* 视频容器 */
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

/* 视频信息 */
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

/* 操作栏 */
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

/* 右侧工具栏 */
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

/* 对话框 */
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

/* 分类/标签网格 */
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

/* 筛选选项 */
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

/* 按钮 */
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

/* 空状态 */
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

/* 加载状态 */
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

/* 桌面端隐藏 */
@media (min-width: 769px) {
  .right-toolbar {
    right: 2rem;
  }
}
</style>
