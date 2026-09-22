<template>
  <section class="diagnosis-worksheet" data-testid="diagnosis-worksheet">
    <header>
      <div>
        <span>DIAGNOSIS WORKSHEET · V1</span>
        <h3>诊断工作单</h3>
        <p>先写清证据链，再提交故障诊断。</p>
      </div>
      <strong :class="{ complete }">{{ completedCount }}/5</strong>
    </header>

    <div class="worksheet-progress"><i :style="{ width: `${completedCount * 20}%` }"></i></div>

    <label v-for="field in fields" :key="field.key">
      <span><b>{{ field.index }}. {{ field.label }}</b><small>{{ field.help }}</small></span>
      <textarea
        v-model.trim="form[field.key]"
        :placeholder="field.placeholder"
        rows="2"
        :data-testid="`worksheet-${field.key}`"
        @input="markDirty"
      ></textarea>
    </label>

    <div class="worksheet-footer">
      <div>
        <b>{{ complete ? '诊断链条已完整' : `还需完成 ${5 - completedCount} 项` }}</b>
        <small>{{ saveMessage || '内容自动保存在当前账号与案例下。' }}</small>
      </div>
      <button type="button" :disabled="saving" data-testid="worksheet-save" @click="save">
        {{ saving ? '保存中…' : '保存工作单' }}
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { studentTrainingApi } from '../api/teacher'
import type { LearningRole } from '../utils/learningGuide'

export interface DiagnosisWorksheetSnapshot {
  version: 1
  userId: number | null
  role: LearningRole
  runId: number | null
  scenarioId: string
  scenarioTitle: string
  phenomenon: string
  evidence: string
  cause: string
  repair: string
  verification: string
  complete: boolean
  savedAt: string
}

type WorksheetField = 'phenomenon' | 'evidence' | 'cause' | 'repair' | 'verification'

const props = defineProps<{
  userId: number | null
  role: LearningRole
  runId: number | null
  scenarioId: string
  scenarioTitle: string
  symptom?: string
}>()

const emit = defineEmits<{
  (event: 'saved', snapshot: DiagnosisWorksheetSnapshot): void
  (event: 'ready-change', ready: boolean): void
  (event: 'progress-change', completed: number): void
}>()

const fields: Array<{ key: WorksheetField; index: number; label: string; help: string; placeholder: string }> = [
  { key: 'phenomenon', index: 1, label: '故障现象', help: '用自己的话复述，不要只抄案例名称', placeholder: '例如：最终起飞检查无法通过，航向数据不稳定……' },
  { key: 'evidence', index: 2, label: '关键证据', help: '记录数据、状态或测试结果', placeholder: '例如：磁场强度异常，EKF状态显示航向估计异常……' },
  { key: 'cause', index: 3, label: '原因判断', help: '说明证据为什么支持这个结论', placeholder: '我判断故障原因是……因为……' },
  { key: 'repair', index: 4, label: '修复措施', help: '记录实际采取的操作或参数调整', placeholder: '我执行了……并将……恢复为……' },
  { key: 'verification', index: 5, label: '验证结果', help: '说明如何证明故障已经排除', placeholder: '重新检查后……，Pre-Arm结果为……' },
]

const form = reactive<Record<WorksheetField, string>>({ phenomenon: '', evidence: '', cause: '', repair: '', verification: '' })
const saving = ref(false)
const dirty = ref(false)
const saveMessage = ref('')

const storageKey = computed(() => `uav-learning-workbook:v1:${props.userId ?? 'guest'}:${props.runId ?? (props.scenarioId || 'free')}`)
const completedCount = computed(() => fields.filter(item => form[item.key].trim().length >= 3).length)
const complete = computed(() => completedCount.value === fields.length)

function snapshot(): DiagnosisWorksheetSnapshot {
  return {
    version: 1,
    userId: props.userId,
    role: props.role,
    runId: props.runId,
    scenarioId: props.scenarioId,
    scenarioTitle: props.scenarioTitle,
    phenomenon: form.phenomenon.trim(),
    evidence: form.evidence.trim(),
    cause: form.cause.trim(),
    repair: form.repair.trim(),
    verification: form.verification.trim(),
    complete: complete.value,
    savedAt: new Date().toISOString(),
  }
}

function load(): void {
  for (const field of fields) form[field.key] = ''
  try {
    const raw = localStorage.getItem(storageKey.value)
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<DiagnosisWorksheetSnapshot>
      for (const field of fields) form[field.key] = String(parsed[field.key] ?? '')
    } else if (props.symptom) {
      form.phenomenon = props.symptom
    }
  } catch { /* a damaged local draft must not block the workbench */ }
  dirty.value = false
  saveMessage.value = ''
}

function contentHash(value: string): string {
  let hash = 2166136261
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index)
    hash = Math.imul(hash, 16777619)
  }
  return (hash >>> 0).toString(16)
}

function persistLocal(value: DiagnosisWorksheetSnapshot): void {
  localStorage.setItem(storageKey.value, JSON.stringify(value))
  localStorage.setItem(`uav-learning-latest:v1:${props.userId ?? 'guest'}`, JSON.stringify(value))
}

async function save(): Promise<DiagnosisWorksheetSnapshot> {
  const value = snapshot()
  saving.value = true
  persistLocal(value)
  try {
    if (props.role === 'student' && props.runId) {
      const serial = JSON.stringify(value)
      await studentTrainingApi.appendEvent(props.runId, {
        event_type: 'diagnosis_worksheet',
        title: value.complete ? '提交完整诊断工作单' : '保存诊断工作单草稿',
        detail: value.complete ? '现象、证据、原因、修复与验证五项已完成。' : `已完成 ${completedCount.value}/5 项。`,
        event_key: `worksheet-v1-${contentHash(serial)}`,
        payload: { worksheet: value },
      })
      saveMessage.value = value.complete ? '已保存并同步到课程记录。' : '草稿已同步，提交诊断前需完成五项。'
    } else {
      saveMessage.value = props.role === 'student' ? '已保存到当前账号。' : '已保存为教学演示工作单。'
    }
    dirty.value = false
    emit('saved', value)
    return value
  } catch {
    saveMessage.value = '已保存到本机，但课程记录同步失败，请稍后重试。'
    return value
  } finally {
    saving.value = false
  }
}

function markDirty(): void {
  dirty.value = true
  saveMessage.value = '有尚未保存的修改。'
}

watch(storageKey, load)
watch(complete, value => emit('ready-change', value), { immediate: true })
watch(completedCount, value => emit('progress-change', value), { immediate: true })
watch(form, () => { if (dirty.value) persistLocal(snapshot()) }, { deep: true })
onMounted(load)

defineExpose({
  isComplete: () => complete.value,
  save,
  getSnapshot: snapshot,
})
</script>

<style scoped>
.diagnosis-worksheet{margin:0 0 14px;padding:14px;border:1px solid rgba(92,174,231,.34);border-radius:10px;background:linear-gradient(145deg,rgba(15,42,66,.96),rgba(10,29,47,.98));color:#dcecf9;box-shadow:0 14px 34px rgba(0,0,0,.14)}header{display:flex;justify-content:space-between;gap:12px;align-items:start}header span{font-size:7px;letter-spacing:.13em;color:#63cfff;font-weight:850}header h3{margin:3px 0;font-size:14px}header p{margin:0;color:#88a7c1;font-size:8px}header strong{display:grid;place-items:center;width:38px;height:38px;border-radius:50%;border:2px solid #476b89;color:#8ba9c1;font-size:11px}header strong.complete{border-color:#3bc885;color:#6ce3aa}.worksheet-progress{height:4px;margin:11px 0 12px;overflow:hidden;border-radius:4px;background:#18354e}.worksheet-progress i{display:block;height:100%;border-radius:4px;background:linear-gradient(90deg,#2f91dd,#38d39a);transition:width .2s}label{display:grid;grid-template-columns:minmax(125px,.42fr) 1fr;gap:10px;align-items:start;padding:8px 0;border-top:1px solid rgba(115,155,188,.13)}label>span{display:grid;gap:3px}label b{font-size:9px}label small{color:#7898b2;font-size:7px;line-height:1.45}textarea{box-sizing:border-box;width:100%;resize:vertical;border:1px solid #284b67;border-radius:7px;background:#071827;color:#dcecf9;padding:8px;font:inherit;font-size:8px;line-height:1.5;outline:0}textarea:focus{border-color:#37a9ee;box-shadow:0 0 0 2px rgba(55,169,238,.1)}.worksheet-footer{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:10px;padding-top:10px;border-top:1px solid rgba(115,155,188,.16)}.worksheet-footer>div{display:grid;gap:2px}.worksheet-footer b{font-size:9px}.worksheet-footer small{color:#7f9db6;font-size:7px}.worksheet-footer button{border:1px solid #2e8bd0;border-radius:7px;background:#1978bd;color:#fff;padding:8px 10px;font-size:8px;font-weight:800;cursor:pointer}.worksheet-footer button:disabled{opacity:.5}@media(max-width:760px){label{grid-template-columns:1fr}}
</style>
