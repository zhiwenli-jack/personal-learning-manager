<template>
  <div class="exam-taking-page">
    <div v-if="loading" class="loading">加载测验中...</div>
    <div v-else-if="!exam" class="empty">测验不存在</div>
    <template v-else>
      <!-- 顶部信息栏 -->
      <div class="exam-header">
        <div class="exam-info">
          <span>题目 {{ currentIndex + 1 }} / {{ questions.length }}</span>
          <span v-if="exam.mode === 'timed'" class="timer">
            剩余时间: {{ formatTime(remainingTime) }}
          </span>
        </div>
        <div class="progress-bar">
          <div class="progress" :style="{ width: progressPercent + '%' }"></div>
        </div>
      </div>

      <!-- 题目内容 -->
      <div class="question-card card">
        <div class="question-header">
          <span class="question-type">{{ questionTypeText(currentQuestion.type) }}</span>
          <span class="difficulty">难度: {{ '★'.repeat(currentQuestion.difficulty) }}</span>
        </div>
        
        <div class="question-content">
          <p>{{ currentQuestion.content }}</p>
        </div>
        
        <!-- 选择题选项 -->
        <div v-if="isChoiceQuestion" class="options">
          <label 
            v-for="(opt, i) in currentQuestion.options" 
            :key="i" 
            class="option-item"
            :class="{ selected: isOptionSelected(opt) }"
          >
            <input 
              v-if="currentQuestion.type === 'multi_choice'"
              type="checkbox"
              :value="opt"
              v-model="currentAnswer"
            >
            <input 
              v-else
              type="radio"
              :value="opt"
              v-model="currentAnswer"
            >
            <span class="option-label">{{ String.fromCharCode(65 + i) }}.</span>
            <span>{{ opt }}</span>
          </label>
        </div>
        
        <!-- 简答题 -->
        <div v-else class="answer-input">
          <textarea 
            v-model="currentAnswer" 
            class="form-control"
            placeholder="请输入你的答案..."
            rows="5"
          ></textarea>
        </div>
      </div>

      <!-- 底部导航 -->
      <div class="exam-footer">
        <button class="btn" @click="prevQuestion" :disabled="currentIndex === 0">
          上一题
        </button>
        <div class="question-nav">
          <span 
            v-for="(q, i) in questions" 
            :key="q.id"
            class="nav-dot"
            :class="{ active: i === currentIndex, answered: answers[q.id] }"
            @click="goToQuestion(i)"
          >
            {{ i + 1 }}
          </span>
        </div>
        <button 
          v-if="currentIndex < questions.length - 1"
          class="btn btn-primary" 
          @click="nextQuestion"
        >
          下一题
        </button>
        <button 
          v-else
          class="btn btn-success" 
          @click="submitExam"
          :disabled="submitting"
        >
          {{ submitting ? '提交中...' : '提交测验' }}
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { examsApi } from '@/api'

const route = useRoute()
const router = useRouter()

const exam = ref(null)
const questions = ref([])
const loading = ref(true)
const submitting = ref(false)
const currentIndex = ref(0)
const answers = ref({})
const remainingTime = ref(0)
let timer = null

const currentQuestion = computed(() => questions.value[currentIndex.value] || {})

const currentAnswer = computed({
  get: () => answers.value[currentQuestion.value.id] || (currentQuestion.value.type === 'multi_choice' ? [] : ''),
  set: (val) => { answers.value[currentQuestion.value.id] = val }
})

const isChoiceQuestion = computed(() => {
  return ['single_choice', 'multi_choice', 'true_false'].includes(currentQuestion.value.type)
})

const progressPercent = computed(() => {
  const answered = Object.keys(answers.value).filter(k => {
    const v = answers.value[k]
    return Array.isArray(v) ? v.length > 0 : v
  }).length
  return (answered / questions.value.length) * 100
})

const questionTypeText = (type) => {
  const map = {
    single_choice: '单选题',
    multi_choice: '多选题',
    true_false: '判断题',
    short_answer: '简答题'
  }
  return map[type] || type
}

const formatTime = (seconds) => {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}

const isOptionSelected = (opt) => {
  const ans = currentAnswer.value
  if (Array.isArray(ans)) return ans.includes(opt)
  return ans === opt
}

const loadExam = async () => {
  loading.value = true
  try {
    const res = await examsApi.get(route.params.id)
    exam.value = res.data
    questions.value = res.data.questions || []
    
    if (exam.value.status === 'completed') {
      router.replace(`/exam/${exam.value.id}/result`)
      return
    }
    
    // 设置计时器
    if (exam.value.mode === 'timed' && exam.value.time_limit) {
      remainingTime.value = exam.value.time_limit * 60
      startTimer()
    }
  } catch (e) {
    console.error('加载测验失败:', e)
  } finally {
    loading.value = false
  }
}

const startTimer = () => {
  timer = setInterval(() => {
    if (remainingTime.value > 0) {
      remainingTime.value--
    } else {
      clearInterval(timer)
      alert('时间到！自动提交测验。')
      submitExam()
    }
  }, 1000)
}

const prevQuestion = () => {
  if (currentIndex.value > 0) currentIndex.value--
}

const nextQuestion = () => {
  if (currentIndex.value < questions.value.length - 1) currentIndex.value++
}

const goToQuestion = (index) => {
  currentIndex.value = index
}

const submitExam = async () => {
  const unanswered = questions.value.filter(q => {
    const ans = answers.value[q.id]
    return !ans || (Array.isArray(ans) && ans.length === 0)
  })
  
  if (unanswered.length > 0) {
    if (!confirm(`还有 ${unanswered.length} 题未作答，确定提交吗？`)) return
  }
  
  submitting.value = true
  try {
    const answerList = questions.value.map(q => ({
      exam_id: exam.value.id,
      question_id: q.id,
      user_answer: Array.isArray(answers.value[q.id]) 
        ? answers.value[q.id].join(',') 
        : (answers.value[q.id] || '')
    }))
    
    await examsApi.submit(exam.value.id, answerList)
    router.push(`/exam/${exam.value.id}/result`)
  } catch (e) {
    alert('提交失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    submitting.value = false
  }
}

onMounted(loadExam)

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.exam-header {
  margin-bottom: 1.5rem;
}

.exam-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.timer {
  color: #ef5350;
  font-weight: bold;
}

.progress-bar {
  height: 6px;
  background: #333;
  border-radius: 3px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: #4fc3f7;
  transition: width 0.3s;
}

.question-card {
  min-height: 300px;
}

.question-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.question-type {
  color: #4fc3f7;
  font-weight: 500;
}

.difficulty {
  color: #ffca28;
}

.question-content {
  font-size: 1.1rem;
  line-height: 1.8;
  margin-bottom: 1.5rem;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.option-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  background: #16213e;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.option-item:hover {
  background: #1a2744;
}

.option-item.selected {
  border-color: #4fc3f7;
  background: rgba(79, 195, 247, 0.1);
}

.option-item input {
  margin-top: 2px;
}

.option-label {
  font-weight: bold;
  color: #4fc3f7;
}

.answer-input textarea {
  min-height: 150px;
}

.exam-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #333;
}

.question-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
}

.nav-dot {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #333;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.3s;
}

.nav-dot:hover {
  background: #444;
}

.nav-dot.active {
  background: #4fc3f7;
  color: #1a1a2e;
}

.nav-dot.answered {
  background: #66bb6a;
  color: white;
}

.nav-dot.active.answered {
  background: #4fc3f7;
}
</style>
