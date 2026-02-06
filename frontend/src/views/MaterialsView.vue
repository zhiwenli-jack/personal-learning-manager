<template>
  <div class="materials-page">
    <div class="page-header">
      <h1>资料管理</h1>
      <button class="btn btn-primary" @click="showAddMaterial = true">上传资料</button>
    </div>

    <!-- 方向筛选 -->
    <div class="filter-bar">
      <select v-model="selectedDirection" class="form-control" @change="loadMaterials">
        <option :value="null">全部方向</option>
        <option v-for="d in directions" :key="d.id" :value="d.id">{{ d.name }}</option>
      </select>
    </div>

    <!-- 资料列表 -->
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="materials.length === 0" class="empty">
      暂无资料，请先上传
    </div>
    <div v-else class="materials-list">
      <div 
        v-for="m in materials" 
        :key="m.id" 
        :data-material-id="m.id"
        class="card material-card"
      >
        <div class="material-header">
          <h3>{{ m.title }}</h3>
          <span :class="['tag', statusClass(m.status)]">{{ statusText(m.status) }}</span>
        </div>
        <p class="material-content">{{ m.content.substring(0, 200) }}{{ m.content.length > 200 ? '...' : '' }}</p>
        
        <!-- 进度条 - 仅在处理中时显示 -->
        <div v-if="m.status === 'pending' && progressData[m.id]" class="progress-section">
          <div class="progress-info">
            <span class="progress-text">{{ progressData[m.id].message }}</span>
            <span class="progress-percent">{{ progressData[m.id].progress }}%</span>
          </div>
          <div class="progress-bar">
            <div 
              class="progress-bar-fill" 
              :style="{ width: progressData[m.id].progress + '%' }"
            ></div>
          </div>
        </div>
        
        <div v-if="m.key_points && m.key_points.length" class="key-points">
          <h4>核心知识点</h4>
          <div class="points-list">
            <span v-for="(p, i) in m.key_points.slice(0, 5)" :key="i" class="tag tag-blue">
              {{ p.point }}
            </span>
            <span v-if="m.key_points.length > 5" class="tag">+{{ m.key_points.length - 5 }}</span>
          </div>
        </div>
        
        <div class="card-footer">
          <span class="time">{{ formatTime(m.created_at) }}</span>
          <button class="btn btn-danger" @click="deleteMaterial(m.id)">删除</button>
        </div>
      </div>
    </div>

    <!-- 上传资料弹窗 -->
    <div v-if="showAddMaterial" class="modal-overlay" @click.self="showAddMaterial = false">
      <div class="modal modal-lg">
        <h3>上传学习资料</h3>
        <div class="form-group">
          <label>学习方向</label>
          <select v-model="newMaterial.direction_id" class="form-control">
            <option :value="null" disabled>请选择方向</option>
            <option v-for="d in directions" :key="d.id" :value="d.id">{{ d.name }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>资料标题</label>
          <input v-model="newMaterial.title" class="form-control" placeholder="如：Python基础教程第一章">
        </div>
        <div class="form-group">
          <label>资料内容</label>
          <textarea 
            v-model="newMaterial.content" 
            class="form-control" 
            rows="10"
            placeholder="粘贴或输入学习资料内容，系统将自动提炼知识点并生成题目..."
          ></textarea>
        </div>
        <div class="modal-actions">
          <button class="btn" @click="showAddMaterial = false">取消</button>
          <button 
            class="btn btn-primary" 
            @click="addMaterial" 
            :disabled="!canSubmit || submitting"
          >
            {{ submitting ? '处理中...' : '上传并生成题目' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { directionsApi, materialsApi } from '@/api'

const route = useRoute()
const directions = ref([])
const materials = ref([])
const loading = ref(true)
const submitting = ref(false)
const showAddMaterial = ref(false)
const selectedDirection = ref(null)
const progressData = ref({}) // 存储各资料的进度信息
const eventSources = ref({}) // 存储SSE连接

const newMaterial = ref({
  direction_id: null,
  title: '',
  content: ''
})

const canSubmit = computed(() => {
  return newMaterial.value.direction_id && 
         newMaterial.value.title && 
         newMaterial.value.content
})

const statusClass = (status) => {
  const map = {
    pending: 'tag-yellow',
    processed: 'tag-green',
    failed: 'tag-red'
  }
  return map[status] || ''
}

const statusText = (status) => {
  const map = {
    pending: '处理中',
    processed: '已完成',
    failed: '处理失败'
  }
  return map[status] || status
}

const formatTime = (time) => {
  return new Date(time).toLocaleString('zh-CN')
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
  loading.value = true
  try {
    const res = await materialsApi.getAll(selectedDirection.value)
    materials.value = res.data
  } catch (e) {
    console.error('加载资料失败:', e)
  } finally {
    loading.value = false
  }
}

const addMaterial = async () => {
  if (!canSubmit.value) return
  submitting.value = true
  try {
    const res = await materialsApi.create(newMaterial.value)
    const materialId = res.data.id
    
    showAddMaterial.value = false
    newMaterial.value = { direction_id: null, title: '', content: '' }
    await loadMaterials()
    
    // 如果状态是pending，启动SSE连接监听进度
    if (res.data.status === 'pending') {
      connectProgressStream(materialId)
    }
    
    // 滚动到新上传的资料位置，显示生成进度
    setTimeout(() => {
      const materialCard = document.querySelector(`[data-material-id="${materialId}"]`)
      if (materialCard) {
        materialCard.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
    }, 300)
  } catch (e) {
    alert('上传失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    submitting.value = false
  }
}

// 连接SSE流获取实时进度
const connectProgressStream = (materialId) => {
  // 如果已有连接，先关闭
  if (eventSources.value[materialId]) {
    eventSources.value[materialId].close()
  }
  
  const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const eventSource = new EventSource(`${baseURL}/api/materials/${materialId}/progress`)
  
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      progressData.value[materialId] = data
      
      // 如果完成或失败，关闭连接并刷新列表
      if (data.step === 'completed' || data.step === 'error') {
        eventSource.close()
        delete eventSources.value[materialId]
        setTimeout(() => {
          loadMaterials()
          delete progressData.value[materialId]
        }, 1000)
      }
    } catch (e) {
      console.error('解析进度数据失败:', e)
    }
  }
  
  eventSource.onerror = (error) => {
    console.error('SSE连接错误:', error)
    eventSource.close()
    delete eventSources.value[materialId]
  }
  
  eventSources.value[materialId] = eventSource
}

const deleteMaterial = async (id) => {
  if (!confirm('确定删除此资料？相关题目也会被删除。')) return
  try {
    await materialsApi.delete(id)
    await loadMaterials()
  } catch (e) {
    alert('删除失败: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(async () => {
  await loadDirections()
  // 从URL获取方向筛选
  if (route.query.direction) {
    selectedDirection.value = parseInt(route.query.direction)
  }
  await loadMaterials()
  
  // 检查是否有pending状态的资料，启动进度监听
  materials.value.forEach(m => {
    if (m.status === 'pending') {
      connectProgressStream(m.id)
    }
  })
})

// 组件卸载时关闭所有SSE连接
onUnmounted(() => {
  Object.values(eventSources.value).forEach(es => es.close())
  eventSources.value = {}
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.page-header h1 {
  color: #4fc3f7;
}

.filter-bar {
  margin-bottom: 1.5rem;
}

.filter-bar select {
  max-width: 300px;
}

.material-card {
  margin-bottom: 1rem;
}

.material-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.material-header h3 {
  color: #4fc3f7;
}

.material-content {
  color: #888;
  font-size: 0.9rem;
  margin-bottom: 1rem;
  line-height: 1.6;
}

.key-points {
  margin-bottom: 1rem;
}

.key-points h4 {
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.points-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 1rem;
  border-top: 1px solid #333;
}

.time {
  color: #666;
  font-size: 0.85rem;
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
  max-width: 600px;
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

/* 进度条样式 */
.progress-section {
  margin-bottom: 1rem;
  padding: 1rem;
  background: #16213e;
  border-radius: 8px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.progress-text {
  color: #4fc3f7;
  font-size: 0.9rem;
}

.progress-percent {
  color: #4fc3f7;
  font-weight: bold;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #0f1419;
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #4fc3f7, #29b6f6);
  transition: width 0.3s ease;
}
</style>
