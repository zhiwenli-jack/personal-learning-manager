<template>
  <div class="exam-result-page">
    <div v-if="loading" class="loading">加载结果中...</div>
    <div v-else-if="!result" class="empty">结果不存在</div>
    <template v-else>
      <!-- 成绩概览 -->
      <div class="result-summary card">
        <h1>测验完成</h1>
        <div class="score-display">
          <div class="score">{{ result.score.toFixed(1) }}</div>
          <div class="score-label">分</div>
        </div>
        <div v-if="result.grade" class="grade">等级: {{ result.grade }}</div>
        <div class="stats">
          <div class="stat-item">
            <span class="stat-value">{{ result.total_questions }}</span>
            <span class="stat-label">总题数</span>
          </div>
          <div class="stat-item">
            <span class="stat-value correct">{{ result.correct_count }}</span>
            <span class="stat-label">正确</span>
          </div>
          <div class="stat-item">
            <span class="stat-value wrong">{{ result.total_questions - result.correct_count }}</span>
            <span class="stat-label">错误</span>
          </div>
        </div>
      </div>

      <!-- 答题详情 -->
      <div class="answers-section">
        <h2>答题详情</h2>
        <div v-for="(ans, i) in result.answers" :key="ans.id" class="card answer-card">
          <div class="answer-header">
            <span class="question-num">第 {{ i + 1 }} 题</span>
            <span :class="['tag', ans.is_correct ? 'tag-green' : 'tag-red']">
              {{ ans.is_correct ? '正确' : '错误' }}
            </span>
            <span class="score-badge">{{ ans.score?.toFixed(1) || 0 }}分</span>
          </div>
          
          <div class="question-content" v-if="questions[ans.question_id]">
            <p>{{ questions[ans.question_id].content }}</p>
          </div>
          
          <div class="answer-compare">
            <div class="your-answer">
              <label>你的答案:</label>
              <p>{{ ans.user_answer || '未作答' }}</p>
            </div>
            <div class="correct-answer" v-if="questions[ans.question_id]">
              <label>正确答案:</label>
              <p>{{ questions[ans.question_id].answer }}</p>
            </div>
          </div>
          
          <div v-if="ans.ai_feedback" class="ai-feedback">
            <label>AI 评语:</label>
            <p>{{ ans.ai_feedback }}</p>
          </div>
          
          <div v-if="questions[ans.question_id]?.explanation" class="explanation">
            <label>解析:</label>
            <p>{{ questions[ans.question_id].explanation }}</p>
          </div>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <router-link to="/exam" class="btn btn-primary">再来一次</router-link>
        <router-link to="/mistakes" class="btn">查看错题本</router-link>
        <router-link to="/" class="btn">返回首页</router-link>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { examsApi, questionsApi } from '@/api'

const route = useRoute()
const result = ref(null)
const questions = ref({})
const loading = ref(true)

const loadResult = async () => {
  loading.value = true
  try {
    const res = await examsApi.getResult(route.params.id)
    result.value = res.data
    
    // 加载题目详情
    const questionIds = res.data.answers.map(a => a.question_id)
    const questionsRes = await questionsApi.getAll()
    questionsRes.data.forEach(q => {
      if (questionIds.includes(q.id)) {
        questions.value[q.id] = q
      }
    })
  } catch (e) {
    console.error('加载结果失败:', e)
  } finally {
    loading.value = false
  }
}

onMounted(loadResult)
</script>

<style scoped>
.result-summary {
  text-align: center;
  padding: 2rem;
  margin-bottom: 2rem;
}

.result-summary h1 {
  color: #4fc3f7;
  margin-bottom: 1.5rem;
}

.score-display {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.score {
  font-size: 4rem;
  font-weight: bold;
  color: #66bb6a;
}

.score-label {
  font-size: 1.5rem;
  color: #888;
}

.grade {
  font-size: 1.5rem;
  color: #ffca28;
  margin-bottom: 1.5rem;
}

.stats {
  display: flex;
  justify-content: center;
  gap: 3rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
}

.stat-value.correct {
  color: #66bb6a;
}

.stat-value.wrong {
  color: #ef5350;
}

.stat-label {
  color: #888;
  font-size: 0.9rem;
}

.answers-section h2 {
  margin-bottom: 1rem;
}

.answer-card {
  margin-bottom: 1rem;
}

.answer-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.question-num {
  font-weight: bold;
  color: #4fc3f7;
}

.score-badge {
  margin-left: auto;
  font-weight: bold;
}

.question-content {
  background: #16213e;
  padding: 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.answer-compare {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.your-answer, .correct-answer, .ai-feedback, .explanation {
  background: #16213e;
  padding: 1rem;
  border-radius: 6px;
}

.your-answer label, .correct-answer label, .ai-feedback label, .explanation label {
  display: block;
  font-size: 0.85rem;
  color: #888;
  margin-bottom: 0.5rem;
}

.ai-feedback {
  border-left: 3px solid #4fc3f7;
  margin-bottom: 1rem;
}

.explanation {
  border-left: 3px solid #66bb6a;
}

.actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 2rem;
}

@media (max-width: 768px) {
  .answer-compare {
    grid-template-columns: 1fr;
  }
}
</style>
