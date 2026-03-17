<template>
  <div class="category-management">
    <div class="header">
      <h2>📁 分类管理</h2>
      <button @click="showCreateDialog = true" class="btn-primary">+ 新建分类</button>
    </div>
    
    <!-- 分类树 -->
    <div class="category-tree" v-if="categories.length > 0">
      <div v-for="category in categories" :key="category.id">
        <div class="category-item" :style="{ marginLeft: getCategoryLevel(category) * 20 + 'px' }">
          <div class="category-info">
            <span class="category-icon">{{ category.icon || '📁' }}</span>
            <span class="category-name">{{ category.name }}</span>
            <span class="category-count">({{ category.video_count }})</span>
          </div>
          <div class="category-actions">
            <button @click="editCategory(category)" class="btn-small">编辑</button>
            <button @click="deleteCategory(category)" class="btn-small btn-danger" :disabled="category.children.length > 0">
              删除
            </button>
          </div>
        </div>
        <!-- 递归渲染子分类 -->
        <div v-if="category.children.length > 0">
          <div v-for="child in category.children" :key="child.id">
            <div class="category-item" :style="{ marginLeft: (getCategoryLevel(child) * 20) + 'px' }">
              <div class="category-info">
                <span class="category-icon">{{ child.icon || '📁' }}</span>
                <span class="category-name">{{ child.name }}</span>
                <span class="category-count">({{ child.video_count }})</span>
              </div>
              <div class="category-actions">
                <button @click="editCategory(child)" class="btn-small">编辑</button>
                <button @click="deleteCategory(child)" class="btn-small btn-danger" :disabled="child.children.length > 0">
                  删除
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div class="empty-state" v-else>
      <div class="empty-icon">📁</div>
      <p>暂无分类</p>
      <p class="empty-hint">点击"新建分类"开始管理</p>
    </div>
    
    <!-- 创建/编辑对话框 -->
    <div class="dialog-overlay" v-if="showCreateDialog">
      <div class="dialog-content">
        <h3>{{ editingCategory ? '编辑分类' : '新建分类' }}</h3>
        <div class="form-group">
          <label>分类名称</label>
          <input v-model="formData.name" type="text" placeholder="例如：动漫、电影" />
        </div>
        <div class="form-group">
          <label>父分类（可选）</label>
          <select v-model="formData.parent_id">
            <option :value="null">无（一级分类）</option>
            <option v-for="cat in flatCategories" :key="cat.id" :value="cat.id">
              {{ ' '.repeat(cat.level || 0) + (cat.icon || '📁') + ' ' + cat.name }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>图标（emoji）</label>
          <input v-model="formData.icon" type="text" placeholder="例如：📺、🎬" />
        </div>
        <div class="form-group">
          <label>排序</label>
          <input v-model.number="formData.sort_order" type="number" placeholder="数字越小越靠前" />
        </div>
        <div class="dialog-actions">
          <button @click="showCreateDialog = false" class="btn-secondary">取消</button>
          <button @click="saveCategory" class="btn-primary">{{ editingCategory ? '保存' : '创建' }}</button>
        </div>
      </div>
    </div>
  </div>
  
  <!-- 底部导航栏（仅移动端） -->
  <BottomNavigation />
</template>

<script>
import { categoryApi } from '../api'
import BottomNavigation from '../components/BottomNavigation.vue'

export default {
  name: 'CategoryManagement',
  components: {
    BottomNavigation
  },
  data() {
    return {
      categories: [],
      showCreateDialog: false,
      editingCategory: null,
      formData: {
        name: '',
        parent_id: null,
        icon: '',
        sort_order: 0
      }
    }
  },
  computed: {
    flatCategories() {
      // 扁平化分类树，用于下拉选择
      const result = []
      
      const flatten = (cats, level = 0) => {
        for (const cat of cats) {
          result.push({ ...cat, level })
          if (cat.children && cat.children.length > 0) {
            flatten(cat.children, level + 1)
          }
        }
      }
      
      flatten(this.categories)
      return result
    }
  },
  mounted() {
    this.loadCategories()
  },
  methods: {
    async loadCategories() {
      try {
        const res = await categoryApi.listCategories()
        this.categories = res.data
      } catch (error) {
        window.showToast('加载分类失败', 'error')
      }
    },
    
    getCategoryLevel(category) {
      let level = 0
      let current = category
      while (current.parent_id) {
        level++
        // 查找父分类
        const findParent = (cats) => {
          for (const cat of cats) {
            if (cat.id === current.parent_id) return cat
            if (cat.children) {
              const found = findParent(cat.children)
              if (found) return found
            }
          }
          return null
        }
        current = findParent(this.categories)
        if (!current) break
      }
      return level
    },
    
    editCategory(category) {
      this.editingCategory = category
      this.formData = {
        name: category.name,
        parent_id: category.parent_id,
        icon: category.icon,
        sort_order: category.sort_order
      }
      this.showCreateDialog = true
    },
    
    async saveCategory() {
      if (!this.formData.name) {
        window.showToast('请输入分类名称', 'warning')
        return
      }
      
      try {
        if (this.editingCategory) {
          await categoryApi.updateCategory(this.editingCategory.id, this.formData)
          window.showToast('分类已更新', 'success')
        } else {
          await categoryApi.createCategory(this.formData)
          window.showToast('分类已创建', 'success')
        }
        
        this.showCreateDialog = false
        this.editingCategory = null
        this.formData = { name: '', parent_id: null, icon: '', sort_order: 0 }
        await this.loadCategories()
        
        // 刷新缓存
        await this.refreshCache()
      } catch (error) {
        window.showToast(error.response?.data?.detail || '操作失败', 'error')
      }
    },
    
    async deleteCategory(category) {
      if (category.children.length > 0) {
        window.showToast('请先删除子分类', 'warning')
        return
      }
      
      if (!confirm(`确定要删除分类 "${category.name}" 吗？`)) return
      
      try {
        await categoryApi.deleteCategory(category.id)
        window.showToast('分类已删除', 'success')
        await this.loadCategories()
        
        // 刷新缓存
        await this.refreshCache()
      } catch (error) {
        window.showToast(error.response?.data?.detail || '删除失败', 'error')
      }
    },
    
    async refreshCache() {
      try {
        const res = await categoryApi.listCategories()
        const rootCategories = res.data.filter(cat => cat.parent_id === null)
        localStorage.setItem('video_categories', JSON.stringify(rootCategories))
      } catch (error) {
        console.error('刷新缓存失败:', error)
      }
    }
  }
}
</script>

<style scoped>
.category-management {
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

.category-tree {
  background-color: #16213e;
  padding: 1.5rem;
  border-radius: 12px;
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  margin: 0.5rem 0;
  background-color: #0f3460;
  border-radius: 8px;
  transition: background-color 0.3s;
}

.category-item:hover {
  background-color: #16213e;
}

.category-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.category-icon {
  font-size: 1.5rem;
}

.category-name {
  font-size: 1.1rem;
  font-weight: 500;
}

.category-count {
  color: #888;
  font-size: 0.9rem;
}

.category-actions {
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

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 8px;
  background-color: #0f3460;
  color: #eee;
  font-size: 1rem;
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
  .category-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }
  
  .category-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .dialog-content {
    padding: 1.5rem;
  }
}
</style>
