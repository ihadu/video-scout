<template>
  <div class="tag-management">
    <div class="header">
      <h2>🏷️ 标签管理</h2>
      <button @click="showCreateDialog = true" class="btn-primary">+ 新建标签</button>
    </div>
    
    <!-- 标签列表 -->
    <div class="tag-list" v-if="tags.length > 0">
      <div class="tag-item" v-for="tag in tags" :key="tag.id">
        <div class="tag-info">
          <span class="tag-color" :style="{ backgroundColor: tag.color }"></span>
          <span class="tag-name">{{ tag.name }}</span>
          <span class="tag-count">({{ tag.video_count }})</span>
        </div>
        <div class="tag-actions">
          <button @click="editTag(tag)" class="btn-small">编辑</button>
          <button @click="deleteTag(tag)" class="btn-small btn-danger">删除</button>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div class="empty-state" v-else>
      <div class="empty-icon">🏷️</div>
      <p>暂无标签</p>
      <p class="empty-hint">点击"新建标签"开始管理</p>
    </div>
    
    <!-- 创建/编辑对话框 -->
    <div class="dialog-overlay" v-if="showCreateDialog">
      <div class="dialog-content">
        <h3>{{ editingTag ? '编辑标签' : '新建标签' }}</h3>
        <div class="form-group">
          <label>标签名称</label>
          <input v-model="formData.name" type="text" placeholder="例如：热血、治愈、完结" />
        </div>
        <div class="form-group">
          <label>颜色</label>
          <div class="color-picker">
            <input type="color" v-model="formData.color" />
            <input type="text" v-model="formData.color" placeholder="#e94560" />
          </div>
        </div>
        <div class="dialog-actions">
          <button @click="showCreateDialog = false" class="btn-secondary">取消</button>
          <button @click="saveTag" class="btn-primary">{{ editingTag ? '保存' : '创建' }}</button>
        </div>
      </div>
    </div>
  </div>
  
  <!-- 底部导航栏（仅移动端） -->
  <BottomNavigation />
</template>

<script>
import { tagApi } from '../api'
import BottomNavigation from '../components/BottomNavigation.vue'

export default {
  name: 'TagManagement',
  components: {
    BottomNavigation
  },
  data() {
    return {
      tags: [],
      showCreateDialog: false,
      editingTag: null,
      formData: {
        name: '',
        color: '#e94560'
      }
    }
  },
  mounted() {
    this.loadTags()
  },
  methods: {
    async loadTags() {
      try {
        const res = await tagApi.listTags()
        this.tags = res.data
      } catch (error) {
        window.showToast('加载标签失败', 'error')
      }
    },
    
    editTag(tag) {
      this.editingTag = tag
      this.formData = {
        name: tag.name,
        color: tag.color
      }
      this.showCreateDialog = true
    },
    
    async saveTag() {
      if (!this.formData.name) {
        window.showToast('请输入标签名称', 'warning')
        return
      }
      
      try {
        if (this.editingTag) {
          await tagApi.updateTag(this.editingTag.id, this.formData)
          window.showToast('标签已更新', 'success')
        } else {
          await tagApi.createTag(this.formData)
          window.showToast('标签已创建', 'success')
        }
        
        this.showCreateDialog = false
        this.editingTag = null
        this.formData = { name: '', color: '#e94560' }
        await this.loadTags()
        
        // 刷新缓存
        await this.refreshCache()
      } catch (error) {
        window.showToast(error.response?.data?.detail || '操作失败', 'error')
      }
    },
    
    async deleteTag(tag) {
      if (!confirm(`确定要删除标签 "${tag.name}" 吗？`)) return
      
      try {
        await tagApi.deleteTag(tag.id)
        window.showToast('标签已删除', 'success')
        await this.loadTags()
        
        // 刷新缓存
        await this.refreshCache()
      } catch (error) {
        window.showToast(error.response?.data?.detail || '删除失败', 'error')
      }
    },
    
    async refreshCache() {
      try {
        const res = await tagApi.listTags()
        localStorage.setItem('video_tags', JSON.stringify(res.data))
      } catch (error) {
        console.error('刷新缓存失败:', error)
      }
    }
  }
}
</script>

<style scoped>
.tag-management {
  max-width: 900px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.header h2 {
  margin: 0;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
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

.tag-list {
  display: grid;
  gap: 1rem;
}

.tag-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.5rem;
  background-color: #16213e;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.tag-item:hover {
  background-color: #0f3460;
}

.tag-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.tag-color {
  width: 24px;
  height: 24px;
  border-radius: 4px;
}

.tag-name {
  font-size: 1.1rem;
  font-weight: 500;
}

.tag-count {
  color: #888;
  font-size: 0.9rem;
}

.tag-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-small {
  padding: 0.4rem 0.8rem;
  background-color: #0f3460;
  color: #eee;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: background-color 0.3s;
}

.btn-small:hover:not(:disabled) {
  background-color: #e94560;
}

.btn-small:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-small.btn-danger {
  background-color: #c62828;
}

.btn-small.btn-danger:hover:not(:disabled) {
  background-color: #ff5252;
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

/* 对话框样式 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.dialog-content {
  background-color: #16213e;
  padding: 2rem;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
}

.dialog-content h3 {
  margin: 0 0 1.5rem 0;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #aaa;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 8px;
  background-color: #0f3460;
  color: #eee;
  font-size: 1rem;
}

.color-picker {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.color-picker input[type="color"] {
  width: 60px;
  height: 40px;
  padding: 0;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.color-picker input[type="text"] {
  flex: 1;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background-color: #0f3460;
  color: #eee;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s;
}

.btn-secondary:hover {
  background-color: #16213e;
}

@media (max-width: 768px) {
  .tag-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .tag-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .dialog-content {
    padding: 1.5rem;
  }
}
</style>
