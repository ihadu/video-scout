import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    // 可以在这里添加请求 token 等
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response
  },
  error => {
    // 统一错误处理
    if (error.response) {
      // 服务器返回错误
      const status = error.response.status
      const detail = error.response.data?.detail || error.response.data?.message
      
      switch (status) {
        case 401:
          window.showToast('未授权，请重新登录', 'error')
          break
        case 403:
          window.showToast('没有权限执行此操作', 'error')
          break
        case 404:
          window.showToast('资源不存在', 'error')
          break
        case 500:
          window.showToast('服务器错误，请稍后重试', 'error')
          break
        default:
          if (detail) {
            window.showToast(detail, 'error')
          }
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      window.showToast('网络连接失败，请检查网络', 'error')
    } else {
      // 请求配置出错
      console.error('请求配置错误:', error.message)
    }
    
    return Promise.reject(error)
  }
)

// 视频相关 API
export const videoApi = {
  // 获取视频列表
  listVideos(params) {
    return api.get('/videos', { params })
  },
  
  // 获取视频详情
  getVideo(id) {
    return api.get(`/videos/${id}`)
  },
  
  // 删除视频索引
  deleteVideo(id) {
    return api.delete(`/videos/${id}`)
  }
}

// 搜索 API
export const searchApi = {
  // 搜索视频
  search(params) {
    return api.get('/search', { params })
  },
  
  // 获取时长分布
  getDurationRanges() {
    return api.get('/search/duration-ranges')
  }
}

// 扫描相关 API
export const scanApi = {
  // 添加扫描目录
  addDirectory(data) {
    return api.post('/scan/add', data)
  },
  
  // 启动扫描
  startScan(directoryId) {
    return api.post('/scan/start', null, { params: { directory_id: directoryId } })
  },
  
  // 取消扫描
  cancelScan(directoryId) {
    return api.post(`/scan/cancel/${directoryId}`)
  },
  
  // 获取扫描状态
  getScanStatus() {
    return api.get('/scan/status')
  },
  
  // 移除扫描目录
  removeDirectory(id, deleteVideos = true) {
    return api.delete(`/scan/remove/${id}`, { params: { delete_videos: deleteVideos } })
  },
  
  // 启用/禁用目录
  toggleDirectory(id) {
    return api.post(`/scan/toggle/${id}`)
  },
  
  // 完整性检查
  verifyAllDirectories() {
    return api.post('/scan/verify')
  },
  
  // 获取无效视频统计
  getVerifyStats() {
    return api.get('/scan/verify/stats')
  }
}

// 视频管理 API
export const videoManagementApi = {
  // 清理无效视频记录
  deleteInvalidVideos() {
    return api.delete('/videos/invalid')
  }
}

// 收藏相关 API
export const favoriteApi = {
  // 获取收藏列表
  getFavorites() {
    return api.get('/favorites')
  },
  
  // 添加收藏
  addFavorite(videoId) {
    return api.post(`/favorites/${videoId}`)
  },
  
  // 取消收藏
  removeFavorite(videoId) {
    return api.delete(`/favorites/${videoId}`)
  },
  
  // 检查是否已收藏
  checkStatus(videoId) {
    return api.get(`/favorites/${videoId}/status`)
  }
}

// 观看历史 API
export const historyApi = {
  // 获取观看历史
  getHistory(limit = 20) {
    return api.get('/history', { params: { limit } })
  },
  
  // 更新观看进度
  updateProgress(videoId, progress) {
    return api.post(`/history/${videoId}/progress`, null, { params: { progress } })
  },
  
  // 清空观看历史
  clearHistory() {
    return api.delete('/history')
  }
}

// 分类和标签 API
export const categoryApi = {
  // 获取所有分类
  listCategories() {
    return api.get('/categories')
  },
  
  // 创建分类
  createCategory(data) {
    return api.post('/categories', data)
  },
  
  // 更新分类
  updateCategory(id, data) {
    return api.put(`/categories/${id}`, data)
  },
  
  // 删除分类
  deleteCategory(id) {
    return api.delete(`/categories/${id}`)
  },
  
  // 获取分类下的视频
  getCategoryVideos(categoryId, page = 1, pageSize = 20) {
    return api.get(`/categories/${categoryId}/videos`, { params: { page, page_size: pageSize } })
  }
}

export const tagApi = {
  // 获取所有标签
  listTags() {
    return api.get('/tags')
  },
  
  // 创建标签
  createTag(data) {
    return api.post('/tags', data)
  },
  
  // 更新标签
  updateTag(id, data) {
    return api.put(`/tags/${id}`, data)
  },
  
  // 删除标签
  deleteTag(id) {
    return api.delete(`/tags/${id}`)
  },
  
  // 获取标签下的视频
  getTagVideos(tagId, page = 1, pageSize = 20) {
    return api.get(`/tags/${tagId}/videos`, { params: { page, page_size: pageSize } })
  }
}

export const videoCategoryApi = {
  // 为视频添加分类
  addCategories(videoId, categoryIds) {
    return api.post(`/videos/${videoId}/categories`, { tag_ids: categoryIds })
  },
  
  // 移除视频分类
  removeCategory(videoId, categoryId) {
    return api.delete(`/videos/${videoId}/categories/${categoryId}`)
  },
  
  // 获取视频的分类
  getCategories(videoId) {
    return api.get(`/videos/${videoId}/categories`)
  }
}

export const videoTagApi = {
  // 为视频添加标签
  addTags(videoId, tagIds) {
    return api.post(`/videos/${videoId}/tags`, { tag_ids: tagIds })
  },
  
  // 移除视频标签
  removeTag(videoId, tagId) {
    return api.delete(`/videos/${videoId}/tags/${tagId}`)
  },
  
  // 获取视频的标签
  getTags(videoId) {
    return api.get(`/videos/${videoId}/tags`)
  }
}

export default api
