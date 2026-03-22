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
      <div v-if="!transcodeStatus || transcodeStatus.status === 'failed'" class="unsupported-content">
        <div class="unsupported-icon">⚠️</div>
        <h3>此格式不支持浏览器播放</h3>
        <p>格式：.{{ videoInfo.format }}</p>
        <p class="hint">浏览器原生不支持 {{ videoInfo.format.toUpperCase() }} 格式</p>
        <div class="unsupported-actions">
          <button class="btn-transcode" @click="startTranscode">
            🎬 转码为 MP4
          </button>
          <a :href="downloadUrl" :download="videoInfo.file_name" class="btn-download">
            💾 下载视频
          </a>
        </div>
      </div>

      <!-- 转码中状态 -->
      <div v-else class="transcoding-status">
        <div class="transcoding-icon">🎬</div>
        <h3>视频转码中</h3>
        <p>正在将 {{ videoInfo.format.toUpperCase() }} 转换为 MP4 格式</p>
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: transcodeStatus.progress + '%' }"></div>
        </div>
        <p class="progress-text">{{ transcodeStatus.progress }}%</p>
        <p class="hint">转码完成后将自动播放</p>
        <button v-if="transcodeStatus.status === 'completed'" class="btn-reload" @click="reloadAfterTranscode">
          🔄 重新加载
        </button>
      </div>
    </div>
    
    <div class="video-details">
      <div class="video-title-wrapper">
        <h2>{{ videoInfo.file_name }}</h2>
        <button class="btn-rename" @click="showRenameDialog" title="重命名">✏️</button>
      </div>
      
      <!-- 视频信息分组 -->
      <div class="info-group">
        <h3>📊 视频信息</h3>
        <div class="video-meta">
          <div class="meta-item" v-if="videoInfo.width && videoInfo.height">
            <span class="meta-icon">📏</span>
            <span class="meta-label">分辨率</span>
            <span class="meta-value">{{ videoInfo.width }}x{{ videoInfo.height }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-icon">⏱️</span>
            <span class="meta-label">时长</span>
            <span class="meta-value">{{ formatDuration(videoInfo.duration) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-icon">💾</span>
            <span class="meta-label">大小</span>
            <span class="meta-value">{{ formatFileSize(videoInfo.file_size) }}</span>
          </div>
          <div class="meta-item" v-if="videoInfo.format">
            <span class="meta-icon">📁</span>
            <span class="meta-label">格式</span>
            <span class="meta-value">{{ videoInfo.format }}</span>
          </div>
          <div class="meta-item" v-if="videoInfo.codec">
            <span class="meta-icon">🎬</span>
            <span class="meta-label">编码</span>
            <span class="meta-value">{{ videoInfo.codec }}</span>
          </div>
        </div>
      </div>
      
      <!-- 分类和标签 -->
      <div class="info-group">
        <div class="category-tag-header">
          <h3>分类</h3>
          <button @click="showAddCategoryDialog = true" class="btn-add-small">+ 添加</button>
        </div>
        <div class="category-tags">
          <span v-if="videoCategories.length === 0" class="empty-text">暂无</span>
          <span v-for="cat in videoCategories" :key="cat.id" class="tag-item category-tag">
            {{ cat.name }}
            <span @click="removeCategory(cat.id)" class="tag-remove">×</span>
          </span>
        </div>
      </div>
      
      <div class="info-group">
        <div class="category-tag-header">
          <h3>标签</h3>
          <button @click="showAddTagDialog = true" class="btn-add-small">+ 添加</button>
        </div>
        <div class="category-tags">
          <span v-if="videoTags.length === 0" class="empty-text">暂无</span>
          <span v-for="tag in videoTags" :key="tag.id" class="tag-item">
            {{ tag.name }}
            <span @click="removeTag(tag.id)" class="tag-remove">×</span>
          </span>
        </div>
      </div>
      
      <!-- 文件信息分组 -->
      <div class="info-group">
        <h3>📂 文件信息</h3>
        <div class="video-info">
          <div class="video-path">
            <span class="meta-icon">📂</span>
            <span>{{ videoInfo.file_path }}</span>
          </div>
          <div class="video-date" v-if="videoInfo.created_at">
            <span class="meta-icon">📅</span>
            <span>添加时间：{{ formatDate(videoInfo.created_at) }}</span>
          </div>
        </div>
      </div>
      
      <!-- 操作按钮 -->
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
  
  <!-- 添加分类对话框 - 底部固定 -->
  <div class="dialog-overlay bottom-sheet" v-if="showAddCategoryDialog">
    <div class="dialog-content dialog-large">
      <div class="dialog-header">
        <h3>添加分类</h3>
        <button class="close-btn" @click="showAddCategoryDialog = false">×</button>
      </div>
      <!-- 搜索框 -->
      <div class="search-box">
        <input
          v-model="categorySearch"
          type="text"
          placeholder="搜索分类..."
          class="search-input"
        />
      </div>
      <!-- 分类网格 -->
      <div class="category-grid">
        <div
          v-for="cat in filteredCategories"
          :key="cat.id"
          class="category-card"
          :class="{ selected: selectedCategories.includes(cat.id) }"
          @click="toggleSelectedCategory(cat.id)"
        >
          <span class="check-mark" v-if="selectedCategories.includes(cat.id)">✓</span>
          <span class="category-name">{{ cat.name }}</span>
          <span v-if="cat.parent_name" class="category-parent">{{ cat.parent_name }}</span>
        </div>
      </div>
      <div class="dialog-actions">
        <button @click="saveCategories" class="btn-primary">保存</button>
      </div>
    </div>
  </div>

  <!-- 重命名对话框 - 保持居中 -->
  <div class="dialog-overlay centered" v-if="showRenameDialog">
    <div class="dialog-content">
      <h3>✏️ 重命名视频</h3>
      <div class="form-group">
        <label>新文件名</label>
        <input
          v-model="newFileName"
          type="text"
          class="form-input"
          placeholder="输入新的文件名"
          maxlength="500"
        />
      </div>
      <div class="dialog-actions">
        <button @click="showRenameDialog = false" class="btn-cancel-dialog">取消</button>
        <button @click="confirmRename" class="btn-primary-dialog">确认</button>
      </div>
    </div>
  </div>

  <!-- 添加标签对话框 - 底部固定 -->
  <div class="dialog-overlay bottom-sheet" v-if="showAddTagDialog">
    <div class="dialog-content dialog-large">
      <div class="dialog-header">
        <h3>添加标签</h3>
        <button class="close-btn" @click="showAddTagDialog = false">×</button>
      </div>
      <!-- 搜索框 -->
      <div class="search-box">
        <input
          v-model="tagSearch"
          type="text"
          placeholder="搜索标签..."
          class="search-input"
        />
      </div>
      <!-- 标签网格 -->
      <div class="tag-grid">
        <div
          v-for="tag in filteredTags"
          :key="tag.id"
          class="tag-card"
          :class="{ selected: selectedTags.includes(tag.id) }"
          @click="toggleSelectedTag(tag.id)"
        >
          <span class="check-mark" v-if="selectedTags.includes(tag.id)">✓</span>
          <span class="tag-name">{{ tag.name }}</span>
        </div>
      </div>
      <div class="dialog-actions">
        <button @click="saveTags" class="btn-primary">保存</button>
      </div>
    </div>
  </div>
</template>

<script>
import { videoApi, favoriteApi, historyApi, videoCategoryApi, videoTagApi, categoryApi, tagApi } from '../api'
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
      showContinueDialog: false,  // 显示继续观看对话框
      
      // 分类和标签
      videoCategories: [],
      videoTags: [],
      allCategories: [],
      allTags: [],
      showAddCategoryDialog: false,
      showAddTagDialog: false,
      showRenameDialog: false,
      newFileName: '',
      selectedCategories: [],
      selectedTags: [],
      
      // 搜索
      categorySearch: '',
      tagSearch: '',

      // 转码状态
      transcodeStatus: null,  // { status: 'pending'|'running'|'completed', progress: number, taskId: number }
      transcodeTimer: null,   // 轮询定时器
    }
  },
  computed: {
    downloadUrl() {
      // 返回视频文件的下载链接
      return `/api/play/${this.videoId}`
    },
    
    // 过滤后的分类
    filteredCategories() {
      let result = this.allCategories
      if (this.categorySearch) {
        const search = this.categorySearch.toLowerCase()
        result = this.allCategories.filter(cat =>
          cat.name.toLowerCase().includes(search) ||
          (cat.parent_name && cat.parent_name.toLowerCase().includes(search))
        )
      }

      // 将已选中的分类排在前面
      return result.sort((a, b) => {
        const aSelected = this.selectedCategories.includes(a.id)
        const bSelected = this.selectedCategories.includes(b.id)
        if (aSelected && !bSelected) return -1
        if (!aSelected && bSelected) return 1
        return 0
      })
    },

    // 过滤后的标签
    filteredTags() {
      let result = this.allTags
      if (this.tagSearch) {
        const search = this.tagSearch.toLowerCase()
        result = this.allTags.filter(tag => tag.name.toLowerCase().includes(search))
      }

      // 将已选中的标签排在前面
      return result.sort((a, b) => {
        const aSelected = this.selectedTags.includes(a.id)
        const bSelected = this.selectedTags.includes(b.id)
        if (aSelected && !bSelected) return -1
        if (!aSelected && bSelected) return 1
        return 0
      })
    }
  },
  mounted() {
    this.videoId = this.$route.params.id
    this.loadVideoInfo()
    this.checkFavoriteStatus()
    this.checkWatchHistory()
    this.loadVideoCategories()
    this.loadVideoTags()
    this.loadAllCategories()
    this.loadAllTags()
    // 添加键盘事件监听
    window.addEventListener('keydown', this.handleKeyDown)
  },
  beforeUnmount() {
    // 离开页面时保存进度
    this.saveProgress()
    if (this.progressTimer) {
      clearTimeout(this.progressTimer)
    }
    // 清理转码定时器
    this.clearTranscodeTimer()
    // 移除键盘事件监听
    window.removeEventListener('keydown', this.handleKeyDown)
  },
  methods: {
    async loadVideoInfo() {
      try {
        // 使用新的 API 获取播放信息
        const res = await axios.get(`/api/play/info/${this.videoId}`)
        this.videoInfo = res.data

        // 自动触发转码：如果不支持浏览器播放，自动开始转码
        if (this.videoInfo && !this.videoInfo.browser_supported) {
          console.log(`[播放页] 视频 ${this.videoId} 不支持浏览器播放，自动触发转码`)
          // 延迟一点执行，让页面先渲染
          setTimeout(() => {
            this.startTranscode()
          }, 500)
        }
      } catch (error) {
        console.error('加载视频失败:', error)
        // 处理 410 错误 - 视频文件不存在
        if (error.response?.status === 410) {
          const detail = error.response.data?.detail
          if (typeof detail === 'object') {
            window.showToast(detail.hint || detail.message || '视频文件不存在', 'error')
          } else {
            window.showToast('视频文件不存在，请检查外接硬盘是否已挂载', 'error')
          }
        } else {
          window.showToast('加载视频失败：' + (error.response?.data?.detail || error.message), 'error')
        }
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
    },
    
    // 快捷键处理
    handleKeyDown(event) {
      // 如果对话框显示中，不处理快捷键
      if (this.showContinueDialog) return
      
      const video = this.$refs.videoPlayer
      if (!video) return
      
      // 忽略输入框中的快捷键
      if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
        return
      }
      
      switch (event.code) {
        case 'Space':
          // 空格：播放/暂停
          event.preventDefault()
          if (video.paused) {
            video.play()
            window.showToast('播放', 'info')
          } else {
            video.pause()
            window.showToast('暂停', 'info')
          }
          break
        
        case 'ArrowLeft':
          // 左箭头：快退 5 秒
          event.preventDefault()
          video.currentTime -= 5
          window.showToast(`快退 5 秒`, 'info')
          break
        
        case 'ArrowRight':
          // 右箭头：快进 5 秒
          event.preventDefault()
          video.currentTime += 5
          window.showToast(`快进 5 秒`, 'info')
          break
        
        case 'ArrowUp':
          // 上箭头：音量 +10%
          event.preventDefault()
          video.volume = Math.min(1, video.volume + 0.1)
          window.showToast(`音量：${Math.round(video.volume * 100)}%`, 'info')
          break
        
        case 'ArrowDown':
          // 下箭头：音量 -10%
          event.preventDefault()
          video.volume = Math.max(0, video.volume - 0.1)
          window.showToast(`音量：${Math.round(video.volume * 100)}%`, 'info')
          break
        
        case 'KeyF':
          // F 键：全屏切换
          event.preventDefault()
          this.toggleFullscreen()
          break
        
        case 'Escape':
          // ESC：退出全屏
          if (document.fullscreenElement) {
            event.preventDefault()
            document.exitFullscreen()
          }
          break
      }
    },
    
    toggleFullscreen() {
      const container = document.querySelector('.player-container')
      if (!container) return
      
      if (!document.fullscreenElement) {
        container.requestFullscreen().catch(err => {
          console.error('全屏失败:', err)
          window.showToast('全屏失败', 'error')
        })
        window.showToast('已进入全屏', 'info')
      } else {
        document.exitFullscreen()
        window.showToast('已退出全屏', 'info')
      }
    },
    
    // 分类和标签相关方法
    async loadVideoCategories() {
      try {
        const res = await videoCategoryApi.getCategories(this.videoId)
        this.videoCategories = res.data
      } catch (error) {
        console.error('加载分类失败:', error)
      }
    },
    
    async loadVideoTags() {
      try {
        const res = await videoTagApi.getTags(this.videoId)
        this.videoTags = res.data
      } catch (error) {
        console.error('加载标签失败:', error)
      }
    },
    
    async loadAllCategories() {
      try {
        const res = await categoryApi.listCategories()
        // 扁平化分类列表
        this.allCategories = []
        const flatten = (cats, level = 0) => {
          for (const cat of cats) {
            this.allCategories.push({ ...cat, level })
            if (cat.children && cat.children.length > 0) {
              flatten(cat.children, level + 1)
            }
          }
        }
        flatten(res.data)
      } catch (error) {
        console.error('加载所有分类失败:', error)
      }
    },
    
    async loadAllTags() {
      try {
        const res = await tagApi.listTags()
        this.allTags = res.data
      } catch (error) {
        console.error('加载所有标签失败:', error)
      }
    },
    
    toggleSelectedCategory(categoryId) {
      const index = this.selectedCategories.indexOf(categoryId)
      if (index > -1) {
        this.selectedCategories.splice(index, 1)
      } else {
        this.selectedCategories.push(categoryId)
      }
    },
    
    toggleSelectedTag(tagId) {
      const index = this.selectedTags.indexOf(tagId)
      if (index > -1) {
        this.selectedTags.splice(index, 1)
      } else {
        this.selectedTags.push(tagId)
      }
    },
    
    async saveCategories() {
      try {
        await videoCategoryApi.addCategories(this.videoId, this.selectedCategories)
        window.showToast('分类已添加', 'success')
        this.showAddCategoryDialog = false
        this.selectedCategories = []
        await this.loadVideoCategories()
      } catch (error) {
        window.showToast(error.response?.data?.detail || '添加失败', 'error')
      }
    },
    
    async saveTags() {
      try {
        await videoTagApi.addTags(this.videoId, this.selectedTags)
        window.showToast('标签已添加', 'success')
        this.showAddTagDialog = false
        this.selectedTags = []
        await this.loadVideoTags()
      } catch (error) {
        window.showToast(error.response?.data?.detail || '添加失败', 'error')
      }
    },
    
    async removeCategory(categoryId) {
      if (!confirm('确定要移除此分类吗？')) return
      
      try {
        await videoCategoryApi.removeCategory(this.videoId, categoryId)
        window.showToast('分类已移除', 'success')
        await this.loadVideoCategories()
      } catch (error) {
        window.showToast('移除失败', 'error')
      }
    },
    
    async removeTag(tagId) {
      if (!confirm('确定要移除此标签吗？')) return
      
      try {
        await videoTagApi.removeTag(this.videoId, tagId)
        window.showToast('标签已移除', 'success')
        await this.loadVideoTags()
      } catch (error) {
        window.showToast('移除失败', 'error')
      }
    },
    
    // 重命名视频
    showRenameDialog() {
      this.newFileName = this.videoInfo.file_name
      this.showRenameDialog = true
    },
    
    async confirmRename() {
      if (!this.newFileName || !this.newFileName.trim()) {
        window.showToast('文件名不能为空', 'warning')
        return
      }
      
      if (this.newFileName === this.videoInfo.file_name) {
        window.showToast('文件名未改变', 'info')
        this.showRenameDialog = false
        return
      }
      
      try {
        await videoApi.renameVideo(this.videoId, { new_name: this.newFileName })
        window.showToast('重命名成功', 'success')
        this.showRenameDialog = false
        await this.loadVideoInfo()
      } catch (error) {
        window.showToast(error.response?.data?.detail || '重命名失败', 'error')
      }
    },

    // 转码相关方法
    async startTranscode() {
      if (this.transcodeStatus && this.transcodeStatus.status === 'running') {
        return
      }

      console.log(`[转码] 开始为视频 ${this.videoId} 启动转码`)
      window.showToast('正在启动转码任务...', 'info')

      try {
        // 发送请求触发转码 - 通过访问播放API自动触发
        const response = await fetch(`/api/play/${this.videoId}`)
        console.log(`[转码] 视频 ${this.videoId} 播放请求状态:`, response.status)

        if (response.status === 503) {
          const detail = await response.json()
          console.log(`[转码] 视频 ${this.videoId} 需要转码，响应详情:`, detail)

          if (detail.error === 'transcoding_required' || detail.error === 'transcoding_in_progress') {
            // 设置转码状态
            this.transcodeStatus = {
              status: detail.error === 'transcoding_required' ? 'pending' : 'running',
              progress: detail.progress || 0,
              taskId: detail.task_id
            }

            // 显示转码提示
            window.showToast(detail.message || '视频正在转码中，请稍候', 'info')

            // 开始轮询转码进度
            this.pollTranscodeStatus()
          }
        } else if (response.ok) {
          // 转码已完成或不需要转码，重新加载视频
          this.transcodeStatus = null
          window.showToast('视频可以播放了', 'success')
          this.loadVideoInfo()  // 重新加载视频信息
        } else {
          console.error(`[转码] 视频 ${this.videoId} 播放请求失败，状态码:`, response.status)
          window.showToast('启动转码失败', 'error')
        }
      } catch (err) {
        console.error(`[转码] 视频 ${this.videoId} 转码请求失败:`, err)
        window.showToast('启动转码失败', 'error')
      }
    },

    async pollTranscodeStatus() {
      console.log(`[转码] 开始轮询视频 ${this.videoId} 的转码状态`)

      // 清除现有定时器
      if (this.transcodeTimer) {
        clearInterval(this.transcodeTimer)
      }

      // 每2秒检查一次转码状态
      this.transcodeTimer = setInterval(async () => {
        try {
          const response = await fetch(`/api/transcode/status/${this.videoId}`)
          if (response.ok) {
            const data = await response.json()
            console.log(`[转码] 视频 ${this.videoId} 状态更新:`, data.status, data.progress !== undefined ? `进度: ${data.progress}%` : '')

            // 更新转码状态
            this.transcodeStatus = {
              status: data.status,
              progress: data.progress || 0,
              taskId: data.task_id
            }

            if (data.status === 'completed') {
              // 转码完成，清除状态并重新加载视频
              clearInterval(this.transcodeTimer)
              this.transcodeTimer = null
              window.showToast('转码完成，开始播放', 'success')

              // 重新加载视频信息（会更新 browser_supported 状态）
              await this.loadVideoInfo()
            } else if (data.status === 'failed') {
              clearInterval(this.transcodeTimer)
              this.transcodeTimer = null
              console.error(`[转码] 视频 ${this.videoId} 转码失败:`, data.error_message)
              window.showToast(`转码失败: ${data.error_message || '未知错误'}`, 'error')
            }
          } else {
            console.error(`[转码] 视频 ${this.videoId} 状态查询失败，状态码:`, response.status)
          }
        } catch (err) {
          console.error(`[转码] 视频 ${this.videoId} 检查转码状态失败:`, err)
        }
      }, 2000)

      // 最多轮询5分钟
      setTimeout(() => {
        if (this.transcodeTimer) {
          clearInterval(this.transcodeTimer)
          this.transcodeTimer = null
          if (this.transcodeStatus && this.transcodeStatus.status !== 'completed') {
            console.error(`[转码] 视频 ${this.videoId} 转码超时`)
            this.transcodeStatus = { status: 'failed', progress: 0, taskId: null }
            window.showToast('转码超时', 'error')
          }
        }
      }, 300000)
    },

    reloadAfterTranscode() {
      // 转码完成后重新加载页面
      this.loadVideoInfo()
    },

    // 清理转码定时器
    clearTranscodeTimer() {
      if (this.transcodeTimer) {
        clearInterval(this.transcodeTimer)
        this.transcodeTimer = null
      }
    }
  },
  watch: {
    showAddCategoryDialog(val) {
      if (val) {
        // 打开时同步当前视频的分类到选中状态
        this.selectedCategories = this.videoCategories.map(c => c.id)
      }
    },
    showAddTagDialog(val) {
      if (val) {
        // 打开时同步当前视频的标签到选中状态
        this.selectedTags = this.videoTags.map(t => t.id)
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

/* 视频标题和重命名按钮 */
.video-title-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.video-title-wrapper h2 {
  margin: 0;
  flex: 1;
}

.btn-rename {
  padding: 0.5rem;
  background-color: #16213e;
  color: #eee;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s;
  line-height: 1;
}

.btn-rename:hover {
  background-color: #e94560;
}

/* 重命名对话框 */
.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  color: #e94560;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.form-input {
  width: 100%;
  padding: 0.75rem 1rem;
  background-color: #16213e;
  border: 2px solid #0f3460;
  border-radius: 8px;
  color: #eee;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-input:focus {
  outline: none;
  border-color: #e94560;
}

.btn-primary-dialog {
  padding: 0.75rem 2rem;
  background-color: #e94560;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s;
}

.btn-primary-dialog:hover {
  background-color: #d63d56;
}

.btn-cancel-dialog {
  padding: 0.75rem 2rem;
  background-color: #16213e;
  color: #eee;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s;
}

.btn-cancel-dialog:hover {
  background-color: #0f3460;
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

/* 转码相关样式 */
.unsupported-content {
  padding: 2rem;
}

.unsupported-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 1.5rem;
  flex-wrap: wrap;
}

.btn-transcode {
  display: inline-block;
  padding: 1rem 2rem;
  background-color: #e94560;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-transcode:hover {
  background-color: #ff6b6b;
}

.transcoding-status {
  padding: 2rem;
}

.transcoding-icon {
  font-size: 5rem;
  margin-bottom: 1rem;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.8;
    transform: scale(1.1);
  }
}

.transcoding-status h3 {
  color: #4caf50;
  margin-bottom: 1rem;
}

.progress-bar {
  width: 80%;
  max-width: 400px;
  height: 20px;
  background-color: #0f3460;
  border-radius: 10px;
  margin: 1.5rem auto;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4caf50, #8bc34a);
  border-radius: 10px;
  transition: width 0.5s ease;
}

.progress-text {
  font-size: 1.2rem;
  color: #4caf50;
  font-weight: bold;
  margin: 0.5rem 0;
}

.btn-reload {
  display: inline-block;
  padding: 1rem 2rem;
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: background-color 0.3s;
  margin-top: 1rem;
}

.btn-reload:hover {
  background-color: #45a049;
}

.video-details {
  background-color: #16213e;
  padding: 1.5rem;
  border-radius: 12px;
}

.video-details h2 {
  margin-bottom: 1.5rem;
  font-size: 1.3rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #0f3460;
}

/* 信息分组 */
.info-group {
  margin-bottom: 1.5rem;
}

.info-group h3 {
  font-size: 1rem;
  color: #e94560;
  margin-bottom: 1rem;
  font-weight: 600;
}

.video-meta {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background-color: #0f3460;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.meta-item:hover {
  background-color: #16213e;
}

.meta-icon {
  font-size: 1.2rem;
}

.meta-label {
  color: #888;
  font-size: 0.85rem;
  min-width: 50px;
}

.meta-value {
  color: #eee;
  font-size: 0.95rem;
  font-weight: 500;
  word-break: break-word;
}

.video-info {
  margin-top: 0.5rem;
}

.video-path {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: #888;
  word-break: break-all;
  margin-bottom: 0.75rem;
  padding: 0.75rem;
  background-color: #0f3460;
  border-radius: 8px;
}

.video-path .meta-icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.video-date {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #666;
  padding: 0.5rem 0.75rem;
  background-color: #0f3460;
  border-radius: 8px;
}

.video-date .meta-icon {
  font-size: 1rem;
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

/* 分类和标签样式 */
.category-tag-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.category-tag-header h3 {
  margin: 0;
  font-size: 0.9rem;
  color: #e94560;
}

.btn-add-small {
  padding: 0.25rem 0.6rem;
  background-color: #e94560;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.75rem;
  transition: background-color 0.3s;
}

.btn-add-small:hover {
  background-color: #ff6b6b;
}

.category-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.empty-text {
  color: #888;
  font-size: 0.8rem;
}

.tag-item {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.3rem 0.6rem;
  background-color: #0f3460;
  border-radius: 4px;
  font-size: 0.8rem;
  transition: background-color 0.3s;
}

.tag-item:hover {
  background-color: #16213e;
}

.category-tag {
  background-color: #16213e;
}

.tag-remove {
  cursor: pointer;
  color: #888;
  font-size: 1rem;
  line-height: 1;
  transition: color 0.3s;
}

.tag-remove:hover {
  color: #e94560;
}

/* 分类/标签选择对话框 - 底部固定 */
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

/* 居中对话框（重命名等） */
.dialog-overlay.centered {
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

/* 居中对话框的内容样式 */
.dialog-overlay.centered .dialog-content {
  height: auto;
  border-radius: 12px;
  padding: 2rem;
  max-width: 400px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.dialog-overlay.centered .dialog-content h3 {
  color: #e94560;
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
}

.dialog-large {
  max-width: 800px;
  min-height: 400px;
}

/* 居中对话框的搜索框 */
.dialog-overlay.centered .search-box {
  margin-bottom: 1.5rem;
}

.dialog-overlay.centered .search-input {
  width: 100%;
  padding: 0.875rem 1.25rem;
  border: 2px solid #0f3460;
  border-radius: 10px;
  background-color: #0f3460;
  color: #eee;
  font-size: 1rem;
  outline: none;
  transition: all 0.3s ease;
}

.dialog-overlay.centered .search-input:focus {
  border-color: #e94560;
  box-shadow: 0 0 0 4px rgba(233, 69, 96, 0.1);
}

.dialog-overlay.centered .search-input::placeholder {
  color: #888;
}

/* 底部固定对话框的搜索框 */
.search-box {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #30363d;
}

.search-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 2px solid #0f3460;
  border-radius: 8px;
  background-color: #0f3460;
  color: #eee;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.3s;
}

.search-input:focus {
  border-color: #e94560;
}

.search-input::placeholder {
  color: #888;
}

/* 底部固定对话框的网格 */
.category-grid,
.tag-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
  padding: 1rem;
  overflow-y: auto;
  flex: 1;
}

@media (min-width: 769px) {
  .category-grid,
  .tag-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* 底部固定对话框的按钮 */
.dialog-actions {
  display: flex;
  justify-content: center;
  padding: 1rem;
  border-top: 1px solid #30363d;
  background-color: #16213e;
}

.btn-primary {
  padding: 0.75rem 2rem;
  background-color: #e94560;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s;
}

.btn-primary:hover {
  background-color: #ff6b6b;
}

/* 居中对话框的分类网格 */
.dialog-overlay.centered .category-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
  max-height: 400px;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0.5rem;
}

@media (max-width: 768px) {
  .dialog-overlay.centered .category-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 480px) {
  .dialog-overlay.centered .category-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.dialog-overlay.centered .category-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0.6rem 0.8rem;
  background-color: #0f3460;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
  border: 2px solid transparent;
  min-height: 50px;
  flex: 1;
}

.dialog-overlay.centered .category-card:hover {
  background-color: #16213e;
  transform: translateY(-2px);
  border-color: rgba(233, 69, 96, 0.3);
}

.dialog-overlay.centered .category-card.selected {
  background-color: rgba(233, 69, 96, 0.15);
  border-color: #e94560;
  box-shadow: 0 4px 12px rgba(233, 69, 96, 0.3);
}

.dialog-overlay.centered .category-card .category-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: #eee;
  word-break: break-word;
  line-height: 1.3;
}

.dialog-overlay.centered .category-parent {
  font-size: 0.7rem;
  color: #888;
  margin-top: 0.2rem;
  word-break: break-word;
}

.dialog-overlay.centered .category-card.selected .category-name {
  color: #e94560;
}

.dialog-overlay.centered .category-card.selected .category-parent {
  color: rgba(233, 69, 96, 0.8);
}

/* 居中对话框的标签网格 */
.dialog-overlay.centered .tag-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
  max-height: 400px;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0.5rem;
}

@media (max-width: 768px) {
  .dialog-overlay.centered .tag-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 480px) {
  .dialog-overlay.centered .tag-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.dialog-overlay.centered .tag-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0.6rem 0.8rem;
  background-color: #0f3460;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid transparent;
  min-height: 50px;
}

.dialog-overlay.centered .tag-card:hover {
  background-color: #16213e;
  transform: translateY(-2px);
  border-color: rgba(233, 69, 96, 0.3);
}

.dialog-overlay.centered .tag-card.selected {
  background-color: rgba(233, 69, 96, 0.15);
  border-color: #e94560;
  box-shadow: 0 4px 12px rgba(233, 69, 96, 0.3);
}

.dialog-overlay.centered .tag-card .tag-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: #eee;
  word-break: break-word;
  line-height: 1.3;
}

/* 居中对话框的按钮 */
.dialog-overlay.centered .dialog-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.dialog-overlay.centered .dialog-buttons button {
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s;
}

.dialog-overlay.centered .btn-cancel {
  background-color: #0f3460;
  color: #eee;
}

.dialog-overlay.centered .btn-cancel:hover {
  background-color: #16213e;
}

.dialog-overlay.centered .btn-continue {
  background-color: #e94560;
  color: white;
}

.dialog-overlay.centered .btn-continue:hover {
  background-color: #ff6b6b;
}

.dialog-overlay.centered .dialog-actions {
  display: flex;
  justify-content: center;
  gap: 1.25rem;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #0f3460;
}

.dialog-overlay.centered .btn-cancel-dialog,
.dialog-overlay.centered .btn-primary {
  padding: 0.875rem 2.5rem;
  min-width: 120px;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 10px;
  cursor: pointer;
  border: 2px solid;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.dialog-overlay.centered .btn-cancel-dialog {
  background-color: #0f3460;
  color: #eee;
  border-color: #0f3460;
}

.dialog-overlay.centered .btn-cancel-dialog:hover {
  background-color: #16213e;
  border-color: #16213e;
  transform: translateY(-2px);
}

.dialog-overlay.centered .btn-primary {
  background-color: #e94560;
  color: white;
  border-color: #e94560;
}

.dialog-overlay.centered .btn-primary:hover {
  background-color: #ff6b6b;
  border-color: #ff6b6b;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(233, 69, 96, 0.4);
}

/* 底部固定对话框的卡片样式 */
.category-card,
.tag-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0.6rem 0.8rem;
  background-color: #0f3460;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: center;
  border: 2px solid transparent;
  min-height: 50px;
  gap: 0.2rem;
}

/* 选中状态时，内容区域左对齐以容纳勾选标记 */
.category-card:hover,
.tag-card:hover {
  background-color: #16213e;
  transform: translateY(-2px);
  border-color: rgba(233, 69, 96, 0.3);
}

.category-card.selected,
.tag-card.selected {
  background-color: rgba(233, 69, 96, 0.25);
  border-color: #e94560;
  box-shadow: 0 4px 12px rgba(233, 69, 96, 0.4);
  align-items: flex-start;
  text-align: left;
}

/* 已选中项的勾选标记 */
.check-mark {
  display: inline;
  color: #e94560;
  font-weight: bold;
  font-size: 1.1em;
  line-height: 1.3;
  vertical-align: middle;
}

.category-card .category-name,
.tag-card .tag-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: #eee;
  word-break: break-word;
  line-height: 1.3;
  display: inline;
}

/* 勾选标记和名称在同一行 */
.category-card.selected .category-name,
.tag-card.selected .tag-name {
  display: inline;
  margin-left: 0.2rem;
}

.category-parent {
  font-size: 0.7rem;
  color: #888;
  margin-top: 0.2rem;
  word-break: break-word;
}

.category-card.selected .category-name {
  color: #e94560;
}

.category-card.selected .category-parent {
  color: rgba(233, 69, 96, 0.8);
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

/* 继续观看对话框 - 保持居中 */
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

.continue-dialog .dialog-content {
  background-color: #16213e;
  padding: 2rem;
  border-radius: 12px;
  text-align: center;
  max-width: 400px;
  width: 90%;
}

.continue-dialog h3 {
  color: #e94560;
  margin-bottom: 1rem;
  font-size: 1.5rem;
}

.continue-dialog p {
  color: #eee;
  margin-bottom: 2rem;
  font-size: 1rem;
}

.continue-dialog .dialog-buttons {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.continue-dialog .dialog-buttons button {
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s;
}

.continue-dialog .btn-cancel {
  background-color: #0f3460;
  color: #eee;
}

.continue-dialog .btn-cancel:hover {
  background-color: #16213e;
}

.continue-dialog .btn-continue {
  background-color: #e94560;
  color: white;
}

.continue-dialog .btn-continue:hover {
  background-color: #ff6b6b;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .video-player {
    padding: 0.5rem;
  }
  
  .player-header {
    flex-direction: row;
    gap: 0.5rem;
  }
  
  .back-btn,
  .favorite-btn {
    padding: 0.5rem 1rem;
    font-size: 0.9rem;
  }
  
  .video-details {
    padding: 1rem;
  }
  
  .video-details h2 {
    font-size: 1.1rem;
  }
  
  .info-group h3 {
    font-size: 0.95rem;
  }
  
  .video-meta {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
  
  .meta-item {
    padding: 0.6rem;
  }
  
  .meta-label {
    min-width: 45px;
    font-size: 0.8rem;
  }
  
  .meta-value {
    font-size: 0.9rem;
  }
  
  .video-path {
    font-size: 0.8rem;
    padding: 0.6rem;
  }
  
  .video-date {
    font-size: 0.75rem;
  }
  
  .btn-delete {
    padding: 0.75rem 1.5rem;
    font-size: 0.9rem;
    width: 100%;
    justify-content: center;
  }
  
  .dialog-content {
    padding: 1.5rem;
    max-width: 90%;
  }
  
  .dialog-content h3 {
    font-size: 1.2rem;
  }
  
  .dialog-content p {
    font-size: 0.9rem;
  }
  
  .dialog-buttons {
    flex-direction: column;
  }
  
  .dialog-buttons button {
    width: 100%;
    padding: 0.75rem;
  }
  
  .unsupported-icon {
    font-size: 3rem;
  }
  
  .btn-download {
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    width: 100%;
    box-sizing: border-box;
    text-align: center;
  }

  .unsupported-actions {
    flex-direction: column;
  }

  .btn-transcode {
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    width: 100%;
    box-sizing: border-box;
  }

  .btn-reload {
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
    width: 100%;
    box-sizing: border-box;
  }

  .transcoding-icon {
    font-size: 3rem;
  }

  .progress-bar {
    width: 90%;
  }
}

/* 小屏幕手机 */
@media (max-width: 480px) {
  .back-btn,
  .favorite-btn {
    flex: 1;
    font-size: 0.85rem;
  }
  
  .video-details h2 {
    font-size: 1rem;
  }
  
  .meta-item {
    flex-wrap: wrap;
  }
  
  .meta-label {
    font-size: 0.75rem;
  }
  
  .meta-value {
    font-size: 0.85rem;
  }
}
</style>
