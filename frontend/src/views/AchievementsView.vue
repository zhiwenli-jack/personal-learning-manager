<template>
  <div class="achievements-page">
    <div class="page-header">
      <h1 class="page-title">
        <span class="gradient-text">成就殿堂</span>
      </h1>
      <p class="page-desc">
        已解锁 <strong>{{ unlockedCount }}</strong> / {{ totalCount }} 个成就
      </p>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else>
      <!-- 已解锁成就 -->
      <section v-if="achievements.unlocked.length" class="ach-section">
        <h2 class="section-title">
          <span class="title-icon">&#x2728;</span>
          已解锁
        </h2>
        <div class="ach-grid">
          <div
            v-for="ach in achievements.unlocked"
            :key="ach.achievement_id"
            class="ach-card unlocked"
            :class="'rarity-' + ach.rarity"
          >
            <div class="ach-icon">{{ iconMap[ach.icon] || '&#x1f3c6;' }}</div>
            <div class="ach-body">
              <div class="ach-name">{{ ach.name }}</div>
              <div class="ach-desc">{{ ach.description }}</div>
              <div class="ach-meta">
                <span :class="'rarity-tag rarity-tag-' + ach.rarity">{{ rarityLabel[ach.rarity] }}</span>
                <span class="ach-time">{{ formatDate(ach.unlocked_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 未解锁成就 -->
      <section v-if="achievements.locked.length" class="ach-section">
        <h2 class="section-title">
          <span class="title-icon">&#x1f512;</span>
          待解锁
        </h2>
        <div class="ach-grid">
          <div
            v-for="ach in achievements.locked"
            :key="ach.achievement_id"
            class="ach-card locked"
          >
            <div class="ach-icon locked-icon">{{ iconMap[ach.icon] || '?' }}</div>
            <div class="ach-body">
              <div class="ach-name">{{ ach.name }}</div>
              <div class="ach-desc">{{ ach.description }}</div>
              <div class="ach-meta">
                <span :class="'rarity-tag rarity-tag-' + ach.rarity">{{ rarityLabel[ach.rarity] }}</span>
                <span class="ach-category">{{ categoryLabel[ach.category] || ach.category }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div v-if="!achievements.unlocked.length && !achievements.locked.length" class="empty-state card">
        <p>暂无成就数据</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { gamificationApi } from '@/api'

const achievements = ref({ unlocked: [], locked: [] })
const loading = ref(true)

const iconMap = {
  target: '\u{1F3AF}',
  scroll: '\u{1F4DC}',
  star: '\u{2B50}',
  trophy: '\u{1F3C6}',
  check: '\u{2705}',
  medal: '\u{1F3C5}',
  book: '\u{1F4D6}',
  globe: '\u{1F30D}',
  eye: '\u{1F441}',
  fire: '\u{1F525}',
  diamond: '\u{1F48E}'
}

const rarityLabel = {
  common: '普通',
  rare: '稀有',
  epic: '史诗',
  legendary: '传说'
}

const categoryLabel = {
  exam: '测验',
  mistake: '错题',
  material: '资料',
  explore: '探索',
  streak: '连续学习'
}

const unlockedCount = computed(() => achievements.value.unlocked.length)
const totalCount = computed(() => achievements.value.unlocked.length + achievements.value.locked.length)

const formatDate = (dt) => {
  if (!dt) return ''
  return new Date(dt).toLocaleDateString('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
}

const loadAchievements = async () => {
  loading.value = true
  try {
    const res = await gamificationApi.getAchievements()
    achievements.value = res.data
  } catch (e) {
    console.error('加载成就失败:', e)
  } finally {
    loading.value = false
  }
}

onMounted(loadAchievements)
</script>

<style scoped>
.achievements-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  text-align: center;
  margin-bottom: 2.5rem;
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.page-title {
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: 0.75rem;
}

.gradient-text {
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-desc {
  color: var(--color-text-secondary);
  font-size: 1.05rem;
}

.page-desc strong {
  color: var(--color-accent-primary);
  font-weight: 700;
}

/* Section */
.ach-section {
  margin-bottom: 2.5rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 1.25rem;
}

.title-icon {
  font-size: 1.5rem;
}

/* Grid */
.ach-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.25rem;
}

/* Card */
.ach-card {
  display: flex;
  gap: 1rem;
  padding: 1.25rem;
  background: var(--gradient-card);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  transition: all 0.3s ease;
  animation: slideUp 0.5s ease-out backwards;
  position: relative;
  overflow: hidden;
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

.ach-card.unlocked:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-glow);
}

/* Rarity border colors for unlocked */
.ach-card.rarity-common {
  border-color: rgba(148, 163, 184, 0.4);
}
.ach-card.rarity-rare {
  border-color: rgba(99, 102, 241, 0.4);
}
.ach-card.rarity-epic {
  border-color: rgba(168, 85, 247, 0.4);
}
.ach-card.rarity-legendary {
  border-color: rgba(255, 215, 0, 0.4);
}

.ach-card.rarity-legendary::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.05), transparent 60%);
  pointer-events: none;
}

/* Locked style */
.ach-card.locked {
  opacity: 0.6;
  border-color: var(--color-border);
}

.ach-card.locked:hover {
  opacity: 0.8;
}

/* Icon */
.ach-icon {
  font-size: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 52px;
  height: 52px;
  border-radius: 14px;
  background: rgba(99, 102, 241, 0.1);
  flex-shrink: 0;
}

.locked-icon {
  filter: grayscale(1);
  background: rgba(100, 116, 139, 0.1);
}

/* Body */
.ach-body {
  flex: 1;
  min-width: 0;
}

.ach-name {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 0.25rem;
}

.ach-desc {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.ach-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

/* Rarity tags */
.rarity-tag {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 8px;
  font-size: 0.7rem;
  font-weight: 700;
}

.rarity-tag-common {
  background: rgba(148, 163, 184, 0.15);
  color: #94a3b8;
}

.rarity-tag-rare {
  background: rgba(99, 102, 241, 0.15);
  color: #818cf8;
}

.rarity-tag-epic {
  background: rgba(168, 85, 247, 0.15);
  color: #a855f7;
}

.rarity-tag-legendary {
  background: rgba(255, 215, 0, 0.15);
  color: #ffd700;
}

.ach-time {
  font-size: 0.7rem;
  color: var(--color-text-tertiary);
}

.ach-category {
  font-size: 0.7rem;
  color: var(--color-text-tertiary);
}

/* Empty */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
}

.empty-state p {
  color: var(--color-text-secondary);
  font-size: 1.1rem;
}

/* Responsive */
@media (max-width: 1024px) {
  .ach-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .ach-grid {
    grid-template-columns: 1fr;
  }

  .page-title {
    font-size: 1.75rem;
  }
}
</style>
