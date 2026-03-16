<template>
  <div id="app">
    <header class="app-header">
      <h1>🎬 Video Scout</h1>
      <nav>
        <router-link to="/">视频库</router-link>
        <router-link to="/categories">分类</router-link>
        <router-link to="/tags">标签</router-link>
        <router-link to="/statistics">统计</router-link>
        <router-link to="/scan">扫描管理</router-link>
        <router-link to="/favorites">收藏</router-link>
        <router-link to="/history">历史</router-link>
      </nav>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  background-color: #1a1a2e;
  color: #eee;
}

#app {
  min-height: 100vh;
}

.app-header {
  background: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.app-header h1 {
  font-size: 1.5rem;
  color: #e94560;
}

.app-header nav {
  display: flex;
  gap: 1.5rem;
}

.app-header nav a {
  color: #eee;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 5px;
  transition: background-color 0.3s;
}

.app-header nav a:hover,
.app-header nav a.router-link-active {
  background-color: #e94560;
}

.app-main {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

@media (max-width: 768px) {
  .app-header {
    flex-direction: column;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
  }
  
  .app-header h1 {
    font-size: 1.2rem;
  }
  
  .app-header nav {
    gap: 0.5rem;
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .app-header nav a {
    padding: 0.5rem 0.75rem;
    font-size: 0.9rem;
  }
  
  .app-main {
    padding: 1rem;
  }
}

/* 小屏幕手机 - 横向滚动导航 */
@media (max-width: 480px) {
  .app-header h1 {
    font-size: 1rem;
  }
  
  .app-header nav {
    gap: 0.25rem;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    justify-content: flex-start;
    padding-bottom: 0.25rem;
  }
  
  .app-header nav a {
    white-space: nowrap;
    font-size: 0.85rem;
    padding: 0.4rem 0.6rem;
  }
}
</style>
