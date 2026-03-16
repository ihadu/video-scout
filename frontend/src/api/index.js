import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

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

export default api
