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
h1 {
  color: #4fc3f7;
  margin-bottom: 1.5rem;
}

.exam-form {
  max-width: 500px;
  margin-bottom: 2rem;
}

.radio-group {
  display: flex;
  gap: 1.5rem;
}

.radio-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.radio-item input {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.btn-lg {
  width: 100%;
  padding: 1rem;
  font-size: 1.1rem;
  margin-top: 1rem;
}

.history-section h2 {
  margin-bottom: 1rem;
}

.exam-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
}

.exam-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.direction {
  font-weight: 500;
  color: #4fc3f7;
}

.exam-score {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.2rem;
  font-weight: bold;
}

.grade {
  color: #66bb6a;
}
</style>
