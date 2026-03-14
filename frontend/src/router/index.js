import { createRouter, createWebHistory } from 'vue-router'
import VideoLibrary from '../views/VideoLibrary.vue'
import VideoPlayer from '../views/VideoPlayer.vue'
import ScanManagement from '../views/ScanManagement.vue'
import Favorites from '../views/Favorites.vue'
import History from '../views/History.vue'

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
  },
  {
    path: '/favorites',
    name: 'Favorites',
    component: Favorites
  },
  {
    path: '/history',
    name: 'History',
    component: History
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
