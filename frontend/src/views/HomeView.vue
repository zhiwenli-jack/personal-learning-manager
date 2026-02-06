<template>
  <div class="home">
    <div class="hero">
      <h1>个人学习管理软件</h1>
      <p>上传资料 → 自动生成题目 → 答题测评 → 错题沉淀</p>
    </div>

    <div class="quick-actions">
      <h2>快速开始</h2>
      <div class="grid grid-3">
        <router-link to="/materials" class="action-card">
          <div class="action-icon">📚</div>
          <h3>上传资料</h3>
          <p>上传学习资料，系统自动生成题目</p>
        </router-link>
        <router-link to="/exam" class="action-card">
          <div class="action-icon">📝</div>
          <h3>开始测验</h3>
          <p>选择方向开始测验，检验学习成果</p>
        </router-link>
        <router-link to="/mistakes" class="action-card">
          <div class="action-icon">📖</div>
          <h3>错题本</h3>
          <p>复习错题，巩固薄弱知识点</p>
        </router-link>
      </div>
    </div>

    <div class="directions-section">
      <div class="section-header">
        <h2>学习方向</h2>
        <button class="btn btn-primary" @click="showAddDirection = true">添加方向</button>
      </div>
      
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="directions.length === 0" class="empty">
        暂无学习方向，请先添加
      </div>
      <div v-else class="grid grid-3">
        <div v-for="d in directions" :key="d.id" class="card direction-card">
          <h3>{{ d.name }}</h3>
          <p>{{ d.description || '暂无描述' }}</p>
          <div class="card-actions">
            <router-link :to="`/materials?direction=${d.id}`" class="btn btn-primary">
              查看资料
            </router-link>
            <button class="btn btn-danger" @click="deleteDirection(d.id)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 添加方向弹窗 -->
    <div v-if="showAddDirection" class="modal-overlay" @click.self="showAddDirection = false">
      <div class="modal">
        <h3>添加学习方向</h3>
        <div class="form-group">
          <label>方向名称</label>
          <input v-model="newDirection.name" class="form-control" placeholder="如：编程、数学、语言">
        </div>
        <div class="form-group">
          <label>描述（可选）</label>
          <textarea v-model="newDirection.description" class="form-control" rows="3"></textarea>
        </div>
        <div class="modal-actions">
          <button class="btn" @click="showAddDirection = false">取消</button>
          <button class="btn btn-primary" @click="addDirection" :disabled="!newDirection.name">
            添加
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { directionsApi } from '@/api'

const directions = ref([])
const loading = ref(true)
const showAddDirection = ref(false)
const newDirection = ref({ name: '', description: '' })

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

const addDirection = async () => {
  if (!newDirection.value.name) return
  try {
    await directionsApi.create(newDirection.value)
    showAddDirection.value = false
    newDirection.value = { name: '', description: '' }
    await loadDirections()
  } catch (e) {
    alert('添加失败: ' + (e.response?.data?.detail || e.message))
  }
}

const deleteDirection = async (id) => {
  if (!confirm('确定删除此方向？相关资料和题目也会被删除。')) return
  try {
    await directionsApi.delete(id)
    await loadDirections()
  } catch (e) {
    alert('删除失败: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(loadDirections)
</script>

<style scoped>
.hero {
  text-align: center;
  padding: 3rem 0;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 12px;
  margin-bottom: 2rem;
}

.hero h1 {
  font-size: 2.5rem;
  color: #4fc3f7;
  margin-bottom: 0.5rem;
}

.hero p {
  color: #888;
  font-size: 1.1rem;
}

.quick-actions {
  margin-bottom: 2rem;
}

.quick-actions h2 {
  margin-bottom: 1rem;
}

.action-card {
  display: block;
  background: #1a1a2e;
  padding: 2rem;
  border-radius: 12px;
  text-align: center;
  text-decoration: none;
  color: inherit;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.action-card:hover {
  border-color: #4fc3f7;
  transform: translateY(-4px);
}

.action-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.action-card h3 {
  color: #4fc3f7;
  margin-bottom: 0.5rem;
}

.action-card p {
  color: #888;
  font-size: 0.9rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.direction-card h3 {
  color: #4fc3f7;
  margin-bottom: 0.5rem;
}

.direction-card p {
  color: #888;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.card-actions {
  display: flex;
  gap: 0.5rem;
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
}

.modal h3 {
  margin-bottom: 1.5rem;
  color: #4fc3f7;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1.5rem;
}
</style>
