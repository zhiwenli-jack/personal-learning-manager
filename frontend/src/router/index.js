import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/HomeView.vue')
  },
  {
    path: '/materials',
    name: 'Materials',
    component: () => import('@/views/MaterialsView.vue')
  },
  {
    path: '/questions',
    name: 'Questions',
    component: () => import('@/views/QuestionsView.vue')
  },
  {
    path: '/exam',
    name: 'ExamStart',
    component: () => import('@/views/ExamStartView.vue')
  },
  {
    path: '/exam/:id',
    name: 'ExamTaking',
    component: () => import('@/views/ExamTakingView.vue')
  },
  {
    path: '/exam/:id/result',
    name: 'ExamResult',
    component: () => import('@/views/ExamResultView.vue')
  },
  {
    path: '/mistakes',
    name: 'Mistakes',
    component: () => import('@/views/MistakesView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
