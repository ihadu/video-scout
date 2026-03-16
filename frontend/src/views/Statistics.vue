<template>
  <div class="statistics">
    <div class="page-header">
      <h2>📊 视频统计</h2>
      <button class="refresh-btn" @click="loadStats" :disabled="loading">
        {{ loading ? '加载中...' : '刷新' }}
      </button>
    </div>
    
    <!-- 概览卡片 -->
    <div class="overview-cards">
      <div class="card">
        <div class="card-icon">🎬</div>
        <div class="card-content">
          <div class="card-value">{{ stats.total_videos || 0 }}</div>
          <div class="card-label">总视频数</div>
        </div>
      </div>
      
      <div class="card">
        <div class="card-icon">⏱️</div>
        <div class="card-content">
          <div class="card-value">{{ stats.total_duration_formatted || '0 小时' }}</div>
          <div class="card-label">总时长</div>
        </div>
      </div>
      
      <div class="card">
        <div class="card-icon">💾</div>
        <div class="card-content">
          <div class="card-value">{{ stats.total_size_formatted || '0 B' }}</div>
          <div class="card-label">总大小</div>
        </div>
      </div>
    </div>
    
    <!-- 分类分布 -->
    <div class="stats-section">
      <h3>📁 分类分布</h3>
      <div class="distribution-list">
        <div 
          v-for="item in stats.category_distribution" 
          :key="item.name" 
          class="distribution-item"
        >
          <span class="item-name">{{ item.name }}</span>
          <div class="item-bar-wrapper">
            <div 
              class="item-bar" 
              :style="{ width: getPercentage(item.count, stats.category_distribution) + '%' }"
            ></div>
          </div>
          <span class="item-count">{{ item.count }}</span>
        </div>
        <div v-if="!stats.category_distribution || stats.category_distribution.length === 0" class="empty-state">
          暂无分类数据
        </div>
      </div>
    </div>
    
    <!-- 标签云 -->
    <div class="stats-section">
      <h3>🏷️ 标签云</h3>
      <div class="tag-cloud">
        <span 
          v-for="tag in stats.tag_cloud" 
          :key="tag.name" 
          class="tag-item"
          :style="{ fontSize: getTagFontSize(tag.count, stats.tag_cloud) + 'px' }"
        >
          {{ tag.name }} ({{ tag.count }})
        </span>
        <div v-if="!stats.tag_cloud || stats.tag_cloud.length === 0" class="empty-state">
          暂无标签数据
        </div>
      </div>
    </div>
    
    <!-- 格式分布 -->
    <div class="stats-section">
      <h3>🎥 格式分布</h3>
      <div class="distribution-list">
        <div 
          v-for="item in stats.format_distribution" 
          :key="item.format" 
          class="distribution-item"
        >
          <span class="item-name">{{ item.format }}</span>
          <div class="item-bar-wrapper">
            <div 
              class="item-bar" 
              :style="{ width: getPercentage(item.count, stats.format_distribution) + '%' }"
            ></div>
          </div>
          <span class="item-count">{{ item.count }}</span>
        </div>
        <div v-if="!stats.format_distribution || stats.format_distribution.length === 0" class="empty-state">
          暂无格式数据
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import videoApi from '../api/index.js'

export default {
  name: 'Statistics',
  data() {
    return {
      stats: {},
      loading: false
    }
  },
  mounted() {
    this.loadStats()
  },
  methods: {
    async loadStats() {
      this.loading = true
      try {
        const res = await videoApi.getStats()
        this.stats = res.data
      } catch (error) {
        console.error('加载统计失败:', error)
        window.showToast('加载统计失败', 'error')
      } finally {
        this.loading = false
      }
    },
    
    getPercentage(count, items) {
      if (!items || items.length === 0) return 0
      const max = Math.max(...items.map(i => i.count))
      return max > 0 ? (count / max) * 100 : 0
    },
    
    getTagFontSize(count, items) {
      if (!items || items.length === 0) return 14
      const min = Math.min(...items.map(i => i.count))
      const max = Math.max(...items.map(i => i.count))
      const range = max - min || 1
      const scale = (count - min) / range
      return 12 + scale * 12  // 12px - 24px
    }
  }
}
</script>

<style scoped>
.statistics {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-header h2 {
  margin: 0;
  color: #e94560;
  font-size: 1.8rem;
}

.refresh-btn {
  padding: 0.5rem 1.5rem;
  background-color: #e94560;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.refresh-btn:hover:not(:disabled) {
  background-color: #d63d56;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 概览卡片 */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.card {
  background-color: #16213e;
  border-radius: 12px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.card:hover {
  transform: translateY(-4px);
}

.card-icon {
  font-size: 2.5rem;
}

.card-content {
  flex: 1;
}

.card-value {
  font-size: 1.8rem;
  font-weight: bold;
  color: #eee;
  margin-bottom: 0.25rem;
}

.card-label {
  color: #888;
  font-size: 0.9rem;
}

/* 统计区块 */
.stats-section {
  background-color: #16213e;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.stats-section h3 {
  color: #e94560;
  margin: 0 0 1.5rem 0;
  font-size: 1.3rem;
}

/* 分布列表 */
.distribution-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.distribution-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.item-name {
  min-width: 120px;
  color: #eee;
  font-size: 0.9rem;
}

.item-bar-wrapper {
  flex: 1;
  background-color: #0f3460;
  border-radius: 4px;
  height: 24px;
  overflow: hidden;
}

.item-bar {
  height: 100%;
  background: linear-gradient(90deg, #e94560, #ff6b6b);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.item-count {
  min-width: 50px;
  text-align: right;
  color: #e94560;
  font-weight: bold;
  font-size: 0.9rem;
}

/* 标签云 */
.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.tag-item {
  padding: 0.5rem 1rem;
  background-color: #0f3460;
  color: #eee;
  border-radius: 20px;
  cursor: default;
  transition: all 0.3s ease;
}

.tag-item:hover {
  background-color: #e94560;
  transform: scale(1.05);
}

/* 空状态 */
.empty-state {
  text-align: center;
  color: #666;
  padding: 2rem;
  font-size: 0.9rem;
}

/* 响应式 */
@media (max-width: 768px) {
  .statistics {
    padding: 1rem;
  }
  
  .overview-cards {
    grid-template-columns: 1fr;
  }
  
  .item-name {
    min-width: 80px;
    font-size: 0.8rem;
  }
  
  .item-count {
    min-width: 40px;
    font-size: 0.8rem;
  }
}
</style>
