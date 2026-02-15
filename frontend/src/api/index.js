import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 180000, // 3分钟超时，适应AI处理时间
  headers: {
    'Content-Type': 'application/json'
  }
})

// 学习方向 API
export const directionsApi = {
  getAll: () => api.get('/directions'),
  create: (data) => api.post('/directions', data),
  delete: (id) => api.delete(`/directions/${id}`)
}

// 资料 API
export const materialsApi = {
  getAll: (directionId) => api.get('/materials', { params: { direction_id: directionId } }),
  create: (data) => api.post('/materials', data),
  get: (id) => api.get(`/materials/${id}`),
  delete: (id) => api.delete(`/materials/${id}`),
  updateDirection: (id, directionId) => api.patch(`/materials/${id}`, { direction_id: directionId })
}

// 题目 API
export const questionsApi = {
  getAll: (params) => api.get('/questions', { params }),
  get: (id) => api.get(`/questions/${id}`),
  update: (id, data) => api.patch(`/questions/${id}`, data),
  delete: (id) => api.delete(`/questions/${id}`),
  rate: (id, rating) => api.patch(`/questions/${id}/rate`, { rating })
}

// 测验 API
export const examsApi = {
  getAll: (params) => api.get('/exams', { params }),
  create: (data) => api.post('/exams', data),
  get: (id) => api.get(`/exams/${id}`),
  submit: (id, answers) => api.post(`/exams/${id}/submit`, { answers }),
  getResult: (id) => api.get(`/exams/${id}/result`)
}

// 错题 API
export const mistakesApi = {
  getAll: (params) => api.get('/mistakes', { params }),
  update: (id, data) => api.patch(`/mistakes/${id}`, data),
  delete: (id) => api.delete(`/mistakes/${id}`)
}

// 知识解析 API
export const parseApi = {
  parseText: (data) => api.post('/parse/text', data),
  parseFile: (title, file, directionId) => {
    const formData = new FormData()
    formData.append('title', title)
    if (directionId) formData.append('direction_id', directionId)
    formData.append('file', file)
    return api.post('/parse/file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  parseUrl: (data) => api.post('/parse/url', data),
  getTasks: (params) => api.get('/parse/tasks', { params }),
  getTaskDetail: (taskId) => api.get(`/parse/tasks/${taskId}`),
  deleteTask: (taskId) => api.delete(`/parse/tasks/${taskId}`),
  updateTaskDirection: (taskId, directionId) => api.patch(`/parse/tasks/${taskId}`, { direction_id: directionId }),
  generateQuestions: (taskId) => api.post(`/parse/tasks/${taskId}/generate-questions`)
}

export default api
