<template>
  <div class="teacher-page">
    <header class="teacher-hero">
      <div>
        <span class="eyebrow">TEACHER WORKBENCH · UAV STUDIO</span>
        <h1>教师工作台</h1>
        <p>围绕“班级—任务—实训过程—成绩”组织无人机装调检修教学。</p>
      </div>
      <div class="teacher-identity">
        <span>{{ auth.user?.display_name || auth.user?.username }}</span>
        <b>{{ auth.user?.role === 'admin' ? '管理员' : '教师' }}</b>
      </div>
    </header>

    <div class="teacher-shell">
      <aside class="teacher-tabs">
        <button v-for="item in visibleTabs" :key="item.key" :class="{ active: activeTab === item.key }" @click="activeTab = item.key">
          <span>{{ item.icon }}</span>
          <div><b>{{ item.label }}</b><small>{{ item.hint }}</small></div>
        </button>
      </aside>

      <main class="teacher-main">
        <div v-if="loading" class="state-card">正在读取教学数据…</div>
        <div v-else-if="error" class="state-card error">{{ error }}</div>

        <template v-else-if="activeTab === 'overview'">
          <section class="metric-grid">
            <article><span>班级</span><b>{{ overview?.class_count ?? 0 }}</b><small>已创建教学班</small></article>
            <article><span>学生</span><b>{{ overview?.student_count ?? 0 }}</b><small>当前班级学生</small></article>
            <article><span>进行中任务</span><b>{{ overview?.active_assignment_count ?? 0 }}</b><small>已发布任务</small></article>
            <article><span>已完成实训</span><b>{{ overview?.completed_run_count ?? 0 }}</b><small>TrainingRun</small></article>
            <article class="accent"><span>平均成绩</span><b>{{ scoreText(overview?.average_score) }}</b><small>已完成任务</small></article>
          </section>

          <section class="panel">
            <div class="panel-head">
              <div><h2>最近实训任务</h2><p>查看任务覆盖人数、完成情况和平均成绩。</p></div>
              <button class="primary" @click="activeTab = 'assignments'">发布新任务</button>
            </div>
            <div v-if="!overview?.recent_assignments.length" class="empty">还没有实训任务。先创建班级，再发布第一项故障实训。</div>
            <div v-else class="assignment-cards">
              <article v-for="item in overview.recent_assignments" :key="item.id" class="assignment-card">
                <div class="assignment-top"><span>{{ item.class_name }}</span><b>{{ item.scenario_id }}</b></div>
                <h3>{{ item.title }}</h3>
                <p>{{ item.scenario_title }}</p>
                <div class="progress-line"><i :style="{ width: completionPercent(item) }"></i></div>
                <div class="assignment-stats">
                  <div><span>完成</span><b>{{ item.completed_count }}/{{ item.assigned_count }}</b></div>
                  <div><span>已开始</span><b>{{ item.started_count }}</b></div>
                  <div><span>平均分</span><b>{{ scoreText(item.average_score) }}</b></div>
                </div>
                <button @click="openAssignmentRuns(item)">查看实训记录</button>
              </article>
            </div>
          </section>
        </template>

        <template v-else-if="activeTab === 'classes'">
          <section class="split-grid">
            <div class="panel">
              <div class="panel-head"><div><h2>班级管理</h2><p>每个班级生成独立邀请码，学生自行加入。</p></div></div>
              <div v-if="!classes.length" class="empty">尚未创建班级。</div>
              <div v-else class="class-list">
                <article v-for="item in classes" :key="item.id" :class="['class-row', { selected: selectedClassId === item.id }]" @click="selectedClassId = item.id">
                  <div><b>{{ item.name }}</b><small>{{ item.academic_year || '未设置学年' }} · {{ item.teacher_name }}</small></div>
                  <div class="class-counts"><span>{{ item.student_count }} 人</span><span>{{ item.assignment_count }} 任务</span></div>
                  <code>{{ item.invite_code }}</code>
                </article>
              </div>
            </div>
            <div class="panel create-panel">
              <div class="panel-head"><div><h2>创建班级</h2><p>邀请码创建后即可发给学生。</p></div></div>
              <label><span>班级名称</span><input v-model.trim="classForm.name" placeholder="例如：23无人机1班" /></label>
              <label><span>学年 / 学期</span><input v-model.trim="classForm.academic_year" placeholder="例如：2026-2027-1" /></label>
              <button class="primary wide" :disabled="creatingClass || classForm.name.length < 2" @click="createClassroom">{{ creatingClass ? '创建中…' : '创建班级' }}</button>
              <div v-if="latestClass" class="invite-result"><span>班级邀请码</span><b>{{ latestClass.invite_code }}</b><small>学生在“我的实训”中输入此邀请码加入。</small></div>
            </div>
          </section>
        </template>

        <template v-else-if="activeTab === 'assignments'">
          <section class="split-grid assignment-layout">
            <div class="panel">
              <div class="panel-head"><div><h2>实训任务</h2><p>教师发布案例，系统自动建立学生TrainingRun。</p></div></div>
              <div class="filter-row">
                <select v-model.number="assignmentClassFilter" @change="refreshAssignments"><option :value="0">全部班级</option><option v-for="item in classes" :key="item.id" :value="item.id">{{ item.name }}</option></select>
              </div>
              <div v-if="!assignments.length" class="empty">暂无任务。</div>
              <div v-else class="task-table">
                <button v-for="item in assignments" :key="item.id" @click="openAssignmentRuns(item)">
                  <span class="task-code">{{ item.scenario_id }}</span>
                  <div><b>{{ item.title }}</b><small>{{ item.class_name }} · {{ item.scenario_title }}</small></div>
                  <span>{{ item.completed_count }}/{{ item.assigned_count }}</span>
                  <strong>{{ scoreText(item.average_score) }}</strong>
                </button>
              </div>
            </div>
            <div class="panel create-panel">
              <div class="panel-head"><div><h2>发布新任务</h2><p>第一版直接使用现有故障案例库。</p></div></div>
              <label><span>班级</span><select v-model.number="assignmentForm.class_id"><option :value="0">请选择</option><option v-for="item in classes" :key="item.id" :value="item.id">{{ item.name }}</option></select></label>
              <label><span>实训案例</span><select v-model="assignmentForm.scenario_id"><option value="">请选择</option><option v-for="item in trainingCases" :key="item.id" :value="item.id">{{ item.id }} · {{ item.title }}</option></select></label>
              <label><span>任务名称</span><input v-model.trim="assignmentForm.title" placeholder="例如：第4次实训——综合故障诊断" /></label>
              <label><span>任务说明</span><textarea v-model.trim="assignmentForm.description" rows="4" placeholder="定位故障、完成修复并通过起飞前检查。"></textarea></label>
              <label><span>截止时间（可选）</span><input v-model="assignmentForm.due_at" type="datetime-local" /></label>
              <div class="requirements">
                <span>任务要求</span><b>故障定位 · 修复验证 · Pre-Arm</b>
              </div>
              <label class="flight-requirement"><input v-model="assignmentForm.flight_validation" type="checkbox" /><span>要求完成 PX4 / 教学模拟飞行验证（起飞→悬停→降落）</span></label>
              <div class="requirements"><span>成绩构成</span><b>{{ assignmentForm.flight_validation ? '案例 70% · 飞行 20% · 规范操作 10%' : '案例 70 + 规范操作 10（按有效权重归一）' }}</b></div>
              <button class="primary wide" :disabled="publishing || !canPublish" @click="publishAssignment">{{ publishing ? '发布中…' : '发布任务' }}</button>
            </div>
          </section>
        </template>

        <template v-else-if="activeTab === 'runs'">
          <section class="panel">
            <div class="panel-head runs-head">
              <div><h2>实训记录</h2><p>成绩只是结果，过程日志用于判断学生如何完成任务。</p></div>
              <div class="filter-row">
                <select v-model.number="runClassFilter" @change="refreshRuns"><option :value="0">全部班级</option><option v-for="item in classes" :key="item.id" :value="item.id">{{ item.name }}</option></select>
                <select v-model.number="runAssignmentFilter" @change="refreshRuns"><option :value="0">全部任务</option><option v-for="item in assignments" :key="item.id" :value="item.id">{{ item.title }}</option></select>
                <select v-model="runStatusFilter" @change="refreshRuns"><option value="">全部状态</option><option value="in_progress">诊断中</option><option value="awaiting_prearm">等待 Pre-Arm</option><option value="awaiting_flight">等待飞行验证</option><option value="completed">已完成</option></select>
              </div>
            </div>
            <div class="records-table">
              <div class="records-header"><span>学生</span><span>任务</span><span>状态</span><span>成绩</span><span>用时</span><span>错误</span><span>提示</span><span>首次通过</span><span></span></div>
              <button v-for="item in runs" :key="item.id" class="record-row" @click="openRunDetail(item.id)">
                <span><b>{{ item.student_name }}</b><small>{{ item.class_name }}</small></span>
                <span><b>{{ item.scenario_id }}</b><small>{{ item.assignment_title }}</small></span>
                <span :class="['status', item.status]">{{ runStatusText(item.status) }}</span>
                <strong>{{ scoreText(item.score) }}</strong>
                <span>{{ durationText(item.elapsed_seconds) }}</span>
                <span>{{ item.wrong_operations }}</span><span>{{ item.hints_used }}</span>
                <span>{{ item.first_pass === null ? '—' : item.first_pass ? '是' : '否' }}</span><span>›</span>
              </button>
              <div v-if="!runs.length" class="empty">当前筛选条件下没有实训记录。</div>
            </div>
          </section>
        </template>

        <template v-else-if="activeTab === 'students'">
          <section class="panel">
            <div class="panel-head runs-head">
              <div><h2>学生情况</h2><p>用真实实训过程逐步形成学生能力画像。</p></div>
              <select v-model.number="studentClassFilter" @change="refreshStudents"><option :value="0">全部班级</option><option v-for="item in classes" :key="item.id" :value="item.id">{{ item.name }}</option></select>
            </div>
            <div class="student-grid">
              <article v-for="item in students" :key="`${item.class_id}-${item.user_id}`">
                <div class="student-avatar">{{ item.display_name.slice(0, 1).toUpperCase() }}</div>
                <div class="student-title"><b>{{ item.display_name }}</b><small>@{{ item.username }} · {{ item.class_name }}</small></div>
                <div class="student-score"><span>平均分</span><b>{{ scoreText(item.average_score) }}</b></div>
                <dl><div><dt>已完成</dt><dd>{{ item.completed_runs }}</dd></div><div><dt>首次通过</dt><dd>{{ rateText(item.first_pass_rate) }}</dd></div><div><dt>提示</dt><dd>{{ item.total_hints }}</dd></div><div><dt>错误</dt><dd>{{ item.total_wrong_operations }}</dd></div></dl>
              </article>
              <div v-if="!students.length" class="empty">班级中还没有学生数据。</div>
            </div>
          </section>
        </template>

        <template v-else-if="activeTab === 'grades'">
          <section class="panel">
            <div class="panel-head runs-head">
              <div><h2>课程成绩与班级分析</h2><p>从 TrainingRun 自动汇总，不需要教师二次录入成绩。</p></div>
              <div class="filter-row">
                <select v-model.number="gradeClassId" @change="refreshGradebook"><option :value="0">请选择班级</option><option v-for="item in classes" :key="item.id" :value="item.id">{{ item.name }}</option></select>
                <button class="primary" :disabled="!gradeClassId || exporting" @click="downloadGradebook">{{ exporting ? '导出中…' : '导出 CSV' }}</button>
              </div>
            </div>
            <div v-if="gradeAnalytics" class="grade-metrics">
              <article><span>完成率</span><b>{{ rateText(gradeAnalytics.completion_rate) }}</b></article>
              <article><span>班级均分</span><b>{{ scoreText(gradeAnalytics.average_score) }}</b></article>
              <article><span>首次通过率</span><b>{{ rateText(gradeAnalytics.first_pass_rate) }}</b></article>
              <article><span>平均用时</span><b>{{ durationText(gradeAnalytics.average_elapsed_seconds) }}</b></article>
              <article><span>平均错误</span><b>{{ numberText(gradeAnalytics.average_wrong_operations) }}</b></article>
              <article><span>飞行验证率</span><b>{{ rateText(gradeAnalytics.flight_validation_rate) }}</b></article>
            </div>
            <div v-if="gradebook" class="gradebook-wrap">
              <table class="gradebook-table">
                <thead><tr><th>学生</th><th v-for="assignment in gradebook.assignments" :key="assignment.id"><span>{{ assignment.title }}</span><small>{{ assignment.scenario_id }}<em v-if="assignment.requires_flight_validation"> · 飞行</em></small></th><th>完成</th><th>平均分</th></tr></thead>
                <tbody>
                  <tr v-for="student in gradebook.students" :key="student.user_id">
                    <th><b>{{ student.display_name }}</b><small>@{{ student.username }}</small></th>
                    <td v-for="cell in student.cells" :key="cell.assignment_id">
                      <button v-if="cell.run_id" :class="['grade-cell', cell.stage]" @click="openRunDetail(cell.run_id)"><b>{{ scoreText(cell.score) }}</b><small>{{ runStatusText(cell.stage) }}</small></button>
                      <span v-else class="grade-empty">—</span>
                    </td>
                    <td>{{ student.completed_count }}/{{ gradebook.assignment_count }}</td><td><strong>{{ scoreText(student.average_score) }}</strong></td>
                  </tr>
                </tbody>
              </table>
              <div v-if="!gradebook.students.length" class="empty">该班级暂无学生。</div>
            </div>
            <div v-else class="empty">选择班级后查看成绩册。</div>
          </section>

          <section v-if="gradeAnalytics?.scenarios.length" class="panel">
            <div class="panel-head"><div><h2>任务表现</h2><p>快速发现完成率或首次通过率偏低的训练任务。</p></div></div>
            <div class="scenario-analysis">
              <article v-for="item in gradeAnalytics.scenarios" :key="item.assignment_id"><div><b>{{ item.title }}</b><small>{{ item.scenario_id }}</small></div><span>完成 {{ rateText(item.completion_rate) }}</span><span>均分 {{ scoreText(item.average_score) }}</span><span>首次 {{ rateText(item.first_pass_rate) }}</span></article>
            </div>
          </section>
        </template>

        <template v-else-if="activeTab === 'users' && auth.user?.role === 'admin'">
          <section class="panel">
            <div class="panel-head"><div><h2>用户角色</h2><p>普通注册始终为学生；只有管理员可以赋予教师身份。</p></div></div>
            <div class="user-table">
              <div class="user-head"><span>用户</span><span>当前身份</span><span>状态</span><span>修改</span></div>
              <div v-for="item in adminUsers" :key="item.id" class="user-row">
                <span><b>{{ item.display_name }}</b><small>@{{ item.username }}</small></span>
                <span class="role-badge">{{ roleText(item.role) }}</span>
                <span>{{ item.is_active ? '正常' : '停用' }}</span>
                <select v-if="item.role !== 'admin'" :value="item.role" @change="changeUserRole(item, $event)"><option value="student">学生</option><option value="teacher">教师</option></select>
                <b v-else>管理员不可修改</b>
              </div>
            </div>
          </section>
        </template>
      </main>
    </div>

    <div v-if="runDetail" class="drawer-backdrop" @click.self="runDetail = null">
      <aside class="run-drawer">
        <header><div><span>TRAINING RUN #{{ runDetail.run.id }}</span><h2>{{ runDetail.run.student_name }} · {{ runDetail.run.scenario_title }}</h2></div><div class="drawer-head-actions"><RouterLink :to="{ path: '/review', query: { run: String(runDetail.run.id) } }">打开训练复盘</RouterLink><button @click="runDetail = null">×</button></div></header>
        <div class="drawer-metrics">
          <div><span>成绩</span><b>{{ scoreText(runDetail.run.score) }}</b></div><div><span>用时</span><b>{{ durationText(runDetail.run.elapsed_seconds) }}</b></div><div><span>错误</span><b>{{ runDetail.run.wrong_operations }}</b></div><div><span>提示</span><b>{{ runDetail.run.hints_used }}</b></div>
        </div>
        <div class="verification-strip"><span :class="{ ok: runDetail.run.prearm_passed }">Pre-Arm {{ runDetail.run.prearm_passed ? '通过' : '未通过' }}</span><span :class="{ ok: runDetail.run.flight_validation_passed }">飞行验证 {{ runDetail.run.flight_validation_passed ? '通过' : '未通过' }}</span><span>{{ runStatusText(runDetail.run.stage) }}</span></div>
        <div class="drawer-metrics component-scores"><div><span>案例</span><b>{{ scoreText(runDetail.run.case_score) }}</b></div><div><span>规范操作</span><b>{{ scoreText(runDetail.run.operation_score) }}</b></div><div><span>飞行</span><b>{{ scoreText(runDetail.run.flight_score) }}</b></div></div>
        <h3>诊断过程</h3>
        <div class="timeline"><article v-for="event in runDetail.events" :key="event.id"><i></i><time>{{ eventTime(event.created_at) }}</time><div><b>{{ event.title }}</b><small>{{ event.detail }}</small></div></article><div v-if="!runDetail.events.length" class="empty">尚无过程事件。</div></div>
      </aside>
    </div>

    <div v-if="notice" class="notice">{{ notice }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'
import { teacherApi } from '../api/teacher'
import { loadFaultTrainingCases, type FaultTrainingCase } from '../utils/training'
import type { AdminUserView, AssignmentView, ClassAnalytics, ClassroomView, GradebookView, StudentSummary, TeacherOverview, TrainingRunDetail, TrainingRunView } from '../types/teacher'

type TabKey = 'overview' | 'classes' | 'assignments' | 'runs' | 'students' | 'grades' | 'users'
const auth = useAuthStore()
const activeTab = ref<TabKey>('overview')
const loading = ref(true)
const error = ref('')
const notice = ref('')
const overview = ref<TeacherOverview | null>(null)
const classes = ref<ClassroomView[]>([])
const assignments = ref<AssignmentView[]>([])
const runs = ref<TrainingRunView[]>([])
const students = ref<StudentSummary[]>([])
const adminUsers = ref<AdminUserView[]>([])
const trainingCases = ref<FaultTrainingCase[]>([])
const runDetail = ref<TrainingRunDetail | null>(null)
const gradebook = ref<GradebookView | null>(null)
const gradeAnalytics = ref<ClassAnalytics | null>(null)
const gradeClassId = ref(0)
const exporting = ref(false)
const selectedClassId = ref(0)
const assignmentClassFilter = ref(0)
const runClassFilter = ref(0)
const runAssignmentFilter = ref(0)
const runStatusFilter = ref('')
const studentClassFilter = ref(0)
const creatingClass = ref(false)
const publishing = ref(false)
const latestClass = ref<ClassroomView | null>(null)
const classForm = reactive({ name: '', academic_year: '' })
const assignmentForm = reactive({ class_id: 0, scenario_id: '', title: '', description: '', due_at: '', flight_validation: true })

const tabs = [
  { key: 'overview' as const, icon: '▦', label: '教学总览', hint: '班级与任务状态' },
  { key: 'classes' as const, icon: '◎', label: '班级管理', hint: '邀请码与成员' },
  { key: 'assignments' as const, icon: '▣', label: '实训任务', hint: '发布案例任务' },
  { key: 'runs' as const, icon: '◫', label: '实训记录', hint: 'TrainingRun / Event' },
  { key: 'students' as const, icon: '♙', label: '学生情况', hint: '过程性学习画像' },
  { key: 'grades' as const, icon: '▤', label: '课程成绩', hint: '成绩册与班级分析' },
  { key: 'users' as const, icon: '⚙', label: '用户角色', hint: '管理员专用' },
]
const visibleTabs = computed(() => tabs.filter(item => item.key !== 'users' || auth.user?.role === 'admin'))
const canPublish = computed(() => assignmentForm.class_id > 0 && Boolean(assignmentForm.scenario_id) && assignmentForm.title.trim().length >= 2)

onMounted(async () => {
  await refreshAll()
  try { trainingCases.value = await loadFaultTrainingCases() } catch { trainingCases.value = [] }
})

watch(() => assignmentForm.scenario_id, id => {
  const item = trainingCases.value.find(value => value.id === id)
  if (item && !assignmentForm.title) assignmentForm.title = `${item.id} · ${item.title}`
})
watch(activeTab, next => { if (next === 'grades') void refreshGradebook() })

async function refreshAll(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    const [overviewData, classData, assignmentData, runData, studentData] = await Promise.all([
      teacherApi.overview(), teacherApi.classes(), teacherApi.assignments(), teacherApi.runs(), teacherApi.students(),
    ])
    overview.value = overviewData; classes.value = classData; assignments.value = assignmentData; runs.value = runData; students.value = studentData
    if (auth.user?.role === 'admin') adminUsers.value = await teacherApi.adminUsers()
    if (!assignmentForm.class_id && classData[0]) assignmentForm.class_id = classData[0].id
    if (!gradeClassId.value && classData[0]) gradeClassId.value = classData[0].id
  } catch (caught) {
    error.value = apiError(caught)
  } finally { loading.value = false }
}

async function createClassroom(): Promise<void> {
  creatingClass.value = true
  try {
    latestClass.value = await teacherApi.createClass(classForm)
    classForm.name = ''; classForm.academic_year = ''
    await refreshAll(); activeTab.value = 'classes'; showNotice('班级已创建，邀请码可以发给学生。')
  } catch (caught) { showNotice(apiError(caught)) } finally { creatingClass.value = false }
}

async function publishAssignment(): Promise<void> {
  if (!canPublish.value) return
  publishing.value = true
  try {
    const dueAt = assignmentForm.due_at ? new Date(assignmentForm.due_at).toISOString() : null
    const created = await teacherApi.createAssignment({
      class_id: assignmentForm.class_id, scenario_id: assignmentForm.scenario_id, title: assignmentForm.title,
      description: assignmentForm.description, due_at: dueAt,
      requirements: { diagnosis: true, repair: true, prearm: true, flight_validation: assignmentForm.flight_validation },
      score_weights: { case_score: 70, flight_validation: 20, operation_norm: 10 },
    })
    assignmentForm.scenario_id = ''; assignmentForm.title = ''; assignmentForm.description = ''; assignmentForm.due_at = ''
    await refreshAll(); showNotice(`已发布到 ${created.class_name}`)
  } catch (caught) { showNotice(apiError(caught)) } finally { publishing.value = false }
}

async function refreshGradebook(): Promise<void> {
  if (!gradeClassId.value) { gradebook.value = null; gradeAnalytics.value = null; return }
  try {
    [gradebook.value, gradeAnalytics.value] = await Promise.all([teacherApi.gradebook(gradeClassId.value), teacherApi.analytics(gradeClassId.value)])
  } catch (caught) { showNotice(apiError(caught)) }
}
async function downloadGradebook(): Promise<void> {
  if (!gradeClassId.value || exporting.value) return
  exporting.value = true
  try {
    const blob = await teacherApi.exportGradebook(gradeClassId.value)
    const url = URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = `UAV-Studio-成绩册-${gradeClassId.value}.csv`
    anchor.click(); URL.revokeObjectURL(url)
  } catch (caught) { showNotice(apiError(caught)) } finally { exporting.value = false }
}

async function refreshAssignments(): Promise<void> { assignments.value = await teacherApi.assignments(assignmentClassFilter.value || undefined) }
async function refreshRuns(): Promise<void> {
  runs.value = await teacherApi.runs({
    class_id: runAssignmentFilter.value ? undefined : (runClassFilter.value || undefined),
    assignment_id: runAssignmentFilter.value || undefined,
    status: runStatusFilter.value || undefined,
  })
}
async function refreshStudents(): Promise<void> { students.value = await teacherApi.students(studentClassFilter.value || undefined) }
async function openAssignmentRuns(item: AssignmentView): Promise<void> { activeTab.value = 'runs'; runAssignmentFilter.value = item.id; await refreshRuns() }
async function openRunDetail(id: number): Promise<void> { runDetail.value = await teacherApi.runDetail(id) }
async function changeUserRole(item: AdminUserView, event: Event): Promise<void> {
  const value = (event.target as HTMLSelectElement).value as 'student' | 'teacher'
  try { const updated = await teacherApi.updateRole(item.id, value); Object.assign(item, updated); showNotice(`已将 ${item.display_name} 设置为${roleText(value)}`) }
  catch (caught) { showNotice(apiError(caught)); (event.target as HTMLSelectElement).value = item.role }
}
function completionPercent(item: AssignmentView): string { return `${item.assigned_count ? Math.round(100 * item.completed_count / item.assigned_count) : 0}%` }
function scoreText(value: number | null | undefined): string { return value === null || value === undefined ? '—' : `${Number(value).toFixed(1)}` }
function rateText(value: number | null): string { return value === null ? '—' : `${value.toFixed(0)}%` }
function durationText(seconds: number | null | undefined): string { const value = Math.max(0, Number(seconds || 0)); const m = Math.floor(value / 60); const s = value % 60; return `${m}:${String(s).padStart(2, '0')}` }
function eventTime(value: string): string { const date = new Date(value); return Number.isNaN(date.getTime()) ? value : date.toLocaleTimeString('zh-CN', { hour12: false }) }
function runStatusText(value: string): string { if (value === 'completed') return '已完成'; if (value === 'in_progress' || value === 'diagnosis') return '诊断中'; if (value === 'awaiting_prearm') return '等待 Pre-Arm'; if (value === 'awaiting_flight') return '等待飞行验证'; if (value === 'not_started') return '未开始'; return value }
function numberText(value: number | null): string { return value === null ? '—' : Number(value).toFixed(1) }
function roleText(value: string): string { return value === 'admin' ? '管理员' : value === 'teacher' ? '教师' : '学生' }
function apiError(error: unknown): string { if (axios.isAxiosError(error) && typeof error.response?.data?.detail === 'string') return error.response.data.detail; return error instanceof Error ? error.message : '操作失败' }
function showNotice(message: string): void { notice.value = message; window.setTimeout(() => { if (notice.value === message) notice.value = '' }, 2600) }
</script>

<style scoped>
.teacher-page{min-height:calc(100vh - 56px);padding:24px clamp(20px,3.5vw,56px) 46px;background:radial-gradient(circle at 8% 0%,rgba(45,129,222,.14),transparent 28%),linear-gradient(180deg,#f5f8fc,#edf3f8);color:#20344d}.teacher-hero{max-width:1540px;margin:0 auto 16px;display:flex;justify-content:space-between;align-items:end;gap:20px}.eyebrow{font-size:9px;letter-spacing:.15em;color:#3978bd;font-weight:850}.teacher-hero h1{margin:4px 0;font-size:29px;letter-spacing:-.035em}.teacher-hero p{margin:0;color:#718197;font-size:11px}.teacher-identity{display:flex;align-items:center;gap:8px;padding:8px 11px;border:1px solid #d7e3ef;border-radius:12px;background:#fff}.teacher-identity span{font-size:10px;font-weight:750}.teacher-identity b,.role-badge{padding:3px 7px;border-radius:999px;background:#eaf4ff;color:#2567ad;font-size:8px}.teacher-shell{max-width:1540px;margin:0 auto;display:grid;grid-template-columns:218px minmax(0,1fr);gap:14px}.teacher-tabs{padding:9px;border:1px solid #dce6f0;border-radius:14px;background:rgba(255,255,255,.9);box-shadow:0 10px 26px rgba(27,49,77,.05);align-self:start}.teacher-tabs button{width:100%;display:grid;grid-template-columns:30px 1fr;gap:8px;align-items:center;padding:11px 9px;border:1px solid transparent;border-radius:9px;background:transparent;color:#48627e;text-align:left;cursor:pointer}.teacher-tabs button>span{display:grid;place-items:center;width:28px;height:28px;border-radius:8px;background:#f1f6fb;color:#3978bd;font-size:15px}.teacher-tabs button div{display:grid;gap:2px}.teacher-tabs b{font-size:10px}.teacher-tabs small{font-size:8px;color:#8b98a8}.teacher-tabs button.active{border-color:#bcd7f3;background:#eef7ff;color:#1e5f9f}.teacher-main{min-width:0}.state-card,.panel{border:1px solid #dce6f0;border-radius:14px;background:rgba(255,255,255,.94);box-shadow:0 10px 28px rgba(28,51,78,.05)}.state-card{padding:30px;text-align:center;color:#718197}.state-card.error{color:#ad4b44;background:#fff8f7}.metric-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:12px}.metric-grid article{min-height:100px;display:grid;align-content:center;gap:2px;padding:15px;border:1px solid #dce6f0;border-radius:12px;background:#fff}.metric-grid span{color:#7a8a9e;font-size:9px}.metric-grid b{font-size:25px;color:#223d5c}.metric-grid small{font-size:8px;color:#98a4b2}.metric-grid .accent{background:linear-gradient(135deg,#245f9f,#317dc4);border-color:#2a70b7}.metric-grid .accent span,.metric-grid .accent small{color:#cce2f7}.metric-grid .accent b{color:white}.panel{padding:16px;margin-bottom:12px}.panel-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:13px}.panel-head h2{margin:0;color:#233d5b;font-size:15px}.panel-head p{margin:3px 0 0;color:#8190a1;font-size:9px}.primary{border:1px solid #256bc0;border-radius:8px;background:#2c75c7;color:white;padding:8px 12px;font-size:9px;font-weight:800;cursor:pointer}.primary:disabled{opacity:.45;cursor:not-allowed}.primary.wide{width:100%;margin-top:4px;min-height:38px}.empty{padding:28px;text-align:center;color:#8c99a9;font-size:10px}.assignment-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:9px}.assignment-card{padding:12px;border:1px solid #e0e8f1;border-radius:10px;background:#fafcff}.assignment-top{display:flex;justify-content:space-between;color:#75869a;font-size:8px}.assignment-top b{color:#3479bd}.assignment-card h3{margin:9px 0 3px;font-size:12px}.assignment-card p{margin:0 0 10px;color:#7b899a;font-size:9px}.progress-line{height:5px;overflow:hidden;border-radius:99px;background:#e8eef5}.progress-line i{display:block;height:100%;background:#3d8bd5}.assignment-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:5px;margin:9px 0}.assignment-stats div{display:grid;gap:2px}.assignment-stats span{color:#8996a6;font-size:7px}.assignment-stats b{font-size:10px}.assignment-card>button{width:100%;border:1px solid #d2e1f0;border-radius:7px;background:#fff;color:#356c9f;padding:7px;font-size:8px;cursor:pointer}.split-grid{display:grid;grid-template-columns:minmax(0,1.35fr) minmax(300px,.65fr);gap:12px}.class-list{display:grid;gap:7px}.class-row{display:grid;grid-template-columns:minmax(0,1fr) auto 100px;gap:10px;align-items:center;padding:10px;border:1px solid #e1e9f2;border-radius:9px;cursor:pointer}.class-row.selected{border-color:#78a9dd;background:#f1f8ff}.class-row>div:first-child{display:grid;gap:2px}.class-row b{font-size:10px}.class-row small{font-size:8px;color:#8997a7}.class-counts{display:flex;gap:7px;color:#667b92;font-size:8px}.class-row code{padding:5px 6px;border-radius:6px;background:#eef4fa;color:#2d669f;font-size:8px;text-align:center}.create-panel label{display:grid;gap:5px;margin-bottom:10px}.create-panel label>span,.requirements span{font-size:8px;color:#607790;font-weight:700}.create-panel input,.create-panel select,.create-panel textarea,.filter-row select,.runs-head select,.user-row select{width:100%;border:1px solid #d6e1ec;border-radius:8px;background:#fbfdff;color:#2a4058;padding:8px;font:inherit;font-size:9px;outline:0}.create-panel textarea{resize:vertical}.requirements{display:flex;justify-content:space-between;padding:9px;border:1px solid #e3eaf2;border-radius:8px;background:#f8fafc}.requirements b{font-size:8px;color:#416788}.invite-result{display:grid;gap:3px;margin-top:12px;padding:12px;border:1px solid #bfe2d0;border-radius:10px;background:#f2fcf7}.invite-result span,.invite-result small{font-size:8px;color:#69877a}.invite-result b{font-size:18px;color:#238359;letter-spacing:.08em}.filter-row{display:flex;gap:7px}.filter-row select{width:auto;min-width:130px}.task-table{display:grid;gap:6px}.task-table button{display:grid;grid-template-columns:90px minmax(0,1fr) 70px 60px;gap:8px;align-items:center;padding:9px 10px;border:1px solid #e2e9f1;border-radius:8px;background:#fff;text-align:left;color:#3d5269;cursor:pointer}.task-table button:hover{border-color:#94b9df;background:#f8fbff}.task-code{color:#3477ba;font-size:9px;font-weight:850}.task-table button div{display:grid;gap:2px}.task-table button b{font-size:9px}.task-table button small{color:#8c99a8;font-size:7px}.task-table button>span:nth-last-child(2){font-size:8px;color:#718399}.task-table strong{font-size:11px;color:#2e6ca9}.runs-head{align-items:end}.records-table{overflow:auto}.records-header,.record-row{min-width:880px;display:grid;grid-template-columns:1.2fr 1.7fr .7fr .55fr .65fr .45fr .45fr .7fr 20px;gap:8px;align-items:center}.records-header{padding:7px 9px;color:#8a98a8;font-size:7px;border-bottom:1px solid #e6edf4}.record-row{width:100%;padding:9px;border:0;border-bottom:1px solid #edf1f5;background:transparent;text-align:left;color:#42576d;cursor:pointer}.record-row:hover{background:#f7faff}.record-row>span{font-size:8px}.record-row>span:first-child,.record-row>span:nth-child(2){display:grid;gap:2px}.record-row b{font-size:9px}.record-row small{font-size:7px;color:#8997a7}.record-row strong{color:#286aab}.status{display:inline-flex!important;width:max-content;padding:3px 6px;border-radius:999px;background:#eef3f7;color:#6c7d8f}.status.completed{background:#eaf8f1;color:#26764e}.status.in_progress{background:#fff6df;color:#956a18}.student-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:9px}.student-grid article{display:grid;grid-template-columns:42px 1fr auto;gap:9px;align-items:center;padding:12px;border:1px solid #e2e9f1;border-radius:10px;background:#fbfcfe}.student-avatar{display:grid;place-items:center;width:40px;height:40px;border-radius:11px;background:#e9f3ff;color:#2d70b4;font-size:15px;font-weight:900}.student-title{display:grid;gap:2px}.student-title b{font-size:10px}.student-title small{font-size:7px;color:#8997a7}.student-score{display:grid;text-align:right}.student-score span{font-size:7px;color:#8b98a7}.student-score b{font-size:16px;color:#2e6da9}.student-grid dl{grid-column:1/-1;display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin:4px 0 0}.student-grid dl div{padding:6px;border-radius:6px;background:#f2f6fa}.student-grid dt{font-size:7px;color:#8b98a7}.student-grid dd{margin:2px 0 0;font-size:9px;font-weight:800}.flight-requirement{display:flex!important;grid-template-columns:18px 1fr;align-items:center!important;gap:6px}.flight-requirement input{width:auto!important}.grade-metrics{display:grid;grid-template-columns:repeat(6,1fr);gap:7px;margin-bottom:12px}.grade-metrics article{display:grid;gap:3px;padding:10px;border:1px solid #e1e9f1;border-radius:9px;background:#f8fbfe}.grade-metrics span{font-size:7px;color:#8594a5}.grade-metrics b{font-size:15px;color:#2e608f}.gradebook-wrap{overflow:auto}.gradebook-table{min-width:900px;width:100%;border-collapse:separate;border-spacing:0;font-size:8px}.gradebook-table th,.gradebook-table td{min-width:112px;padding:7px;border-right:1px solid #e5ebf2;border-bottom:1px solid #e5ebf2;text-align:center;background:#fff}.gradebook-table thead th{position:sticky;top:0;background:#f4f8fc;z-index:2}.gradebook-table thead th:first-child,.gradebook-table tbody th{position:sticky;left:0;z-index:3;min-width:130px;text-align:left}.gradebook-table tbody th{background:#fbfdff}.gradebook-table th span,.gradebook-table th small,.gradebook-table tbody th b,.gradebook-table tbody th small{display:block}.gradebook-table th small,.gradebook-table tbody th small{margin-top:2px;color:#8493a4;font-size:7px}.gradebook-table th em{color:#337cc1;font-style:normal}.grade-cell{width:100%;display:grid;gap:2px;padding:5px;border:1px solid #dce6ef;border-radius:6px;background:#f8fafc;color:#47627e;cursor:pointer}.grade-cell b{font-size:11px}.grade-cell small{font-size:6px}.grade-cell.completed{background:#edf9f3;border-color:#c5e5d3;color:#24734b}.grade-cell.awaiting_flight{background:#fff8e8;border-color:#efd89f;color:#8b6517}.grade-cell.awaiting_prearm{background:#fff2ed;border-color:#edcbc0;color:#9a5845}.grade-empty{color:#aab4bf}.scenario-analysis{display:grid;gap:6px}.scenario-analysis article{display:grid;grid-template-columns:minmax(0,1fr) repeat(3,110px);gap:8px;align-items:center;padding:9px;border:1px solid #e3eaf2;border-radius:8px}.scenario-analysis article div{display:grid}.scenario-analysis b{font-size:9px}.scenario-analysis small,.scenario-analysis span{font-size:7px;color:#7e8e9f}.component-scores{grid-template-columns:repeat(3,1fr)!important}.status.awaiting_flight{background:#fff6df;color:#956a18}.status.awaiting_prearm{background:#fff0eb;color:#9d5e4b}@media(max-width:1200px){.grade-metrics{grid-template-columns:repeat(3,1fr)}}
.user-table{display:grid}.user-head,.user-row{display:grid;grid-template-columns:1.5fr .7fr .6fr 1fr;gap:10px;align-items:center;padding:9px}.user-head{color:#8795a6;font-size:8px;border-bottom:1px solid #e6edf4}.user-row{border-bottom:1px solid #edf1f5}.user-row>span:first-child{display:grid;gap:2px}.user-row b{font-size:9px}.user-row small{font-size:7px;color:#8b98a7}.drawer-backdrop{position:fixed;z-index:80;inset:56px 0 0;background:rgba(11,27,45,.32);display:flex;justify-content:flex-end}.run-drawer{width:min(620px,94vw);height:100%;overflow:auto;padding:18px;background:#fff;box-shadow:-24px 0 60px rgba(12,32,58,.18)}.run-drawer header{display:flex;justify-content:space-between;align-items:start;border-bottom:1px solid #e5ebf2;padding-bottom:12px}.run-drawer header span{color:#4381be;font-size:8px;font-weight:800}.run-drawer h2{margin:4px 0;font-size:17px}.drawer-head-actions{display:flex;align-items:center;gap:7px}.drawer-head-actions a{padding:7px 9px;border-radius:7px;background:#eaf4ff;color:#286db4;text-decoration:none;font-size:8px;font-weight:800}.run-drawer header button{border:0;background:#eff4f8;width:30px;height:30px;border-radius:8px;cursor:pointer}.drawer-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:7px;margin:12px 0}.drawer-metrics div{padding:9px;border:1px solid #e1e9f1;border-radius:8px;display:grid;gap:2px}.drawer-metrics span{font-size:7px;color:#8997a6}.drawer-metrics b{font-size:14px}.verification-strip{display:flex;gap:7px;margin-bottom:18px}.verification-strip span{padding:5px 8px;border-radius:999px;background:#f5eeee;color:#99605a;font-size:8px}.verification-strip span.ok{background:#eaf8f0;color:#28784f}.run-drawer h3{font-size:12px}.timeline{padding-left:8px}.timeline article{position:relative;display:grid;grid-template-columns:72px 1fr;gap:9px;padding:8px 8px 8px 18px;border-left:1px solid #d8e5f1}.timeline i{position:absolute;left:-4px;top:13px;width:7px;height:7px;border-radius:50%;background:#3b84ca}.timeline time{font-size:8px;color:#7e8d9e}.timeline article div{display:grid;gap:2px}.timeline b{font-size:9px}.timeline small{font-size:8px;color:#7b8998;line-height:1.5}.notice{position:fixed;z-index:120;bottom:22px;left:50%;transform:translateX(-50%);padding:8px 13px;border-radius:999px;background:#203b59;color:#fff;font-size:9px;box-shadow:0 10px 24px rgba(0,0,0,.17)}@media(max-width:1150px){.metric-grid{grid-template-columns:repeat(3,1fr)}.teacher-shell{grid-template-columns:180px minmax(0,1fr)}.split-grid{grid-template-columns:1fr}.teacher-tabs small{display:none}}@media(max-width:820px){.teacher-shell{grid-template-columns:1fr}.teacher-tabs{display:flex;overflow:auto}.teacher-tabs button{min-width:130px}.metric-grid{grid-template-columns:1fr 1fr}.teacher-hero{align-items:start;flex-direction:column}}
</style>
