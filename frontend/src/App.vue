<template>
  <div id="app">
    <nav class="navbar">
      <div class="nav-brand">
        <router-link to="/">个人学习管理</router-link>
      </div>
      <div class="nav-links">
        <router-link to="/">首页</router-link>
        <router-link to="/materials">资料管理</router-link>
        <router-link to="/questions">题目管理</router-link>
        <router-link to="/exam">开始测验</router-link>
        <router-link to="/mistakes">错题本</router-link>
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
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: #1a1a2e;
  color: white;
}

.nav-brand a {
  font-size: 1.5rem;
  font-weight: bold;
  color: #4fc3f7;
  text-decoration: none;
}

.nav-links {
  display: flex;
  gap: 2rem;
}

.nav-links a {
  color: #e0e0e0;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: all 0.3s;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  background: #4fc3f7;
  color: #1a1a2e;
}

.main-content {
  padding: 2rem;
  min-height: calc(100vh - 80px);
}
</style>
