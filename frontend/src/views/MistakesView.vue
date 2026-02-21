<template>
  <div class="mistakes-page">
    <div class="page-header">
      <h1>错题本</h1>
      <div class="filter-controls">
        <select v-model="filters.direction_id" class="form-control" @change="loadMistakes">
          <option :value="null">全部方向</option>
          <option v-for="d in directions" :key="d.id" :value="d.id">{{ d.name }}</option>
        </select>
        <select v-model="filters.mastered" class="form-control" @change="loadMistakes">
          <option :value="null">全部状态</option>
          <option :value="false">未掌握</option>
          <option :value="true">已掌握</option>
        </select>
        <select v-model="filters.error_prone" class="form-control" @change="loadMistakes">
          <option :value="null">全部题目</option>
          <option :value="true">易错题</option>
        </select>
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="mistakes.length === 0" class="empty">
      <p>暂无错题记录</p>
      <p class="hint">完成测验后，错误的题目会自动收录到这里</p>
    </div>
    <div v-else class="mistakes-list">
      <div v-for="m in filteredMistakes" :key="m.id" class="card mistake-card">
        <div class="mistake-header">
          <div class="header-left">
            <span v-if="m.error_prone" class="tag tag-red">易错题</span>
            <span class="error-count">出错 {{ m.error_count || 1 }} 次</span>
            <span class="review-count">已复习 {{ m.review_count }} 次</span>
          </div>
          <span :class="['tag', m.mastered ? 'tag-green' : 'tag-yellow']">
            {{ m.mastered ? '已掌握' : '未掌握' }}
          </span>
        </div>
        
        <div class="question-content" v-if="m.question">
          <div class="question-type">
            {{ questionTypeText(m.question.type) }} | 难度 {{ '★'.repeat(m.question.difficulty) }}
          </div>
          <p class="question-text">{{ m.question.content }}</p>
          
          <div v-if="m.question.options" class="options">
            <div v-for="(opt, i) in m.question.options" :key="i" class="option">
              {{ String.fromCharCode(65 + i) }}. {{ opt }}
            </div>
          </div>
        </div>
        
        <div class="answer-section" v-if="showAnswers[m.id]">
          <div class="correct-answer">
            <label>正确答案:</label>
            <p>{{ m.question?.answer }}</p>
          </div>
          <div v-if="m.question?.explanation" class="explanation">
            <label>解析:</label>
            <p>{{ m.question.explanation }}</p>
          </div>
        </div>
        
        <div class="mistake-actions">
          <button class="btn" @click="toggleAnswer(m.id)">
            {{ showAnswers[m.id] ? '隐藏答案' : '查看答案' }}
          </button>
          <button 
            class="btn btn-success" 
            @click="markMastered(m.id, !m.mastered)"
          >
            {{ m.mastered ? '标记未掌握' : '标记已掌握' }}
          </button>
          <button class="btn btn-primary" @click="reviewMistake(m.id)">
            记录复习
          </button>
          <button class="btn btn-danger" @click="deleteMistake(m.id)">
            移除
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { directionsApi, mistakesApi } from '@/api'

const directions = ref([])
const mistakes = ref([])
const loading = ref(true)
const showAnswers = reactive({})

const filters = reactive({
  direction_id: null,
  mastered: null,
  error_prone: null
})

// 前端过滤易错题
const filteredMistakes = computed(() => {
  if (filters.error_prone === null) return mistakes.value
  return mistakes.value.filter(m => m.error_prone === filters.error_prone)
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

const loadDirections = async () => {
  try {
    const res = await directionsApi.getAll()
    directions.value = res.data
  } catch (e) {
    console.error('加载方向失败:', e)
  }
}

const loadMistakes = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.direction_id) params.direction_id = filters.direction_id
    if (filters.mastered !== null) params.mastered = filters.mastered
    
    const res = await mistakesApi.getAll(params)
    mistakes.value = res.data
  } catch (e) {
    console.error('加载错题失败:', e)
  } finally {
    loading.value = false
  }
}

const toggleAnswer = (id) => {
  showAnswers[id] = !showAnswers[id]
}

const markMastered = async (id, mastered) => {
  try {
    await mistakesApi.update(id, { mastered })
    await loadMistakes()
  } catch (e) {
    alert('操作失败: ' + (e.response?.data?.detail || e.message))
  }
}

const reviewMistake = async (id) => {
  try {
    await mistakesApi.update(id, {})
    await loadMistakes()
  } catch (e) {
    alert('操作失败: ' + (e.response?.data?.detail || e.message))
  }
}

const deleteMistake = async (id) => {
  if (!confirm('确定将此题从错题本中移除？')) return
  try {
    await mistakesApi.delete(id)
    await loadMistakes()
  } catch (e) {
    alert('移除失败: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(async () => {
  await loadDirections()
  await loadMistakes()
})
</script>

<style scoped>
.mistakes-page {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.page-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-primary);
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.filter-controls {
  display: flex;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background: var(--gradient-card);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
  flex-wrap: wrap;
}

.filter-controls select {
  min-width: 180px;
}

.empty {
  text-align: center;
  padding: 5rem 2rem;
  color: var(--color-text-tertiary);
}

.empty::before {
  content: '✓';
  display: block;
  font-size: 4rem;
  margin-bottom: 1.5rem;
  opacity: 0.5;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.empty .hint {
  color: var(--color-text-secondary);
  margin-top: 1rem;
  font-size: 0.95rem;
  line-height: 1.6;
}

.mistake-card {
  margin-bottom: 1.5rem;
  animation: slideUp 0.4s ease-out backwards;
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

.mistake-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border);
  gap: 1rem;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.error-count {
  color: var(--color-error);
  font-size: 0.875rem;
  font-weight: 500;
}

.error-count::before {
  content: '';
}

.tag-red {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.review-count {
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.review-count::before {
  content: '🔄';
}

.question-content {
  background: var(--color-bg-tertiary);
  padding: 1.25rem;
  border-radius: var(--radius-md);
  margin-bottom: 1rem;
  border: 1px solid var(--color-border);
}

.question-type {
  font-size: 0.875rem;
  color: var(--color-accent-primary);
  margin-bottom: 0.75rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.question-type::before {
  content: '📋';
}

.question-text {
  font-size: 1.1rem;
  line-height: 1.7;
  margin-bottom: 1rem;
  color: var(--color-text-primary);
  font-weight: 500;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.option {
  padding: 0.75rem 1rem;
  background: rgba(99, 102, 241, 0.05);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--color-border);
  transition: all var(--transition-fast);
}

.option:hover {
  background: rgba(99, 102, 241, 0.1);
  border-left-color: var(--color-accent-primary);
}

.answer-section {
  margin-bottom: 1rem;
}

.correct-answer, .explanation {
  background: var(--color-bg-tertiary);
  padding: 1rem 1.25rem;
  border-radius: var(--radius-sm);
  margin-bottom: 0.75rem;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.correct-answer {
  border-left: 4px solid var(--color-success);
  background: var(--color-success-bg);
}

.explanation {
  border-left: 4px solid var(--color-accent-primary);
  background: rgba(99, 102, 241, 0.05);
}

.correct-answer label, .explanation label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.correct-answer label::before {
  content: '✓';
}

.explanation label::before {
  content: '💡';
}

.correct-answer label {
  color: var(--color-success);
}

.explanation label {
  color: var(--color-accent-primary);
}

.correct-answer p, .explanation p {
  margin: 0;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

.mistake-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}

/* Tag styles override */
.mistake-card .tag {
  font-size: 0.75rem;
  padding: 0.25rem 0.75rem;
  margin: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .filter-controls {
    width: 100%;
  }
  
  .filter-controls select {
    flex: 1;
  }
  
  .mistake-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .mistake-actions {
    width: 100%;
  }
  
  .mistake-actions .btn {
    flex: 1;
    min-width: 120px;
  }
}
</style>
