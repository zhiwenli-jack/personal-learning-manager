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
  return map[type] || ''
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
.page-header {
  margin-bottom: 1.5rem;
}

.page-header h1 {
  color: #4fc3f7;
}

.filter-bar {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.filter-bar select {
  flex: 1;
  min-width: 200px;
}

.question-card {
  margin-bottom: 1rem;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid #333;
}

.header-left {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.question-content {
  margin-bottom: 1rem;
}

.question-text {
  font-size: 1.1rem;
  color: #e0e0e0;
  margin-bottom: 1rem;
  line-height: 1.6;
}

.options-list {
  margin-bottom: 1rem;
}

.option-item {
  padding: 0.5rem;
  margin-bottom: 0.5rem;
  background: #16213e;
  border-radius: 4px;
  display: flex;
  gap: 0.5rem;
}

.option-label {
  color: #4fc3f7;
  font-weight: bold;
  min-width: 30px;
}

.answer-section {
  padding: 0.75rem;
  background: #16213e;
  border-radius: 4px;
  margin-bottom: 0.75rem;
}

.answer-section strong {
  color: #4fc3f7;
}

.answer-text {
  color: #81c784;
  font-weight: 500;
}

.explanation-section {
  padding: 0.75rem;
  background: #1a1a2e;
  border-radius: 4px;
  border-left: 3px solid #4fc3f7;
}

.explanation-section strong {
  color: #4fc3f7;
}

.rating-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid #333;
}

.rating-label {
  color: #888;
  margin-right: 0.5rem;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: #1a1a2e;
  padding: 2rem;
  border-radius: 12px;
  width: 100%;
  max-width: 400px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-lg {
  max-width: 700px;
}

.modal h3 {
  margin-bottom: 1.5rem;
  color: #4fc3f7;
}

.option-edit {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.5rem;
}

.option-edit .option-label {
  color: #4fc3f7;
  font-weight: bold;
  min-width: 30px;
}

.form-hint {
  display: block;
  color: #888;
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1.5rem;
}
</style>
