<template>
  <div class="library-page">
    <header class="library-head">
      <div>
        <h2>组件库</h2>
        <p>无人机工程组件数据库 · 3D资产 · 性能数据 · 适配关系</p>
      </div>
      <div class="library-head-actions">
        <input v-model="search" class="library-search" placeholder="搜索名称或组件ID" @input="scheduleLoad" />
        <button class="secondary-action compact-action" :disabled="!selected || busy" @click="cloneSelected">
          复制为新组件
        </button>
      </div>
    </header>

    <div class="library-shell">
      <aside class="library-categories">
        <button
          :class="['category-button', { active: selectedType === null }]"
          @click="setType(null)"
        >
          <span>全部组件</span><b>{{ allCount }}</b>
        </button>
        <button
          v-for="item in categories"
          :key="item.type"
          :class="['category-button', { active: selectedType === item.type }]"
          @click="setType(item.type)"
        >
          <span>{{ item.label }}</span><b>{{ item.count }}</b>
        </button>
        <div class="library-stat">
          <span>当前结果</span>
          <b>{{ components.length }}</b>
        </div>
      </aside>

      <main class="library-browser">
        <div v-if="loading" class="library-empty">正在读取组件库…</div>
        <div v-else-if="error" class="library-empty error">{{ error }}</div>
        <div v-else-if="components.length === 0" class="library-empty">没有匹配的组件。</div>
        <div v-else class="library-card-grid">
          <button
            v-for="component in components"
            :key="component.id"
            :class="['library-card', { selected: selected?.id === component.id, fault: isFault(component) }]"
            :data-component-id="component.id"
            @click="selectComponent(component)"
          >
            <div class="library-card-image">
              <img v-if="thumbnail(component)" :src="thumbnail(component)" :alt="component.name" />
              <span v-else>无缩略图</span>
              <em v-if="isFault(component)">教学故障</em>
            </div>
            <div class="library-card-body">
              <div class="library-card-title">
                <b>{{ component.name }}</b>
                <small>#{{ component.id }}</small>
              </div>
              <span>{{ TYPE_LABELS[component.type] }} · {{ (component.mass_kg * 1000).toFixed(0) }} g</span>
              <div class="library-card-tags">
                <i v-if="component.visual">3D</i>
                <i v-for="tag in component.library.tags.slice(0, 2)" :key="tag">{{ tag }}</i>
              </div>
            </div>
          </button>
        </div>
      </main>

      <aside class="library-detail">
        <template v-if="selected">
          <div class="detail-title">
            <div>
              <small>{{ TYPE_LABELS[selected.type] }} · #{{ selected.id }}</small>
              <h3>{{ selected.name }}</h3>
            </div>
            <button class="text-action" @click="beginEdit">编辑</button>
          </div>

          <div class="detail-tabs">
            <button v-for="tab in tabs" :key="tab.id" :class="{ active: detailTab === tab.id }" @click="detailTab = tab.id">
              {{ tab.label }}
            </button>
          </div>

          <div v-if="editMode" class="component-editor">
            <label>组件名称<input v-model="draft.name" /></label>
            <label>质量 (kg)<input v-model.number="draft.mass_kg" type="number" min="0.001" step="0.001" /></label>
            <label>标签<input v-model="tagsText" placeholder="课程, 自定义" /></label>
            <label>备注<textarea v-model="draft.notes" rows="3"></textarea></label>
            <label>工程参数 JSON<textarea v-model="parametersText" class="json-editor" rows="12"></textarea></label>
            <p v-if="editorError" class="editor-error">{{ editorError }}</p>
            <div class="editor-actions">
              <button class="secondary-action" @click="cancelEdit">取消</button>
              <button class="primary-action compact" :disabled="busy" @click="saveEdit">保存组件</button>
            </div>
          </div>

          <template v-else>
            <section v-if="detailTab === 'basic'" class="detail-section">
              <ComponentPreview :component="selected" />
              <dl class="detail-list">
                <div><dt>名称</dt><dd>{{ selected.name }}</dd></div>
                <div><dt>类型</dt><dd>{{ TYPE_LABELS[selected.type] }}</dd></div>
                <div><dt>质量</dt><dd>{{ selected.mass_kg.toFixed(3) }} kg</dd></div>
                <div><dt>3D资产</dt><dd>{{ selected.visual ? '已配置' : '缺失' }}</dd></div>
              </dl>
              <div v-if="selected.library.tags.length" class="detail-tags">
                <span v-for="tag in selected.library.tags" :key="tag">{{ tag }}</span>
              </div>
              <p class="detail-note">{{ selected.library.notes || '暂无组件备注。' }}</p>
            </section>

            <section v-else-if="detailTab === 'engineering'" class="detail-section">
              <h4>工程参数</h4>
              <dl class="detail-list parameter-list">
                <div v-for="(value, key) in selected.parameters_json" :key="key">
                  <dt>{{ parameterLabel(String(key)) }}</dt>
                  <dd>{{ formatValue(value) }}</dd>
                </div>
              </dl>
            </section>

            <section v-else-if="detailTab === 'performance'" class="detail-section">
              <h4>性能数据</h4>
              <template v-if="motorProfiles.length">
                <div v-for="(profile, index) in motorProfiles" :key="index" class="profile-card">
                  <b>{{ profile.battery_voltage_v }} V · Prop #{{ profile.propeller_id }}</b>
                  <span>{{ profile.source ?? 'Educational Sample Data' }}</span>
                  <table>
                    <thead><tr><th>Throttle</th><th>Thrust</th><th>Current</th><th>Power</th></tr></thead>
                    <tbody>
                      <tr v-for="point in profile.points" :key="point.throttle">
                        <td>{{ Math.round(point.throttle * 100) }}%</td>
                        <td>{{ point.thrust_n }} N</td>
                        <td>{{ point.current_a }} A</td>
                        <td>{{ point.power_w }} W</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </template>
              <div v-else class="detail-placeholder">该组件没有独立性能曲线，工程能力由参数范围描述。</div>
            </section>

            <section v-else-if="detailTab === 'visual'" class="detail-section">
              <ComponentPreview :component="selected" />
              <dl v-if="selected.visual" class="detail-list">
                <div><dt>Asset Key</dt><dd>{{ selected.visual.asset_key }}</dd></div>
                <div><dt>模型文件</dt><dd>{{ selected.visual.file ?? selected.visual.cw_file ?? '-' }}</dd></div>
                <div><dt>CCW模型</dt><dd>{{ selected.visual.ccw_file ?? '-' }}</dd></div>
                <div><dt>缩略图</dt><dd>{{ selected.visual.thumbnail ?? '-' }}</dd></div>
                <div><dt>Scale</dt><dd>{{ selected.visual.scale }}</dd></div>
              </dl>
            </section>

            <section v-else class="detail-section">
              <h4>适配关系</h4>
              <div v-if="selected.compatibility.length === 0" class="detail-placeholder">当前没有额外适配规则。</div>
              <div v-for="group in selected.compatibility" :key="group.label" class="compat-group">
                <div class="compat-title"><b>{{ group.label }}</b><span>{{ group.note }}</span></div>
                <div class="compat-items">
                  <span v-if="group.component_ids.length === 0">暂无匹配组件</span>
                  <button v-for="id in group.component_ids" :key="id" @click="selectById(id)">
                    {{ nameById(id) }}
                  </button>
                </div>
              </div>
            </section>
          </template>
        </template>
        <div v-else class="library-empty">选择一个组件查看详情。</div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import ComponentPreview from '../components/ComponentPreview.vue'
import {
  cloneLibraryComponent,
  fetchLibraryComponents,
  updateLibraryComponent,
} from '../api/componentLibrary'
import type { ComponentType } from '../types/aircraft'
import type { LibraryComponent, LibraryComponentUpdate } from '../types/componentLibrary'
import { UAV_ASSET_BASE } from '../three/assetRegistry'
import { useAssemblyStore } from '../stores/assembly'

const TYPE_LABELS: Record<ComponentType, string> = {
  frame: '机架',
  motor: '电机',
  esc: '电调',
  propeller: '螺旋桨',
  battery: '电池',
  power_module: '电源模块',
  flight_controller: '飞控',
  gnss: 'GNSS / 罗盘',
  payload: '任务载荷',
}

const TYPE_ORDER = Object.keys(TYPE_LABELS) as ComponentType[]
const tabs = [
  { id: 'basic', label: '基本信息' },
  { id: 'engineering', label: '工程参数' },
  { id: 'performance', label: '性能数据' },
  { id: 'visual', label: '3D资产' },
  { id: 'compatibility', label: '适配关系' },
] as const

type DetailTab = typeof tabs[number]['id']
const assemblyStore = useAssemblyStore()
const components = ref<LibraryComponent[]>([])
const allComponents = ref<LibraryComponent[]>([])
const selected = ref<LibraryComponent | null>(null)
const selectedType = ref<ComponentType | null>(null)
const search = ref('')
const loading = ref(false)
const busy = ref(false)
const error = ref('')
const detailTab = ref<DetailTab>('basic')
const editMode = ref(false)
const editorError = ref('')
let searchTimer: number | null = null

const draft = reactive<LibraryComponentUpdate>({
  name: '', mass_kg: 0.1, parameters_json: {}, notes: '', tags: [],
})
const parametersText = ref('{}')
const tagsText = ref('')

const allCount = computed(() => allComponents.value.length)
const categories = computed(() => TYPE_ORDER.map(type => ({
  type,
  label: TYPE_LABELS[type],
  count: allComponents.value.filter(item => item.type === type).length,
})))
const motorProfiles = computed(() => {
  const raw = selected.value?.parameters_json.profiles
  return Array.isArray(raw) ? raw as Array<any> : []
})

onMounted(async () => {
  await Promise.all([loadAllCounts(), loadComponents()])
})

async function loadAllCounts(): Promise<void> {
  try { allComponents.value = await fetchLibraryComponents() } catch { allComponents.value = [] }
}

async function loadComponents(preserveSelection = true): Promise<void> {
  loading.value = true
  error.value = ''
  const previousId = preserveSelection ? selected.value?.id : null
  try {
    components.value = await fetchLibraryComponents(selectedType.value, search.value)
    if (previousId) selected.value = components.value.find(item => item.id === previousId) ?? null
    if (!selected.value && components.value.length) selected.value = components.value[0]
  } catch {
    error.value = '无法读取组件库，请确认后端已启动。'
  } finally {
    loading.value = false
  }
}

function scheduleLoad(): void {
  if (searchTimer !== null) window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(() => { void loadComponents(false) }, 220)
}

function setType(type: ComponentType | null): void {
  selectedType.value = type
  selected.value = null
  editMode.value = false
  void loadComponents(false)
}

function selectComponent(component: LibraryComponent): void {
  selected.value = component
  detailTab.value = 'basic'
  editMode.value = false
}

function thumbnail(component: LibraryComponent): string {
  return component.visual?.thumbnail ? `${UAV_ASSET_BASE}${component.visual.thumbnail}` : ''
}

function isFault(component: LibraryComponent): boolean {
  return component.name.startsWith('故障示例') || component.library.tags.includes('教学故障')
}

function parameterLabel(key: string): string {
  const labels: Record<string, string> = {
    motor_diagonal_m: '电机对角轴距', kv: 'KV', profiles: '性能曲线',
    max_current_a: '最大电流', voltage_min_v: '最低电压', voltage_max_v: '最高电压',
    diameter_in: '桨径', pitch_in: '桨距', direction: '旋向配置',
    cell_count: '电芯数', capacity_mah: '容量', nominal_voltage_v: '标称电压',
    max_continuous_current_a: '最大持续电流', usable_capacity_ratio: '可用容量比例',
    mount: '安装槽位', mount_points: '标准安装点',
  }
  return labels[key] ?? key
}

function formatValue(value: unknown): string {
  if (Array.isArray(value)) return `${value.length} 组`
  if (value && typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

function beginEdit(): void {
  if (!selected.value) return
  draft.name = selected.value.name
  draft.mass_kg = selected.value.mass_kg
  draft.parameters_json = JSON.parse(JSON.stringify(selected.value.parameters_json))
  draft.notes = selected.value.library.notes
  draft.tags = [...selected.value.library.tags]
  parametersText.value = JSON.stringify(draft.parameters_json, null, 2)
  tagsText.value = draft.tags.join(', ')
  editorError.value = ''
  editMode.value = true
}

function cancelEdit(): void { editMode.value = false; editorError.value = '' }

async function saveEdit(): Promise<void> {
  if (!selected.value) return
  editorError.value = ''
  let parameters: Record<string, unknown>
  try {
    const parsed = JSON.parse(parametersText.value)
    if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new Error('工程参数必须是 JSON 对象')
    parameters = parsed as Record<string, unknown>
  } catch (caught) {
    editorError.value = caught instanceof Error ? caught.message : 'JSON格式错误'
    return
  }
  busy.value = true
  try {
    const updated = await updateLibraryComponent(selected.value.id, {
      name: draft.name,
      mass_kg: draft.mass_kg,
      parameters_json: parameters,
      notes: draft.notes,
      tags: tagsText.value.split(',').map(item => item.trim()).filter(Boolean),
    })
    selected.value = updated
    editMode.value = false
    await Promise.all([loadAllCounts(), loadComponents(true), assemblyStore.refreshComponents()])
  } catch (caught: any) {
    editorError.value = caught?.response?.data?.detail ?? '组件保存失败。'
  } finally {
    busy.value = false
  }
}

async function cloneSelected(): Promise<void> {
  if (!selected.value) return
  const name = window.prompt('新组件名称', `${selected.value.name}-Copy`)?.trim()
  if (!name) return
  busy.value = true
  try {
    const created = await cloneLibraryComponent(selected.value.id, name)
    selectedType.value = created.type
    search.value = ''
    await Promise.all([loadAllCounts(), loadComponents(false), assemblyStore.refreshComponents()])
    selected.value = components.value.find(item => item.id === created.id) ?? created
  } finally {
    busy.value = false
  }
}

function nameById(id: number): string {
  return allComponents.value.find(item => item.id === id)?.name ?? `#${id}`
}

function selectById(id: number): void {
  const item = allComponents.value.find(component => component.id === id)
  if (!item) return
  selectedType.value = item.type
  search.value = ''
  void loadComponents(false).then(() => {
    selected.value = components.value.find(component => component.id === id) ?? item
  })
}
</script>

<style scoped>
.library-page { height: 100%; display:grid; grid-template-rows:72px minmax(0,1fr); padding:12px; gap:12px; overflow:hidden; }
.library-head { display:flex; align-items:center; justify-content:space-between; gap:16px; padding:0 4px; }
.library-head h2 { margin:0; color:#17283f; font-size:20px; }.library-head p { margin:4px 0 0; color:#708096; font-size:11px; }
.library-head-actions { display:flex; align-items:center; gap:8px; }.library-search { width:260px; border:1px solid #d8e2ee; border-radius:7px; background:#fff; padding:9px 10px; font-size:11px; outline:none; }.library-search:focus{border-color:#75a5eb;box-shadow:0 0 0 2px rgba(37,99,235,.07)}
.compact-action { width:auto; margin:0; padding:9px 12px; white-space:nowrap; }
.library-shell { min-height:0; display:grid; grid-template-columns:176px minmax(0,1fr) 380px; gap:12px; }
.library-categories,.library-browser,.library-detail { min-width:0; min-height:0; border:1px solid #dfe7f1; border-radius:8px; background:#fff; box-shadow:0 6px 18px rgba(20,40,70,.04); }
.library-categories { padding:10px; overflow:auto; }.category-button { width:100%; display:grid; grid-template-columns:1fr auto; align-items:center; gap:8px; margin-bottom:5px; padding:9px 10px; border:1px solid transparent; border-radius:6px; background:transparent; color:#526379; text-align:left; font-size:11px; }.category-button b{font-size:10px;color:#8794a6}.category-button:hover{background:#f6f9fd}.category-button.active{background:#eef5ff;border-color:#d8e8ff;color:#1f5da8;font-weight:700}.library-stat{margin-top:10px;padding:10px;border-top:1px solid #edf1f5;display:flex;justify-content:space-between;color:#78869a;font-size:10px}.library-stat b{color:#31445d}
.library-browser { padding:10px; overflow:auto; }.library-card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:10px}.library-card{min-width:0;overflow:hidden;border:1px solid #dfe6ef;border-radius:8px;background:#fff;padding:0;text-align:left;transition:border-color .15s ease,box-shadow .15s ease,transform .15s ease}.library-card:hover{border-color:#9ec2f7;box-shadow:0 5px 16px rgba(28,67,112,.08);transform:translateY(-1px)}.library-card.selected{border-color:#3b82f6;box-shadow:0 0 0 2px rgba(37,99,235,.08)}.library-card.fault{border-color:#efcfca}.library-card-image{position:relative;height:122px;display:grid;place-items:center;background:linear-gradient(180deg,#f7faff,#edf3f9);overflow:hidden}.library-card-image img{display:block;width:auto;height:auto;max-width:92%;max-height:92%;object-fit:contain;object-position:center}.library-card-image>span{color:#8a96a6;font-size:10px}.library-card-image em{position:absolute;left:7px;top:7px;padding:3px 6px;border-radius:9px;background:#fff1f0;color:#b42318;font-style:normal;font-size:9px;font-weight:700}.library-card-body{padding:9px}.library-card-title{display:flex;align-items:start;justify-content:space-between;gap:6px}.library-card-title b{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#22344c;font-size:11px}.library-card-title small{color:#8a96a7;font-size:9px}.library-card-body>span{display:block;margin-top:5px;color:#6c7a8f;font-size:9px}.library-card-tags{display:flex;gap:4px;flex-wrap:wrap;margin-top:7px}.library-card-tags i{padding:2px 5px;border-radius:4px;background:#f0f5fb;color:#5d6e84;font-style:normal;font-size:8px}
.library-detail{overflow:auto;padding:12px}.detail-title{display:flex;align-items:start;justify-content:space-between;gap:10px}.detail-title small{color:#8491a2;font-size:9px}.detail-title h3{margin:3px 0 0;color:#1d3049;font-size:15px}.text-action{border:1px solid #d6e1ee;border-radius:6px;background:#fff;color:#2563eb;padding:6px 9px;font-size:10px}.detail-tabs{display:flex;gap:2px;margin:12px 0;border-bottom:1px solid #e8edf4;overflow-x:auto}.detail-tabs button{flex:0 0 auto;border:0;border-bottom:2px solid transparent;background:transparent;padding:8px 7px;color:#6b7b8f;font-size:9px}.detail-tabs button.active{border-bottom-color:#2563eb;color:#1f5da8;font-weight:700}.detail-section h4{margin:2px 0 10px;color:#31445d;font-size:12px}.detail-list{margin:10px 0}.detail-list>div{display:grid;grid-template-columns:105px minmax(0,1fr);gap:10px;padding:7px 0;border-bottom:1px solid #eef2f6;font-size:10px}.detail-list dt{color:#718095}.detail-list dd{margin:0;color:#293b53;text-align:right;overflow-wrap:anywhere;font-weight:600}.parameter-list dd{max-width:220px}.detail-tags{display:flex;gap:5px;flex-wrap:wrap;margin:9px 0}.detail-tags span{padding:3px 6px;border-radius:5px;background:#eef5ff;color:#2c66b0;font-size:9px}.detail-note{padding:9px;border-radius:6px;background:#f8fafc;color:#68778d;font-size:10px;line-height:1.5}.profile-card{margin-bottom:10px;padding:9px;border:1px solid #e1e8f0;border-radius:7px}.profile-card>b{display:block;color:#2a3c54;font-size:10px}.profile-card>span{display:block;margin:3px 0 7px;color:#7a889a;font-size:8px}.profile-card table{width:100%;border-collapse:collapse;font-size:8px}.profile-card th,.profile-card td{padding:4px;border-bottom:1px solid #edf1f5;text-align:right}.profile-card th:first-child,.profile-card td:first-child{text-align:left}.detail-placeholder{padding:20px;border:1px dashed #d9e2ed;border-radius:7px;text-align:center;color:#8190a2;font-size:10px}.compat-group{margin-bottom:10px;padding:9px;border:1px solid #e2e8f0;border-radius:7px}.compat-title{display:flex;justify-content:space-between;gap:8px}.compat-title b{color:#2d4059;font-size:10px}.compat-title span{color:#8a96a6;font-size:8px;text-align:right}.compat-items{display:flex;gap:5px;flex-wrap:wrap;margin-top:8px}.compat-items button,.compat-items span{border:1px solid #dbe5f0;border-radius:5px;background:#f8fbff;color:#4e6481;padding:4px 6px;font-size:8px}.library-empty{height:100%;display:grid;place-items:center;padding:30px;color:#7b899a;font-size:11px}.library-empty.error{color:#b42318}
.component-editor{display:grid;gap:9px}.component-editor label{display:grid;gap:4px;color:#5b6c82;font-size:9px}.component-editor input,.component-editor textarea{width:100%;border:1px solid #d8e2ed;border-radius:6px;padding:7px 8px;background:#fff;color:#26384f;font:inherit;outline:none}.component-editor textarea{resize:vertical;line-height:1.45}.component-editor .json-editor{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:9px}.editor-error{margin:0;padding:7px;border-radius:5px;background:#fff1f0;color:#b42318;font-size:9px}.editor-actions{display:grid;grid-template-columns:1fr 1fr;gap:7px}.editor-actions button{margin:0}
@media (max-width:1280px){.library-shell{grid-template-columns:150px minmax(0,1fr) 320px}.library-card-grid{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}.library-search{width:210px}}
</style>
