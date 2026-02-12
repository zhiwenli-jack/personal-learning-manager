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
.exam-taking-page {
  padding: 2rem;
  max-width: 1000px;
  margin: 0 auto;
}

.exam-header {
  margin-bottom: 2rem;
  padding: 1.25rem;
  background: var(--gradient-card);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  animation: slideDown 0.4s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.exam-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.exam-info span {
  font-weight: 500;
  color: var(--color-text-primary);
}

.timer {
  color: var(--color-error);
  font-weight: 700;
  font-size: 1.1rem;
  padding: 0.5rem 1rem;
  background: var(--color-error-bg);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.timer::before {
  content: '⏱';
}

.progress-bar {
  height: 8px;
  background: var(--color-bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: var(--gradient-primary);
  border-radius: 4px;
  transition: width 0.4s ease;
  box-shadow: 0 0 10px rgba(99, 102, 241, 0.3);
}

.question-card {
  min-height: 320px;
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.25rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border);
  flex-wrap: wrap;
  gap: 0.75rem;
}

.question-type {
  color: var(--color-accent-primary);
  font-weight: 600;
  font-size: 0.95rem;
  padding: 0.375rem 0.875rem;
  background: var(--color-accent-glow);
  border-radius: 20px;
}

.difficulty {
  color: var(--color-warning);
  font-weight: 600;
  font-size: 0.9rem;
}

.question-content {
  font-size: 1.15rem;
  line-height: 1.8;
  margin-bottom: 1.5rem;
  color: var(--color-text-primary);
  font-weight: 500;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.option-item {
  display: flex;
  align-items: flex-start;
  gap: 0.875rem;
  padding: 1rem 1.25rem;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-base);
  border: 2px solid transparent;
  position: relative;
}

.option-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 0;
  background: var(--gradient-primary);
  transition: height var(--transition-base);
  border-radius: 0 4px 4px 0;
}

.option-item:hover {
  background: rgba(99, 102, 241, 0.08);
  border-color: var(--color-border);
  transform: translateX(4px);
}

.option-item:hover::before {
  height: 60%;
}

.option-item.selected {
  border-color: var(--color-accent-primary);
  background: rgba(99, 102, 241, 0.12);
  transform: translateX(4px);
}

.option-item.selected::before {
  height: 100%;
}

.option-item input {
  margin-top: 3px;
  accent-color: var(--color-accent-primary);
  cursor: pointer;
}

.option-label {
  font-weight: 700;
  color: var(--color-accent-primary);
  font-size: 1rem;
}

.answer-input textarea {
  min-height: 180px;
  font-size: 1rem;
  line-height: 1.6;
}

.exam-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-border);
  flex-wrap: wrap;
  gap: 1.5rem;
}

.question-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  flex: 1;
}

.nav-dot {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--color-bg-tertiary);
  border: 2px solid var(--color-border);
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  transition: all var(--transition-base);
}

.nav-dot:hover {
  border-color: var(--color-accent-primary);
  color: var(--color-text-primary);
  transform: scale(1.1);
}

.nav-dot.active {
  background: var(--gradient-primary);
  border-color: var(--color-accent-primary);
  color: white;
  box-shadow: 0 0 12px rgba(99, 102, 241, 0.4);
}

.nav-dot.answered {
  background: var(--color-success);
  border-color: var(--color-success);
  color: white;
}

.nav-dot.active.answered {
  background: var(--gradient-primary);
  border-color: var(--color-accent-primary);
}

/* Responsive */
@media (max-width: 768px) {
  .exam-taking-page {
    padding: 1rem;
  }
  
  .exam-footer {
    flex-direction: column;
  }
  
  .exam-footer .btn {
    width: 100%;
  }
  
  .question-nav {
    order: -1;
    width: 100%;
  }
  
  .nav-dot {
    width: 32px;
    height: 32px;
    font-size: 0.85rem;
  }
}
</style>
