<template>
  <div class="review-page">
    <header class="review-hero">
      <div>
        <span>LEARNING REVIEW · V1</span>
        <h1>训练复盘</h1>
        <p>用“现象—证据—原因—修复—验证”回看一次完整的装调检修过程。</p>
      </div>
      <div class="review-role"><small>当前视角</small><b>{{ roleLabel }}</b></div>
    </header>

    <div v-if="loading" class="review-state">正在读取训练记录…</div>
    <div v-else-if="error" class="review-state error">{{ error }}</div>

    <main v-else class="review-grid">
      <section class="review-card result-card">
        <div class="card-head"><div><span>任务结果</span><h2>{{ run?.scenario_title || worksheet?.scenarioTitle || '自由训练复盘' }}</h2></div><strong>{{ scoreText }}</strong></div>
        <div class="result-strip">
          <div><small>状态</small><b>{{ statusText }}</b></div>
          <div><small>用时</small><b>{{ durationText }}</b></div>
          <div><small>提示</small><b>{{ run?.hints_used ?? '—' }}</b></div>
          <div><small>错误操作</small><b>{{ run?.wrong_operations ?? '—' }}</b></div>
        </div>
        <div class="stage-strip">
          <span class="ok">诊断{{ diagnosisPassed ? '通过' : '待完成' }}</span>
          <span :class="{ ok: run?.prearm_passed }">Pre-Arm{{ run?.prearm_passed ? '通过' : '待完成' }}</span>
          <span :class="{ ok: run?.flight_validation_passed }">飞行{{ run?.flight_validation_passed ? '通过' : '待完成' }}</span>
        </div>
      </section>

      <section class="review-card worksheet-card">
        <div class="card-head"><div><span>诊断证据链</span><h2>诊断工作单</h2></div><em :class="{ ok: worksheet?.complete }">{{ worksheet?.complete ? '完整' : '待完善' }}</em></div>
        <div v-if="worksheet" class="worksheet-list">
          <article v-for="item in worksheetRows" :key="item.label"><i>{{ item.index }}</i><div><small>{{ item.label }}</small><p>{{ item.value || '尚未填写' }}</p></div></article>
        </div>
        <div v-else class="empty">本次记录没有诊断工作单。可返回系统调试页补充。</div>
      </section>

      <section class="review-card score-card">
        <div class="card-head"><div><span>形成性评价</span><h2>成绩构成与改进重点</h2></div></div>
        <div class="score-grid">
          <div><small>案例诊断</small><b>{{ componentScore(run?.case_score) }}</b></div>
          <div><small>规范操作</small><b>{{ componentScore(run?.operation_score) }}</b></div>
          <div><small>飞行验证</small><b>{{ componentScore(run?.flight_score) }}</b></div>
        </div>
        <ul><li v-for="item in recommendations" :key="item">{{ item }}</li></ul>
      </section>

      <section class="review-card timeline-card">
        <div class="card-head"><div><span>过程记录</span><h2>训练时间线</h2></div><b>{{ detail?.events.length ?? 0 }} 项</b></div>
        <div class="timeline">
          <article v-for="event in visibleEvents" :key="event.id"><i></i><time>{{ eventTime(event.created_at) }}</time><div><b>{{ event.title }}</b><small>{{ event.detail }}</small></div></article>
          <div v-if="!visibleEvents.length" class="empty">当前没有服务器过程事件。</div>
        </div>
      </section>

      <section class="review-card transfer-card">
        <div><span>迁移到实体操作</span><h2>下次面对真实无人机，我应该先做什么？</h2><p>先确认安全边界，再按同一证据链检查：观察现象、读取状态、定位模块、执行最小修复、重新验证。不要用反复更换部件代替诊断。</p></div>
        <RouterLink :to="returnTarget">{{ auth.user?.role === 'student' ? '返回我的实训' : '返回教师工作台' }}</RouterLink>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { studentTrainingApi, teacherApi } from '../api/teacher'
import { useAuthStore } from '../stores/auth'
import type { TrainingRunDetail, TrainingRunView } from '../types/teacher'
import type { DiagnosisWorksheetSnapshot } from '../components/DiagnosisWorksheet.vue'

const route = useRoute()
const auth = useAuthStore()
const loading = ref(true)
const error = ref('')
const detail = ref<TrainingRunDetail | null>(null)
const worksheet = ref<DiagnosisWorksheetSnapshot | null>(null)
const reviewReady = ref(false)
let reviewLoadGeneration = 0

const run = computed<TrainingRunView | null>(() => detail.value?.run ?? null)
const runId = computed(() => {
  const raw = Array.isArray(route.query.run) ? route.query.run[0] : route.query.run
  const value = Number(raw)
  return Number.isInteger(value) && value > 0 ? value : null
})
const roleLabel = computed(() => auth.user?.role === 'admin' ? '管理员验收' : auth.user?.role === 'teacher' ? '教师指导' : '学生学习')
const returnTarget = computed(() => auth.user?.role === 'student' ? '/training' : '/teacher')
const diagnosisPassed = computed(() => Boolean((run.value?.result?.grading as Record<string, unknown> | undefined)?.diagnosis_passed) || Boolean(run.value?.case_score))
const scoreText = computed(() => run.value?.score == null ? '—' : Math.round(run.value.score))
const statusText = computed(() => ({ completed: '已完成', awaiting_flight: '等待飞行验证', awaiting_prearm: '等待Pre-Arm', diagnosis: '诊断中' } as Record<string, string>)[run.value?.stage ?? ''] ?? (run.value ? run.value.status : '本地草稿'))
const durationText = computed(() => {
  if (!run.value) return '—'
  const minutes = Math.floor(run.value.elapsed_seconds / 60)
  const seconds = run.value.elapsed_seconds % 60
  return `${minutes}:${String(seconds).padStart(2, '0')}`
})
const visibleEvents = computed(() => detail.value?.events.filter(item => item.event_type !== 'diagnosis_worksheet') ?? [])
const worksheetRows = computed(() => worksheet.value ? [
  { index: 1, label: '故障现象', value: worksheet.value.phenomenon },
  { index: 2, label: '关键证据', value: worksheet.value.evidence },
  { index: 3, label: '原因判断', value: worksheet.value.cause },
  { index: 4, label: '修复措施', value: worksheet.value.repair },
  { index: 5, label: '验证结果', value: worksheet.value.verification },
] : [])
const recommendations = computed(() => {
  const items: string[] = []
  if (!worksheet.value?.complete) items.push('补全诊断工作单，尤其要写清“证据为什么支持原因判断”。')
  if ((run.value?.hints_used ?? 0) > 0) items.push(`本次使用了 ${run.value?.hints_used} 次提示，建议在练习模式下重新完成同类案例。`)
  if ((run.value?.wrong_operations ?? 0) > 0) items.push(`回看 ${run.value?.wrong_operations} 次错误操作，区分无效尝试和有证据的检查。`)
  if (run.value && !run.value.prearm_passed) items.push('尚未形成有效飞行许可，应继续处理起飞前门禁。')
  if (run.value && !run.value.flight_validation_passed) items.push('尚未完成基础飞行闭环，不能把“修复完成”等同于“系统可飞”。')
  if (!items.length) items.push('本次证据链完整。下一步可在不使用提示的情况下完成同类故障。')
  return items
})

function componentScore(value: number | null | undefined): string { return value == null ? '—' : `${Math.round(value)}分` }
function eventTime(value: string): string { const date = new Date(value); return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN') }

function latestWorksheetFromEvents(value: TrainingRunDetail): DiagnosisWorksheetSnapshot | null {
  const events = [...value.events].reverse()
  for (const event of events) {
    const candidate = event.payload?.worksheet
    if (candidate && typeof candidate === 'object') return candidate as DiagnosisWorksheetSnapshot
  }
  return null
}

function loadLocalWorksheet(): DiagnosisWorksheetSnapshot | null {
  try {
    const raw = localStorage.getItem(`uav-learning-latest:v1:${auth.user?.id ?? 'guest'}`)
    if (!raw) return null
    const value = JSON.parse(raw) as DiagnosisWorksheetSnapshot
    return value.userId == null || value.userId === auth.user?.id ? value : null
  } catch { return null }
}

async function loadReview(): Promise<void> {
  const generation = ++reviewLoadGeneration
  loading.value = true
  error.value = ''
  detail.value = null
  worksheet.value = null
  try {
    if (runId.value) {
      const loaded = auth.user?.role === 'student'
        ? await studentTrainingApi.runDetail(runId.value)
        : await teacherApi.runDetail(runId.value)
      if (generation !== reviewLoadGeneration) return
      detail.value = loaded
      const resultWorksheet = loaded.run.result?.diagnosis_worksheet
      worksheet.value = latestWorksheetFromEvents(loaded)
        ?? (resultWorksheet && typeof resultWorksheet === 'object' ? resultWorksheet as DiagnosisWorksheetSnapshot : null)
    } else {
      worksheet.value = loadLocalWorksheet()
    }
  } catch (caught) {
    if (generation !== reviewLoadGeneration) return
    error.value = caught instanceof Error ? caught.message : '训练复盘读取失败。'
  } finally {
    if (generation === reviewLoadGeneration) loading.value = false
  }
}

onMounted(async () => {
  await auth.initialize()
  reviewReady.value = true
  await loadReview()
})

watch(runId, () => { if (reviewReady.value) void loadReview() })
</script>

<style scoped>
.review-page{height:100%;min-height:0;overflow:auto;padding:26px clamp(18px,4vw,60px) 50px;background:radial-gradient(circle at 15% 0%,rgba(55,132,218,.12),transparent 32%),linear-gradient(180deg,#f5f9fd,#edf3f8);color:#203852}.review-hero{max-width:1400px;margin:0 auto 16px;display:flex;justify-content:space-between;align-items:end}.review-hero span,.card-head span{font-size:8px;letter-spacing:.14em;color:#3678ba;font-weight:850}.review-hero h1{margin:5px 0 4px;font-size:28px}.review-hero p{margin:0;color:#74869a;font-size:10px}.review-role{display:grid;gap:2px;padding:9px 13px;border:1px solid #cdddeb;border-radius:10px;background:#fff}.review-role small{font-size:7px;color:#8190a0}.review-role b{font-size:10px}.review-state{max-width:1400px;margin:30px auto;padding:30px;text-align:center;border:1px dashed #cfdae6;border-radius:12px;background:#fff;color:#718297}.review-state.error{color:#ac493f}.review-grid{max-width:1400px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:13px}.review-card{padding:16px;border:1px solid #d9e4ee;border-radius:14px;background:rgba(255,255,255,.96);box-shadow:0 10px 28px rgba(23,49,78,.05)}.card-head{display:flex;align-items:start;justify-content:space-between;gap:12px}.card-head h2{margin:4px 0 0;font-size:16px}.card-head>strong{font-size:32px;color:#2775bd}.card-head em{padding:5px 8px;border-radius:999px;background:#fff1e8;color:#a66a30;font-size:8px;font-style:normal}.card-head em.ok{background:#eaf8f1;color:#25764c}.result-card{grid-column:1/-1}.result-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:14px}.result-strip div,.score-grid div{display:grid;gap:3px;padding:10px;border:1px solid #e1e9f1;border-radius:9px;background:#f8fafc}.result-strip small,.score-grid small{font-size:7px;color:#7c8b9d}.result-strip b,.score-grid b{font-size:12px}.stage-strip{display:flex;gap:7px;margin-top:10px}.stage-strip span{padding:5px 8px;border-radius:999px;background:#f2f4f7;color:#7b8795;font-size:8px;font-weight:800}.stage-strip span.ok{background:#e8f8ef;color:#26784d}.worksheet-list{display:grid;gap:8px;margin-top:13px}.worksheet-list article{display:grid;grid-template-columns:24px 1fr;gap:8px;padding:9px;border:1px solid #e0e8f0;border-radius:9px;background:#fbfdff}.worksheet-list i{display:grid;place-items:center;width:22px;height:22px;border-radius:50%;background:#e8f2fd;color:#2e70b7;font-style:normal;font-size:8px;font-weight:850}.worksheet-list small{font-size:7px;color:#78889a}.worksheet-list p{margin:3px 0 0;font-size:9px;line-height:1.55}.score-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:13px}.score-card ul{margin:12px 0 0;padding-left:18px;color:#52677e;font-size:9px;line-height:1.65}.timeline{display:grid;gap:8px;margin-top:13px;max-height:400px;overflow:auto}.timeline article{display:grid;grid-template-columns:8px 100px 1fr;gap:8px;align-items:start}.timeline article>i{width:7px;height:7px;margin-top:4px;border-radius:50%;background:#3b88d2}.timeline time{font-size:7px;color:#8391a1}.timeline article div{display:grid}.timeline article b{font-size:9px}.timeline article small{margin-top:2px;color:#75869a;font-size:7px;line-height:1.5}.empty{padding:24px;text-align:center;color:#8a97a6;font-size:9px}.transfer-card{grid-column:1/-1;display:flex;align-items:center;justify-content:space-between;gap:20px;border-color:#bcdac9;background:linear-gradient(135deg,#f1fbf6,#fff)}.transfer-card span{font-size:8px;color:#39805b;font-weight:850}.transfer-card h2{margin:5px 0;font-size:15px}.transfer-card p{max-width:900px;margin:0;color:#61786b;font-size:9px;line-height:1.6}.transfer-card a{flex:0 0 auto;padding:9px 13px;border-radius:8px;background:#2e7b55;color:#fff;text-decoration:none;font-size:9px;font-weight:850}@media(max-width:850px){.review-grid{grid-template-columns:1fr}.result-card,.transfer-card{grid-column:1}.result-strip{grid-template-columns:1fr 1fr}.transfer-card{align-items:start;flex-direction:column}}
</style>
