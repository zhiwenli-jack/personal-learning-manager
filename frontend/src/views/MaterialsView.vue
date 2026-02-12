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

    <!-- 警告提示 -->
    <div v-if="showApiKeyWarning" class="alert alert-warning">
      <p>⚠️ API密钥未配置</p>
      <p>请联系管理员设置QWEN_API_KEY，否则无法处理学习资料。</p>
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
        <div class="material-content markdown-body" v-html="renderMaterialContent(m.content)"></div>
        
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
          <!-- 输入方式切换 -->
          <div class="input-mode-tabs">
            <button 
              :class="['tab-btn', { active: inputMode === 'text' }]" 
              @click="inputMode = 'text'"
            >文本输入</button>
            <button 
              :class="['tab-btn', { active: inputMode === 'file' }]" 
              @click="inputMode = 'file'"
            >上传MD文件</button>
          </div>
          <!-- 文本输入模式 -->
          <textarea 
            v-if="inputMode === 'text'"
            v-model="newMaterial.content" 
            class="form-control" 
            rows="10"
            placeholder="粘贴或输入学习资料内容，系统将自动提炼知识点并生成题目..."
          ></textarea>
          <!-- MD文件上传模式 -->
          <div v-else class="file-upload-area">
            <div 
              class="drop-zone"
              :class="{ 'drag-over': isDragOver }"
              @dragover.prevent="isDragOver = true"
              @dragleave="isDragOver = false"
              @drop.prevent="handleFileDrop"
              @click="fileInput?.click()"
            >
              <input 
                ref="fileInput"
                type="file" 
                accept=".md" 
                style="display: none"
                @change="handleFileSelect"
              >
              <div v-if="!selectedFile" class="drop-hint">
                <span class="drop-icon">&#128196;</span>
                <p>点击选择或拖拽 .md 文件到此处</p>
                <p class="drop-sub">仅支持 Markdown (.md) 文件</p>
              </div>
              <div v-else class="file-info">
                <span class="file-name">{{ selectedFile.name }}</span>
                <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
                <button class="btn-remove" @click.stop="clearFile">&times;</button>
              </div>
            </div>
            <!-- Markdown 预览 -->
            <div v-if="newMaterial.content && inputMode === 'file'" class="md-preview">
              <div class="md-preview-header">
                <span>内容预览</span>
              </div>
              <div class="md-preview-body markdown-body" v-html="previewHtml"></div>
            </div>
          </div>
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
import { marked } from 'marked'

const route = useRoute()
const directions = ref([])
const materials = ref([])
const loading = ref(true)
const submitting = ref(false)
const showAddMaterial = ref(false)
const selectedDirection = ref(null)
const progressData = ref({}) // 存储各资料的进度信息
const eventSources = ref({}) // 存储SSE连接
const showApiKeyWarning = ref(false) // 显示API密钥警告

const newMaterial = ref({
  direction_id: null,
  title: '',
  content: ''
})

const inputMode = ref('text')
const selectedFile = ref(null)
const isDragOver = ref(false)
const fileInput = ref(null)

// Markdown 预览 HTML
const previewHtml = computed(() => {
  if (!newMaterial.value.content) return ''
  return marked(newMaterial.value.content)
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

// 渲染资料内容：截取前500字符，解析为Markdown HTML
const renderMaterialContent = (content) => {
  if (!content) return ''
  const truncated = content.length > 500 ? content.substring(0, 500) + '...' : content
  return marked(truncated)
}

const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const readMdFile = (file) => {
  if (!file || !file.name.endsWith('.md')) {
    alert('请选择 .md 格式的文件')
    return
  }
  selectedFile.value = file
  const reader = new FileReader()
  reader.onload = (e) => {
    newMaterial.value.content = e.target.result
    // 自动填充标题（去掉 .md 后缀）
    if (!newMaterial.value.title) {
      newMaterial.value.title = file.name.replace(/\.md$/, '')
    }
  }
  reader.onerror = () => {
    alert('文件读取失败，请重试')
  }
  reader.readAsText(file, 'UTF-8')
}

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) readMdFile(file)
}

const handleFileDrop = (event) => {
  isDragOver.value = false
  const file = event.dataTransfer.files[0]
  if (file) readMdFile(file)
}

const clearFile = () => {
  selectedFile.value = null
  newMaterial.value.content = ''
  if (fileInput.value) fileInput.value.value = ''
}

const loadDirections = async () => {
  try {
    const res = await directionsApi.getAll()
    directions.value = res.data
  } catch (e) {
    console.error('加载方向失败:', e)
    alert('加载学习方向失败: ' + (e.response?.data?.detail || e.message))
  }
}

const loadMaterials = async () => {
  loading.value = true
  try {
    const res = await materialsApi.getAll(selectedDirection.value)
    materials.value = res.data
    // 检查是否有API密钥相关的错误
    showApiKeyWarning.value = false
  } catch (e) {
    console.error('加载资料失败:', e)
    // 检查是否是API密钥问题
    if (e.response?.status === 500 && e.response.data.detail.includes('API密钥')) {
      showApiKeyWarning.value = true
    }
    alert('加载资料失败: ' + (e.response?.data?.detail || e.message))
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
    selectedFile.value = null
    inputMode.value = 'text'
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
    console.error('上传失败:', e)
    // 检查错误类型
    if (e.response?.status === 500) {
      alert('上传失败: ' + (e.response?.data?.detail || '服务器内部错误'))
    } else if (e.response?.status === 404) {
      alert('上传失败: ' + (e.response?.data?.detail || '找不到指定资源'))
    } else {
      alert('上传失败: ' + (e.response?.data?.detail || e.message))
    }
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
      
      // 如果处理完成，更新资料状态并关闭连接
      if (data.step === 'completed' || data.step === 'error') {
        eventSource.close()
        // 刷新资料列表以更新状态
        setTimeout(() => loadMaterials(), 500)
      }
    } catch (e) {
      console.error('解析进度数据失败:', e)
    }
  }
  
  eventSource.onerror = (err) => {
    console.error('SSE连接错误:', err)
    eventSource.close()
    // 关闭连接后刷新页面以获取最终状态
    setTimeout(() => loadMaterials(), 1000)
  }
  
  // 存储事件源引用，便于后续管理
  eventSources.value[materialId] = eventSource
}

const deleteMaterial = async (id) => {
  if (!confirm('确定要删除这个资料吗？这将同时删除与之关联的所有题目。')) return
  
  try {
    await materialsApi.delete(id)
    await loadMaterials()
  } catch (e) {
    console.error('删除失败:', e)
    alert('删除失败: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(async () => {
  await loadDirections()
  await loadMaterials()
})

onUnmounted(() => {
  // 组件卸载时关闭所有SSE连接
  Object.values(eventSources.value).forEach(es => {
    if (es) es.close()
  })
})
</script>

<style scoped>
.materials-page {
  padding: 2rem;
  max-width: 1400px;
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

.filter-bar {
  margin-bottom: 1.5rem;
}

.filter-bar .form-control {
  max-width: 300px;
}

.materials-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 1.5rem;
}

.material-card {
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

.material-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  gap: 1rem;
}

.material-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.4;
  word-break: break-word;
  flex: 1;
}

.material-content {
  margin-bottom: 1rem;
  max-height: 180px;
  overflow-y: auto;
  padding-right: 0.5rem;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  line-height: 1.7;
}

.material-content ::v-deep h1,
.material-content ::v-deep h2,
.material-content ::v-deep h3 {
  color: var(--color-text-primary);
  margin-top: 0.75rem;
}

.material-content ::v-deep p {
  margin-bottom: 0.5rem;
}

/* Progress Styles */
.progress-section {
  margin: 1rem 0;
  padding: 1rem;
  background: rgba(99, 102, 241, 0.05);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.progress-text {
  color: var(--color-text-secondary);
}

.progress-percent {
  font-weight: 600;
  color: var(--color-accent-primary);
}

.progress-bar {
  height: 8px;
  background: var(--color-bg-tertiary);
  border-radius: 4px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--gradient-primary);
  border-radius: 4px;
  transition: width 0.4s ease;
  box-shadow: 0 0 10px rgba(99, 102, 241, 0.3);
}

/* Key Points */
.key-points {
  margin: 1rem 0;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}

.key-points h4 {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.key-points h4::before {
  content: '💡';
}

.points-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

/* Tag Styles Override */
.material-card .tag {
  font-size: 0.75rem;
  padding: 0.25rem 0.75rem;
  margin: 0;
}

.tag-yellow {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.tag-green {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.tag-red {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--color-border);
}

.time {
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
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
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-lg);
  animation: scaleIn 0.3s ease-out;
}

.modal h3 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 1.5rem;
}

.modal-lg {
  max-width: 900px;
  max-height: 90vh;
  overflow-y: auto;
}

/* Input Mode Tabs */
.input-mode-tabs {
  display: flex;
  margin-bottom: 1rem;
  border-bottom: 1px solid var(--color-border);
  gap: 0.5rem;
}

.tab-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  border-bottom: 2px solid transparent;
  font-weight: 500;
  transition: all var(--transition-fast);
  position: relative;
}

.tab-btn:hover {
  color: var(--color-text-primary);
}

.tab-btn.active {
  color: var(--color-accent-primary);
  border-bottom-color: var(--color-accent-primary);
}

/* File Upload */
.file-upload-area {
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-md);
  padding: 2rem;
  text-align: center;
  transition: all var(--transition-base);
}

.drop-zone {
  cursor: pointer;
  transition: all var(--transition-base);
}

.drop-zone:hover {
  border-color: var(--color-accent-primary);
}

.drop-zone.drag-over {
  border-color: var(--color-accent-primary);
  background: rgba(99, 102, 241, 0.05);
  transform: scale(1.02);
}

.drop-hint {
  color: var(--color-text-secondary);
}

.drop-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.2));
  transition: transform var(--transition-base);
}

.drop-zone:hover .drop-icon {
  transform: scale(1.1) rotate(-5deg);
}

.drop-sub {
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.file-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}

.file-name {
  flex-grow: 1;
  text-align: left;
  margin-right: 0.75rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--color-text-primary);
  font-weight: 500;
}

.file-size {
  color: var(--color-text-tertiary);
  font-size: 0.875rem;
}

.btn-remove {
  background: var(--color-error);
  color: white;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--transition-fast);
}

.btn-remove:hover {
  background: #dc2626;
  transform: scale(1.1);
}

/* Markdown Preview */
.md-preview {
  margin-top: 1.5rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.md-preview-header {
  padding: 0.75rem 1rem;
  background: var(--color-bg-tertiary);
  font-weight: 600;
  color: var(--color-text-primary);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.md-preview-header::before {
  content: '📄';
}

.md-preview-body {
  padding: 1.5rem;
  max-height: 350px;
  overflow-y: auto;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  line-height: 1.7;
}

.md-preview-body ::v-deep h1,
.md-preview-body ::v-deep h2,
.md-preview-body ::v-deep h3 {
  color: var(--color-text-primary);
  margin: 1rem 0 0.5rem;
}

.md-preview-body ::v-deep p {
  margin-bottom: 0.75rem;
}

.md-preview-body ::v-deep ul,
.md-preview-body ::v-deep ol {
  padding-left: 1.5rem;
  margin-bottom: 0.75rem;
}

.md-preview-body ::v-deep code {
  background: var(--color-bg-tertiary);
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-size: 0.85rem;
}

.md-preview-body ::v-deep pre {
  background: var(--color-bg-tertiary);
  padding: 1rem;
  border-radius: var(--radius-sm);
  overflow-x: auto;
  margin: 0.75rem 0;
}

/* Alert */
.alert {
  padding: 1rem 1.25rem;
  border-radius: var(--radius-sm);
  margin-bottom: 1.5rem;
  border-left: 4px solid;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  animation: slideInLeft 0.3s ease-out;
}

@keyframes slideInLeft {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.alert-warning {
  background: rgba(245, 158, 11, 0.1);
  color: var(--color-warning);
  border-color: var(--color-warning);
}

.alert::before {
  content: '⚠️';
  font-size: 1.25rem;
}

.alert p {
  margin: 0;
  font-size: 0.9rem;
}

/* Responsive */
@media (max-width: 768px) {
  .materials-list {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .modal-lg {
    max-width: 100%;
    margin: 1rem;
  }
}
</style>