<template>
  <div class="training-page">
    <header class="training-hero">
      <div>
        <span class="eyebrow">MY TRAINING · UAV STUDIO</span>
        <h1>我的实训</h1>
        <p>加入教师班级，接收装调检修任务，并从任务直接进入故障案例。</p>
      </div>
      <button class="refresh" :disabled="loading" @click="refresh">{{ loading ? '刷新中…' : '刷新任务' }}</button>
    </header>

    <main class="training-shell">
      <section class="join-card">
        <div><b>加入班级</b><small>输入教师工作台生成的班级邀请码</small></div>
        <input v-model.trim="inviteCode" maxlength="32" placeholder="例如 UAV-A1B2C3" @keyup.enter="joinClass" />
        <button :disabled="joining || !inviteCode" @click="joinClass">{{ joining ? '加入中…' : '加入' }}</button>
      </section>

      <section v-if="classes.length" class="class-strip">
        <article v-for="item in classes" :key="item.class_id"><span>班级</span><b>{{ item.class_name }}</b><small>{{ item.teacher_name }} · {{ formatDate(item.joined_at) }}</small></article>
      </section>

      <section class="assignment-section">
        <div class="section-title"><div><h2>实训任务</h2><p>开始任务后系统会创建 TrainingRun，并自动记录调试过程。</p></div><span>{{ assignments.length }} 项</span></div>
        <div v-if="error" class="error">{{ error }}</div>
        <div v-if="!loading && assignments.length === 0" class="empty">暂时没有实训任务。若尚未加入班级，请先输入邀请码。</div>
        <div class="assignment-grid">
          <article v-for="item in assignments" :key="item.id" :class="['assignment-card', item.run_status]">
            <div class="card-top"><span>{{ item.class_name }}</span><b>{{ item.scenario_id }}</b></div>
            <h3>{{ item.title }}</h3>
            <p>{{ item.description || item.scenario_title }}</p>
            <div class="case-line"><span>案例</span><b>{{ item.scenario_title }}</b><em>{{ stars(item.difficulty) }}</em></div>
            <div class="task-meta"><div><span>建议时间</span><b>{{ item.recommended_minutes }} min</b></div><div><span>截止</span><b>{{ dueText(item.due_at) }}</b></div></div>
            <div v-if="item.run_status === 'completed'" class="completed-result"><span>已完成</span><b>{{ scoreText(item.score) }}<em>/100</em></b><small>用时 {{ durationText(item.elapsed_seconds) }}</small></div>
            <div v-else-if="item.run_status !== 'not_started'" class="progress-state"><i></i><span>{{ trainingStatusText(item.run_stage || item.run_status) }} · 已记录 {{ durationText(item.elapsed_seconds) }}</span></div>
            <button :disabled="startingId === item.id" @click="startAssignment(item)">{{ startingId === item.id ? '正在进入…' : taskActionText(item) }}</button>
          </article>
        </div>
      </section>
    </main>

    <div v-if="notice" class="notice">{{ notice }}</div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { studentTrainingApi } from '../api/teacher'
import { useAssemblyStore } from '../stores/assembly'
import type { EnrollmentView, StudentAssignmentView } from '../types/teacher'
import { buildStudentTrainingRoute, trainingStatusText } from '../utils/trainingFlow'

const router = useRouter()
const assembly = useAssemblyStore()
const loading = ref(true)
const joining = ref(false)
const startingId = ref<number | null>(null)
const inviteCode = ref('')
const classes = ref<EnrollmentView[]>([])
const assignments = ref<StudentAssignmentView[]>([])
const error = ref('')
const notice = ref('')

onMounted(async () => { await assembly.initialize(); await refresh() })

async function refresh(): Promise<void> {
  loading.value = true; error.value = ''
  try { [classes.value, assignments.value] = await Promise.all([studentTrainingApi.classes(), studentTrainingApi.assignments()]) }
  catch (caught) { error.value = apiError(caught) }
  finally { loading.value = false }
}

async function joinClass(): Promise<void> {
  if (!inviteCode.value) return
  joining.value = true
  try { const joined = await studentTrainingApi.joinClass(inviteCode.value); inviteCode.value = ''; showNotice(`已加入 ${joined.class_name}`); await refresh() }
  catch (caught) { showNotice(apiError(caught)) }
  finally { joining.value = false }
}

async function startAssignment(item: StudentAssignmentView): Promise<void> {
  startingId.value = item.id
  try {
    if (item.run_status === 'completed' && item.run_id) {
      await router.push({ path: '/review', query: { run: String(item.run_id) } })
      return
    }
    const run = await studentTrainingApi.startAssignment(item.id, assembly.activeAircraftId)
    await router.push(buildStudentTrainingRoute({
      runId: run.id, assignmentId: item.id, scenarioId: run.scenario_id, status: run.stage || run.status,
    }))
  } catch (caught) { showNotice(apiError(caught)) }
  finally { startingId.value = null }
}


function taskActionText(item: StudentAssignmentView): string {
  if (item.run_status === 'completed') return '查看训练复盘'
  if (item.run_stage === 'awaiting_flight' || item.run_status === 'awaiting_flight') return '进入飞行验证'
  if (item.run_status !== 'not_started') return '继续实训'
  return '开始实训'
}
function stars(value: number): string { return '★'.repeat(Math.max(1, Math.min(3, value))) }
function scoreText(value: number | null): string { return value === null ? '—' : value.toFixed(0) }
function durationText(value: number): string { const m = Math.floor(Math.max(0, value) / 60); const s = Math.max(0, value) % 60; return `${m}:${String(s).padStart(2, '0')}` }
function dueText(value: string | null): string { if (!value) return '不限'; const d = new Date(value); return Number.isNaN(d.getTime()) ? value : d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) }
function formatDate(value: string): string { const d = new Date(value); return Number.isNaN(d.getTime()) ? value : d.toLocaleDateString('zh-CN') }
function apiError(err: unknown): string { if (axios.isAxiosError(err) && typeof err.response?.data?.detail === 'string') return err.response.data.detail; return err instanceof Error ? err.message : '操作失败' }
function showNotice(message: string): void { notice.value = message; window.setTimeout(() => { if (notice.value === message) notice.value = '' }, 2600) }
</script>

<style scoped>
.training-page{height:100%;min-height:0;overflow:auto;padding:26px clamp(20px,4vw,62px) 50px;background:radial-gradient(circle at 12% 0%,rgba(58,136,225,.13),transparent 30%),linear-gradient(180deg,#f5f9fd,#edf3f8);color:#203852}.training-hero{max-width:1440px;margin:0 auto 16px;display:flex;justify-content:space-between;align-items:end}.eyebrow{font-size:9px;color:#3978bd;letter-spacing:.15em;font-weight:800}.training-hero h1{margin:4px 0;font-size:29px}.training-hero p{margin:0;color:#718298;font-size:11px}.refresh{border:1px solid #cbdbea;border-radius:8px;background:#fff;color:#406383;padding:8px 12px;font-size:9px;font-weight:750;cursor:pointer}.training-shell{max-width:1440px;margin:0 auto}.join-card{display:grid;grid-template-columns:minmax(220px,1fr) minmax(220px,360px) 90px;gap:10px;align-items:center;padding:13px 14px;border:1px solid #d9e5f0;border-radius:13px;background:#fff;box-shadow:0 9px 24px rgba(30,53,80,.05)}.join-card>div{display:grid;gap:2px}.join-card b{font-size:11px}.join-card small{font-size:8px;color:#8795a6}.join-card input{border:1px solid #d5e0eb;border-radius:8px;padding:9px 10px;font:inherit;font-size:10px;outline:0;text-transform:uppercase}.join-card button,.assignment-card>button{border:1px solid #2f77c5;border-radius:8px;background:#347fcf;color:white;padding:9px;font-size:9px;font-weight:800;cursor:pointer}.join-card button:disabled,.assignment-card>button:disabled{opacity:.45;cursor:not-allowed}.class-strip{display:flex;gap:8px;margin:10px 0;overflow:auto}.class-strip article{min-width:210px;display:grid;gap:2px;padding:10px 12px;border:1px solid #dce6ef;border-radius:10px;background:rgba(255,255,255,.88)}.class-strip span{font-size:7px;color:#8391a1}.class-strip b{font-size:10px}.class-strip small{font-size:7px;color:#8997a7}.assignment-section{margin-top:18px}.section-title{display:flex;justify-content:space-between;align-items:end;margin-bottom:10px}.section-title h2{margin:0;font-size:16px}.section-title p{margin:3px 0 0;color:#7e8d9f;font-size:9px}.section-title>span{padding:4px 8px;border-radius:999px;background:#eaf3fc;color:#3973ad;font-size:8px;font-weight:800}.assignment-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:12px}.assignment-card{display:flex;flex-direction:column;min-height:315px;padding:14px;border:1px solid #dce6f0;border-radius:14px;background:#fff;box-shadow:0 10px 26px rgba(28,51,78,.05)}.assignment-card.completed{border-color:#bee1ce}.assignment-card.in_progress{border-color:#e8ce91}.card-top{display:flex;justify-content:space-between;color:#7e8e9f;font-size:8px}.card-top b{color:#3778b7}.assignment-card h3{margin:12px 0 5px;font-size:14px}.assignment-card p{min-height:38px;margin:0 0 10px;color:#748397;font-size:9px;line-height:1.55}.case-line{display:grid;grid-template-columns:auto 1fr auto;gap:7px;align-items:center;padding:9px;border-radius:8px;background:#f5f8fb}.case-line span{font-size:7px;color:#8895a5}.case-line b{font-size:9px}.case-line em{color:#e1a52f;font-style:normal;font-size:9px}.task-meta{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin:8px 0}.task-meta div{display:grid;gap:2px;padding:7px;border:1px solid #e5ebf2;border-radius:7px}.task-meta span{font-size:7px;color:#8a97a6}.task-meta b{font-size:9px}.completed-result{display:grid;grid-template-columns:1fr auto;align-items:center;margin:auto 0 8px;padding:9px;border-radius:8px;background:#edf9f3}.completed-result>span{font-size:8px;color:#3a7d59}.completed-result>b{font-size:18px;color:#26794e}.completed-result em{font-size:8px;font-style:normal}.completed-result small{grid-column:1/-1;font-size:7px;color:#6d8c7b}.progress-state{margin:auto 0 8px;display:flex;align-items:center;gap:7px;padding:8px;border-radius:8px;background:#fff7e6;color:#8e691c;font-size:8px}.progress-state i{width:7px;height:7px;border-radius:50%;background:#e6ad37;box-shadow:0 0 0 4px rgba(230,173,55,.12)}.assignment-card>button{margin-top:auto}.empty,.error{padding:28px;text-align:center;border:1px dashed #d6e1eb;border-radius:10px;color:#8694a4;font-size:9px}.error{color:#aa5149;border-color:#efcfcb;background:#fff8f7}.notice{position:fixed;z-index:80;left:50%;bottom:23px;transform:translateX(-50%);padding:8px 13px;border-radius:999px;background:#213d5c;color:#fff;font-size:9px;box-shadow:0 10px 28px rgba(0,0,0,.16)}@media(max-width:720px){.join-card{grid-template-columns:1fr}.training-hero{align-items:start;flex-direction:column;gap:10px}}
</style>
