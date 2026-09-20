<template>
  <div class="aircraft-library-page">
    <header class="library-hero">
      <div>
        <span class="eyebrow">AIRCRAFT DESIGN LIBRARY</span>
        <h1>我的飞机</h1>
        <p>每一架飞机都是独立保存的设计。装配、工程参数与飞行实验都跟随当前飞机。</p>
      </div>
      <div class="hero-actions">
        <button class="secondary-button" :disabled="store.libraryLoading" @click="store.refreshLibrary()">
          刷新
        </button>
        <button class="primary-button" data-testid="new-aircraft" @click="openCreateDialog()">
          + 新建设计
        </button>
      </div>
    </header>

    <section class="library-summary">
      <div>
        <strong>{{ store.aircraftLibrary.length }}</strong>
        <span>飞机设计</span>
      </div>
      <div>
        <strong>{{ validDesignCount }}</strong>
        <span>通过工程检查</span>
      </div>
      <div>
        <strong>{{ totalExperiments }}</strong>
        <span>累计飞行实验</span>
      </div>
      <div class="autosave-summary">
        <i :class="store.saveStatus"></i>
        <span>当前设计 {{ store.saveStatusZh }}</span>
      </div>
    </section>

    <main class="design-grid" data-testid="aircraft-library-grid">
      <article
        v-for="item in store.aircraftLibrary"
        :key="item.aircraft.id"
        :class="['design-card', { active: item.aircraft.id === store.activeAircraftId }]"
        :data-aircraft-id="item.aircraft.id"
        data-testid="aircraft-design-card"
      >
        <div class="design-preview">
          <AircraftMiniature
            :aircraft="item.aircraft"
            :components="store.components"
          />
          <span v-if="item.aircraft.id === store.activeAircraftId" class="active-badge">
            当前设计
          </span>
          <span :class="['validation-badge', item.validation.passed ? 'ok' : 'error']">
            {{ item.validation.passed ? '可飞行' : '待完善' }}
          </span>
        </div>

        <div class="design-body">
          <div class="design-heading">
            <div>
              <h2>{{ item.aircraft.name }}</h2>
              <p>{{ item.description || '暂无设计说明。' }}</p>
            </div>
            <button
              class="icon-button"
              :title="`${item.aircraft.name} 设计信息`"
              @click="openEditDialog(item)"
            >
              ···
            </button>
          </div>

          <div class="design-metrics">
            <div>
              <span>总质量</span>
              <b>{{ metricMass(item) }}</b>
            </div>
            <div>
              <span>推重比</span>
              <b>{{ metricTwr(item) }}</b>
            </div>
            <div>
              <span>预计续航</span>
              <b>{{ metricEndurance(item) }}</b>
            </div>
          </div>

          <div class="design-meta">
            <span>{{ formatRelative(item.updated_at) }}</span>
            <span>{{ item.experiment_count }} 次实验</span>
            <span>#{{ item.aircraft.id }}</span>
          </div>

          <div class="design-actions">
            <button
              class="open-button"
              data-testid="open-aircraft-design"
              @click="openAircraft(item.aircraft.id!)"
            >
              {{ item.aircraft.id === store.activeAircraftId ? '继续设计' : '打开设计' }}
            </button>
            <button
              class="quiet-button"
              data-testid="duplicate-aircraft-design"
              @click="duplicate(item)"
            >
              复制方案
            </button>
          </div>
        </div>
      </article>

      <button class="new-design-card" @click="openCreateDialog()">
        <span>+</span>
        <b>新建设计</b>
        <small>从参考机、空白 Quad-X 或 450 机架开始</small>
      </button>
    </main>

    <div v-if="notice" class="library-notice">{{ notice }}</div>

    <div v-if="createDialogOpen" class="modal-backdrop" @click.self="createDialogOpen = false">
      <section class="design-modal" data-testid="new-aircraft-dialog">
        <header>
          <div>
            <span class="eyebrow">NEW AIRCRAFT</span>
            <h2>新建设计</h2>
          </div>
          <button class="modal-close" @click="createDialogOpen = false">×</button>
        </header>

        <div class="template-grid">
          <button
            v-for="template in store.aircraftTemplates"
            :key="template.key"
            :class="['template-card', { selected: template.key === createForm.templateKey }]"
            :data-template-key="template.key"
            @click="createForm.templateKey = template.key"
          >
            <span class="template-icon">{{ templateIcon(template.key) }}</span>
            <b>{{ template.name }}</b>
            <small>{{ template.description }}</small>
          </button>
        </div>

        <label class="form-field">
          <span>设计名称</span>
          <input v-model.trim="createForm.name" maxlength="120" placeholder="例如：长航时巡检机 V1" />
        </label>
        <label class="form-field">
          <span>设计说明</span>
          <textarea
            v-model.trim="createForm.description"
            maxlength="1000"
            rows="3"
            placeholder="记录用途、目标载荷或设计思路。"
          ></textarea>
        </label>

        <footer>
          <button class="secondary-button" @click="createDialogOpen = false">取消</button>
          <button
            class="primary-button"
            :disabled="creating || !createForm.templateKey"
            data-testid="create-aircraft-submit"
            @click="createDesign()"
          >
            {{ creating ? '正在创建…' : '创建并进入装配' }}
          </button>
        </footer>
      </section>
    </div>

    <div v-if="editDialogOpen && editingItem" class="modal-backdrop" @click.self="editDialogOpen = false">
      <section class="design-modal compact" data-testid="edit-aircraft-dialog">
        <header>
          <div>
            <span class="eyebrow">DESIGN INFO</span>
            <h2>设计信息</h2>
          </div>
          <button class="modal-close" @click="editDialogOpen = false">×</button>
        </header>

        <label class="form-field">
          <span>名称</span>
          <input v-model.trim="editForm.name" maxlength="120" />
        </label>
        <label class="form-field">
          <span>设计说明</span>
          <textarea v-model.trim="editForm.description" maxlength="1000" rows="4"></textarea>
        </label>

        <div class="edit-meta">
          <span>创建：{{ formatDate(editingItem.created_at) }}</span>
          <span>更新：{{ formatDate(editingItem.updated_at) }}</span>
          <span>实验：{{ editingItem.experiment_count }} 次</span>
        </div>

        <div class="danger-zone">
          <button
            class="delete-button"
            :disabled="store.aircraftLibrary.length <= 1 || editingItem.experiment_count > 0"
            :title="deleteDisabledReason(editingItem)"
            data-testid="delete-aircraft-design"
            @click="deleteDesign(editingItem)"
          >
            删除设计
          </button>
          <small v-if="editingItem.experiment_count > 0">
            已有实验记录，为保证可追溯性不可删除。
          </small>
        </div>

        <footer>
          <button class="secondary-button" @click="editDialogOpen = false">取消</button>
          <button class="primary-button" :disabled="editing" @click="saveMetadata()">
            {{ editing ? '保存中…' : '保存信息' }}
          </button>
        </footer>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import AircraftMiniature from '../components/AircraftMiniature.vue'
import { useAssemblyStore } from '../stores/assembly'
import type { AircraftLibraryItem } from '../types/aircraft'

const store = useAssemblyStore()
const router = useRouter()
const createDialogOpen = ref(false)
const editDialogOpen = ref(false)
const creating = ref(false)
const editing = ref(false)
const notice = ref('')
const editingItem = ref<AircraftLibraryItem | null>(null)

const createForm = reactive({
  templateKey: 'reference-650',
  name: '',
  description: '',
})
const editForm = reactive({
  name: '',
  description: '',
})

const validDesignCount = computed(
  () => store.aircraftLibrary.filter(item => item.validation.passed).length,
)
const totalExperiments = computed(
  () => store.aircraftLibrary.reduce((sum, item) => sum + item.experiment_count, 0),
)

onMounted(async () => {
  await store.initialize()
  if (store.aircraftTemplates.length === 0) {
    await store.refreshTemplates()
  }
  if (store.aircraftLibrary.length === 0) {
    await store.refreshLibrary()
  }
})

function showNotice(message: string): void {
  notice.value = message
  globalThis.setTimeout(() => {
    if (notice.value === message) notice.value = ''
  }, 2600)
}

function openCreateDialog(): void {
  createForm.templateKey = store.aircraftTemplates[0]?.key ?? 'reference-650'
  createForm.name = ''
  createForm.description = ''
  createDialogOpen.value = true
}

async function createDesign(): Promise<void> {
  if (!createForm.templateKey || creating.value) return
  creating.value = true
  try {
    await store.createFromTemplate(
      createForm.templateKey,
      createForm.name || undefined,
      createForm.description,
    )
    createDialogOpen.value = false
    await router.push('/assembly')
  } finally {
    creating.value = false
  }
}

async function openAircraft(aircraftId: number): Promise<void> {
  await store.loadAircraft(aircraftId)
  await router.push('/assembly')
}

async function duplicate(item: AircraftLibraryItem): Promise<void> {
  if (!item.aircraft.id) return
  const copy = await store.duplicateAircraft(item.aircraft.id)
  showNotice(`已复制为「${copy.aircraft.name}」`)
}

function openEditDialog(item: AircraftLibraryItem): void {
  editingItem.value = item
  editForm.name = item.aircraft.name
  editForm.description = item.description
  editDialogOpen.value = true
}

async function saveMetadata(): Promise<void> {
  if (!editingItem.value?.aircraft.id || !editForm.name || editing.value) return
  editing.value = true
  try {
    await store.updateAircraftMetadata(editingItem.value.aircraft.id, {
      name: editForm.name,
      description: editForm.description,
    })
    editDialogOpen.value = false
    showNotice('设计信息已保存')
  } finally {
    editing.value = false
  }
}

async function deleteDesign(item: AircraftLibraryItem): Promise<void> {
  if (!item.aircraft.id) return
  if (item.experiment_count > 0 || store.aircraftLibrary.length <= 1) return
  const confirmed = globalThis.confirm?.(
    `删除「${item.aircraft.name}」？此操作不可撤销。`,
  )
  if (!confirmed) return
  await store.deleteAircraft(item.aircraft.id)
  editDialogOpen.value = false
  editingItem.value = null
  showNotice('飞机设计已删除')
}

function deleteDisabledReason(item: AircraftLibraryItem): string {
  if (store.aircraftLibrary.length <= 1) return '至少保留一架飞机设计'
  if (item.experiment_count > 0) return '已有实验记录，不能删除'
  return ''
}

function metricMass(item: AircraftLibraryItem): string {
  return item.engineering ? `${item.engineering.total_mass_kg.toFixed(2)} kg` : '—'
}

function metricTwr(item: AircraftLibraryItem): string {
  return item.engineering ? item.engineering.thrust_weight_ratio.toFixed(2) : '—'
}

function metricEndurance(item: AircraftLibraryItem): string {
  return item.engineering ? `${item.engineering.estimated_flight_time_min.toFixed(1)} min` : '—'
}

function formatRelative(value: string): string {
  const time = new Date(value).getTime()
  if (!Number.isFinite(time)) return '时间未知'
  const seconds = Math.max(0, Math.round((Date.now() - time) / 1000))
  if (seconds < 60) return '刚刚修改'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes} 分钟前修改`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours} 小时前修改`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days} 天前修改`
  return formatDate(value)
}

function formatDate(value: string): string {
  const date = new Date(value)
  return Number.isNaN(date.getTime())
    ? '未知'
    : date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      })
}

function templateIcon(key: string): string {
  if (key.includes('blank')) return '◇'
  if (key.includes('450')) return '450'
  return '650'
}
</script>

<style scoped>
.aircraft-library-page {
  height: calc(100vh - 56px);
  overflow: auto;
  padding: 28px clamp(22px, 4vw, 64px) 48px;
  background:
    radial-gradient(circle at 18% 0%, rgba(88, 164, 255, .13), transparent 31%),
    linear-gradient(180deg, #f6f9fd 0%, #edf3f9 100%);
}
.library-hero {
  max-width: 1480px;
  margin: 0 auto 18px;
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 24px;
}
.eyebrow {
  color: #3976bc;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: .16em;
}
.library-hero h1 {
  margin: 4px 0 4px;
  color: #172b45;
  font-size: 30px;
  letter-spacing: -.035em;
}
.library-hero p {
  max-width: 720px;
  margin: 0;
  color: #6a7b91;
  font-size: 12px;
  line-height: 1.65;
}
.hero-actions { display: flex; gap: 9px; }
.primary-button,
.secondary-button,
.open-button,
.quiet-button {
  border-radius: 9px;
  padding: 9px 14px;
  font-size: 10px;
  font-weight: 800;
  cursor: pointer;
}
.primary-button {
  border: 1px solid #2563eb;
  background: #2563eb;
  color: #fff;
  box-shadow: 0 8px 18px rgba(37,99,235,.18);
}
.secondary-button,
.quiet-button {
  border: 1px solid #ccd9e9;
  background: #fff;
  color: #36516f;
}
.primary-button:disabled,
.secondary-button:disabled { opacity: .55; cursor: not-allowed; }

.library-summary {
  max-width: 1480px;
  margin: 0 auto 18px;
  min-height: 64px;
  display: flex;
  align-items: stretch;
  overflow: hidden;
  border: 1px solid #dce6f2;
  border-radius: 14px;
  background: rgba(255,255,255,.84);
  box-shadow: 0 8px 24px rgba(22,45,78,.05);
}
.library-summary > div {
  min-width: 140px;
  display: grid;
  align-content: center;
  gap: 2px;
  padding: 10px 18px;
  border-right: 1px solid #e8eef5;
}
.library-summary strong { color: #203b5c; font-size: 17px; }
.library-summary span { color: #7a899d; font-size: 9px; }
.library-summary .autosave-summary {
  margin-left: auto;
  grid-template-columns: auto 1fr;
  align-items: center;
  align-content: center;
  border-right: 0;
}
.autosave-summary i {
  width: 8px; height: 8px; border-radius: 50%; background: #38b779;
}
.autosave-summary i.saving { background: #4f93e8; }
.autosave-summary i.error { background: #e15a50; }

.design-grid {
  max-width: 1480px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  align-items: stretch;
}
.design-card,
.new-design-card {
  min-height: 392px;
  overflow: hidden;
  border: 1px solid #dbe5f1;
  border-radius: 16px;
  background: rgba(255,255,255,.94);
  box-shadow: 0 12px 28px rgba(27,52,86,.06);
  transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease;
}
.design-card:hover {
  transform: translateY(-2px);
  border-color: #b7cce7;
  box-shadow: 0 18px 36px rgba(27,52,86,.09);
}
.design-card.active {
  border-color: #6ca5ee;
  box-shadow: 0 0 0 2px rgba(48,126,229,.08), 0 18px 36px rgba(27,52,86,.09);
}
.design-preview {
  position: relative;
  height: 188px;
  border-bottom: 1px solid #e6edf5;
}
.active-badge,
.validation-badge {
  position: absolute;
  z-index: 4;
  top: 10px;
  padding: 4px 7px;
  border-radius: 999px;
  font-size: 8px;
  font-weight: 800;
  backdrop-filter: blur(8px);
}
.active-badge {
  left: 10px;
  border: 1px solid rgba(74,140,226,.26);
  background: rgba(238,247,255,.90);
  color: #2865ad;
}
.validation-badge {
  right: 10px;
  border: 1px solid rgba(44,157,99,.22);
  background: rgba(239,252,246,.91);
  color: #28764d;
}
.validation-badge.error {
  border-color: rgba(222,125,74,.22);
  background: rgba(255,248,239,.93);
  color: #9d622d;
}
.design-body { padding: 14px; }
.design-heading {
  display: grid;
  grid-template-columns: minmax(0,1fr) auto;
  gap: 8px;
}
.design-heading h2 {
  margin: 0;
  overflow: hidden;
  color: #1c3451;
  font-size: 15px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.design-heading p {
  min-height: 30px;
  margin: 5px 0 0;
  display: -webkit-box;
  overflow: hidden;
  color: #78879a;
  font-size: 9px;
  line-height: 1.55;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
.icon-button,
.modal-close {
  width: 28px; height: 28px; border: 0; border-radius: 7px;
  background: #f2f6fb; color: #64758a; cursor: pointer;
}
.design-metrics {
  display: grid;
  grid-template-columns: repeat(3,1fr);
  gap: 6px;
  margin-top: 13px;
}
.design-metrics div {
  display: grid;
  gap: 3px;
  padding: 8px;
  border: 1px solid #e4ebf3;
  border-radius: 8px;
  background: #f8fafc;
}
.design-metrics span { color: #8592a3; font-size: 8px; }
.design-metrics b { color: #314b69; font-size: 10px; }
.design-meta {
  display: flex;
  gap: 8px;
  margin: 11px 0;
  color: #8a97a7;
  font-size: 8px;
}
.design-meta span + span::before { content: '·'; margin-right: 8px; }
.design-actions { display: grid; grid-template-columns: 1.35fr .9fr; gap: 7px; }
.open-button { border: 1px solid #2f7bd8; background: #eff6ff; color: #245eaa; }
.quiet-button { padding: 8px 10px; }

.new-design-card {
  display: grid;
  place-items: center;
  align-content: center;
  gap: 7px;
  border-style: dashed;
  background: rgba(250,252,255,.62);
  color: #6c7f95;
  cursor: pointer;
}
.new-design-card:hover { border-color: #78a8e8; background: #f5f9ff; }
.new-design-card > span {
  display: grid; place-items: center; width: 48px; height: 48px;
  border: 1px solid #b9cee8; border-radius: 14px;
  background: #fff; color: #3779c7; font-size: 27px;
}
.new-design-card b { color: #35587f; font-size: 13px; }
.new-design-card small { max-width: 220px; text-align: center; font-size: 9px; line-height: 1.55; }

.library-notice {
  position: fixed;
  z-index: 40;
  left: 50%;
  bottom: 24px;
  transform: translateX(-50%);
  padding: 8px 13px;
  border: 1px solid #cbd9e8;
  border-radius: 999px;
  background: rgba(24,45,70,.92);
  color: #f6f9ff;
  font-size: 10px;
  box-shadow: 0 10px 28px rgba(0,0,0,.18);
}
.modal-backdrop {
  position: fixed;
  z-index: 50;
  inset: 56px 0 0;
  display: grid;
  place-items: center;
  padding: 22px;
  background: rgba(12,25,42,.34);
  backdrop-filter: blur(4px);
}
.design-modal {
  width: min(760px, 94vw);
  max-height: calc(100vh - 110px);
  overflow: auto;
  padding: 18px;
  border: 1px solid #d8e3ef;
  border-radius: 16px;
  background: #fff;
  box-shadow: 0 28px 70px rgba(11,29,54,.22);
}
.design-modal.compact { width: min(520px, 94vw); }
.design-modal > header {
  display: flex; justify-content: space-between; align-items: start;
  margin-bottom: 15px;
}
.design-modal h2 { margin: 3px 0 0; color:#203852; font-size:18px; }
.template-grid {
  display: grid;
  grid-template-columns: repeat(3,1fr);
  gap: 9px;
  margin-bottom: 14px;
}
.template-card {
  min-height: 128px;
  display: grid;
  align-content: start;
  gap: 5px;
  padding: 11px;
  border: 1px solid #dfe7f1;
  border-radius: 10px;
  background: #f9fbfd;
  text-align: left;
  cursor: pointer;
}
.template-card.selected {
  border-color: #4d91e6;
  background: #f0f7ff;
  box-shadow: 0 0 0 2px rgba(53,126,222,.08);
}
.template-icon {
  display: grid; place-items: center; width: 34px; height: 34px;
  border-radius: 9px; background:#eaf3ff; color:#3775be;
  font-size: 12px; font-weight: 900;
}
.template-card b { color:#2a4768; font-size:10px; }
.template-card small { color:#75869a; font-size:8px; line-height:1.5; }
.form-field { display:grid; gap:5px; margin-top:11px; }
.form-field > span { color:#556b84; font-size:9px; font-weight:700; }
.form-field input,
.form-field textarea {
  width:100%; border:1px solid #d7e1ed; border-radius:8px;
  background:#fbfcfe; color:#273c54; padding:9px 10px;
  font:inherit; font-size:10px; outline:0;
}
.form-field input:focus,
.form-field textarea:focus { border-color:#75a6e8; box-shadow:0 0 0 2px rgba(48,121,219,.08); }
.design-modal footer {
  display:flex; justify-content:flex-end; gap:8px; margin-top:16px;
}
.edit-meta {
  display:flex; flex-wrap:wrap; gap:8px; margin-top:12px;
  color:#8492a4; font-size:8px;
}
.danger-zone {
  margin-top:15px; padding:11px;
  border:1px solid #f0d6d2; border-radius:9px; background:#fffafa;
}
.delete-button {
  border:1px solid #e1a8a1; border-radius:7px; background:#fff;
  color:#b0443a; padding:7px 10px; font-size:9px; font-weight:800;
}
.delete-button:disabled { opacity:.45; cursor:not-allowed; }
.danger-zone small { margin-left:8px; color:#9a7773; font-size:8px; }

@media(max-width:900px){
  .library-hero{align-items:start;flex-direction:column}
  .library-summary{overflow:auto}
  .template-grid{grid-template-columns:1fr}
}
</style>
