<template>
  <div class="materials-page">
    <div class="page-header">
      <h1>资料管理</h1>
      <button v-if="activeTab === 'materials'" class="btn btn-primary" @click="showAddMaterial = true">上传资料</button>
    </div>

    <!-- Tab 切换 -->
    <div class="page-tabs">
      <button 
        :class="['page-tab-btn', { active: activeTab === 'materials' }]" 
        @click="activeTab = 'materials'"
      >资料管理</button>
      <button 
        :class="['page-tab-btn', { active: activeTab === 'parse' }]" 
        @click="activeTab = 'parse'"
      >知识解析</button>
    </div>

    <!-- ============ 资料管理 Tab ============ -->
    <div v-if="activeTab === 'materials'">
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
        
        <!-- 方向编辑 -->
        <div class="material-direction">
          <span class="direction-label">学习方向：</span>
          <select 
            v-model="m.direction_id" 
            class="form-control form-control-sm"
            @change="updateMaterialDirection(m.id, m.direction_id)"
          >
            <option v-for="d in directions" :key="d.id" :value="d.id">{{ d.name }}</option>
          </select>
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
            >上传文件</button>
            <button 
              :class="['tab-btn', { active: inputMode === 'url' }]" 
              @click="inputMode = 'url'"
            >网页链接</button>
          </div>
          <!-- 文本输入模式 -->
          <textarea 
            v-if="inputMode === 'text'"
            v-model="newMaterial.content" 
            class="form-control" 
            rows="10"
            placeholder="粘贴或输入学习资料内容，系统将自动提炼知识点并生成题目..."
          ></textarea>
          <!-- 文件上传模式 -->
          <div v-else-if="inputMode === 'file'" class="file-upload-area">
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
                accept=".pdf,.docx,.md,.txt" 
                style="display: none"
                @change="handleFileSelect"
              >
              <div v-if="!selectedFile" class="drop-hint">
                <span class="drop-icon">&#128196;</span>
                <p>点击选择或拖拽文件到此处</p>
                <p class="drop-sub">支持 .pdf, .docx, .md, .txt 格式</p>
              </div>
              <div v-else class="file-info">
                <span class="file-name">{{ selectedFile.name }}</span>
                <span class="file-size">{{ formatFileSize(selectedFile.size) }}</span>
                <button class="btn-remove" @click.stop="clearFile">&times;</button>
              </div>
            </div>
          </div>
          <!-- URL输入模式 -->
          <div v-else-if="inputMode === 'url'" class="form-group url-input-group">
            <input 
              v-model="newMaterial.url" 
              class="form-control" 
              placeholder="https://example.com/article"
            >
            <p class="input-hint">输入网页链接，系统将自动抓取内容并生成题目</p>
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

    <!-- ============ 知识解析 Tab ============ -->
    <div v-if="activeTab === 'parse'" class="parse-tab">
      <!-- 方向筛选 -->
      <div class="filter-bar">
        <select v-model="parseSelectedDirection" class="form-control" @change="loadParseTasks">
          <option :value="null">全部方向</option>
          <option v-for="d in directions" :key="d.id" :value="d.id">{{ d.name }}</option>
        </select>
      </div>

      <!-- 解析表单 -->
      <div class="card parse-form-card">
        <h3>新建解析任务</h3>
        <div class="form-group">
          <label>学习方向（可选）</label>
          <select v-model="parseForm.direction_id" class="form-control">
            <option :value="null">不指定方向</option>
            <option v-for="d in directions" :key="d.id" :value="d.id">{{ d.name }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>资料标题</label>
          <input v-model="parseForm.title" class="form-control" placeholder="如：Python 装饰器详解">
        </div>

        <!-- 输入模式切换 -->
        <div class="input-mode-tabs">
          <button 
            :class="['tab-btn', { active: parseInputMode === 'text' }]" 
            @click="switchParseMode('text')"
          >文本输入</button>
          <button 
            :class="['tab-btn', { active: parseInputMode === 'file' }]" 
            @click="switchParseMode('file')"
          >上传文件</button>
          <button 
            :class="['tab-btn', { active: parseInputMode === 'url' }]" 
            @click="switchParseMode('url')"
          >网页链接</button>
        </div>

        <!-- 文本输入模式 -->
        <div v-if="parseInputMode === 'text'" class="form-group">
          <textarea 
            v-model="parseForm.text" 
            class="form-control" 
            rows="8"
            placeholder="粘贴或输入要解析的学习资料内容..."
          ></textarea>
        </div>

        <!-- 文件上传模式 -->
        <div v-if="parseInputMode === 'file'" class="form-group">
          <div class="file-upload-area">
            <div 
              class="drop-zone"
              :class="{ 'drag-over': parseIsDragOver }"
              @dragover.prevent="parseIsDragOver = true"
              @dragleave="parseIsDragOver = false"
              @drop.prevent="handleParseFileDrop"
              @click="parseFileInput?.click()"
            >
              <input 
                ref="parseFileInput"
                type="file" 
                accept=".pdf,.docx,.md,.txt" 
                style="display: none"
                @change="handleParseFileSelect"
              >
              <div v-if="!parseForm.file" class="drop-hint">
                <span class="drop-icon">&#128196;</span>
                <p>点击选择或拖拽文件到此处</p>
                <p class="drop-sub">支持 .pdf, .docx, .md, .txt 格式</p>
              </div>
              <div v-else class="file-info">
                <span class="file-name">{{ parseForm.file.name }}</span>
                <span class="file-size">{{ formatFileSize(parseForm.file.size) }}</span>
                <button class="btn-remove" @click.stop="clearParseFile">&times;</button>
              </div>
            </div>
          </div>
        </div>

        <!-- URL 输入模式 -->
        <div v-if="parseInputMode === 'url'" class="form-group">
          <input 
            v-model="parseForm.url" 
            class="form-control" 
            placeholder="https://example.com/article"
          >
        </div>

        <button 
          class="btn btn-primary" 
          @click="submitParseTask" 
          :disabled="!canSubmitParse || parseSubmitting"
        >
          {{ parseSubmitting ? '解析中...' : '开始解析' }}
        </button>
      </div>

      <!-- 解析任务列表 -->
      <h3 class="section-title" v-if="!parseLoading">解析记录</h3>
      <div v-if="parseLoading" class="loading">加载中...</div>
      <div v-else-if="parseTasks.length === 0" class="empty">
        暂无解析任务，请创建新任务
      </div>
      <div v-else class="parse-tasks-list">
        <div 
          v-for="task in parseTasks" 
          :key="task.id" 
          class="card task-card"
          @click="showTaskDetailFn(task.id)"
        >
          <div class="task-header">
            <h3>{{ task.title }}</h3>
            <span :class="['tag', parseStatusClass(task.status)]">
              {{ parseStatusText(task.status) }}
            </span>
          </div>
          <div class="task-meta">
            <span class="tag tag-blue">{{ parseSourceText(task.source_type) }}</span>
            <span class="time">{{ formatTime(task.created_at) }}</span>
          </div>
          <div v-if="task.summary" class="task-summary">
            {{ task.summary }}
          </div>
          <div class="card-footer">
            <button class="btn btn-sm" @click.stop="showTaskDetailFn(task.id)">查看详情</button>
            <button class="btn btn-sm btn-danger" @click.stop="deleteParseTask(task.id)">删除</button>
          </div>
        </div>
      </div>

      <!-- 任务详情弹窗 -->
      <div v-if="showTaskDetailModal" class="modal-overlay" @click.self="showTaskDetailModal = false">
        <div class="modal modal-lg">
          <div class="modal-detail-header">
            <h3>{{ taskDetail?.title }}</h3>
            <button class="btn-close" @click="showTaskDetailModal = false">&times;</button>
          </div>
          
          <div v-if="taskDetail" class="task-detail-content">
            <!-- 基本信息 -->
            <div class="detail-section">
              <h4>基本信息</h4>
              <div class="info-grid">
                <div class="info-row">
                  <span class="info-label">来源类型</span>
                  <span class="tag tag-blue">{{ parseSourceText(taskDetail.source_type) }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">状态</span>
                  <span :class="['tag', parseStatusClass(taskDetail.status)]">
                    {{ parseStatusText(taskDetail.status) }}
                  </span>
                </div>
                <div class="info-row">
                  <span class="info-label">创建时间</span>
                  <span>{{ formatTime(taskDetail.created_at) }}</span>
                </div>
                <div class="info-row">
                  <span class="info-label">学习方向</span>
                  <select 
                    v-model="taskDetail.direction_id" 
                    class="form-control form-control-sm"
                    @change="updateTaskDirection(taskDetail.id, taskDetail.direction_id)"
                  >
                    <option :value="null">未指定</option>
                    <option v-for="d in directions" :key="d.id" :value="d.id">{{ d.name }}</option>
                  </select>
                </div>
              </div>
              <div v-if="taskDetail.summary" class="detail-summary">
                <span class="info-label">摘要</span>
                <p>{{ taskDetail.summary }}</p>
              </div>
            </div>

            <!-- 操作按钮 -->
            <div v-if="taskDetail.status === 'completed'" class="detail-section detail-actions">
              <button 
                class="btn btn-primary" 
                @click="generateQuestionsFromTask(taskDetail.id)"
                :disabled="!taskDetail.direction_id || generatingQuestions"
              >
                {{ generatingQuestions ? '生成中...' : '生成题目' }}
              </button>
              <span v-if="!taskDetail.direction_id" class="hint-text">请先选择学习方向</span>
            </div>

            <!-- 知识点列表 -->
            <div v-if="taskDetail.knowledge_points?.length" class="detail-section">
              <h4>知识点 ({{ taskDetail.knowledge_points.length }})</h4>
              <div class="knowledge-points-list">
                <div 
                  v-for="kp in taskDetail.knowledge_points" 
                  :key="kp.id" 
                  class="knowledge-point-item"
                >
                  <div class="kp-header">
                    <span class="kp-name">{{ kp.name }}</span>
                    <span class="tag tag-blue">重要度 {{ kp.importance }}/5</span>
                    <span v-if="kp.category" class="tag tag-purple">{{ kp.category }}</span>
                  </div>
                  <p class="kp-description">{{ kp.description }}</p>
                </div>
              </div>
            </div>

            <!-- 最佳实践列表 -->
            <div v-if="taskDetail.best_practices?.length" class="detail-section">
              <h4>最佳实践 ({{ taskDetail.best_practices.length }})</h4>
              <div class="best-practices-list">
                <div 
                  v-for="bp in taskDetail.best_practices" 
                  :key="bp.id" 
                  class="best-practice-item"
                >
                  <h5>{{ bp.title }}</h5>
                  <p class="bp-content">{{ bp.content }}</p>
                  <div v-if="bp.scenario" class="bp-extra">
                    <strong>适用场景：</strong>{{ bp.scenario }}
                  </div>
                  <div v-if="bp.notes" class="bp-extra">
                    <strong>注意事项：</strong>{{ bp.notes }}
                  </div>
                </div>
              </div>
            </div>

            <!-- 错误信息 -->
            <div v-if="taskDetail.error_message" class="detail-section">
              <h4>错误信息</h4>
              <div class="error-message">{{ taskDetail.error_message }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { directionsApi, materialsApi, parseApi } from '@/api'
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
  content: '',
  url: ''
})

const inputMode = ref('text')
const selectedFile = ref(null)
const isDragOver = ref(false)
const fileInput = ref(null)

// ============ Tab 切换 ============
const activeTab = ref('materials')

// ============ 知识解析相关 ============
const parseSelectedDirection = ref(null)
const parseLoading = ref(false)
const parseSubmitting = ref(false)
const parseTasks = ref([])
const parseInputMode = ref('text')
const parseIsDragOver = ref(false)
const parseFileInput = ref(null)
const showTaskDetailModal = ref(false)
const taskDetail = ref(null)
const generatingQuestions = ref(false)

const parseForm = ref({
  direction_id: null,
  title: '',
  text: '',
  file: null,
  url: ''
})

// Markdown 预览 HTML
const previewHtml = computed(() => {
  if (!newMaterial.value.content) return ''
  return marked(newMaterial.value.content)
})

const canSubmit = computed(() => {
  if (!newMaterial.value.direction_id || !newMaterial.value.title) return false
  switch (inputMode.value) {
    case 'text': return newMaterial.value.content.trim().length > 0
    case 'file': return selectedFile.value !== null
    case 'url': return newMaterial.value.url.trim().length > 0
    default: return false
  }
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

const validateAndSetFile = (file) => {
  const allowedExtensions = ['.pdf', '.docx', '.md', '.txt']
  const fileExt = '.' + file.name.split('.').pop().toLowerCase()
  if (!allowedExtensions.includes(fileExt)) {
    alert('不支持的文件格式，请上传 .pdf, .docx, .md 或 .txt 文件')
    return
  }
  selectedFile.value = file
  // 自动填充标题（去掉扩展名）
  if (!newMaterial.value.title) {
    newMaterial.value.title = file.name.replace(/\.[^/.]+$/, '')
  }
}

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) validateAndSetFile(file)
}

const handleFileDrop = (event) => {
  isDragOver.value = false
  const file = event.dataTransfer.files[0]
  if (file) validateAndSetFile(file)
}

const clearFile = () => {
  selectedFile.value = null
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
    let res
    switch (inputMode.value) {
      case 'text':
        res = await materialsApi.create({
          title: newMaterial.value.title,
          content: newMaterial.value.content,
          direction_id: newMaterial.value.direction_id
        })
        break
      case 'file':
        res = await materialsApi.uploadFile(
          newMaterial.value.title,
          selectedFile.value,
          newMaterial.value.direction_id
        )
        break
      case 'url':
        res = await materialsApi.fromUrl({
          title: newMaterial.value.title,
          url: newMaterial.value.url,
          direction_id: newMaterial.value.direction_id
        })
        break
    }
    const materialId = res.data.id
    
    showAddMaterial.value = false
    newMaterial.value = { direction_id: null, title: '', content: '', url: '' }
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
    } else if (e.response?.status === 400) {
      alert('上传失败: ' + (e.response?.data?.detail || '请求参数错误'))
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

// ============ 知识解析：计算属性 ============
const canSubmitParse = computed(() => {
  if (!parseForm.value.title) return false
  switch (parseInputMode.value) {
    case 'text': return parseForm.value.text.trim().length > 0
    case 'file': return parseForm.value.file !== null
    case 'url': return parseForm.value.url.trim().length > 0
    default: return false
  }
})

// ============ 知识解析：数据加载 ============
const loadParseTasks = async () => {
  parseLoading.value = true
  try {
    const res = await parseApi.getTasks({ direction_id: parseSelectedDirection.value })
    parseTasks.value = res.data
  } catch (e) {
    console.error('加载解析任务失败:', e)
    alert('加载解析任务失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    parseLoading.value = false
  }
}

// ============ 知识解析：表单提交 ============
const submitParseTask = async () => {
  if (!canSubmitParse.value) return
  parseSubmitting.value = true
  try {
    switch (parseInputMode.value) {
      case 'text':
        await parseApi.parseText({
          title: parseForm.value.title,
          text: parseForm.value.text,
          direction_id: parseForm.value.direction_id
        })
        break
      case 'file':
        await parseApi.parseFile(
          parseForm.value.title,
          parseForm.value.file,
          parseForm.value.direction_id
        )
        break
      case 'url':
        await parseApi.parseUrl({
          title: parseForm.value.title,
          url: parseForm.value.url,
          direction_id: parseForm.value.direction_id
        })
        break
    }
    parseForm.value = { direction_id: null, title: '', text: '', file: null, url: '' }
    parseInputMode.value = 'text'
    if (parseFileInput.value) parseFileInput.value.value = ''
    await loadParseTasks()
  } catch (e) {
    console.error('提交解析任务失败:', e)
    alert('提交失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    parseSubmitting.value = false
  }
}

// ============ 知识解析：输入模式切换 ============
const switchParseMode = (mode) => {
  parseInputMode.value = mode
}

// ============ 知识解析：文件处理 ============
const handleParseFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) validateAndSetParseFile(file)
}

const handleParseFileDrop = (event) => {
  parseIsDragOver.value = false
  const file = event.dataTransfer.files[0]
  if (file) validateAndSetParseFile(file)
}

const validateAndSetParseFile = (file) => {
  const allowedExtensions = ['.pdf', '.docx', '.md', '.txt']
  const fileExt = '.' + file.name.split('.').pop().toLowerCase()
  if (!allowedExtensions.includes(fileExt)) {
    alert('不支持的文件格式，请上传 .pdf, .docx, .md 或 .txt 文件')
    return
  }
  parseForm.value.file = file
  if (!parseForm.value.title) {
    parseForm.value.title = file.name.replace(/\.[^/.]+$/, '')
  }
}

const clearParseFile = () => {
  parseForm.value.file = null
  if (parseFileInput.value) parseFileInput.value.value = ''
}

// ============ 知识解析：任务详情与删除 ============
const showTaskDetailFn = async (taskId) => {
  try {
    const res = await parseApi.getTaskDetail(taskId)
    taskDetail.value = res.data
    showTaskDetailModal.value = true
  } catch (e) {
    console.error('加载任务详情失败:', e)
    alert('加载详情失败: ' + (e.response?.data?.detail || e.message))
  }
}

const deleteParseTask = async (taskId) => {
  if (!confirm('确定要删除这个解析任务吗？')) return
  try {
    await parseApi.deleteTask(taskId)
    await loadParseTasks()
  } catch (e) {
    console.error('删除任务失败:', e)
    alert('删除失败: ' + (e.response?.data?.detail || e.message))
  }
}

// ============ 更新方向 ============
const updateMaterialDirection = async (materialId, directionId) => {
  try {
    await materialsApi.updateDirection(materialId, directionId)
  } catch (e) {
    console.error('更新方向失败:', e)
    alert('更新方向失败: ' + (e.response?.data?.detail || e.message))
    await loadMaterials() // 失败后刷新恢复原状态
  }
}

const updateTaskDirection = async (taskId, directionId) => {
  try {
    await parseApi.updateTaskDirection(taskId, directionId)
    await loadParseTasks() // 刷新列表
  } catch (e) {
    console.error('更新方向失败:', e)
    alert('更新方向失败: ' + (e.response?.data?.detail || e.message))
  }
}

// ============ 从解析任务生成题目 ============
const generateQuestionsFromTask = async (taskId) => {
  if (!confirm('确定要基于此解析结果生成题目吗？这将创建一份新的学习资料。')) return
  
  generatingQuestions.value = true
  try {
    const res = await parseApi.generateQuestions(taskId)
    alert(`题目生成成功！已创建资料「${res.data.title}」`)
    showTaskDetailModal.value = false
    // 切换到资料管理 Tab 并刷新
    activeTab.value = 'materials'
    await loadMaterials()
  } catch (e) {
    console.error('生成题目失败:', e)
    alert('生成题目失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    generatingQuestions.value = false
  }
}

// ============ 知识解析：状态映射 ============
const parseStatusClass = (status) => {
  const map = { pending: 'tag-yellow', processing: 'tag-yellow', completed: 'tag-green', failed: 'tag-red' }
  return map[status] || ''
}

const parseStatusText = (status) => {
  const map = { pending: '待处理', processing: '处理中', completed: '已完成', failed: '失败' }
  return map[status] || status
}

const parseSourceText = (sourceType) => {
  const map = { text: '文本', file: '文件', url: '网页' }
  return map[sourceType] || sourceType
}

onMounted(async () => {
  await loadDirections()
  await loadMaterials()
})

// 切换到知识解析 Tab 时自动加载任务列表
watch(activeTab, (newTab) => {
  if (newTab === 'parse' && parseTasks.value.length === 0) {
    loadParseTasks()
  }
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

/* URL Input */
.url-input-group {
  margin-top: 0;
}

.input-hint {
  margin: 0.5rem 0 0;
  font-size: 0.8rem;
  color: var(--color-text-tertiary);
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

  .parse-tasks-list {
    grid-template-columns: 1fr;
  }

  .page-tabs .page-tab-btn {
    padding: 0.75rem 1rem;
    font-size: 0.9rem;
  }
}

/* ============ Page Tab System ============ */
.page-tabs {
  display: flex;
  margin-bottom: 2rem;
  border-bottom: 2px solid var(--color-border);
  gap: 0.5rem;
}

.page-tab-btn {
  padding: 1rem 2rem;
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all var(--transition-fast);
  margin-bottom: -2px;
}

.page-tab-btn:hover {
  color: var(--color-text-primary);
}

.page-tab-btn.active {
  color: var(--color-accent-primary);
  border-bottom-color: var(--color-accent-primary);
}

/* ============ Parse Tab ============ */
.parse-tab {
  animation: slideUp 0.4s ease-out;
}

.parse-form-card {
  margin-bottom: 2rem;
  padding: 1.5rem;
}

.parse-form-card h3 {
  margin: 0 0 1.5rem 0;
  font-size: 1.25rem;
  color: var(--color-text-primary);
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 1.5rem;
}

/* Parse Tasks List */
.parse-tasks-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 1.5rem;
}

.task-card {
  cursor: pointer;
  transition: all var(--transition-base);
  animation: slideUp 0.4s ease-out backwards;
}

.task-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.15);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
  gap: 1rem;
}

.task-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  flex: 1;
  word-break: break-word;
}

.task-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.task-summary {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* ============ Task Detail Modal ============ */
.modal-detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border);
}

.modal-detail-header h3 {
  margin: 0;
  flex: 1;
  word-break: break-word;
}

.btn-close {
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  font-size: 2rem;
  cursor: pointer;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.btn-close:hover {
  background: var(--color-error-bg, rgba(239, 68, 68, 0.1));
  color: var(--color-error);
}

.task-detail-content {
  max-height: 70vh;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.detail-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--color-border);
}

.detail-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.detail-section h4 {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin: 0 0 1rem 0;
}

.info-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  margin-bottom: 1rem;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.info-label {
  font-weight: 500;
  color: var(--color-text-secondary);
  font-size: 0.875rem;
}

.detail-summary {
  margin-top: 0.75rem;
}

.detail-summary p {
  margin: 0.5rem 0 0 0;
  color: var(--color-text-primary);
  line-height: 1.7;
  font-size: 0.95rem;
}

/* Knowledge Points */
.knowledge-points-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.knowledge-point-item {
  background: var(--color-bg-tertiary);
  padding: 1rem 1.25rem;
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--color-accent-primary);
}

.kp-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}

.kp-name {
  font-weight: 600;
  color: var(--color-text-primary);
  font-size: 1rem;
}

.kp-description {
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0;
  font-size: 0.9rem;
}

/* Best Practices */
.best-practices-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.best-practice-item {
  background: var(--color-bg-tertiary);
  padding: 1rem 1.25rem;
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--color-success);
}

.best-practice-item h5 {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.bp-content {
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0 0 0.75rem 0;
  font-size: 0.9rem;
}

.bp-extra {
  padding: 0.5rem 0.75rem;
  background: rgba(99, 102, 241, 0.05);
  border-radius: 4px;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  margin-top: 0.5rem;
  line-height: 1.5;
}

.bp-extra strong {
  color: var(--color-text-primary);
  margin-right: 0.25rem;
}

/* Error Message */
.error-message {
  padding: 1rem;
  background: rgba(239, 68, 68, 0.1);
  border-radius: var(--radius-sm);
  color: var(--color-error);
  font-size: 0.9rem;
  line-height: 1.6;
}

/* Material Direction Edit */
.material-direction {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--color-border);
}

.direction-label {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.form-control-sm {
  padding: 0.4rem 0.75rem;
  font-size: 0.875rem;
  max-width: 200px;
}

/* Detail Actions */
.detail-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding-top: 1rem;
}

.hint-text {
  font-size: 0.875rem;
  color: var(--color-text-tertiary);
}
</style>