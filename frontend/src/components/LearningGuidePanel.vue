<template>
  <div v-if="open" class="guide-backdrop" @click.self="$emit('close')">
    <aside class="learning-guide-panel" role="dialog" aria-modal="true" aria-label="本页学习指引">
      <header>
        <div><span>{{ guide.eyebrow }}</span><h2>{{ guide.title }}</h2></div>
        <button type="button" aria-label="关闭学习指引" @click="$emit('close')">×</button>
      </header>

      <section class="guide-goal"><small>本页目标</small><p>{{ guide.objective }}</p></section>
      <section class="guide-current"><small>现在要做</small><b>{{ guide.currentTask }}</b></section>

      <section>
        <h3>建议步骤</h3>
        <ol><li v-for="(step, index) in guide.steps" :key="step"><i>{{ index + 1 }}</i><span>{{ step }}</span></li></ol>
      </section>

      <section v-if="guide.observe?.length" class="guide-observe">
        <h3>重点观察</h3>
        <ul><li v-for="item in guide.observe" :key="item"><i>◎</i><span>{{ item }}</span></li></ul>
      </section>

      <section v-if="guide.mistakes?.length" class="guide-mistakes">
        <h3>常见误区</h3>
        <ul><li v-for="item in guide.mistakes" :key="item"><i>!</i><span>{{ item }}</span></li></ul>
      </section>

      <section class="guide-standard"><small>完成标准</small><p>{{ guide.completion }}</p></section>
      <section class="guide-why"><small>为什么要做</small><p>{{ guide.why }}</p></section>

      <section v-if="guide.glossary.length" class="guide-glossary">
        <h3>本页术语</h3>
        <details v-for="item in guide.glossary" :key="item.term">
          <summary>{{ item.term }}</summary><p>{{ item.definition }}</p>
        </details>
      </section>

      <footer>
        <button type="button" @click="$emit('close')">继续当前任务</button>
        <RouterLink v-if="guide.nextTo" :to="guide.nextTo" @click="$emit('close')">{{ guide.nextLabel }} →</RouterLink>
      </footer>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { pageLearningGuide, type LearningRole } from '../utils/learningGuide'

const props = defineProps<{ open: boolean; role: LearningRole }>()
defineEmits<{ (event: 'close'): void }>()
const route = useRoute()
const guide = computed(() => pageLearningGuide(route, props.role))
</script>

<style scoped>
.guide-backdrop{position:fixed;z-index:120;inset:0;background:rgba(9,23,40,.42);backdrop-filter:blur(2px)}.learning-guide-panel{position:absolute;top:0;right:0;width:min(430px,94vw);height:100%;box-sizing:border-box;overflow:auto;padding:22px;background:#f8fbff;color:#203852;box-shadow:-20px 0 60px rgba(9,27,49,.22)}header{display:flex;align-items:flex-start;justify-content:space-between;gap:14px;padding-bottom:15px;border-bottom:1px solid #dce6f0}header span{font-size:8px;letter-spacing:.13em;color:#3377bd;font-weight:850}header h2{margin:5px 0 0;font-size:20px}header button{border:1px solid #d4e0eb;border-radius:8px;background:#fff;color:#62758b;width:30px;height:30px;font-size:18px;cursor:pointer}section{margin-top:15px;padding:13px;border:1px solid #dce6f0;border-radius:11px;background:#fff}section small{display:block;margin-bottom:5px;color:#6f8093;font-size:8px;font-weight:800}section p{margin:0;font-size:11px;line-height:1.65}.guide-goal{border-color:#bcd7f4;background:#f1f7ff}.guide-current{border-color:#7eb4ee;background:linear-gradient(135deg,#eaf4ff,#f5f9ff)}.guide-current b{font-size:12px;line-height:1.55}.guide-standard{border-color:#bae0ca;background:#f1fbf6}.guide-why{border-color:#ead9ae;background:#fffaf0}h3{margin:0 0 8px;font-size:11px}ol{display:grid;gap:7px;margin:0;padding:0;list-style:none}li{display:flex;align-items:center;gap:8px;font-size:10px}li i{display:grid;place-items:center;flex:0 0 20px;height:20px;border-radius:50%;background:#eaf2fb;color:#2f70b8;font-style:normal;font-size:8px;font-weight:850}details{border-top:1px solid #e6edf4;padding:8px 0}details:first-of-type{border-top:0}summary{color:#2f6da9;font-size:10px;font-weight:800;cursor:pointer}details p{margin-top:6px;color:#637489;font-size:9px}footer{position:sticky;bottom:-22px;display:grid;grid-template-columns:1fr 1.2fr;gap:8px;margin:18px -22px -22px;padding:13px 22px;background:rgba(248,251,255,.96);border-top:1px solid #dce6f0}footer button,footer a{display:grid;place-items:center;border-radius:9px;padding:10px;text-decoration:none;font-size:9px;font-weight:850}footer button{border:1px solid #cddbe8;background:#fff;color:#536a83;cursor:pointer}footer a{border:1px solid #2f73c5;background:#347fd1;color:#fff}
.learning-guide-panel ul{display:grid;gap:7px;margin:0;padding:0;list-style:none}.learning-guide-panel li{align-items:flex-start;line-height:1.55}.guide-observe{border-color:#bddceb;background:#f3fbff}.guide-observe li i{background:#dff4fb;color:#18779a}.guide-mistakes{border-color:#efd7b6;background:#fffaf2}.guide-mistakes li i{background:#fff0d8;color:#a76a19}
</style>
