<template>
  <div class="explorer-map-page">
    <div class="page-header">
      <h1 class="page-title">
        <span class="gradient-text">探险地图</span>
      </h1>
      <p class="page-desc">每个方向都是一片待探索的大陆，完成题目来提高探索率</p>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="progressList.length === 0" class="empty-state card">
      <div class="empty-icon">&#x1f5fa;&#xfe0f;</div>
      <p>还没有可探索的大陆</p>
      <p class="empty-hint">请先添加学习方向并上传资料生成题目</p>
      <router-link to="/" class="btn btn-primary">返回首页</router-link>
    </div>

    <div v-else class="map-grid">
      <div
        v-for="dp in progressList"
        :key="dp.direction_id"
        class="continent-card card"
        :class="{ conquered: dp.exploration_rate >= 100 }"
      >
        <div class="continent-header">
          <div class="continent-title-row">
            <h3>{{ dp.direction_name }}</h3>
            <span v-if="dp.exploration_rate >= 100" class="conquered-badge">已征服</span>
          </div>
          <p class="continent-desc">{{ dp.direction_description || '未知领域，等待探索' }}</p>
        </div>

        <div class="exploration-progress">
          <div class="progress-label">
            <span>探索进度</span>
            <span class="progress-percent">{{ dp.exploration_rate.toFixed(1) }}%</span>
          </div>
          <div class="progress-bar">
            <div
              class="progress-fill"
              :style="{ width: Math.min(100, dp.exploration_rate) + '%' }"
              :class="progressClass(dp.exploration_rate)"
            ></div>
          </div>
        </div>

        <div class="continent-stats">
          <div class="c-stat">
            <div class="c-stat-value">{{ dp.answered_questions }}/{{ dp.total_questions }}</div>
            <div class="c-stat-label">已答/总题</div>
          </div>
          <div class="c-stat">
            <div class="c-stat-value correct-text">{{ dp.correct_questions }}</div>
            <div class="c-stat-label">正确</div>
          </div>
          <div class="c-stat">
            <div class="c-stat-value mastered-text">{{ dp.mastered_count }}</div>
            <div class="c-stat-label">已掌握</div>
          </div>
        </div>

        <div class="continent-footer">
          <span v-if="dp.last_studied_at" class="last-studied">
            上次探索: {{ formatTime(dp.last_studied_at) }}
          </span>
          <span v-else class="last-studied">尚未开始探索</span>
          <router-link :to="`/exam?direction=${dp.direction_id}`" class="btn btn-primary btn-sm">
            {{ dp.exploration_rate >= 100 ? '再次挑战' : '继续探索' }}
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { gamificationApi, directionsApi } from '@/api'

const progressList = ref([])
const loading = ref(true)

const formatTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  const now = new Date()
  const diff = now - d
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

const progressClass = (rate) => {
  if (rate >= 100) return 'fill-complete'
  if (rate >= 70) return 'fill-high'
  if (rate >= 40) return 'fill-mid'
  return 'fill-low'
}

const loadData = async () => {
  loading.value = true
  try {
    const [progressRes, directionsRes] = await Promise.all([
      gamificationApi.getDirectionProgress(),
      directionsApi.getAll()
    ])
    const progressMap = {}
    for (const p of progressRes.data) {
      progressMap[p.direction_id] = p
    }
    // 合并：已有进度的方向 + 没有进度的方向
    const merged = []
    for (const dir of directionsRes.data) {
      if (progressMap[dir.id]) {
        merged.push(progressMap[dir.id])
      } else {
        merged.push({
          direction_id: dir.id,
          direction_name: dir.name,
          direction_description: dir.description,
          total_questions: 0,
          answered_questions: 0,
          correct_questions: 0,
          mastered_count: 0,
          exploration_rate: 0,
          last_studied_at: null
        })
      }
    }
    progressList.value = merged
  } catch (e) {
    console.error('加载探险地图失败:', e)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.explorer-map-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 2.5rem;
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.page-title {
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: 0.75rem;
}

.gradient-text {
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-desc {
  color: var(--color-text-secondary);
  font-size: 1.05rem;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-state p {
  color: var(--color-text-secondary);
  margin-bottom: 0.5rem;
  font-size: 1.1rem;
}

.empty-hint {
  font-size: 0.9rem !important;
  margin-bottom: 1.5rem !important;
}

/* Map Grid */
.map-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

/* Continent Card */
.continent-card {
  padding: 1.75rem;
  position: relative;
  overflow: hidden;
  animation: slideUp 0.5s ease-out backwards;
  transition: all 0.3s ease;
}

.continent-card:nth-child(1) { animation-delay: 0.05s; }
.continent-card:nth-child(2) { animation-delay: 0.1s; }
.continent-card:nth-child(3) { animation-delay: 0.15s; }
.continent-card:nth-child(4) { animation-delay: 0.2s; }
.continent-card:nth-child(5) { animation-delay: 0.25s; }
.continent-card:nth-child(6) { animation-delay: 0.3s; }

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

.continent-card:hover {
  border-color: var(--color-accent-primary);
  box-shadow: var(--shadow-glow);
  transform: translateY(-4px);
}

.continent-card.conquered {
  border-color: rgba(16, 185, 129, 0.4);
}

.continent-card.conquered::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.03), transparent 60%);
  pointer-events: none;
}

.continent-header {
  margin-bottom: 1.25rem;
}

.continent-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.continent-title-row h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin: 0;
}

.conquered-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.75rem;
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-success);
  flex-shrink: 0;
}

.continent-desc {
  color: var(--color-text-secondary);
  font-size: 0.875rem;
  line-height: 1.5;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Exploration Progress */
.exploration-progress {
  margin-bottom: 1.25rem;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.progress-percent {
  font-weight: 700;
  color: var(--color-accent-primary);
}

.progress-bar {
  width: 100%;
  height: 10px;
  background: var(--color-bg-tertiary);
  border-radius: 5px;
  overflow: hidden;
  border: 1px solid var(--color-border);
}

.progress-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.fill-low {
  background: linear-gradient(90deg, #6366f1, #818cf8);
  box-shadow: 0 0 8px rgba(99, 102, 241, 0.4);
}

.fill-mid {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
  box-shadow: 0 0 8px rgba(245, 158, 11, 0.4);
}

.fill-high {
  background: linear-gradient(90deg, #8b5cf6, #a78bfa);
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.4);
}

.fill-complete {
  background: linear-gradient(90deg, #10b981, #34d399);
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
}

/* Stats */
.continent-stats {
  display: flex;
  justify-content: space-around;
  margin-bottom: 1.25rem;
  padding: 0.75rem 0;
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

.c-stat {
  text-align: center;
}

.c-stat-value {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text-primary);
}

.c-stat-value.correct-text {
  color: var(--color-success);
}

.c-stat-value.mastered-text {
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.c-stat-label {
  font-size: 0.7rem;
  color: var(--color-text-tertiary);
  margin-top: 0.15rem;
}

/* Footer */
.continent-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.last-studied {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

/* Responsive */
@media (max-width: 1024px) {
  .map-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .map-grid {
    grid-template-columns: 1fr;
  }

  .page-title {
    font-size: 1.75rem;
  }
}
</style>
