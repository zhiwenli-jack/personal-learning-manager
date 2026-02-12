<template>
  <div id="app">
    <nav class="navbar">
      <div class="nav-brand">
        <router-link to="/">个人学习管理</router-link>
      </div>
      <div class="nav-links">
        <router-link to="/"><span>首页</span></router-link>
        <router-link to="/materials"><span>资料管理</span></router-link>
        <router-link to="/questions"><span>题目管理</span></router-link>
        <router-link to="/exam"><span>开始测验</span></router-link>
        <router-link to="/mistakes"><span>错题本</span></router-link>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
</script>

<style scoped>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2.5rem;
  background: linear-gradient(135deg, rgba(10, 14, 39, 0.95) 0%, rgba(17, 24, 56, 0.95) 100%);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: var(--shadow-lg);
  animation: slideDown 0.5s ease-out;
}

@keyframes slideDown {
  from {
    transform: translateY(-100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.nav-brand a {
  font-size: 1.5rem;
  font-weight: 700;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-decoration: none;
  position: relative;
  transition: all var(--transition-base);
}

.nav-brand a::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 0;
  width: 0;
  height: 2px;
  background: var(--gradient-primary);
  transition: width var(--transition-base);
}

.nav-brand a:hover::after {
  width: 100%;
}

.nav-links {
  display: flex;
  gap: 1.5rem;
  align-items: center;
}

.nav-links a {
  color: var(--color-text-secondary);
  text-decoration: none;
  padding: 0.625rem 1.25rem;
  border-radius: var(--radius-sm);
  font-weight: 500;
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}

.nav-links a::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: var(--gradient-primary);
  opacity: 0;
  transition: opacity var(--transition-base);
}

.nav-links a:hover {
  color: white;
  transform: translateY(-2px);
}

.nav-links a:hover::before {
  opacity: 1;
}

.nav-links a span {
  position: relative;
  z-index: 1;
}

.nav-links a.router-link-active {
  background: var(--gradient-primary);
  color: white;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.nav-links a.router-link-active span {
  position: relative;
}

.main-content {
  flex: 1;
  padding: 2rem;
  min-height: calc(100vh - 72px);
  position: relative;
}

.main-content::before {
  content: '';
  position: fixed;
  top: 72px;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 1200px;
  height: calc(100vh - 72px);
  background: var(--gradient-glow);
  pointer-events: none;
  z-index: -1;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .navbar {
    padding: 1rem;
    flex-wrap: wrap;
  }
  
  .nav-brand a {
    font-size: 1.25rem;
  }
  
  .nav-links {
    gap: 0.5rem;
    margin-top: 0.5rem;
    width: 100%;
    justify-content: center;
  }
  
  .nav-links a {
    padding: 0.5rem 0.75rem;
    font-size: var(--font-size-sm);
  }
  
  .main-content {
    padding: 1rem;
  }
}

/* 添加路由过渡动画 */
.router-view-enter-active,
.router-view-leave-active {
  transition: all var(--transition-slow);
}

.router-view-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.router-view-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
</style>
