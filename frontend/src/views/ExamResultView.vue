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
        
        <!-- 游戏化奖励 -->
        <div v-if="gamification" class="gamification-rewards">
          <div class="exp-gain">
            <span class="exp-icon">&#x2B50;</span>
            <span class="exp-amount">+{{ gamification.exp_gained }} EXP</span>
          </div>
          <div v-if="gamification.level_up" class="level-up-notice">
            <div class="level-change">Level {{ gamification.old_level }} &#x2192; Level {{ gamification.new_level }}</div>
            <div class="title-change">{{ gamification.new_title }}</div>
          </div>
          <div v-if="gamification.achievements_unlocked && gamification.achievements_unlocked.length" class="achievements-notice">
            <div v-for="ach in gamification.achievements_unlocked" :key="ach.id" class="ach-badge">
              <span class="ach-name">{{ ach.name }}</span>
            </div>
          </div>
          <div v-if="gamification.tasks_completed && gamification.tasks_completed.length" class="tasks-notice">
            <span v-for="t in gamification.tasks_completed" :key="t" class="task-done-tag">{{ t }}</span>
          </div>
        </div>
        
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
const gamification = ref(null)

const loadResult = async () => {
  loading.value = true
  try {
    const res = await examsApi.getResult(route.params.id)
    result.value = res.data
    
    // 检查是否有游戏化数据（从 sessionStorage 获取，由提交时存储）
    const gData = sessionStorage.getItem(`exam_gamification_${route.params.id}`)
    if (gData) {
      gamification.value = JSON.parse(gData)
      sessionStorage.removeItem(`exam_gamification_${route.params.id}`)
    }
    
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
.exam-result-page {
  padding: 2rem;
  max-width: 1000px;
  margin: 0 auto;
}

.result-summary {
  text-align: center;
  padding: 3rem 2rem;
  margin-bottom: 2.5rem;
  background: var(--gradient-card);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-lg);
  animation: slideDown 0.5s ease-out;
  position: relative;
  overflow: hidden;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.result-summary::before {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.05) 0%, transparent 50%);
  animation: rotate 20s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.result-summary h1 {
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 1.5rem;
  font-size: 2rem;
  font-weight: 800;
  position: relative;
  z-index: 1;
}

.score-display {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  position: relative;
  z-index: 1;
}

.score {
  font-size: 5rem;
  font-weight: 800;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1;
}

.score-label {
  font-size: 1.75rem;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.grade {
  font-size: 1.5rem;
  color: var(--color-warning);
  margin-bottom: 2rem;
  font-weight: 600;
  padding: 0.5rem 1.5rem;
  background: var(--color-warning-bg);
  border-radius: 20px;
  display: inline-block;
  position: relative;
  z-index: 1;
}

.stats {
  display: flex;
  justify-content: center;
  gap: 3rem;
  position: relative;
  z-index: 1;
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.stat-value {
  font-size: 2.25rem;
  font-weight: 800;
  line-height: 1;
}

.stat-value.correct {
  color: var(--color-success);
}

.stat-value.wrong {
  color: var(--color-error);
}

.stat-label {
  color: var(--color-text-tertiary);
  font-size: 0.9rem;
  font-weight: 500;
}

.answers-section {
  margin-bottom: 2.5rem;
}

.answers-section h2 {
  margin-bottom: 1.5rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.answers-section h2::before {
  content: '📋';
}

.answer-card {
  margin-bottom: 1.5rem;
  animation: slideUp 0.4s ease-out backwards;
}

.answer-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border);
  flex-wrap: wrap;
}

.question-num {
  font-weight: 700;
  color: var(--color-accent-primary);
  font-size: 1rem;
}

.score-badge {
  margin-left: auto;
  font-weight: 700;
  color: var(--color-text-primary);
  padding: 0.375rem 0.875rem;
  background: var(--color-accent-glow);
  border-radius: 12px;
}

.question-content {
  background: var(--color-bg-tertiary);
  padding: 1.25rem;
  border-radius: var(--radius-md);
  margin-bottom: 1rem;
  border: 1px solid var(--color-border);
}

.question-content p {
  margin: 0;
  color: var(--color-text-primary);
  font-size: 1rem;
  line-height: 1.6;
}

.answer-compare {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.your-answer, .correct-answer, .ai-feedback, .explanation {
  background: var(--color-bg-tertiary);
  padding: 1rem 1.25rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
}

.your-answer label, .correct-answer label, .ai-feedback label, .explanation label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 0.625rem;
}

.your-answer label::before {
  content: '✏️';
}

.correct-answer label::before {
  content: '✓';
}

.ai-feedback label::before {
  content: '🤖';
}

.explanation label::before {
  content: '💡';
}

.your-answer label {
  color: var(--color-text-secondary);
}

.correct-answer label {
  color: var(--color-success);
}

.ai-feedback label {
  color: var(--color-accent-primary);
}

.explanation label {
  color: var(--color-accent-primary);
}

.your-answer p, .correct-answer p, .ai-feedback p, .explanation p {
  margin: 0;
  color: var(--color-text-secondary);
  font-size: 0.95rem;
  line-height: 1.6;
}

.ai-feedback {
  border-left: 4px solid var(--color-accent-primary);
  margin-bottom: 1rem;
}

.explanation {
  border-left: 4px solid var(--color-success);
}

/* Gamification Rewards */
.gamification-rewards {
  position: relative;
  z-index: 1;
  margin: 1.5rem 0;
  padding: 1.25rem;
  background: rgba(99, 102, 241, 0.08);
  border-radius: var(--radius-md);
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.exp-gain {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.exp-icon {
  font-size: 1.5rem;
}

.exp-amount {
  font-size: 1.5rem;
  font-weight: 800;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.level-up-notice {
  text-align: center;
  padding: 1rem;
  margin-bottom: 0.75rem;
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.15), rgba(255, 237, 78, 0.1));
  border: 1px solid rgba(255, 215, 0, 0.3);
  border-radius: var(--radius-md);
}

.level-change {
  font-size: 1.25rem;
  font-weight: 800;
  color: #ffd700;
  margin-bottom: 0.25rem;
}

.title-change {
  font-size: 0.9rem;
  color: #ffed4e;
  font-weight: 600;
}

.achievements-notice {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}

.ach-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.35rem 0.85rem;
  background: rgba(168, 85, 247, 0.15);
  border: 1px solid rgba(168, 85, 247, 0.3);
  border-radius: 12px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #a855f7;
}

.tasks-notice {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.task-done-tag {
  padding: 0.25rem 0.65rem;
  background: rgba(16, 185, 129, 0.15);
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-success);
}

.actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 2.5rem;
  padding-top: 2rem;
  border-top: 1px solid var(--color-border);
  flex-wrap: wrap;
}

.actions .btn {
  min-width: 140px;
}

/* Tag override */
.answer-header .tag {
  font-size: 0.75rem;
  padding: 0.25rem 0.75rem;
  margin: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .exam-result-page {
    padding: 1rem;
  }
  
  .result-summary {
    padding: 2rem 1.5rem;
  }
  
  .score {
    font-size: 3.5rem;
  }
  
  .score-label {
    font-size: 1.25rem;
  }
  
  .stats {
    gap: 1.5rem;
  }
  
  .stat-value {
    font-size: 1.75rem;
  }
  
  .answer-compare {
    grid-template-columns: 1fr;
  }
  
  .actions {
    flex-direction: column;
  }
  
  .actions .btn {
    width: 100%;
  }
}
</style>
