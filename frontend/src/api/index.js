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
  removeDirectory(id) {
    return api.delete(`/scan/remove/${id}`)
  },
  
  // 启用/禁用目录
  toggleDirectory(id) {
    return api.post(`/scan/toggle/${id}`)
  }
}

export default api
