<template>
  <div class="exam-start-page">
    <h1>开始测验</h1>
    
    <div class="card exam-form">
      <div class="form-group">
        <label>选择学习方向</label>
        <select v-model="examConfig.direction_id" class="form-control">
          <option :value="null" disabled>请选择方向</option>
          <option v-for="d in directions" :key="d.id" :value="d.id">{{ d.name }}</option>
        </select>
      </div>
      
      <div class="form-group">
        <label>测验模式</label>
        <div class="radio-group">
          <label class="radio-item">
            <input type="radio" v-model="examConfig.mode" value="untimed">
            <span>不限时</span>
          </label>
          <label class="radio-item">
            <input type="radio" v-model="examConfig.mode" value="timed">
            <span>限时</span>
          </label>
        </div>
      </div>
      
      <div v-if="examConfig.mode === 'timed'" class="form-group">
        <label>限时时间（分钟）</label>
        <input type="number" v-model.number="examConfig.time_limit" class="form-control" min="5" max="120">
      </div>
      
      <div class="form-group">
        <label>评分方式</label>
        <div class="radio-group">
          <label class="radio-item">
            <input type="radio" v-model="examConfig.score_type" value="hundred">
            <span>100分制</span>
          </label>
          <label class="radio-item">
            <input type="radio" v-model="examConfig.score_type" value="grade">
            <span>等级制 (A/B/C/D)</span>
          </label>
        </div>
      </div>
      
      <div class="form-group">
        <label>题目数量</label>
        <input type="number" v-model.number="examConfig.question_count" class="form-control" min="5" max="50">
      </div>
      
      <button 
        class="btn btn-primary btn-lg" 
        @click="startExam" 
        :disabled="!examConfig.direction_id || starting"
      >
        {{ starting ? '创建中...' : '开始测验' }}
      </button>
    </div>
    
    <!-- 历史测验 -->
    <div class="history-section">
      <h2>历史测验</h2>
      <div v-if="exams.length === 0" class="empty">暂无测验记录</div>
      <div v-else class="exams-list">
        <div v-for="e in exams" :key="e.id" class="card exam-card">
          <div class="exam-info">
            <span class="direction">{{ getDirectionName(e.direction_id) }}</span>
            <span :class="['tag', e.status === 'completed' ? 'tag-green' : 'tag-yellow']">
              {{ e.status === 'completed' ? '已完成' : '进行中' }}
            </span>
          </div>
          <div class="exam-score" v-if="e.status === 'completed'">
            <span v-if="e.score !== null">{{ e.score.toFixed(1) }}分</span>
            <span v-if="e.grade" class="grade">{{ e.grade }}</span>
          </div>
          <div class="exam-actions">
            <router-link 
              v-if="e.status === 'in_progress'" 
              :to="`/exam/${e.id}`" 
              class="btn btn-primary"
            >
              继续答题
            </router-link>
            <router-link 
              v-else 
              :to="`/exam/${e.id}/result`" 
              class="btn btn-success"
            >
              查看结果
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { directionsApi, examsApi } from '@/api'

const router = useRouter()
const directions = ref([])
const exams = ref([])
const starting = ref(false)

const examConfig = ref({
  direction_id: null,
  mode: 'untimed',
  time_limit: 30,
  score_type: 'hundred',
  question_count: 10
})

const getDirectionName = (id) => {
  const d = directions.value.find(d => d.id === id)
  return d ? d.name : '未知方向'
}

const loadDirections = async () => {
  try {
    const res = await directionsApi.getAll()
    directions.value = res.data
  } catch (e) {
    console.error('加载方向失败:', e)
  }
}

const loadExams = async () => {
  try {
    const res = await examsApi.getAll()
    exams.value = res.data.slice(0, 10) // 只显示最近10条
  } catch (e) {
    console.error('加载测验失败:', e)
  }
}

const startExam = async () => {
  if (!examConfig.value.direction_id) return
  starting.value = true
  try {
    const res = await examsApi.create(examConfig.value)
    router.push(`/exam/${res.data.id}`)
  } catch (e) {
    alert('创建测验失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    starting.value = false
  }
}

onMounted(async () => {
  await loadDirections()
  await loadExams()
})
</script>

<style scoped>
.exam-start-page {
  padding: 2rem;
  max-width: 1000px;
  margin: 0 auto;
}

h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-primary);
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 2rem;
}

.exam-form {
  max-width: 600px;
  margin-bottom: 3rem;
  padding: 2rem;
  background: var(--gradient-card);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-lg);
  animation: slideUp 0.4s ease-out;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.radio-group {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  padding: 0.75rem 1.25rem;
  border: 2px solid var(--color-border);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
  flex: 1;
  min-width: 120px;
}

.radio-item:hover {
  border-color: var(--color-accent-primary);
  background: rgba(99, 102, 241, 0.05);
}

.radio-item input[type="radio"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
  accent-color: var(--color-accent-primary);
}

.radio-item input[type="radio"]:checked + span {
  color: var(--color-accent-primary);
  font-weight: 600;
}

.radio-item span {
  color: var(--color-text-secondary);
  transition: color var(--transition-fast);
}

.btn-lg {
  width: 100%;
  padding: 1rem 2rem;
  font-size: 1.1rem;
  font-weight: 600;
  margin-top: 1.5rem;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  transition: all var(--transition-base);
}

.btn-lg:hover {
  box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
  transform: translateY(-2px);
}

.btn-lg:active {
  transform: translateY(0);
}

.history-section {
  animation: slideUp 0.4s ease-out 0.2s backwards;
}

.history-section h2 {
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.history-section h2::before {
  content: '📊';
}

.exams-list {
  display: grid;
  gap: 1rem;
}

.exam-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.25rem 1.5rem;
  transition: all var(--transition-base);
}

.exam-card:hover {
  border-color: var(--color-accent-primary);
  box-shadow: var(--shadow-glow);
  transform: translateX(5px);
}

.exam-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.direction {
  font-weight: 600;
  color: var(--color-accent-primary);
  font-size: 1rem;
}

.exam-score {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.25rem;
  font-weight: 700;
  margin-right: 1rem;
}

.exam-score span:not(.grade) {
  color: var(--color-text-primary);
}

.grade {
  color: var(--color-success);
  padding: 0.25rem 0.75rem;
  background: var(--color-success-bg);
  border-radius: 12px;
  font-size: 0.9rem;
}

.exam-actions {
  display: flex;
  gap: 0.75rem;
}

.exam-actions .btn {
  flex-shrink: 0;
}

/* Tag styles override */
.exam-card .tag {
  font-size: 0.75rem;
  padding: 0.25rem 0.75rem;
  margin: 0;
}

/* Empty state */
.empty {
  text-align: center;
  padding: 4rem 2rem;
  color: var(--color-text-tertiary);
}

.empty::before {
  content: '📝';
  display: block;
  font-size: 4rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

/* Responsive */
@media (max-width: 768px) {
  .exam-start-page {
    padding: 1rem;
  }
  
  .exam-form {
    padding: 1.5rem;
  }
  
  .radio-item {
    flex: 1 1 calc(50% - 0.75rem);
  }
  
  .exam-card {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .exam-info {
    width: 100%;
  }
  
  .exam-actions {
    width: 100%;
  }
  
  .exam-actions .btn {
    flex: 1;
  }
}
</style>
