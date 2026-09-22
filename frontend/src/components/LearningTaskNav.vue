<template>
  <section class="learning-task-nav" aria-label="学习任务导航">
    <div class="learning-task-title">
      <span>LEARNING PATH</span>
      <b>装—调—检—修—验</b>
    </div>
    <nav>
      <RouterLink
        v-for="(stage, index) in LEARNING_STAGES"
        :key="stage.key"
        :to="learningStageTarget(stage.key, role, route)"
        :class="{ active: stage.key === currentStage }"
        :aria-current="stage.key === currentStage ? 'step' : undefined"
      >
        <i>{{ index + 1 }}</i>
        <span>{{ stage.title }}</span>
      </RouterLink>
    </nav>
    <button type="button" @click="$emit('open-guide')">本页指引</button>
    <div class="current-reminder">
      <b>现在要做：</b><span>{{ guide.currentTask }}</span><em>完成标准：{{ guide.completion }}</em>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  LEARNING_STAGES,
  learningStageForRoute,
  learningStageTarget,
  pageLearningGuide,
  type LearningRole,
} from '../utils/learningGuide'

defineEmits<{ (event: 'open-guide'): void }>()
const props = defineProps<{ role: LearningRole }>()

const route = useRoute()
const currentStage = computed(() => learningStageForRoute(route))
const guide = computed(() => pageLearningGuide(route, props.role))
</script>

<style scoped>
.learning-task-nav{position:relative;z-index:18;display:grid;grid-template-columns:150px minmax(0,1fr) 82px;align-items:center;gap:6px 12px;min-height:48px;padding:6px 16px;border-bottom:1px solid #d8e3ef;background:rgba(248,251,255,.97);box-shadow:0 4px 14px rgba(20,48,82,.05)}
.learning-task-title{display:grid;gap:1px}.learning-task-title span{font-size:9px;letter-spacing:.14em;color:#5380af;font-weight:850}.learning-task-title b{font-size:12px;color:#203a58}
nav{display:grid;grid-template-columns:repeat(7,minmax(72px,1fr));align-items:center;gap:5px}nav a{position:relative;display:flex;align-items:center;justify-content:center;gap:5px;min-width:0;padding:6px 4px;border:1px solid #dfe7f0;border-radius:8px;background:#fff;color:#708095;text-decoration:none;font-size:10px;font-weight:750;transition:.15s}nav a::after{content:'›';position:absolute;right:-6px;color:#a8b4c1}nav a:last-child::after{display:none}nav a i{display:grid;place-items:center;width:18px;height:18px;border-radius:50%;background:#edf2f7;color:#6c7d91;font-style:normal;font-size:9px}nav a.active{border-color:#73a8e8;background:#edf5ff;color:#2465b4;box-shadow:0 0 0 2px rgba(48,119,207,.08)}nav a.active i{background:#3077cf;color:#fff}.learning-task-nav>button{border:1px solid #8eb8e5;border-radius:8px;background:#eef6ff;color:#2d6db6;padding:7px 8px;font-size:10px;font-weight:850;cursor:pointer}
.current-reminder{grid-column:1/-1;display:flex;align-items:center;gap:6px;min-width:0;padding:4px 8px;border-radius:6px;background:#eef5fc;color:#526b85;font-size:10px}.current-reminder b{color:#286bad;white-space:nowrap}.current-reminder span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.current-reminder em{margin-left:auto;color:#728399;font-style:normal;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
@media(max-width:1050px){.learning-task-nav{grid-template-columns:1fr auto}.learning-task-title{display:none}nav{display:flex;overflow:auto;justify-content:flex-start}.learning-task-nav>button{grid-column:2;grid-row:1}nav a{min-width:86px}.current-reminder em{display:none}}
</style>
