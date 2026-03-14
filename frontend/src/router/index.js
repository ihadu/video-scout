import { createRouter, createWebHistory } from 'vue-router'
import VideoLibrary from '../views/VideoLibrary.vue'
import VideoPlayer from '../views/VideoPlayer.vue'
import ScanManagement from '../views/ScanManagement.vue'

const routes = [
  {
    path: '/',
    name: 'VideoLibrary',
    component: VideoLibrary
  },
  {
    path: '/play/:id',
    name: 'VideoPlayer',
    component: VideoPlayer
  },
  {
    path: '/scan',
    name: 'ScanManagement',
    component: ScanManagement
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
