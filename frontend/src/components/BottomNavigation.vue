<template>
  <nav class="bottom-navigation" :class="{ 'hidden': isHidden }">
    <router-link 
      v-for="item in navItems" 
      :key="item.path"
      :to="item.path"
      class="nav-item"
      :class="{ active: $route.path === item.path }"
    >
      <span class="nav-icon">{{ item.icon }}</span>
      <span class="nav-text">{{ item.text }}</span>
    </router-link>
  </nav>
</template>

<script>
export default {
  name: 'BottomNavigation',
  data() {
    return {
      navItems: [
        { path: '/videos', icon: '📁', text: '视频库' },
        { path: '/favorites', icon: '❤️', text: '收藏' },
        { path: '/discover', icon: '▶️', text: '发现' }
      ],
      isHidden: false
    }
  },
  methods: {
    hide() {
      this.isHidden = true
    },
    show() {
      this.isHidden = false
    }
  }
}
</script>

<style scoped>
.bottom-navigation {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: #0f3460;
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 0.5rem 0;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  transition: transform 0.3s ease;
}

.bottom-navigation.hidden {
  transform: translateY(100%);
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.5rem 1rem;
  color: #888;
  text-decoration: none;
  transition: color 0.3s;
  flex: 1;
}

.nav-item.active {
  color: #e94560;
}

.nav-icon {
  font-size: 1.5rem;
}

.nav-text {
  font-size: 0.75rem;
}

/* 桌面端隐藏 */
@media (min-width: 769px) {
  .bottom-navigation {
    display: none;
  }
}
</style>
