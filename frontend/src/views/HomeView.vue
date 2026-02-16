<template>
  <div class="home">
    <div class="hero">
      <div class="hero-content">
        <h1 class="hero-title">
          <span class="gradient-text">个人学习管理</span>
        </h1>
        <p class="hero-subtitle">
          <span class="step">上传资料</span>
          <span class="arrow">→</span>
          <span class="step">自动生成题目</span>
          <span class="arrow">→</span>
          <span class="step">答题测评</span>
          <span class="arrow">→</span>
          <span class="step">错题沉淀</span>
        </p>
        <div class="hero-stats">
          <div class="stat-item">
            <div class="stat-number">{{ directions.length }}</div>
            <div class="stat-label">学习方向</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-number">{{ materialsCount }}</div>
            <div class="stat-label">学习资料</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-number">{{ questionsCount }}</div>
            <div class="stat-label">生成题目</div>
          </div>
        </div>
      </div>
      <div class="hero-visual">
        <div class="floating-shape shape-1"></div>
        <div class="floating-shape shape-2"></div>
        <div class="floating-shape shape-3"></div>
      </div>
    </div>

    <!-- 探险家档案 + 每日任务 -->
    <div v-if="profile" class="explorer-section">
      <div class="explorer-profile card">
        <div class="profile-header">
          <div class="level-badge">Lv.{{ profile.level }}</div>
          <div class="profile-info">
            <h3 class="profile-name">{{ profile.username }}</h3>
            <span class="profile-title">{{ profile.title }}</span>
          </div>
          <div class="streak-info" v-if="profile.streak_days > 0">
            <span class="streak-icon">&#x1f525;</span>
            <span class="streak-count">{{ profile.streak_days }}天</span>
          </div>
        </div>
        <div class="exp-bar-container">
          <div class="exp-bar">
            <div class="exp-fill" :style="{ width: expPercentCalc + '%' }"></div>
          </div>
          <div class="exp-text">
            {{ profile.total_exp }} / {{ profile.next_level_exp }} EXP
          </div>
        </div>
        <div class="profile-stats">
          <div class="p-stat">
            <div class="p-stat-value">{{ profile.total_exp }}</div>
            <div class="p-stat-label">总经验</div>
          </div>
          <div class="p-stat">
            <div class="p-stat-value">{{ profile.level }}</div>
            <div class="p-stat-label">等级</div>
          </div>
          <div class="p-stat">
            <div class="p-stat-value">{{ profile.streak_days }}</div>
            <div class="p-stat-label">连续天数</div>
          </div>
        </div>
        <router-link to="/map" class="btn btn-primary btn-block">
          &#x1f5fa;&#xfe0f; 查看探险地图
        </router-link>
      </div>

      <div class="daily-tasks card">
        <div class="tasks-header">
          <h3>
            <span class="title-icon">&#x1f4cb;</span>
            每日任务
          </h3>
          <span class="tasks-progress">{{ completedTaskCount }}/{{ dailyTasks.length }}</span>
        </div>
        <div v-if="dailyTasks.length === 0" class="empty-tasks">今日任务加载中...</div>
        <div v-else class="tasks-list">
          <div
            v-for="task in dailyTasks"
            :key="task.task_id"
            class="task-item"
            :class="{ completed: task.completed }"
          >
            <div class="task-left">
              <span class="task-check" :class="{ done: task.completed }">
                {{ task.completed ? '&#x2714;' : '' }}
              </span>
              <div class="task-info">
                <span class="task-name">{{ task.name }}</span>
                <span class="task-desc">{{ task.description }}</span>
              </div>
            </div>
            <div class="task-right">
              <div class="task-progress-bar">
                <div class="task-progress-fill" :style="{ width: (task.current / task.target * 100) + '%' }"></div>
              </div>
              <span class="task-reward">+{{ task.exp_reward }} EXP</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="quick-actions">
      <h2 class="section-title">
        <span class="title-icon">🚀</span>
        快速开始
      </h2>
      <div class="grid grid-3">
        <router-link to="/materials" class="action-card">
          <div class="action-icon">
            <span>📚</span>
            <div class="icon-bg"></div>
          </div>
          <h3>上传资料</h3>
          <p>上传学习资料，系统自动生成题目</p>
          <div class="card-arrow">→</div>
        </router-link>
        <router-link to="/exam" class="action-card">
          <div class="action-icon">
            <span>📝</span>
            <div class="icon-bg"></div>
          </div>
          <h3>开始测验</h3>
          <p>选择方向开始测验，检验学习成果</p>
          <div class="card-arrow">→</div>
        </router-link>
        <router-link to="/mistakes" class="action-card">
          <div class="action-icon">
            <span>📖</span>
            <div class="icon-bg"></div>
          </div>
          <h3>错题本</h3>
          <p>复习错题，巩固薄弱知识点</p>
          <div class="card-arrow">→</div>
        </router-link>
      </div>
    </div>

    <div class="directions-section">
      <div class="section-header">
        <h2 class="section-title">
          <span class="title-icon">🎯</span>
          学习方向
        </h2>
        <button class="btn btn-primary" @click="showAddDirection = true">
          <span>+</span>
          添加方向
        </button>
      </div>
      
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="directions.length === 0" class="empty">
        <p>暂无学习方向，请先添加</p>
      </div>
      <div v-else class="grid grid-3">
        <div 
          v-for="(d, index) in directions" 
          :key="d.id" 
          class="card direction-card"
          :style="{ animationDelay: `${index * 0.1}s` }"
        >
          <div class="direction-header">
            <h3>{{ d.name }}</h3>
            <span class="direction-badge">{{ getMaterialsCount(d.id) }} 资料集</span>
          </div>
          <p>{{ d.description || '暂无描述' }}</p>
          <div class="card-actions">
            <router-link :to="`/materials?direction=${d.id}`" class="btn btn-primary btn-sm">
              查看资料
            </router-link>
            <button class="btn btn-danger btn-sm" @click="deleteDirection(d.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加方向弹窗 -->
    <transition name="modal">
      <div v-if="showAddDirection" class="modal-overlay" @click.self="showAddDirection = false">
        <div class="modal">
          <h3>
            <span class="modal-icon">✨</span>
            添加学习方向
          </h3>
          <div class="form-group">
            <label>方向名称</label>
            <input v-model="newDirection.name" class="form-control" placeholder="如：编程、数学、语言">
          </div>
          <div class="form-group">
            <label>描述（可选）</label>
            <textarea v-model="newDirection.description" class="form-control" rows="3" placeholder="简要描述这个学习方向..."></textarea>
          </div>
          <div class="modal-actions">
            <button class="btn" @click="showAddDirection = false">取消</button>
            <button class="btn btn-primary" @click="addDirection" :disabled="!newDirection.name">
              添加方向
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { directionsApi, materialsApi, questionsApi, gamificationApi } from '@/api'

const directions = ref([])
const materialsCount = ref(0)
const questionsCount = ref(0)
const loading = ref(true)
const showAddDirection = ref(false)
const newDirection = ref({ name: '', description: '' })

// 游戏化数据
const profile = ref(null)
const dailyTasks = ref([])

const expPercent = computed(() => {
  if (!profile.value || !profile.value.next_level_exp) return 0
  const current = profile.value.total_exp
  // 当前等级的起始经验
  const nextExp = profile.value.next_level_exp
  const toNext = profile.value.exp_to_next
  const currentLevelStart = nextExp - (nextExp - current + toNext) + toNext
  if (nextExp <= currentLevelStart) return 100
  return Math.min(100, Math.round(((current - (nextExp - toNext - (toNext > 0 ? 0 : 0))) / (toNext + (current - (nextExp - toNext)))) * 100)) || Math.round((1 - profile.value.exp_to_next / Math.max(1, profile.value.next_level_exp - (profile.value.next_level_exp - profile.value.exp_to_next - profile.value.total_exp + profile.value.total_exp))) * 100) || 0
})

const expPercentCalc = computed(() => {
  if (!profile.value) return 0
  const totalExp = profile.value.total_exp
  const nextExp = profile.value.next_level_exp
  const toNext = profile.value.exp_to_next
  const currentLevelBase = nextExp - toNext
  if (currentLevelBase >= nextExp) return 100
  const range = nextExp - currentLevelBase
  const progress = totalExp - currentLevelBase
  return range > 0 ? Math.min(100, Math.round((progress / range) * 100)) : 0
})

const completedTaskCount = computed(() => dailyTasks.value.filter(t => t.completed).length)

const loadDirections = async () => {
  loading.value = true
  try {
    const res = await directionsApi.getAll()
    directions.value = res.data
  } catch (e) {
    console.error('加载方向失败:', e)
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const [materialsRes, questionsRes] = await Promise.all([
      materialsApi.getAll(),
      questionsApi.getAll()
    ])
    materialsCount.value = materialsRes.data.length
    questionsCount.value = questionsRes.data.length
  } catch (e) {
    console.error('加载统计数据失败:', e)
  }
}

const addDirection = async () => {
  if (!newDirection.value.name) return
  try {
    await directionsApi.create(newDirection.value)
    showAddDirection.value = false
    newDirection.value = { name: '', description: '' }
    await loadDirections()
    await loadStats()
  } catch (e) {
    alert('添加失败: ' + (e.response?.data?.detail || e.message))
  }
}

const deleteDirection = async (id) => {
  if (!confirm('确定删除此方向？相关资料和题目也会被删除。')) return
  try {
    await directionsApi.delete(id)
    await loadDirections()
    await loadStats()
  } catch (e) {
    alert('删除失败: ' + (e.response?.data?.detail || e.message))
  }
}

const getMaterialsCount = (directionId) => {
  if (!materialsCount.value) return '0'
  return '多个'
}

const loadProfile = async () => {
  try {
    const res = await gamificationApi.getProfile()
    profile.value = res.data
  } catch (e) {
    console.error('加载档案失败:', e)
  }
}

const loadDailyTasks = async () => {
  try {
    const res = await gamificationApi.getDailyTasks()
    dailyTasks.value = res.data
  } catch (e) {
    console.error('加载任务失败:', e)
  }
}

onMounted(async () => {
  await Promise.all([loadDirections(), loadStats(), loadProfile(), loadDailyTasks()])
})
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
}

/* Hero Section */
.hero {
  position: relative;
  padding: 4rem 2rem;
  background: var(--gradient-card);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-xl);
  margin-bottom: 3rem;
  overflow: hidden;
  border: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hero::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: 
    radial-gradient(circle at 20% 80%, rgba(99, 102, 241, 0.1) 0%, transparent 40%),
    radial-gradient(circle at 80% 20%, rgba(139, 92, 246, 0.1) 0%, transparent 40%);
  animation: rotate 30s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.hero-content {
  position: relative;
  z-index: 1;
  flex: 1;
}

.hero-title {
  font-size: 3rem;
  font-weight: 800;
  margin-bottom: 1.5rem;
  line-height: 1.2;
}

.gradient-text {
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 2rem;
  font-size: 1.1rem;
  color: var(--color-text-secondary);
}

.step {
  padding: 0.5rem 1rem;
  background: rgba(99, 102, 241, 0.1);
  border-radius: 20px;
  color: var(--color-accent-primary);
  font-weight: 500;
  transition: all var(--transition-base);
}

.step:hover {
  background: rgba(99, 102, 241, 0.2);
  transform: scale(1.05);
}

.arrow {
  color: var(--color-text-tertiary);
  font-weight: bold;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.stat-item {
  text-align: center;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 800;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.stat-label {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: var(--color-border);
}

.hero-visual {
  position: relative;
  width: 300px;
  height: 300px;
  flex-shrink: 0;
}

.floating-shape {
  position: absolute;
  border-radius: 50%;
  animation: float 6s ease-in-out infinite;
}

.shape-1 {
  width: 200px;
  height: 200px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
  top: 0;
  right: 0;
  animation-delay: 0s;
}

.shape-2 {
  width: 120px;
  height: 120px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(168, 85, 247, 0.3));
  bottom: 20px;
  left: 20px;
  animation-delay: 2s;
}

.shape-3 {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.4), rgba(139, 92, 246, 0.4));
  top: 50%;
  right: 30px;
  animation-delay: 4s;
}

@keyframes float {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-20px) rotate(10deg);
  }
}

/* Quick Actions */
.quick-actions {
  margin-bottom: 3rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 1.5rem;
}

.title-icon {
  font-size: 1.75rem;
}

.action-card {
  display: block;
  background: var(--gradient-card);
  backdrop-filter: blur(20px);
  padding: 2rem;
  border-radius: var(--radius-lg);
  text-decoration: none;
  color: inherit;
  transition: all var(--transition-base);
  border: 1px solid var(--color-border);
  position: relative;
  overflow: hidden;
  animation: slideUp 0.5s ease-out backwards;
}

.action-card:nth-child(1) { animation-delay: 0.1s; }
.action-card:nth-child(2) { animation-delay: 0.2s; }
.action-card:nth-child(3) { animation-delay: 0.3s; }

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.action-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--gradient-primary);
  opacity: 0;
  transition: opacity var(--transition-base);
}

.action-card:hover {
  border-color: var(--color-accent-primary);
  box-shadow: var(--shadow-glow);
  transform: translateY(-8px);
}

.action-card:hover::before {
  opacity: 0.1;
}

.action-icon {
  position: relative;
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1;
}

.action-icon span {
  font-size: 2.5rem;
  position: relative;
  z-index: 1;
}

.icon-bg {
  position: absolute;
  width: 100%;
  height: 100%;
  background: var(--gradient-primary);
  border-radius: 50%;
  opacity: 0.2;
  transition: all var(--transition-base);
}

.action-card:hover .icon-bg {
  opacity: 0.3;
  transform: scale(1.1);
}

.action-card h3 {
  position: relative;
  z-index: 1;
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  color: var(--color-text-primary);
}

.action-card p {
  position: relative;
  z-index: 1;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  line-height: 1.6;
}

.card-arrow {
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  font-size: 1.5rem;
  color: var(--color-accent-primary);
  opacity: 0;
  transform: translateX(-10px);
  transition: all var(--transition-base);
  z-index: 1;
}

.action-card:hover .card-arrow {
  opacity: 1;
  transform: translateX(0);
}

/* Directions Section */
.directions-section {
  margin-bottom: 2rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.direction-card {
  animation: slideUp 0.5s ease-out backwards;
}

.direction-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}

.direction-card h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0;
}

.direction-badge {
  padding: 0.25rem 0.75rem;
  background: var(--color-accent-glow);
  border-radius: 12px;
  font-size: 0.75rem;
  color: var(--color-accent-primary);
  font-weight: 600;
}

.direction-card p {
  color: var(--color-text-secondary);
  margin-bottom: 1.25rem;
  font-size: 0.9rem;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-actions {
  display: flex;
  gap: 0.75rem;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal {
  background: var(--gradient-card);
  backdrop-filter: blur(20px);
  padding: 2rem;
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 500px;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-lg);
  animation: scaleIn 0.3s ease-out;
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.modal h3 {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
}

.modal-icon {
  font-size: 1.75rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-border);
}

/* Modal Transition */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal,
.modal-leave-to .modal {
  transform: scale(0.9);
}

/* Responsive */
@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    text-align: center;
    padding: 2rem;
  }
  
  .hero-title {
    font-size: 2rem;
  }
  
  .hero-subtitle {
    justify-content: center;
  }
  
  .hero-stats {
    justify-content: center;
    gap: 1.5rem;
  }
  
  .hero-visual {
    width: 200px;
    height: 200px;
  }
  
  .shape-1 {
    width: 150px;
    height: 150px;
  }
  
  .shape-2 {
    width: 100px;
    height: 100px;
  }
  
  .shape-3 {
    width: 60px;
    height: 60px;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .explorer-section {
    grid-template-columns: 1fr;
  }
}

/* Explorer Section */
.explorer-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 3rem;
  animation: fadeInUp 0.6s ease-out;
}

.explorer-profile {
  padding: 1.5rem;
}

.profile-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.level-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 56px;
  height: 56px;
  padding: 0 0.75rem;
  background: var(--gradient-primary);
  border-radius: 16px;
  font-weight: 800;
  font-size: 1.1rem;
  color: white;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.profile-info {
  flex: 1;
}

.profile-name {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0 0 0.25rem;
}

.profile-title {
  font-size: 0.85rem;
  color: var(--color-accent-primary);
  font-weight: 500;
}

.streak-info {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.35rem 0.75rem;
  background: rgba(245, 158, 11, 0.15);
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #f59e0b;
}

.streak-icon {
  font-size: 1.1rem;
}

.exp-bar-container {
  margin-bottom: 1.25rem;
}

.exp-bar {
  position: relative;
  width: 100%;
  height: 20px;
  background: var(--color-bg-tertiary);
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid var(--color-border);
}

.exp-fill {
  height: 100%;
  background: var(--gradient-primary);
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 10px rgba(99, 102, 241, 0.5);
  border-radius: 10px;
}

.exp-text {
  text-align: right;
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin-top: 0.35rem;
}

.profile-stats {
  display: flex;
  justify-content: space-around;
  margin-bottom: 1.25rem;
  padding: 0.75rem 0;
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

.p-stat {
  text-align: center;
}

.p-stat-value {
  font-size: 1.25rem;
  font-weight: 700;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.p-stat-label {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin-top: 0.15rem;
}

.btn-block {
  display: block;
  width: 100%;
  text-align: center;
}

/* Daily Tasks */
.daily-tasks {
  padding: 1.5rem;
}

.tasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.tasks-header h3 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
}

.tasks-progress {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-accent-primary);
  padding: 0.25rem 0.65rem;
  background: var(--color-accent-glow);
  border-radius: 10px;
}

.empty-tasks {
  text-align: center;
  color: var(--color-text-secondary);
  padding: 2rem 0;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.task-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: rgba(99, 102, 241, 0.05);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  transition: all var(--transition-base);
}

.task-item.completed {
  border-color: rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.08);
}

.task-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex: 1;
}

.task-check {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  flex-shrink: 0;
}

.task-check.done {
  background: var(--color-success);
  border-color: var(--color-success);
  color: white;
}

.task-info {
  display: flex;
  flex-direction: column;
}

.task-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.task-desc {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.task-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.35rem;
  min-width: 100px;
}

.task-progress-bar {
  width: 80px;
  height: 6px;
  background: var(--color-bg-tertiary);
  border-radius: 3px;
  overflow: hidden;
}

.task-progress-fill {
  height: 100%;
  background: var(--gradient-primary);
  transition: width 0.5s ease-out;
  border-radius: 3px;
}

.task-item.completed .task-progress-fill {
  background: var(--color-success);
}

.task-reward {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--color-accent-primary);
}
</style>
