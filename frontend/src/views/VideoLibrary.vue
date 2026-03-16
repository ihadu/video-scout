<template>
  <div class="video-library">
    <!-- 固定筛选栏 -->
    <div class="filter-bar">
      <!-- 全部按钮 -->
      <div class="filter-all">
        <button 
          class="filter-btn"
          :class="{ active: !selectedCategory && !selectedTag }"
          @click="clearFilters"
        >
          全部
        </button>
      </div>
      
      <!-- 分类筛选 -->
      <div class="filter-row">
        <span class="filter-label">分类：</span>
        <button 
          class="filter-btn"
          :class="{ active: !selectedCategory }"
          @click="selectedCategory = null"
        >
          全部 ({{ totalVideos }})
        </button>
        <button 
          v-for="cat in categories" 
          :key="cat.id" 
          class="filter-btn"
          :class="{ active: selectedCategory === cat.id }"
          @click="selectedCategory = cat.id"
        >
          {{ cat.name }} ({{ cat.video_count || 0 }})
        </button>
      </div>
      
      <!-- 标签筛选 -->
      <div class="filter-row">
        <span class="filter-label">标签：</span>
        <button 
          class="filter-btn"
          :class="{ active: !selectedTag }"
          @click="selectedTag = null"
        >
          全部 ({{ totalVideos }})
        </button>
        <button 
          v-for="tag in tags" 
          :key="tag.id" 
          class="filter-btn"
          :class="{ active: selectedTag === tag.id }"
          @click="selectedTag = tag.id"
        >
          {{ tag.name }} ({{ tag.video_count || 0 }})
        </button>
      </div>
    </div>
    
    <!-- 搜索和过滤栏 -->
    <div class="search-bar">
      <div class="search-input-wrapper">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="搜索视频..." 
          @input="handleSearch"
        />
        <button @click="handleSearch">🔍</button>
      </div>
      
      <div class="filters">
        <select v-model="durationFilter" @change="handleFilter">
          <option value="">所有时长</option>
          <option value="short">短视频 (&lt;1 分钟)</option>
          <option value="medium">中视频 (1-10 分钟)</option>
          <option value="long">长视频 (&gt;10 分钟)</option>
        </select>
        
        <select v-model="formatFilter" @change="handleFilter">
          <option value="">所有格式</option>
          <option value=".mp4">MP4</option>
          <option value=".mkv">MKV</option>
          <option value=".avi">AVI</option>
          <option value=".mov">MOV</option>
          <option value=".webm">WebM</option>
        </select>
        
        <select v-model="sortBy" @change="handleSort">
          <option value="modified_at">最近更新</option>
          <option value="created_at">最近添加</option>
          <option value="file_name">名称</option>
          <option value="duration">时长</option>
          <option value="file_size">大小</option>
        </select>
        
        <select v-model="sortOrder" @change="handleSort">
          <option value="desc">降序</option>
          <option value="asc">升序</option>
        </select>
      </div>
      
      <div class="video-count" v-if="total > 0">
        共 {{ total }} 个视频
      </div>
    </div>
    
    <!-- 视频网格 -->
    <div class="video-grid" v-if="videos.length > 0">
      <div 
        v-for="video in videos" 
        :key="video.id" 
        class="video-card"
        @click="playVideo(video.id)"
      >
        <div class="video-thumbnail">
          <img 
            :src="`/api/play/thumbnail/${video.id}`" 
            :alt="video.file_name"
            @error="handleImageError"
            @load="() => handleImageLoad(video.id)"
          />
          <div class="thumbnail-loading" v-if="!video.thumbnailLoaded">
            <div class="spinner-small"></div>
          </div>
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
        </div>
      </div>
    </div>
    
    <!-- 骨架屏加载 -->
    <div class="skeleton-grid" v-if="loading">
      <div class="skeleton-card" v-for="i in 6" :key="i">
        <div class="skeleton-thumbnail"></div>
        <div class="skeleton-info">
          <div class="skeleton-title"></div>
          <div class="skeleton-meta"></div>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div class="empty-state" v-else-if="!loading">
      <div class="empty-icon">🎬</div>
      <p>暂无视频</p>
      <p class="empty-hint">前往"扫描管理"添加视频目录</p>
      <router-link to="/scan" class="btn-primary">去添加</router-link>
    </div>
    
    <!-- 分页 -->
    <div class="pagination" v-if="total > pageSize">
      <button 
        :disabled="page === 1" 
        @click="changePage(page - 1)"
      >
        ← 上一页
      </button>
      <span>第 {{ page }} / {{ totalPages }} 页</span>
      <button 
        :disabled="page === totalPages" 
        @click="changePage(page + 1)"
      >
        下一页 →
      </button>
    </div>
    
    <!-- 统计信息 -->
    <div class="stats" v-if="durationStats.total > 0">
      <span>📊 共 {{ durationStats.total }} 个视频</span>
      <span>短视频：{{ durationStats.short }}</span>
      <span>中视频：{{ durationStats.medium }}</span>
      <span>长视频：{{ durationStats.long }}</span>
    </div>
  </div>
</template>

<script>
import { videoApi, searchApi, categoryApi, tagApi } from '../api'

export default {
  name: 'VideoLibrary',
  data() {
    return {
      videos: [],
      total: 0,
      page: 1,
      pageSize: 10,
      searchQuery: '',
      durationFilter: '',
      formatFilter: '',
      sortBy: 'modified_at',
      sortOrder: 'desc',
      loading: false,
      durationStats: { total: 0, short: 0, medium: 0, long: 0 },
      searchTimer: null,
      thumbnailLoading: {},
      // 分类和标签
      categories: [],
      tags: [],
      selectedCategory: null,
      selectedTag: null,
      totalVideos: 0  // 所有视频总数
    }
  },
  computed: {
    totalPages() {
      return Math.ceil(this.total / this.pageSize)
    }
  },
  mounted() {
    this.loadCategories()
    this.loadTags()
    this.parseURL()  // 从 URL 读取筛选状态
    this.loadVideos()
    this.loadDurationStats()
  },
  watch: {
    // 监听筛选状态变化，同步到 URL
    selectedCategory: 'syncURL',
    selectedTag: 'syncURL',
    page: 'syncURL'
  },
  methods: {
    // 同步筛选状态到 URL
    syncURL() {
      const params = new URLSearchParams()
      if (this.selectedCategory) params.set('category', this.selectedCategory)
      if (this.selectedTag) params.set('tag', this.selectedTag)
      if (this.page !== 1) params.set('page', this.page)
      
      const newURL = params.toString() ? `?${params.toString()}` : ''
      window.history.replaceState(null, '', newURL)
    },
    
    // 从 URL 读取筛选状态
    parseURL() {
      const params = new URLSearchParams(window.location.search)
      const categoryId = params.get('category')
      const tagId = params.get('tag')
      const page = params.get('page')
      
      if (categoryId) this.selectedCategory = parseInt(categoryId)
      if (tagId) this.selectedTag = parseInt(tagId)
      if (page) this.page = parseInt(page)
    },
    
    async loadCategories() {
      try {
        // 尝试从缓存读取
        const cached = localStorage.getItem('video_categories')
        if (cached) {
          this.categories = JSON.parse(cached)
          return
        }
        
        const res = await categoryApi.listCategories()
        this.categories = res.data.filter(cat => cat.parent_id === null)
        
        // 缓存分类列表
        localStorage.setItem('video_categories', JSON.stringify(this.categories))
      } catch (error) {
        console.error('加载分类失败:', error)
      }
    },
    
    async loadTags() {
      try {
        // 尝试从缓存读取
        const cached = localStorage.getItem('video_tags')
        if (cached) {
          this.tags = JSON.parse(cached)
          return
        }
        
        const res = await tagApi.listTags()
        this.tags = res.data
        
        // 缓存标签列表
        localStorage.setItem('video_tags', JSON.stringify(this.tags))
      } catch (error) {
        console.error('加载标签失败:', error)
      }
    },
    
    clearFilters() {
      this.selectedCategory = null
      this.selectedTag = null
      this.syncURL()
      this.loadVideos()
    },
    
    async loadVideos() {
      this.loading = true
      try {
        const params = {
          page: this.page,
          page_size: this.pageSize,
          sort: this.sortBy,
          order: this.sortOrder
        }
        
        // 处理时长过滤
        if (this.durationFilter === 'short') {
          params.max_duration = 60  // < 1 分钟
        } else if (this.durationFilter === 'medium') {
          params.min_duration = 60  // 1-10 分钟
          params.max_duration = 600
        } else if (this.durationFilter === 'long') {
          params.min_duration = 600  // > 10 分钟
        }
        
        // 处理格式过滤
        if (this.formatFilter) {
          params.format = this.formatFilter
        }
        
        // 处理分类筛选
        if (this.selectedCategory) {
          params.category_id = this.selectedCategory
        }
        
        // 处理标签筛选
        if (this.selectedTag) {
          params.tag_id = this.selectedTag
        }
        
        if (this.searchQuery) {
          const res = await searchApi.search({ ...params, q: this.searchQuery })
          this.videos = res.data.videos.map(v => ({ ...v, thumbnailLoaded: false }))
          this.total = res.data.total
        } else {
          const res = await videoApi.listVideos(params)
          this.videos = res.data.videos.map(v => ({ ...v, thumbnailLoaded: false }))
          this.total = res.data.total
          
          // 保存所有视频总数（用于"全部"按钮显示）
          if (!this.selectedCategory && !this.selectedTag) {
            this.totalVideos = this.total
          }
        }
      } catch (error) {
        console.error('加载视频失败:', error)
        window.showToast('加载视频失败：' + (error.response?.data?.detail || error.message), 'error')
      } finally {
        this.loading = false
      }
    },
    
    async loadDurationStats() {
      try {
        const res = await searchApi.getDurationRanges()
        this.durationStats = res.data
      } catch (error) {
        console.error('加载时长统计失败:', error)
      }
    },
    
    handleSearch() {
      // 防抖：300ms 后执行搜索
      if (this.searchTimer) {
        clearTimeout(this.searchTimer)
      }
      this.searchTimer = setTimeout(() => {
        this.page = 1
        this.loadVideos()
      }, 300)
    },
    
    handleFilter() {
      this.page = 1
      this.loadVideos()
    },
    
    handleSort() {
      this.page = 1
      this.loadVideos()
    },
    
    changePage(newPage) {
      if (newPage >= 1 && newPage <= this.totalPages) {
        this.page = newPage
        this.loadVideos()
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
    },
    
    handleImageLoad(videoId) {
      // 标记缩略图已加载
      const video = this.videos.find(v => v.id === videoId)
      if (video) {
        video.thumbnailLoaded = true
      }
    }
  }
}
</script>

<style scoped>
.video-library {
  max-width: 1400px;
  margin: 0 auto;
}

/* 固定筛选栏 */
.filter-bar {
  position: sticky;
  top: 0;
  background-color: #0f3460;
  padding: 1rem 2rem;
  z-index: 100;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  margin: 0 -2rem 1rem -2rem;
}

.filter-all {
  margin-bottom: 0.75rem;
}

.filter-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

/* 移动端：横向滚动 */
@media (max-width: 768px) {
  .filter-bar {
    padding: 0.75rem 1rem;
    margin: 0 -1rem 1rem -1rem;
  }
  
  .filter-row {
    flex-wrap: nowrap;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    -ms-overflow-style: none;
  }
  
  .filter-row::-webkit-scrollbar {
    display: none;
  }
  
  .filter-label {
    flex-shrink: 0;
  }
  
  .filter-btn {
    flex-shrink: 0;
    padding: 0.35rem 0.75rem;
    font-size: 0.8rem;
  }
  
  .filter-all {
    margin-bottom: 0.5rem;
  }
  
  .filter-all button {
    padding: 0.35rem 0.75rem;
    font-size: 0.8rem;
  }
}

.filter-row:last-child {
  margin-bottom: 0;
}

.filter-label {
  color: #e94560;
  font-weight: 600;
  font-size: 0.9rem;
  white-space: nowrap;
}

.filter-btn {
  padding: 0.4rem 1rem;
  background-color: #16213e;
  color: #eee;
  border: 2px solid transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.filter-btn:hover {
  background-color: #1a2744;
}

.filter-btn.active {
  background-color: rgba(233, 69, 96, 0.15);
  border-color: #e94560;
  color: #e94560;
}

.search-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  gap: 1rem;
  flex-wrap: wrap;
}

.search-input-wrapper {
  display: flex;
  flex: 1;
  min-width: 200px;
}

.search-input-wrapper input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 8px 0 0 8px;
  background-color: #16213e;
  color: #eee;
  font-size: 1rem;
}

.search-input-wrapper button {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0 8px 8px 0;
  background-color: #e94560;
  color: white;
  cursor: pointer;
  font-size: 1rem;
}

.filters {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.filters select {
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 8px;
  background-color: #16213e;
  color: #eee;
  font-size: 0.9rem;
  cursor: pointer;
}

.video-count {
  padding: 0.75rem 1rem;
  background-color: #16213e;
  border-radius: 8px;
  color: #e94560;
  font-size: 0.9rem;
  font-weight: 600;
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
  padding-top: 56.25%; /* 16:9 */
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

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 3rem;
  padding: 1rem;
}

.pagination button {
  padding: 0.5rem 1.5rem;
  background-color: #16213e;
  color: #eee;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.pagination button:hover:not(:disabled) {
  background-color: #e94560;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.stats {
  display: flex;
  justify-content: center;
  gap: 2rem;
  margin-top: 2rem;
  padding: 1rem;
  background-color: #16213e;
  border-radius: 8px;
  font-size: 0.9rem;
  color: #888;
  flex-wrap: wrap;
}

/* 骨架屏样式 */
.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.skeleton-card {
  background-color: #16213e;
  border-radius: 12px;
  overflow: hidden;
}

.skeleton-thumbnail {
  width: 100%;
  padding-top: 56.25%;
  background: linear-gradient(90deg, #16213e 25%, #0f3460 50%, #16213e 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
}

.skeleton-info {
  padding: 1rem;
}

.skeleton-title {
  height: 1.2rem;
  width: 80%;
  background: linear-gradient(90deg, #16213e 25%, #0f3460 50%, #16213e 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 4px;
  margin-bottom: 0.5rem;
}

.skeleton-meta {
  height: 0.8rem;
  width: 40%;
  background: linear-gradient(90deg, #16213e 25%, #0f3460 50%, #16213e 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
  border-radius: 4px;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 缩略图加载动画 */
.thumbnail-loading {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(15, 52, 96, 0.8);
}

.spinner-small {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: #e94560;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .search-bar {
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .search-input-wrapper {
    width: 100%;
  }
  
  .filters {
    width: 100%;
    justify-content: center;
  }
  
  .filters select {
    flex: 1;
    min-width: 120px;
  }
  
  .video-count {
    width: 100%;
    justify-content: center;
  }
  
  .video-grid,
  .skeleton-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
  }
  
  .video-card {
    border-radius: 8px;
  }
  
  .video-info h3 {
    font-size: 0.9rem;
  }
  
  .video-meta {
    font-size: 0.75rem;
  }
  
  .pagination {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .pagination button {
    width: 100%;
  }
  
  .stats {
    flex-direction: column;
    gap: 0.5rem;
    font-size: 0.8rem;
  }
  
  .empty-state {
    padding: 2rem 1rem;
  }
  
  .empty-icon {
    font-size: 3rem;
  }
}

/* 平板优化 */
@media (min-width: 769px) and (max-width: 1024px) {
  .video-grid,
  .skeleton-grid {
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  }
}
</style>
