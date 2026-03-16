<template>
  <div class="scan-management">
    <h2>📁 扫描目录管理</h2>
    
    <!-- 添加目录表单 -->
    <div class="add-directory-form">
      <h3>添加扫描目录</h3>
      <form @submit.prevent="addDirectory">
        <div class="form-group">
          <label>目录路径</label>
          <input 
            v-model="newDirectory.path" 
            type="text" 
            placeholder="/path/to/videos"
            required
          />
        </div>
        <div class="form-group">
          <label>目录名称（可选）</label>
          <input 
            v-model="newDirectory.name" 
            type="text" 
            placeholder="我的视频库"
          />
        </div>
        <button type="submit" class="btn-primary" :disabled="adding">
          {{ adding ? '添加中...' : '添加目录' }}
        </button>
      </form>
    </div>
    
    <!-- 全局操作按钮 -->
    <div class="global-actions" v-if="directories.length > 0">
      <button 
        @click="verifyAllDirectories" 
        class="btn-secondary"
        :disabled="verifying"
      >
        🔍 {{ verifying ? '检查中...' : '完整性检查' }}
      </button>
      
      <button 
        @click="cleanInvalidVideos" 
        class="btn-warning"
        :disabled="cleaning"
      >
        🧹 {{ cleaning ? '清理中...' : '清理无效记录' }}
      </button>
      
      <div class="stats-info" v-if="invalidStats">
        <span>无效记录：<strong>{{ invalidStats.invalid_videos }}</strong></span>
        <span>总记录：<strong>{{ invalidStats.total_videos }}</strong></span>
      </div>
    </div>
    
    <!-- 目录列表 -->
    <div class="directory-list" v-if="directories.length > 0">
      <h3>已添加的目录 ({{ directories.length }})</h3>
      
      <div class="directory-card" v-for="dir in directories" :key="dir.id">
        <div class="directory-header">
          <h4>{{ dir.name }}</h4>
          <span :class="['status-badge', dir.is_active ? 'active' : 'inactive']">
            {{ dir.is_active ? '活跃' : '禁用' }}
          </span>
        </div>
        
        <div class="directory-path">
          📂 {{ dir.path }}
        </div>
        
        <div class="directory-last-scanned" v-if="dir.last_scanned">
          最后扫描：{{ formatDate(dir.last_scanned) }}
        </div>
        
        <!-- 扫描进度 -->
        <div class="scan-progress" v-if="dir.scan_task">
          <div class="progress-header">
            <span>扫描进度</span>
            <span>{{ dir.scan_task.progress }}%</span>
          </div>
          <div class="progress-bar">
            <div 
              class="progress-fill" 
              :style="{ width: dir.scan_task.progress + '%' }"
              :class="dir.scan_task.status"
            ></div>
          </div>
          <div class="progress-details">
            <span v-if="dir.scan_task.scanned_count">
              已扫描：{{ dir.scan_task.scanned_count }}
            </span>
            <span v-if="dir.scan_task.success_count">
              成功：{{ dir.scan_task.success_count }}
            </span>
            <span v-if="dir.scan_task.failed_count">
              失败：{{ dir.scan_task.failed_count }}
            </span>
            <span v-if="dir.scan_task.status === 'running'" class="status-running">
              ⏳ 扫描中...
            </span>
            <span v-else-if="dir.scan_task.status === 'completed'" class="status-completed">
              ✅ 完成
            </span>
            <span v-else-if="dir.scan_task.status === 'failed'" class="status-failed">
              ❌ 失败
            </span>
          </div>
        </div>
        
        <div class="directory-actions">
          <button 
            @click="startScan(dir.id)" 
            class="btn-secondary"
            :disabled="scanning || (dir.scan_task && dir.scan_task.status === 'running')"
          >
            🔄 扫描
          </button>
          
          <button 
            v-if="dir.scan_task && dir.scan_task.status === 'running'"
            @click="cancelScan(dir.id)" 
            class="btn-warning"
          >
            ⏹️ 取消
          </button>
          
          <button 
            @click="toggleDirectory(dir.id)" 
            class="btn-secondary"
          >
            {{ dir.is_active ? '⏸️ 禁用' : '▶️ 启用' }}
          </button>
          
          <button 
            @click="removeDirectory(dir.id)" 
            class="btn-danger"
          >
            🗑️ 删除
          </button>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div class="empty-state" v-else>
      <div class="empty-icon">📁</div>
      <p>暂无扫描目录</p>
      <p class="empty-hint">添加一个目录开始扫描视频</p>
    </div>
    
    <!-- 扫描结果 -->
    <div class="scan-result" v-if="scanResult">
      <h3>📊 扫描结果</h3>
      <pre>{{ JSON.stringify(scanResult, null, 2) }}</pre>
    </div>
  </div>
</template>

<script>
import { scanApi, videoManagementApi } from '../api'

export default {
  name: 'ScanManagement',
  data() {
    return {
      newDirectory: {
        path: '',
        name: ''
      },
      directories: [],
      adding: false,
      scanning: false,
      scanResult: null,
      pollingInterval: null,
      verifying: false,
      cleaning: false,
      invalidStats: null
    }
  },
  mounted() {
    this.loadDirectories()
    this.loadInvalidStats()
    // 启动轮询，每 3 秒更新一次扫描进度
    this.pollingInterval = setInterval(() => {
      this.loadDirectories()
    }, 3000)
  },
  beforeUnmount() {
    // 清理轮询
    if (this.pollingInterval) {
      clearInterval(this.pollingInterval)
    }
  },
  methods: {
    async loadDirectories() {
      try {
        const res = await scanApi.getScanStatus()
        this.directories = res.data.directories || []
      } catch (error) {
        console.error('加载目录失败:', error)
        window.showToast('加载目录失败：' + (error.response?.data?.detail || error.message), 'error')
      }
    },
    
    async addDirectory() {
      if (!this.newDirectory.path) {
        window.showToast('请输入目录路径', 'warning')
        return
      }
      
      this.adding = true
      try {
        await scanApi.addDirectory(this.newDirectory)
        this.newDirectory = { path: '', name: '' }
        await this.loadDirectories()
        window.showToast('目录添加成功', 'success')
      } catch (error) {
        window.showToast(error.response?.data?.detail || '添加目录失败', 'error')
      } finally {
        this.adding = false
      }
    },
    
    async startScan(directoryId) {
      this.scanning = true
      this.scanResult = null
      
      try {
        const res = await scanApi.startScan(directoryId)
        this.scanResult = res.data
        await this.loadDirectories()
        window.showToast('扫描任务已启动', 'success')
      } catch (error) {
        window.showToast(error.response?.data?.detail || '扫描失败', 'error')
      } finally {
        this.scanning = false
      }
    },
    
    async cancelScan(directoryId) {
      if (!confirm('确定要取消扫描吗？')) return
      
      try {
        await scanApi.cancelScan(directoryId)
        await this.loadDirectories()
        window.showToast('扫描任务已取消', 'success')
      } catch (error) {
        window.showToast(error.response?.data?.detail || '取消失败', 'error')
      }
    },
    
    async toggleDirectory(id) {
      try {
        const res = await scanApi.toggleDirectory(id)
        await this.loadDirectories()
        window.showToast(res.data.message || '操作成功', 'success')
      } catch (error) {
        window.showToast('操作失败', 'error')
      }
    },
    
    async removeDirectory(id) {
      if (!confirm('确定要删除这个目录吗？\n\n⚠️ 注意：这将同时删除该目录下的所有视频记录！')) return
      
      try {
        await scanApi.removeDirectory(id, true)  // delete_videos=true
        await this.loadDirectories()
        await this.loadInvalidStats()
        window.showToast('目录已删除', 'success')
      } catch (error) {
        window.showToast(error.response?.data?.detail || '删除失败', 'error')
      }
    },
    
    formatDate(dateStr) {
      if (!dateStr) return '-'
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN')
    },
    
    async loadInvalidStats() {
      try {
        const res = await scanApi.getVerifyStats()
        this.invalidStats = res.data
      } catch (error) {
        console.error('加载统计失败:', error)
      }
    },
    
    async verifyAllDirectories() {
      this.verifying = true
      try {
        await scanApi.verifyAllDirectories()
        window.showToast('完整性检查任务已启动', 'success')
        // 延迟刷新统计
        setTimeout(() => this.loadInvalidStats(), 2000)
      } catch (error) {
        window.showToast(error.response?.data?.detail || '检查失败', 'error')
      } finally {
        this.verifying = false
      }
    },
    
    async cleanInvalidVideos() {
      if (!this.invalidStats || this.invalidStats.invalid_videos === 0) {
        window.showToast('没有需要清理的无效记录', 'info')
        return
      }
      
      if (!confirm(`确定要清理 ${this.invalidStats.invalid_videos} 条无效记录吗？\n\n这将永久删除数据库中的无效记录。`)) return
      
      this.cleaning = true
      try {
        const res = await videoManagementApi.deleteInvalidVideos()
        window.showToast(`清理完成：删除 ${res.data.deleted_count} 条记录`, 'success')
        await this.loadInvalidStats()
      } catch (error) {
        window.showToast(error.response?.data?.detail || '清理失败', 'error')
      } finally {
        this.cleaning = false
      }
    }
  }
}
</script>

<style scoped>
.scan-management {
  max-width: 900px;
  margin: 0 auto;
}

h2 {
  margin-bottom: 2rem;
}

h3 {
  margin-bottom: 1rem;
  color: #e94560;
}

.global-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background-color: #16213e;
  border-radius: 12px;
  flex-wrap: wrap;
}

.stats-info {
  margin-left: auto;
  display: flex;
  gap: 1.5rem;
  font-size: 0.9rem;
  color: #aaa;
}

.stats-info strong {
  color: #e94560;
}

.add-directory-form {
  background-color: #16213e;
  padding: 2rem;
  border-radius: 12px;
  margin-bottom: 2rem;
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
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 8px;
  background-color: #0f3460;
  color: #eee;
  font-size: 1rem;
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

.btn-primary:hover:not(:disabled) {
  background-color: #ff6b6b;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.directory-list {
  margin-bottom: 2rem;
}

.directory-card {
  background-color: #16213e;
  padding: 1.5rem;
  border-radius: 12px;
  margin-bottom: 1rem;
}

.directory-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.directory-header h4 {
  font-size: 1.2rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
}

.status-badge.active {
  background-color: #4caf50;
  color: white;
}

.status-badge.inactive {
  background-color: #888;
  color: white;
}

.directory-path {
  color: #aaa;
  margin-bottom: 0.5rem;
  word-break: break-all;
}

.directory-last-scanned {
  color: #888;
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.scan-progress {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #0f3460;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  color: #aaa;
}

.progress-bar {
  height: 8px;
  background-color: #0f3460;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  transition: width 0.3s ease;
}

.progress-fill.running {
  background: linear-gradient(90deg, #e94560, #ff6b6b);
  animation: pulse 1.5s infinite;
}

.progress-fill.completed {
  background-color: #4caf50;
}

.progress-fill.failed {
  background-color: #c62828;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.progress-details {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  font-size: 0.85rem;
  color: #888;
}

.status-running {
  color: #e94560;
}

.status-completed {
  color: #4caf50;
}

.status-failed {
  color: #c62828;
}

.directory-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.btn-secondary {
  padding: 0.5rem 1rem;
  background-color: #0f3460;
  color: #eee;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #16213e;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-warning {
  padding: 0.5rem 1rem;
  background-color: #ff9800;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-warning:hover {
  background-color: #f57c00;
}

.btn-danger {
  padding: 0.5rem 1rem;
  background-color: #c62828;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-danger:hover {
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

.scan-result {
  background-color: #16213e;
  padding: 1.5rem;
  border-radius: 12px;
  margin-top: 2rem;
}

.scan-result pre {
  background-color: #0f3460;
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
  color: #4caf50;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .scan-management {
    max-width: 100%;
  }
  
  h2 {
    font-size: 1.3rem;
  }
  
  h3 {
    font-size: 1.1rem;
  }
  
  .add-directory-form {
    padding: 1rem;
  }
  
  .form-group input {
    font-size: 0.95rem;
    padding: 0.6rem 0.8rem;
  }
  
  .btn-primary {
    width: 100%;
    padding: 0.75rem;
  }
  
  .directory-card {
    padding: 1rem;
  }
  
  .directory-header h4 {
    font-size: 1.1rem;
  }
  
  .directory-actions {
    flex-direction: column;
    gap: 0.4rem;
  }
  
  .directory-actions button {
    width: 100%;
    padding: 0.6rem;
    font-size: 0.9rem;
  }
  
  .global-actions {
    flex-direction: column;
    padding: 1rem;
  }
  
  .global-actions button {
    width: 100%;
  }
  
  .stats-info {
    width: 100%;
    justify-content: center;
    flex-direction: column;
    gap: 0.5rem;
  }
}

/* 小屏幕手机 */
@media (max-width: 480px) {
  h2 {
    font-size: 1.1rem;
  }
  
  .directory-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .progress-details {
    flex-direction: column;
    gap: 0.25rem;
  }
}
</style>
