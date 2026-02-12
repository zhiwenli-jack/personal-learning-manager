<template>
  <div class="questions-page">
    <div class="page-header">
      <h1>题目管理</h1>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <select v-model="filters.direction_id" class="form-control" @change="loadQuestions">
        <option :value="null">全部方向</option>
        <option v-for="d in directions" :key="d.id" :value="d.id">{{ d.name }}</option>
      </select>
      
      <select v-model="filters.question_type" class="form-control" @change="loadQuestions">
        <option :value="null">全部类型</option>
        <option value="single_choice">单选题</option>
        <option value="multiple_choice">多选题</option>
        <option value="true_false">判断题</option>
        <option value="short_answer">简答题</option>
      </select>
      
      <select v-model="filters.material_id" class="form-control" @change="loadQuestions">
        <option :value="null">全部资料</option>
        <option v-for="m in materials" :key="m.id" :value="m.id">{{ m.title }}</option>
      </select>
    </div>

    <!-- 题目列表 -->
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="questions.length === 0" class="empty">
      暂无题目，请先上传资料生成题目
    </div>
    <div v-else class="questions-list">
      <div v-for="q in questions" :key="q.id" class="card question-card">
        <div class="question-header">
          <div class="header-left">
            <span :class="['tag', typeClass(q.type)]">{{ typeText(q.type) }}</span>
            <span class="tag tag-gray">难度: {{ q.difficulty }}/5</span>
            <span v-if="q.rating" :class="['tag', ratingClass(q.rating)]">
              {{ q.rating === 'good' ? '好题' : '待优化' }}
            </span>
          </div>
          <div class="header-actions">
            <button class="btn btn-sm" @click="editQuestion(q)">编辑</button>
            <button class="btn btn-sm btn-danger" @click="deleteQuestion(q.id)">删除</button>
          </div>
        </div>

        <div class="question-content">
          <p class="question-text">{{ q.content }}</p>
          
          <!-- 选择题选项 -->
          <div v-if="q.options && q.options.length" class="options-list">
            <div v-for="(opt, i) in q.options" :key="i" class="option-item">
              <span class="option-label">{{ String.fromCharCode(65 + i) }}.</span>
              <span>{{ opt }}</span>
            </div>
          </div>
          
          <!-- 答案 -->
          <div class="answer-section">
            <strong>答案：</strong>
            <span class="answer-text">{{ formatAnswer(q.answer, q.type) }}</span>
          </div>
          
          <!-- 解析 -->
          <div v-if="q.explanation" class="explanation-section">
            <strong>解析：</strong>
            <span>{{ q.explanation }}</span>
          </div>
        </div>

        <!-- 评价操作 -->
        <div v-if="!q.rating" class="rating-actions">
          <span class="rating-label">这道题怎么样？</span>
          <button class="btn btn-sm btn-success" @click="rateQuestion(q.id, 'good')">好题</button>
          <button class="btn btn-sm btn-warning" @click="rateQuestion(q.id, 'poor')">待优化</button>
        </div>
      </div>
    </div>

    <!-- 编辑题目弹窗 -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal modal-lg">
        <h3>编辑题目</h3>
        
        <div class="form-group">
          <label>题目内容</label>
          <textarea 
            v-model="editingQuestion.content" 
            class="form-control" 
            rows="3"
            placeholder="请输入题目内容"
          ></textarea>
        </div>
        
        <!-- 选项编辑 -->
        <div v-if="editingQuestion.options" class="form-group">
          <label>选项</label>
          <div v-for="(opt, i) in editingQuestion.options" :key="i" class="option-edit">
            <span class="option-label">{{ String.fromCharCode(65 + i) }}.</span>
            <input 
              v-model="editingQuestion.options[i]" 
              class="form-control"
              placeholder="选项内容"
            >
          </div>
        </div>
        
        <div class="form-group">
          <label>答案</label>
          <input 
            v-model="editingQuestion.answer" 
            class="form-control"
            placeholder="请输入正确答案"
          >
          <small class="form-hint">多选题答案用逗号分隔，如: A,B,C</small>
        </div>
        
        <div class="form-group">
          <label>解析</label>
          <textarea 
            v-model="editingQuestion.explanation" 
            class="form-control" 
            rows="3"
            placeholder="答案解析（可选）"
          ></textarea>
        </div>
        
        <div class="form-group">
          <label>难度 (1-5)</label>
          <input 
            v-model.number="editingQuestion.difficulty" 
            type="number" 
            min="1" 
            max="5"
            class="form-control"
          >
        </div>
        
        <div class="modal-actions">
          <button class="btn" @click="showEditModal = false">取消</button>
          <button 
            class="btn btn-primary" 
            @click="saveQuestion"
            :disabled="!editingQuestion.content || !editingQuestion.answer"
          >
            保存
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { directionsApi, materialsApi, questionsApi } from '@/api'

const directions = ref([])
const materials = ref([])
const questions = ref([])
const loading = ref(true)
const showEditModal = ref(false)
const editingQuestion = ref({})

const filters = ref({
  direction_id: null,
  material_id: null,
  question_type: null
})

const typeClass = (type) => {
  const map = {
    single_choice: 'tag-blue',
    multiple_choice: 'tag-purple',
    true_false: 'tag-green',
    short_answer: 'tag-orange'
  }
  return map[type] || 'tag-gray'
}

const typeText = (type) => {
  const map = {
    single_choice: '单选',
    multiple_choice: '多选',
    true_false: '判断',
    short_answer: '简答'
  }
  return map[type] || type
}

const ratingClass = (rating) => {
  return rating === 'good' ? 'tag-green' : 'tag-yellow'
}

const formatAnswer = (answer, type) => {
  if (type === 'true_false') {
    return answer === 'true' || answer === '正确' ? '正确' : '错误'
  }
  return answer
}

const loadDirections = async () => {
  try {
    const res = await directionsApi.getAll()
    directions.value = res.data
  } catch (e) {
    console.error('加载方向失败:', e)
  }
}

const loadMaterials = async () => {
  try {
    const res = await materialsApi.getAll(filters.value.direction_id)
    materials.value = res.data
  } catch (e) {
    console.error('加载资料失败:', e)
  }
}

const loadQuestions = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.value.direction_id) params.direction_id = filters.value.direction_id
    if (filters.value.material_id) params.material_id = filters.value.material_id
    if (filters.value.question_type) params.question_type = filters.value.question_type
    
    const res = await questionsApi.getAll(params)
    questions.value = res.data
  } catch (e) {
    console.error('加载题目失败:', e)
  } finally {
    loading.value = false
  }
}

const editQuestion = (question) => {
  // 深拷贝避免直接修改原数据
  editingQuestion.value = {
    id: question.id,
    content: question.content,
    options: question.options ? [...question.options] : null,
    answer: question.answer,
    explanation: question.explanation || '',
    difficulty: question.difficulty
  }
  showEditModal.value = true
}

const saveQuestion = async () => {
  try {
    const { id, ...updateData } = editingQuestion.value
    await questionsApi.update(id, updateData)
    showEditModal.value = false
    await loadQuestions()
    alert('题目更新成功')
  } catch (e) {
    alert('保存失败: ' + (e.response?.data?.detail || e.message))
  }
}

const deleteQuestion = async (id) => {
  if (!confirm('确定删除此题目？')) return
  try {
    await questionsApi.delete(id)
    await loadQuestions()
  } catch (e) {
    alert('删除失败: ' + (e.response?.data?.detail || e.message))
  }
}

const rateQuestion = async (id, rating) => {
  try {
    await questionsApi.rate(id, rating)
    await loadQuestions()
  } catch (e) {
    alert('评价失败: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(async () => {
  await loadDirections()
  await loadMaterials()
  await loadQuestions()
})
</script>

<style scoped>
.questions-page {
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 1.5rem;
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

.filter-bar {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  padding: 1rem;
  background: var(--gradient-card);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border);
}

.filter-bar select {
  flex: 1;
  min-width: 200px;
}

.question-card {
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

.question-header {
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
  gap: 0.5rem;
  flex-wrap: wrap;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.question-content {
  margin-bottom: 1.5rem;
}

.question-text {
  font-size: 1.1rem;
  color: var(--color-text-primary);
  margin-bottom: 1.25rem;
  line-height: 1.7;
  font-weight: 500;
}

.options-list {
  margin-bottom: 1rem;
}

.option-item {
  padding: 0.75rem 1rem;
  margin-bottom: 0.75rem;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  border: 1px solid transparent;
  transition: all var(--transition-fast);
}

.option-item:hover {
  border-color: var(--color-border);
  background: rgba(99, 102, 241, 0.05);
}

.option-label {
  color: var(--color-accent-primary);
  font-weight: 700;
  min-width: 30px;
  flex-shrink: 0;
}

.answer-section {
  padding: 1rem;
  background: var(--color-success-bg);
  border-radius: var(--radius-sm);
  margin-bottom: 1rem;
  border-left: 4px solid var(--color-success);
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.answer-section strong {
  color: var(--color-success);
  font-weight: 600;
  flex-shrink: 0;
}

.answer-text {
  color: var(--color-success);
  font-weight: 600;
  font-size: 1.05rem;
}

.explanation-section {
  padding: 1rem;
  background: rgba(99, 102, 241, 0.05);
  border-radius: var(--radius-sm);
  border-left: 4px solid var(--color-accent-primary);
}

.explanation-section strong {
  color: var(--color-accent-primary);
  font-weight: 600;
  display: block;
  margin-bottom: 0.5rem;
}

.rating-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
  flex-wrap: wrap;
}

.rating-label {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
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

.modal {
  background: var(--gradient-card);
  backdrop-filter: blur(20px);
  padding: 2rem;
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-lg);
  animation: scaleIn 0.3s ease-out;
}

.modal h3 {
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
}

.modal-lg {
  max-width: 750px;
}

.option-edit {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 0.75rem;
}

.option-edit .option-label {
  color: var(--color-accent-primary);
  font-weight: 700;
  min-width: 30px;
  flex-shrink: 0;
}

.form-hint {
  display: block;
  color: var(--color-text-tertiary);
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-border);
}

/* Responsive */
@media (max-width: 768px) {
  .question-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-left {
    width: 100%;
  }
  
  .header-actions {
    width: 100%;
  }
  
  .header-actions .btn {
    flex: 1;
  }
  
  .modal-lg {
    max-width: 100%;
    margin: 1rem;
  }
}
</style>
