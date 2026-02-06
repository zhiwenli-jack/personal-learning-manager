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
      </div>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="mistakes.length === 0" class="empty">
      <p>暂无错题记录</p>
      <p class="hint">完成测验后，错误的题目会自动收录到这里</p>
    </div>
    <div v-else class="mistakes-list">
      <div v-for="m in mistakes" :key="m.id" class="card mistake-card">
        <div class="mistake-header">
          <span class="review-count">已复习 {{ m.review_count }} 次</span>
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
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { directionsApi, mistakesApi } from '@/api'

const directions = ref([])
const mistakes = ref([])
const loading = ref(true)
const showAnswers = reactive({})

const filters = reactive({
  direction_id: null,
  mastered: null
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

onMounted(async () => {
  await loadDirections()
  await loadMistakes()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.page-header h1 {
  color: #4fc3f7;
}

.filter-controls {
  display: flex;
  gap: 1rem;
}

.filter-controls select {
  min-width: 150px;
}

.empty {
  text-align: center;
  padding: 3rem;
}

.empty .hint {
  color: #666;
  margin-top: 0.5rem;
  font-size: 0.9rem;
}

.mistake-card {
  margin-bottom: 1rem;
}

.mistake-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.review-count {
  color: #888;
  font-size: 0.9rem;
}

.question-content {
  background: #16213e;
  padding: 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
}

.question-type {
  font-size: 0.85rem;
  color: #4fc3f7;
  margin-bottom: 0.5rem;
}

.question-text {
  font-size: 1.1rem;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.option {
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.answer-section {
  margin-bottom: 1rem;
}

.correct-answer, .explanation {
  background: #16213e;
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 0.5rem;
}

.correct-answer {
  border-left: 3px solid #66bb6a;
}

.explanation {
  border-left: 3px solid #4fc3f7;
}

.correct-answer label, .explanation label {
  display: block;
  font-size: 0.85rem;
  color: #888;
  margin-bottom: 0.5rem;
}

.mistake-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .filter-controls {
    width: 100%;
  }
  
  .filter-controls select {
    flex: 1;
  }
}
</style>
