<template>
  <div class="learning-mode-page">
    <div class="page-header">
      <h1 class="page-title"><span class="gradient-text">学习模式</span></h1>
      <p class="page-subtitle">将学习资料智能提炼为分级课程，构建知识体系</p>
    </div>

    <!-- 标签页导航 -->
    <div class="page-tabs">
      <button :class="['page-tab-btn', { active: activeTab === 'overview' }]" @click="activeTab = 'overview'">课程概览</button>
      <button :class="['page-tab-btn', { active: activeTab === 'tree' }]" @click="switchTab('tree')" :disabled="!selectedCourse">知识树</button>
      <button :class="['page-tab-btn', { active: activeTab === 'mindmap' }]" @click="switchTab('mindmap')" :disabled="!selectedCourse">思维导图</button>
      <button :class="['page-tab-btn', { active: activeTab === 'progress' }]" @click="switchTab('progress')" :disabled="!selectedCourse">学习进度</button>
      <button :class="['page-tab-btn', { active: activeTab === 'recommendations' }]" @click="switchTab('recommendations')" :disabled="!selectedCourse">个性化推荐</button>
    </div>

    <!-- Tab 1: 课程概览 -->
    <div v-if="activeTab === 'overview'" class="tab-content">
      <div class="overview-layout">
        <!-- 左侧: 课程列表 -->
        <div class="courses-panel">
          <div class="panel-header">
            <h3>我的课程</h3>
            <button class="btn btn-primary btn-sm" @click="showCreateModal = true">+ 新建课程</button>
          </div>
          <div v-if="loading.courses" class="loading-state">加载中...</div>
          <div v-else-if="courses.length === 0" class="empty-state">
            <p>暂无课程，点击上方按钮创建</p>
          </div>
          <div v-else class="courses-list">
            <div
              v-for="course in courses"
              :key="course.id"
              :class="['course-card', 'card', { selected: selectedCourse && selectedCourse.id === course.id }]"
              @click="selectCourse(course)"
            >
              <div class="course-card-header">
                <h4>{{ course.title }}</h4>
                <span :class="['status-tag', 'tag-' + course.status]">{{ statusLabel(course.status) }}</span>
              </div>
              <p v-if="course.description" class="course-desc">{{ course.description }}</p>
              <div class="course-meta">
                <span>{{ course.material_count }} 份资料</span>
                <span>{{ course.total_points }} 个知识点</span>
              </div>
              <div v-if="course.status === 'completed'" class="progress-bar-mini">
                <div class="progress-bar-mini-fill" :style="{ width: course.progress_rate + '%' }"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧: 课程详情 -->
        <div class="detail-panel">
          <div v-if="!selectedCourse" class="empty-state">
            <p>选择左侧课程查看详情，或创建新课程</p>
          </div>
          <div v-else class="course-detail">
            <div class="detail-header">
              <h2>{{ selectedCourse.title }}</h2>
              <div class="detail-actions">
                <button
                  v-if="selectedCourse.status === 'pending' || selectedCourse.status === 'failed'"
                  class="btn btn-primary"
                  :disabled="loading.generate"
                  @click="generateCourse"
                >
                  {{ loading.generate ? 'AI 生成中...' : 'AI 生成课程' }}
                </button>
                <button
                  v-if="selectedCourse.status === 'completed'"
                  class="btn btn-secondary"
                  :disabled="loading.generate"
                  @click="generateCourse"
                >
                  {{ loading.generate ? '重新生成中...' : '重新生成' }}
                </button>
                <button class="btn btn-danger btn-sm" @click="deleteCourse">删除</button>
              </div>
            </div>
            <p v-if="selectedCourse.description" class="detail-desc">{{ selectedCourse.description }}</p>

            <div v-if="selectedCourse.status === 'generating'" class="generating-hint">
              <div class="spinner"></div>
              <p>AI 正在分析资料并生成课程内容，请稍候...</p>
            </div>

            <div v-if="selectedCourse.status === 'failed'" class="error-hint">
              <p>生成失败，请重试</p>
            </div>

            <div v-if="courseDetail" class="detail-stats">
              <div class="stat-grid">
                <div class="stat-card card">
                  <div class="stat-value">{{ courseDetail.total_points }}</div>
                  <div class="stat-label">知识点总数</div>
                </div>
                <div class="stat-card card">
                  <div class="stat-value">{{ courseDetail.mastered_points }}</div>
                  <div class="stat-label">已掌握</div>
                </div>
                <div class="stat-card card">
                  <div class="stat-value">{{ courseDetail.progress_rate.toFixed(1) }}%</div>
                  <div class="stat-label">学习进度</div>
                </div>
                <div class="stat-card card">
                  <div class="stat-value">{{ courseDetail.material_count }}</div>
                  <div class="stat-label">资料数</div>
                </div>
              </div>

              <!-- 知识点概况 -->
              <div v-if="courseDetail.knowledge_points.length > 0" class="kp-summary">
                <h3>知识点概况</h3>
                <div class="tier-summary">
                  <div class="tier-item">
                    <span class="tier-badge tier-beginner">入门</span>
                    <span>{{ tierCount('beginner') }} 个</span>
                  </div>
                  <div class="tier-item">
                    <span class="tier-badge tier-intermediate">进阶</span>
                    <span>{{ tierCount('intermediate') }} 个</span>
                  </div>
                  <div class="tier-item">
                    <span class="tier-badge tier-advanced">高级</span>
                    <span>{{ tierCount('advanced') }} 个</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 2: 知识树 -->
    <div v-if="activeTab === 'tree'" class="tab-content">
      <div v-if="!courseDetail || courseDetail.knowledge_points.length === 0" class="empty-state">
        <p>暂无知识点数据，请先生成课程内容</p>
      </div>
      <div v-else class="knowledge-tree">
        <div class="tree-columns">
          <div v-for="tier in ['beginner', 'intermediate', 'advanced']" :key="tier" class="tree-column">
            <h3 class="column-title">
              <span :class="['tier-badge', 'tier-' + tier]">{{ tierLabel(tier) }}</span>
              <span class="column-count">{{ tierPoints(tier).length }} 个知识点</span>
            </h3>
            <div class="tree-nodes">
              <div
                v-for="point in tierPoints(tier)"
                :key="point.id"
                :class="['knowledge-node', 'card', masteryClass(point.mastery_level)]"
              >
                <div class="node-header">
                  <span class="node-name">{{ point.name }}</span>
                  <span class="node-importance">
                    <span v-for="s in point.importance" :key="s" class="star">*</span>
                  </span>
                </div>
                <p class="node-desc" v-if="expandedNodes.has(point.id)">{{ point.description }}</p>
                <div class="node-meta">
                  <div class="mastery-ring" :title="'掌握度: ' + point.mastery_level.toFixed(0) + '%'">
                    <svg viewBox="0 0 36 36" class="ring-svg">
                      <path class="ring-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                      <path class="ring-fill" :stroke-dasharray="point.mastery_level + ', 100'" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                    </svg>
                    <span class="ring-text">{{ point.mastery_level.toFixed(0) }}%</span>
                  </div>
                  <span v-if="point.category" class="tag tag-blue">{{ point.category }}</span>
                  <span class="est-time">{{ point.estimated_minutes }}min</span>
                </div>
                <div class="node-relations" v-if="getPointRelations(point.id).length > 0">
                  <span v-for="rel in getPointRelations(point.id)" :key="rel.id" class="rel-tag" :title="rel.description">
                    {{ relTypeIcon(rel.relation_type) }} {{ rel.source_point_id === point.id ? rel.target_point_name : rel.source_point_name }}
                  </span>
                </div>
                <button class="node-toggle" @click="toggleNode(point.id)">
                  {{ expandedNodes.has(point.id) ? '收起' : '展开' }}
                </button>
                <div class="node-actions">
                  <button
                    v-if="point.mastery_level < 70"
                    class="btn btn-sm btn-learn"
                    :disabled="updatingPoints.has(point.id)"
                    @click="markAsLearned(point, 80)"
                  >
                    {{ updatingPoints.has(point.id) ? '更新中...' : '标记已学习' }}
                  </button>
                  <button
                    v-if="point.mastery_level >= 70 && point.mastery_level < 90"
                    class="btn btn-sm btn-master"
                    :disabled="updatingPoints.has(point.id)"
                    @click="markAsLearned(point, 100)"
                  >
                    {{ updatingPoints.has(point.id) ? '更新中...' : '标记精通' }}
                  </button>
                  <span v-if="point.mastery_level >= 90" class="mastered-label">已精通</span>
                  <button
                    v-if="point.mastery_level > 0"
                    class="btn btn-sm btn-reset-mastery"
                    :disabled="updatingPoints.has(point.id)"
                    @click="markAsLearned(point, 0)"
                  >
                    重置
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab 3: 思维导图 -->
    <div v-if="activeTab === 'mindmap'" class="tab-content">
      <div v-if="!mindmapData || !mindmapData.mindmap_markdown" class="empty-state">
        <p>暂无思维导图数据，请先生成课程内容</p>
      </div>
      <div v-else class="mindmap-container">
        <div class="mindmap-toolbar">
          <button class="btn btn-sm btn-secondary" @click="resetMindmap">重置视图</button>
          <button class="btn btn-sm btn-secondary" @click="fitMindmap">自适应</button>
        </div>
        <div class="mindmap-wrapper">
          <svg ref="mindmapSvg" class="mindmap-svg"></svg>
        </div>
      </div>
    </div>

    <!-- Tab 4: 学习进度 -->
    <div v-if="activeTab === 'progress'" class="tab-content">
      <div v-if="!progressData" class="empty-state">
        <p>暂无进度数据</p>
      </div>
      <div v-else class="progress-dashboard">
        <!-- 总体进度 -->
        <div class="progress-overview">
          <div class="progress-ring-large card">
            <svg viewBox="0 0 120 120" class="ring-svg-large">
              <circle class="ring-bg-large" cx="60" cy="60" r="52" />
              <circle
                class="ring-fill-large"
                cx="60" cy="60" r="52"
                :stroke-dasharray="(progressData.progress_rate / 100 * 326.7) + ' 326.7'"
              />
            </svg>
            <div class="ring-center-text">
              <span class="ring-percent">{{ progressData.progress_rate.toFixed(1) }}%</span>
              <span class="ring-label">总体进度</span>
            </div>
          </div>
          <div class="progress-stats-grid">
            <div class="progress-stat card">
              <span class="tier-badge tier-beginner">入门</span>
              <span class="progress-stat-value">{{ progressData.beginner_mastered }}/{{ progressData.beginner_total }}</span>
            </div>
            <div class="progress-stat card">
              <span class="tier-badge tier-intermediate">进阶</span>
              <span class="progress-stat-value">{{ progressData.intermediate_mastered }}/{{ progressData.intermediate_total }}</span>
            </div>
            <div class="progress-stat card">
              <span class="tier-badge tier-advanced">高级</span>
              <span class="progress-stat-value">{{ progressData.advanced_mastered }}/{{ progressData.advanced_total }}</span>
            </div>
            <div class="progress-stat card">
              <span class="stat-icon">~</span>
              <span class="progress-stat-value">{{ progressData.estimated_remaining_minutes }} 分钟</span>
              <span class="progress-stat-label">预估剩余</span>
            </div>
          </div>
        </div>

        <!-- 薄弱知识点 -->
        <div v-if="progressData.weak_points.length > 0" class="weak-points-section">
          <h3>薄弱知识点</h3>
          <div class="weak-points-table">
            <table class="data-table">
              <thead>
                <tr>
                  <th>知识点</th>
                  <th>层级</th>
                  <th>掌握度</th>
                  <th>练习次数</th>
                  <th>正确次数</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="wp in progressData.weak_points" :key="wp.id">
                  <td>{{ wp.name }}</td>
                  <td><span :class="['tier-badge', 'tier-' + wp.tier]">{{ tierLabel(wp.tier) }}</span></td>
                  <td>
                    <div class="progress-bar-mini inline">
                      <div class="progress-bar-mini-fill fill-weak" :style="{ width: wp.mastery_level + '%' }"></div>
                    </div>
                    <span>{{ wp.mastery_level.toFixed(0) }}%</span>
                  </td>
                  <td>{{ wp.practice_count }}</td>
                  <td>{{ wp.correct_count }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div v-else class="empty-state">
          <p>暂无薄弱知识点（尚未开始练习或全部掌握）</p>
        </div>
      </div>
    </div>

    <!-- Tab 5: 个性化推荐 -->
    <div v-if="activeTab === 'recommendations'" class="tab-content">
      <div class="recommendations-header">
        <h3>AI 学习推荐</h3>
        <button class="btn btn-primary btn-sm" :disabled="loading.recommendations" @click="loadRecommendations">
          {{ loading.recommendations ? '分析中...' : '刷新推荐' }}
        </button>
      </div>
      <div v-if="loading.recommendations" class="loading-state">
        <div class="spinner"></div>
        <p>AI 正在分析你的学习数据...</p>
      </div>
      <div v-else-if="recommendationsData && recommendationsData.recommendations.length > 0" class="recommendations-list">
        <div
          v-for="(rec, idx) in recommendationsData.recommendations"
          :key="rec.knowledge_point_id"
          class="recommendation-card card"
        >
          <div class="rec-header">
            <span class="rec-rank">#{{ idx + 1 }}</span>
            <h4>{{ rec.knowledge_point_name }}</h4>
            <span :class="['tier-badge', 'tier-' + rec.tier]">{{ tierLabel(rec.tier) }}</span>
          </div>
          <p class="rec-reason">{{ rec.reason }}</p>
          <div v-if="rec.related_weak_points && rec.related_weak_points.length > 0" class="rec-weak">
            <span class="rec-weak-label">关联薄弱点：</span>
            <span v-for="wp in rec.related_weak_points" :key="wp" class="tag tag-orange">{{ wp }}</span>
          </div>
          <div class="rec-priority">
            <span v-for="s in rec.priority" :key="s" class="priority-star">*</span>
          </div>
        </div>
      </div>
      <div v-else class="empty-state">
        <p>全部知识点已掌握，或暂无推荐数据。点击"刷新推荐"获取AI建议。</p>
      </div>
    </div>

    <!-- 创建课程弹窗 -->
    <transition name="modal">
      <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
        <div class="modal card">
          <h3>创建学习课程</h3>
          <div class="form-group">
            <label>课程标题 *</label>
            <input v-model="newCourse.title" type="text" placeholder="输入课程标题" class="form-input" />
          </div>
          <div class="form-group">
            <label>课程描述</label>
            <textarea v-model="newCourse.description" placeholder="简要描述课程内容（可选）" class="form-input" rows="2"></textarea>
          </div>
          <div class="form-group">
            <label>选择学习方向（可选，用于筛选资料）</label>
            <select v-model="newCourse.direction_id" class="form-input" @change="filterMaterials">
              <option :value="null">全部方向</option>
              <option v-for="d in directions" :key="d.id" :value="d.id">{{ d.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>选择资料 * (至少选择1份)</label>
            <div class="materials-checklist">
              <div v-if="filteredMaterials.length === 0" class="empty-hint">暂无可用资料，请先上传资料</div>
              <label v-for="m in filteredMaterials" :key="m.id" class="checkbox-item">
                <input type="checkbox" :value="m.id" v-model="newCourse.material_ids" />
                <span class="checkbox-label">{{ m.title }}</span>
                <span class="checkbox-meta">{{ m.status === 'processed' ? '已处理' : m.status }}</span>
              </label>
            </div>
          </div>
          <div class="modal-actions">
            <button class="btn btn-secondary" @click="showCreateModal = false">取消</button>
            <button class="btn btn-primary" :disabled="!canCreate || loading.create" @click="createCourse">
              {{ loading.create ? '创建中...' : '创建课程' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { learningModeApi, directionsApi, materialsApi } from '@/api'

// ========== 状态 ==========
const activeTab = ref('overview')
const courses = ref([])
const selectedCourse = ref(null)
const courseDetail = ref(null)
const mindmapData = ref(null)
const progressData = ref(null)
const recommendationsData = ref(null)
const directions = ref([])
const allMaterials = ref([])
const filteredMaterials = ref([])
const expandedNodes = ref(new Set())
const updatingPoints = ref(new Set())
const showCreateModal = ref(false)

const loading = ref({
  courses: false,
  create: false,
  generate: false,
  detail: false,
  mindmap: false,
  progress: false,
  recommendations: false,
})

const newCourse = ref({
  title: '',
  description: '',
  direction_id: null,
  material_ids: [],
})

// markmap 实例
let markmapInstance = null
const mindmapSvg = ref(null)

// ========== 计算属性 ==========
const canCreate = computed(() => {
  return newCourse.value.title.trim() && newCourse.value.material_ids.length > 0
})

// ========== 方法 ==========
function statusLabel(status) {
  const map = { pending: '待生成', generating: '生成中', completed: '已完成', failed: '生成失败' }
  return map[status] || status
}

function tierLabel(tier) {
  const map = { beginner: '入门', intermediate: '进阶', advanced: '高级' }
  return map[tier] || tier
}

function tierCount(tier) {
  if (!courseDetail.value) return 0
  return courseDetail.value.knowledge_points.filter(p => p.tier === tier).length
}

function tierPoints(tier) {
  if (!courseDetail.value) return []
  return courseDetail.value.knowledge_points.filter(p => p.tier === tier)
}

function masteryClass(level) {
  if (level >= 90) return 'mastery-expert'
  if (level >= 70) return 'mastery-good'
  if (level >= 1) return 'mastery-learning'
  return 'mastery-none'
}

function relTypeIcon(type) {
  const map = { prerequisite: '<-', related: '<>', extends: '>>' }
  return map[type] || '-'
}

function getPointRelations(pointId) {
  if (!courseDetail.value) return []
  return courseDetail.value.relations.filter(r => r.source_point_id === pointId || r.target_point_id === pointId).slice(0, 3)
}

function toggleNode(id) {
  if (expandedNodes.value.has(id)) {
    expandedNodes.value.delete(id)
  } else {
    expandedNodes.value.add(id)
  }
  expandedNodes.value = new Set(expandedNodes.value)
}

function filterMaterials() {
  if (newCourse.value.direction_id) {
    filteredMaterials.value = allMaterials.value.filter(m => m.direction_id === newCourse.value.direction_id)
  } else {
    filteredMaterials.value = [...allMaterials.value]
  }
  newCourse.value.material_ids = []
}

// ========== API 调用 ==========
async function markAsLearned(point, masteryLevel) {
  if (!selectedCourse.value) return
  updatingPoints.value.add(point.id)
  updatingPoints.value = new Set(updatingPoints.value)
  try {
    const res = await learningModeApi.updatePointMastery(selectedCourse.value.id, point.id, masteryLevel)
    // 更新本地数据
    point.mastery_level = res.data.mastery_level
    point.practice_count = res.data.practice_count
    point.correct_count = res.data.correct_count
    // 同步课程统计
    if (courseDetail.value) {
      const points = courseDetail.value.knowledge_points
      const mastered = points.filter(p => p.mastery_level >= 70).length
      courseDetail.value.mastered_points = mastered
      courseDetail.value.progress_rate = points.length > 0 ? (mastered / points.length * 100) : 0
    }
    if (selectedCourse.value) {
      selectedCourse.value.mastered_points = courseDetail.value?.mastered_points || 0
      selectedCourse.value.progress_rate = courseDetail.value?.progress_rate || 0
    }
  } catch (e) {
    alert('更新失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    updatingPoints.value.delete(point.id)
    updatingPoints.value = new Set(updatingPoints.value)
  }
}

async function loadCourses() {
  loading.value.courses = true
  try {
    const res = await learningModeApi.getCourses()
    courses.value = res.data
  } catch (e) {
    console.error('加载课程失败:', e)
  } finally {
    loading.value.courses = false
  }
}

async function loadDirectionsAndMaterials() {
  try {
    const [dRes, mRes] = await Promise.all([
      directionsApi.getAll(),
      materialsApi.getAll(),
    ])
    directions.value = dRes.data
    allMaterials.value = mRes.data.filter(m => m.status === 'processed')
    filteredMaterials.value = [...allMaterials.value]
  } catch (e) {
    console.error('加载方向/资料失败:', e)
  }
}

async function selectCourse(course) {
  selectedCourse.value = course
  courseDetail.value = null
  if (course.status === 'completed') {
    loading.value.detail = true
    try {
      const res = await learningModeApi.getCourseDetail(course.id)
      courseDetail.value = res.data
    } catch (e) {
      console.error('加载课程详情失败:', e)
    } finally {
      loading.value.detail = false
    }
  }
}

async function createCourse() {
  if (!canCreate.value) return
  loading.value.create = true
  try {
    const res = await learningModeApi.createCourse({
      title: newCourse.value.title.trim(),
      description: newCourse.value.description || null,
      direction_id: newCourse.value.direction_id,
      material_ids: newCourse.value.material_ids,
    })
    courses.value.unshift(res.data)
    selectedCourse.value = res.data
    showCreateModal.value = false
    newCourse.value = { title: '', description: '', direction_id: null, material_ids: [] }
  } catch (e) {
    alert('创建课程失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value.create = false
  }
}

async function generateCourse() {
  if (!selectedCourse.value) return
  loading.value.generate = true
  selectedCourse.value.status = 'generating'
  try {
    const res = await learningModeApi.generateCourse(selectedCourse.value.id)
    courseDetail.value = res.data
    selectedCourse.value.status = 'completed'
    selectedCourse.value.total_points = res.data.total_points
    selectedCourse.value.mastered_points = res.data.mastered_points
    selectedCourse.value.progress_rate = res.data.progress_rate
    // 刷新列表
    await loadCourses()
    // 重新选中
    const updated = courses.value.find(c => c.id === selectedCourse.value.id)
    if (updated) selectedCourse.value = updated
  } catch (e) {
    selectedCourse.value.status = 'failed'
    alert('生成课程失败: ' + (e.response?.data?.detail || e.message))
  } finally {
    loading.value.generate = false
  }
}

async function deleteCourse() {
  if (!selectedCourse.value) return
  if (!confirm('确定删除此课程？')) return
  try {
    await learningModeApi.deleteCourse(selectedCourse.value.id)
    courses.value = courses.value.filter(c => c.id !== selectedCourse.value.id)
    selectedCourse.value = null
    courseDetail.value = null
  } catch (e) {
    alert('删除失败: ' + (e.response?.data?.detail || e.message))
  }
}

async function switchTab(tab) {
  activeTab.value = tab
  if (!selectedCourse.value || selectedCourse.value.status !== 'completed') return

  if (tab === 'tree' && !courseDetail.value) {
    loading.value.detail = true
    try {
      const res = await learningModeApi.getCourseDetail(selectedCourse.value.id)
      courseDetail.value = res.data
    } catch (e) {
      console.error('加载详情失败:', e)
    } finally {
      loading.value.detail = false
    }
  }

  if (tab === 'mindmap') {
    loading.value.mindmap = true
    try {
      const res = await learningModeApi.getMindmap(selectedCourse.value.id)
      mindmapData.value = res.data
      await nextTick()
      renderMindmap()
    } catch (e) {
      console.error('加载思维导图失败:', e)
    } finally {
      loading.value.mindmap = false
    }
  }

  if (tab === 'progress') {
    loading.value.progress = true
    try {
      const res = await learningModeApi.getProgress(selectedCourse.value.id)
      progressData.value = res.data
    } catch (e) {
      console.error('加载进度失败:', e)
    } finally {
      loading.value.progress = false
    }
  }

  if (tab === 'recommendations') {
    await loadRecommendations()
  }
}

async function loadRecommendations() {
  if (!selectedCourse.value) return
  loading.value.recommendations = true
  try {
    const res = await learningModeApi.getRecommendations(selectedCourse.value.id)
    recommendationsData.value = res.data
  } catch (e) {
    console.error('加载推荐失败:', e)
  } finally {
    loading.value.recommendations = false
  }
}

// ========== 思维导图 ==========
async function renderMindmap() {
  if (!mindmapSvg.value || !mindmapData.value?.mindmap_markdown) return

  try {
    const { Transformer } = await import('markmap-lib')
    const { Markmap } = await import('markmap-view')

    const transformer = new Transformer()
    const { root } = transformer.transform(mindmapData.value.mindmap_markdown)

    // 清空已有内容
    mindmapSvg.value.innerHTML = ''
    markmapInstance = Markmap.create(mindmapSvg.value, {
      autoFit: true,
      color: (node) => {
        const depth = node.state?.depth || 0
        const colors = ['#6366f1', '#8b5cf6', '#a855f7', '#3b82f6', '#10b981', '#f59e0b']
        return colors[depth % colors.length]
      },
    }, root)
  } catch (e) {
    console.error('渲染思维导图失败:', e)
  }
}

function resetMindmap() {
  if (markmapInstance) {
    renderMindmap()
  }
}

function fitMindmap() {
  if (markmapInstance) {
    markmapInstance.fit()
  }
}

// ========== 生命周期 ==========
onMounted(async () => {
  await Promise.all([loadCourses(), loadDirectionsAndMaterials()])
})
</script>

<style scoped>
.learning-mode-page {
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 2rem;
}

.page-title {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.gradient-text {
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  color: var(--color-text-secondary);
  font-size: 1rem;
}

/* ========== 标签页 ========== */
.page-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 0.5rem;
  flex-wrap: wrap;
}

.page-tab-btn {
  padding: 0.625rem 1.25rem;
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  font-weight: 500;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--transition-base);
}

.page-tab-btn:hover:not(:disabled) {
  color: var(--color-text-primary);
  background: var(--color-bg-tertiary);
}

.page-tab-btn.active {
  color: white;
  background: var(--gradient-primary);
}

.page-tab-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ========== 概览布局 ========== */
.overview-layout {
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 1.5rem;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.panel-header h3 {
  margin: 0;
  color: var(--color-text-primary);
}

.courses-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 70vh;
  overflow-y: auto;
}

.course-card {
  padding: 1rem;
  cursor: pointer;
  transition: all var(--transition-base);
}

.course-card:hover {
  border-color: var(--color-accent-primary);
}

.course-card.selected {
  border-color: var(--color-accent-primary);
  box-shadow: 0 0 12px rgba(99, 102, 241, 0.3);
}

.course-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.course-card-header h4 {
  margin: 0;
  font-size: 0.95rem;
  color: var(--color-text-primary);
}

.course-desc {
  color: var(--color-text-secondary);
  font-size: 0.8rem;
  margin-bottom: 0.5rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.course-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

/* 状态标签 */
.status-tag {
  font-size: 0.7rem;
  padding: 0.2rem 0.5rem;
  border-radius: 10px;
  white-space: nowrap;
}

.tag-pending { background: rgba(148, 163, 184, 0.2); color: var(--color-text-secondary); }
.tag-generating { background: rgba(245, 158, 11, 0.2); color: var(--color-warning); }
.tag-completed { background: rgba(16, 185, 129, 0.2); color: var(--color-success); }
.tag-failed { background: rgba(239, 68, 68, 0.2); color: var(--color-error); }

/* 进度条 */
.progress-bar-mini {
  height: 4px;
  background: var(--color-bg-tertiary);
  border-radius: 2px;
  margin-top: 0.5rem;
  overflow: hidden;
}

.progress-bar-mini.inline {
  display: inline-block;
  width: 60px;
  margin-top: 0;
  margin-right: 0.5rem;
  vertical-align: middle;
}

.progress-bar-mini-fill {
  height: 100%;
  background: var(--gradient-primary);
  border-radius: 2px;
  transition: width var(--transition-base);
}

.fill-weak {
  background: linear-gradient(90deg, #ef4444, #f59e0b);
}

/* ========== 详情面板 ========== */
.detail-panel {
  min-height: 400px;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.detail-header h2 {
  margin: 0;
  color: var(--color-text-primary);
}

.detail-actions {
  display: flex;
  gap: 0.5rem;
}

.detail-desc {
  color: var(--color-text-secondary);
  margin-bottom: 1.5rem;
}

.generating-hint,
.error-hint {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.5rem;
  border-radius: var(--radius-md);
  margin-bottom: 1rem;
}

.generating-hint {
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.3);
  color: var(--color-accent-primary);
}

.error-hint {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: var(--color-error);
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  padding: 1rem;
  text-align: center;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  margin-top: 0.25rem;
}

/* 知识点概况 */
.kp-summary h3 {
  margin-bottom: 0.75rem;
  color: var(--color-text-primary);
}

.tier-summary {
  display: flex;
  gap: 1.5rem;
}

.tier-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--color-text-secondary);
}

.tier-badge {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 600;
}

.tier-beginner { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
.tier-intermediate { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
.tier-advanced { background: rgba(139, 92, 246, 0.2); color: #8b5cf6; }

/* ========== 知识树 ========== */
.tree-columns {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.column-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.column-count {
  font-size: 0.8rem;
  color: var(--color-text-tertiary);
  font-weight: 400;
}

.tree-nodes {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.knowledge-node {
  padding: 1rem;
  transition: all var(--transition-base);
}

.knowledge-node.mastery-none { border-left: 3px solid var(--color-text-tertiary); }
.knowledge-node.mastery-learning { border-left: 3px solid var(--color-warning); }
.knowledge-node.mastery-good { border-left: 3px solid var(--color-success); }
.knowledge-node.mastery-expert { border-left: 3px solid #fbbf24; }

.node-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.node-name {
  font-weight: 600;
  color: var(--color-text-primary);
  font-size: 0.9rem;
}

.node-importance .star {
  color: #fbbf24;
}

.node-desc {
  color: var(--color-text-secondary);
  font-size: 0.8rem;
  line-height: 1.5;
  margin-bottom: 0.5rem;
}

.node-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.mastery-ring {
  position: relative;
  width: 32px;
  height: 32px;
}

.ring-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-bg {
  fill: none;
  stroke: var(--color-bg-tertiary);
  stroke-width: 3;
}

.ring-fill {
  fill: none;
  stroke: var(--color-accent-primary);
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray var(--transition-base);
}

.ring-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.5rem;
  color: var(--color-text-secondary);
}

.est-time {
  font-size: 0.7rem;
  color: var(--color-text-tertiary);
}

.node-relations {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
  margin-top: 0.5rem;
}

.rel-tag {
  font-size: 0.65rem;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
  background: rgba(99, 102, 241, 0.1);
  color: var(--color-accent-primary);
}

.node-toggle {
  margin-top: 0.5rem;
  background: none;
  border: none;
  color: var(--color-accent-primary);
  font-size: 0.75rem;
  cursor: pointer;
  padding: 0;
}

.node-toggle:hover {
  text-decoration: underline;
}

.node-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.btn-learn {
  background: rgba(16, 185, 129, 0.15);
  color: var(--color-success);
  border: 1px solid rgba(16, 185, 129, 0.3);
}

.btn-learn:hover:not(:disabled) {
  background: rgba(16, 185, 129, 0.25);
}

.btn-master {
  background: rgba(251, 191, 36, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.btn-master:hover:not(:disabled) {
  background: rgba(251, 191, 36, 0.25);
}

.btn-reset-mastery {
  background: transparent;
  color: var(--color-text-tertiary);
  border: 1px solid var(--color-border);
  font-size: 0.7rem;
  padding: 0.25rem 0.5rem;
}

.btn-reset-mastery:hover:not(:disabled) {
  color: var(--color-text-secondary);
  border-color: var(--color-text-tertiary);
}

.mastered-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #fbbf24;
}

/* ========== 思维导图 ========== */
.mindmap-container {
  position: relative;
}

.mindmap-toolbar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.mindmap-wrapper {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.mindmap-svg {
  width: 100%;
  height: 600px;
}

/* ========== 学习进度 ========== */
.progress-overview {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.progress-ring-large {
  position: relative;
  width: 180px;
  height: 180px;
  padding: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ring-svg-large {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.ring-bg-large {
  fill: none;
  stroke: var(--color-bg-tertiary);
  stroke-width: 8;
}

.ring-fill-large {
  fill: none;
  stroke: url(#progressGradient);
  stroke: var(--color-accent-primary);
  stroke-width: 8;
  stroke-linecap: round;
  transition: stroke-dasharray var(--transition-slow);
}

.ring-center-text {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.ring-percent {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
}

.ring-label {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
}

.progress-stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  align-content: center;
}

.progress-stat {
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.progress-stat-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.progress-stat-label {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.stat-icon {
  font-size: 1.2rem;
}

/* 薄弱知识点表格 */
.weak-points-section h3 {
  margin-bottom: 1rem;
  color: var(--color-text-primary);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  background: var(--gradient-card);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.data-table th {
  padding: 0.875rem 1rem;
  background: var(--color-bg-tertiary);
  font-weight: 600;
  color: var(--color-text-secondary);
  text-align: left;
  font-size: 0.8rem;
}

.data-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-primary);
  font-size: 0.85rem;
}

.data-table tbody tr:hover {
  background: rgba(99, 102, 241, 0.04);
}

/* ========== 推荐 ========== */
.recommendations-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.recommendations-header h3 {
  color: var(--color-text-primary);
  margin: 0;
}

.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.recommendation-card {
  padding: 1.25rem;
}

.rec-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.rec-rank {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-accent-primary);
  min-width: 2rem;
}

.rec-header h4 {
  margin: 0;
  color: var(--color-text-primary);
  flex: 1;
}

.rec-reason {
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  line-height: 1.6;
  margin-bottom: 0.75rem;
}

.rec-weak {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}

.rec-weak-label {
  font-size: 0.8rem;
  color: var(--color-text-tertiary);
}

.tag-orange {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.rec-priority {
  display: flex;
  gap: 2px;
}

.priority-star {
  color: #fbbf24;
  font-size: 1rem;
}

/* ========== 通用 ========== */
.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: var(--color-text-tertiary);
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  min-height: 200px;
  color: var(--color-text-secondary);
  flex-direction: column;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-bg-tertiary);
  border-top-color: var(--color-accent-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 按钮 */
.btn {
  padding: 0.625rem 1.25rem;
  border: none;
  border-radius: var(--radius-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-base);
  font-size: 0.875rem;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--gradient-primary);
  color: white;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
}

.btn-primary:hover:not(:disabled) {
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.5);
  transform: translateY(-1px);
}

.btn-secondary {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover:not(:disabled) {
  border-color: var(--color-accent-primary);
}

.btn-danger {
  background: rgba(239, 68, 68, 0.2);
  color: var(--color-error);
}

.btn-danger:hover:not(:disabled) {
  background: rgba(239, 68, 68, 0.3);
}

.btn-sm {
  padding: 0.375rem 0.875rem;
  font-size: 0.8rem;
}

/* 弹窗 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.modal {
  width: 560px;
  max-width: 90vw;
  max-height: 80vh;
  overflow-y: auto;
  padding: 2rem;
}

.modal h3 {
  margin: 0 0 1.5rem;
  color: var(--color-text-primary);
}

.modal-enter-active,
.modal-leave-active {
  transition: all var(--transition-base);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--color-text-secondary);
  font-size: 0.85rem;
  font-weight: 500;
}

.form-input {
  width: 100%;
  padding: 0.625rem 0.875rem;
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
  font-size: 0.9rem;
  transition: border-color var(--transition-base);
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-accent-primary);
}

.materials-checklist {
  max-height: 250px;
  overflow-y: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 0.5rem;
}

.empty-hint {
  padding: 1rem;
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: 0.85rem;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background var(--transition-base);
}

.checkbox-item:hover {
  background: var(--color-bg-tertiary);
}

.checkbox-label {
  flex: 1;
  color: var(--color-text-primary);
  font-size: 0.85rem;
}

.checkbox-meta {
  font-size: 0.7rem;
  color: var(--color-text-tertiary);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 1.5rem;
}

/* 标签 */
.tag {
  display: inline-flex;
  padding: 0.2rem 0.6rem;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 600;
}

.tag-blue {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

/* 响应式 */
@media (max-width: 1024px) {
  .overview-layout {
    grid-template-columns: 1fr;
  }

  .tree-columns {
    grid-template-columns: 1fr;
  }

  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .progress-overview {
    grid-template-columns: 1fr;
    justify-items: center;
  }
}

@media (max-width: 640px) {
  .stat-grid {
    grid-template-columns: 1fr;
  }

  .progress-stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
