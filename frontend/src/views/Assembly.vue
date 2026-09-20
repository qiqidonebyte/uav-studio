<template>
  <div class="workbench-grid assembly-grid">
    <aside class="panel left-panel">
      <section class="panel-section">
        <h3>装配流程</h3>
        <button
          v-for="(step, index) in ASSEMBLY_STEPS"
          :key="step.id"
          :class="['assembly-step', { active: index === activeStepIndex }]"
          @click="activateStep(index)"
        >
          <span class="step-index">{{ index + 1 }}</span>
          <span>
            <b>{{ step.title }}</b>
            <small>{{ step.detail }}</small>
          </span>
          <em :class="stepStatus(step)">
            {{ stateText[stepStatus(step)] }}
          </em>
        </button>
      </section>

      <section class="panel-section component-picker">
        <h3>{{ activeStep.title }} · 组件选择</h3>
        <p class="step-description">{{ activeStep.detail }}</p>

        <template v-if="activeStep.id === 'check'">
          <div class="check-summary" :class="store.validation.passed ? 'passed' : 'failed'">
            <b>{{ store.validation.passed ? '装配检查通过' : '装配检查未通过' }}</b>
            <span>
              {{ store.validation.blocking_errors.length }} 个阻断错误 ·
              {{ store.validation.warnings.length }} 个警告
            </span>
          </div>
          <button
            class="primary-action"
            :disabled="store.saving"
            @click="store.refreshCalculation()"
          >
            {{ store.saving ? '正在检查…' : '运行装配检查' }}
          </button>
        </template>

        <template v-else>
          <div
            v-for="slot in activeStep.slots"
            :key="slot"
            class="slot-picker component-card-slot"
            :class="{ selected: store.selectedSlot === slot }"
            @click="store.selectSlot(slot)"
          >
            <div class="slot-picker-head">
              <div>
                <b>{{ SLOT_LABELS[slot] }}</b>
                <small v-if="slot !== 'frame'" class="mount-completion">
                  {{ completionText(slot) }}
                </small>
              </div>
              <span :class="store.componentForSlot(slot) ? 'installed' : 'empty'">
                {{ store.componentForSlot(slot)?.name ?? '未选择' }}
              </span>
            </div>

            <div
              v-if="store.pendingInstall?.slot === slot"
              class="assembly-session-card"
              data-testid="assembly-session-card"
            >
              <span class="session-dot"></span>
              <div>
                <b>正在进行 3D 装配</b>
                <small>
                  {{ pendingComponentName }} ·
                  {{ completionText(slot) }}
                </small>
              </div>
              <button type="button" @click.stop="store.cancelMountAssembly()">取消</button>
            </div>

            <div class="component-card-list">
              <ComponentCard
                v-for="component in availableComponents(slot)"
                :key="component.id"
                :component="component"
                :installed="installedId(slot) === component.id && isSlotPhysicallyComplete(slot)"
                :selected="candidateFor(slot) === component.id"
                :disabled="store.saving"
                :specs="componentSpecs(component)"
                :action-label="cardActionLabel(slot)"
                :secondary-action-label="slot === 'frame' ? '' : '3D装配'"
                @choose="chooseCandidate(slot, component.id)"
                @install="install(slot, component.id)"
                @secondary="begin3dAssembly(slot, component.id)"
              />
            </div>

            <div v-if="availableComponents(slot).length === 0" class="component-list-empty">
              当前组件库没有可用于 {{ SLOT_LABELS[slot] }} 的组件。
            </div>

            <button
              v-if="isOptionalSlot(slot) && store.componentForSlot(slot)"
              class="ghost-action component-remove-action"
              :disabled="store.saving"
              @click.stop="remove(slot)"
            >
              移除当前{{ SLOT_LABELS[slot] }}
            </button>
          </div>
        </template>

        <p v-if="store.error" class="inline-error">{{ store.error }}</p>
      </section>
    </aside>

    <main class="stage-panel assembly-stage">
      <div class="stage-titlebar">
        <div>
          <b>{{ store.aircraftName }}</b>
          <span>
            {{
              store.pendingInstall
                ? `受约束 3D 装配 · ${SLOT_LABELS[store.pendingInstall.slot]}`
                : '四旋翼 X 型数字样机'
            }}
          </span>
        </div>
        <div class="stage-title-actions">
          <span :class="['assembly-save-state', store.saveStatus]">
            <i></i>{{ store.saveStatusZh }}
          </span>
          <RouterLink class="stage-library-link" to="/aircraft">我的飞机</RouterLink>
          <button
            class="stage-copy-button"
            :disabled="store.saving || !store.canCreateAircraft"
            :title="store.canCreateAircraft ? '复制当前飞机为独立设计' : `已达到 ${store.aircraftLimit} 架上限`"
            @click="saveAsCopy()"
          >
            另存为副本
          </button>
          <div class="stage-live-state">
            <span
              :class="store.pendingInstall ? 'assembly-dot' : (store.validation.passed ? 'ok-dot' : 'pending-dot')"
            ></span>
            {{
              store.pendingInstall
                ? '选择蓝色 Mount Anchor'
                : (store.validation.passed ? '装配有效' : '装配未完成')
            }}
          </div>
        </div>
      </div>
      <DroneScene
        :aircraft="store.aircraft"
        :components="store.components"
        :selected-slot="store.selectedSlot"
        :selected-mount-id="store.selectedMountId"
        :pending-install="store.pendingInstall"
        :install-animation="store.lastInstallation"
        :remove-animation="store.lastRemoval"
        :engineering="store.engineering"
        :issue-slots="issueSlots"
        :issue-mounts="issueMounts"
        :issue-mount-ids="issueMountIds"
        interactive
        @select-slot="selectSceneSlot"
        @select-mount="selectSceneMount"
        @install-at-mount="installAtMount"
        @spatial-diagnostics="updateSpatialDiagnostics"
      />
      <div v-if="store.loading" class="stage-loading">正在读取组件库与飞机装配数据…</div>
      <div v-else-if="!store.aircraft && store.error" class="stage-loading error">
        {{ store.error }}
      </div>
    </main>

    <aside class="panel inspector-panel">
      <section class="inspector-section">
        <div class="inspector-heading">
          <div>
            <h3>装配检查器</h3>
            <p>
              {{
                selectedMount
                  ? selectedMount.label
                  : (store.selectedSlot ? SLOT_LABELS[store.selectedSlot] : '尚未选择部件')
              }}
            </p>
          </div>
          <span
            v-if="selectedMount"
            :class="['component-state', { pending: !selectedMountInstalled }]"
          >
            {{ selectedMountInstalled ? '已安装' : '待安装' }}
          </span>
          <span v-else-if="selectedComponent" class="component-state">已配置</span>
        </div>

        <div v-if="selectedMount" class="mount-inspector" data-testid="mount-inspector">
          <div class="mount-id-row">
            <span>Mount Anchor</span>
            <code>{{ selectedMount.id }}</code>
          </div>
          <div class="mount-position">
            <span>X {{ formatMillimeters(selectedMount.position.x) }}</span>
            <span>Y {{ formatMillimeters(selectedMount.position.y) }}</span>
            <span>Z {{ formatMillimeters(selectedMount.position.z) }}</span>
          </div>
        </div>

        <dl v-if="selectedComponent" class="component-properties">
          <div><dt>名称</dt><dd>{{ selectedComponent.name }}</dd></div>
          <div><dt>类别</dt><dd>{{ componentTypeLabel(selectedComponent.type) }}</dd></div>
          <div><dt>质量</dt><dd>{{ selectedComponent.mass_kg.toFixed(3) }} kg</dd></div>
          <div v-if="selectedComponent.visual">
            <dt>3D 资产</dt>
            <dd>{{ selectedComponent.visual.asset_key }}</dd>
          </div>
          <div
            v-for="parameter in displayParameters(selectedComponent)"
            :key="parameter.label"
          >
            <dt>{{ parameter.label }}</dt>
            <dd>{{ parameter.value }}</dd>
          </div>
        </dl>

        <div v-else-if="selectedMount" class="empty-inspector">
          <b>该安装位当前为空</b>
          <span>从左侧选择组件并进入 3D 装配，Ghost 会吸附到此安装点。</span>
        </div>
        <div v-else class="empty-inspector">
          <b>点击 3D 部件</b>
          <span>现在可以定位到具体 M1–M4 或单组件 Mount Anchor。</span>
        </div>

        <button
          v-if="selectedMount && selectedMountInstalled && selectedMount.slot !== 'frame'"
          class="mount-remove-button"
          :disabled="store.saving || Boolean(store.removingMountId)"
          data-testid="remove-selected-mount"
          @click="store.removeMount(selectedMount.id)"
        >
          {{ store.removingMountId === selectedMount.id ? '拆卸动画…' : '拆卸此安装位' }}
        </button>
      </section>

      <section class="inspector-section">
        <div class="inspector-heading">
          <div>
            <h3>空间工程检查</h3>
            <p>基于 Mount / Rotor Disc / GLB Envelope</p>
          </div>
          <span :class="['check-badge', spatialHasError ? 'error' : 'ok']">
            {{ spatialHasError ? '干涉' : '正常' }}
          </span>
        </div>
        <div v-if="spatialDiagnostics.length === 0" class="spatial-ok">
          <b>未发现空间干涉</b>
          <span>旋翼盘与当前教学安装包络正常。</span>
        </div>
        <button
          v-for="diagnostic in spatialDiagnostics"
          :key="diagnostic.code"
          :class="['validation-item', diagnostic.severity, 'diagnostic-button']"
          @click="focusSpatialDiagnostic(diagnostic)"
        >
          <b>{{ diagnostic.severity === 'error' ? '空间错误' : '空间提醒' }}</b>
          <span>{{ diagnostic.message }}</span>
        </button>
      </section>

      <section class="inspector-section">
        <h3>整机工程参数</h3>
        <dl v-if="store.engineering" class="engineering-values">
          <div><dt>总质量</dt><dd>{{ store.engineering.total_mass_kg.toFixed(3) }} kg</dd></div>
          <div><dt>最大总推力</dt><dd>{{ store.engineering.max_total_thrust_n.toFixed(1) }} N</dd></div>
          <div><dt>推重比</dt><dd>{{ store.engineering.thrust_weight_ratio.toFixed(2) }}</dd></div>
          <div><dt>悬停油门</dt><dd>{{ (store.engineering.hover_throttle * 100).toFixed(1) }} %</dd></div>
          <div><dt>最大电流</dt><dd>{{ store.engineering.max_current_a.toFixed(1) }} A</dd></div>
          <div><dt>最大功率</dt><dd>{{ formatPower(store.engineering.max_power_w) }}</dd></div>
          <div><dt>预计续航</dt><dd>{{ store.engineering.estimated_flight_time_min.toFixed(1) }} min</dd></div>
        </dl>
        <div v-else class="empty-inspector compact">
          <span>安装全部必需组件后显示后端工程计算结果。</span>
        </div>
      </section>

      <section class="inspector-section">
        <h3>重心位置</h3>
        <dl v-if="store.engineering">
          <div><dt>X</dt><dd>{{ formatMillimeters(store.engineering.center_of_gravity_m.x) }}</dd></div>
          <div><dt>Y</dt><dd>{{ formatMillimeters(store.engineering.center_of_gravity_m.y) }}</dd></div>
          <div><dt>Z</dt><dd>{{ formatMillimeters(store.engineering.center_of_gravity_m.z) }}</dd></div>
        </dl>
        <div v-else class="empty-inspector compact"><span>等待工程计算。</span></div>
      </section>

      <section class="inspector-section">
        <div class="inspector-heading">
          <div>
            <h3>装配检查</h3>
            <p>工程 + 物理 Mount 双重验证</p>
          </div>
          <span :class="['check-badge', store.validation.passed ? 'ok' : 'error']">
            {{ store.validation.passed ? '通过' : '阻断' }}
          </span>
        </div>

        <button
          v-for="issue in store.validation.blocking_errors"
          :key="issue.code"
          class="validation-item error diagnostic-button"
          @click="focusIssue(issue)"
        >
          <b>阻断错误</b>
          <span>{{ issue.message }}</span>
        </button>
        <button
          v-for="issue in store.validation.warnings"
          :key="issue.code"
          class="validation-item warning diagnostic-button"
          @click="focusIssue(issue)"
        >
          <b>警告</b>
          <span>{{ issue.message }}</span>
        </button>
        <p v-if="store.validation.passed && store.validation.warnings.length === 0" class="check-ok">
          工程参数、必需 Mount 和空间检查均已通过。
        </p>

        <RouterLink
          v-if="store.validation.passed"
          class="launch-link"
          to="/flight"
        >
          进入飞行实验
        </RouterLink>
        <span v-else class="launch-link disabled">装配检查通过后可进入飞行实验</span>
      </section>
    </aside>

    <section class="bottom-panel assembly-bottom">
      <div class="assembly-hint">
        <b>Digital Assembly 2.0：</b>
        组件选择 → 3D 装配 → Mount Anchor → Ghost Snap → 安装动画 → 空间检查 → 工程验证。
      </div>
      <div class="assembly-progress">
        <span>已完成 {{ completedStepCount }} / {{ ASSEMBLY_STEPS.length }} 步</span>
        <div class="progress-track">
          <i :style="{ width: `${(completedStepCount / ASSEMBLY_STEPS.length) * 100}%` }"></i>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import ComponentCard from '../components/ComponentCard.vue'
import DroneScene from '../components/DroneScene.vue'
import { useAssemblyStore } from '../stores/assembly'
import type {
  AssemblyIssue,
  Component,
  ComponentType,
  MotorName,
} from '../types/aircraft'
import type {
  MountPoint,
  SpatialDiagnostic,
} from '../three/assemblySemantics'
import {
  ASSEMBLY_STEPS,
  getStepStatus,
  installedComponentId,
  SLOT_LABELS,
  slotComponents,
  type AssemblySlot,
  type AssemblyStep,
} from '../utils/assembly'

const store = useAssemblyStore()
const activeStepIndex = ref(0)
const candidateSelections = reactive<Partial<Record<AssemblySlot, number>>>({})
const spatialDiagnostics = ref<SpatialDiagnostic[]>([])
const stateText = {
  done: '已配置',
  warning: '警告',
  error: '错误',
  pending: '未配置',
} as const

const activeStep = computed(() => ASSEMBLY_STEPS[activeStepIndex.value])
const selectedMount = computed<MountPoint | null>(() =>
  store.selectedMountId
    ? store.mountPoints.find(item => item.id === store.selectedMountId) ?? null
    : null,
)
const selectedMountComponent = computed(() =>
  store.selectedMountId ? store.componentForMount(store.selectedMountId) : null,
)
const selectedComponent = computed(() =>
  selectedMount.value
    ? selectedMountComponent.value
    : (store.selectedSlot ? store.componentForSlot(store.selectedSlot) : null),
)
const selectedMountInstalled = computed(() => Boolean(selectedMountComponent.value))
const pendingComponentName = computed(() => {
  const pending = store.pendingInstall
  if (!pending) return ''
  return store.components.find(item => item.id === pending.componentId)?.name ?? `#${pending.componentId}`
})
const completedStepCount = computed(() =>
  ASSEMBLY_STEPS.filter(step => {
    const status = stepStatus(step)
    return status === 'done' || status === 'warning'
  }).length,
)
const allIssues = computed(() => [
  ...store.validation.blocking_errors,
  ...store.validation.warnings,
])
const issueSlots = computed<AssemblySlot[]>(() =>
  [...new Set(
    allIssues.value.flatMap(issue => issue.affected_slots ?? []),
  )] as AssemblySlot[],
)
const issueMounts = computed<MotorName[]>(() =>
  [...new Set(
    allIssues.value.flatMap(issue => issue.affected_mounts ?? []),
  )] as MotorName[],
)
const issueMountIds = computed(() =>
  [...new Set(
    allIssues.value.flatMap(issue => issue.affected_mount_ids ?? []),
  )],
)
const spatialHasError = computed(
  () => spatialDiagnostics.value.some(item => item.severity === 'error'),
)

const parameterLabels: Record<string, string> = {
  motor_diagonal_m: '电机对角轴距',
  battery_position_m: '电池安装位置',
  power_module_position_m: '电源模块位置',
  flight_controller_position_m: '飞控安装位置',
  gnss_mount_position_m: 'GNSS 安装位置',
  mount_points: '标准安装点',
  kv: 'KV 值',
  profiles: '教学性能曲线',
  max_current_a: '最大电流',
  voltage_min_v: '最低电压',
  voltage_max_v: '最高电压',
  diameter_in: '桨径',
  pitch_in: '桨距',
  direction: '旋向配置',
  cell_count: '电芯数',
  capacity_mah: '电池容量',
  nominal_voltage_v: '标称电压',
  max_continuous_current_a: '最大持续电流',
  usable_capacity_ratio: '可用容量比例',
  mount: '安装槽位',
}

const typeLabels: Record<ComponentType, string> = {
  frame: '机架',
  motor: '电机',
  esc: '电调',
  propeller: '螺旋桨',
  battery: '电池',
  power_module: '电源模块',
  flight_controller: '飞控',
  gnss: 'GNSS/罗盘',
  payload: '任务载荷',
}

onMounted(async () => {
  await store.initialize()
  if (!store.selectedSlot && store.aircraft?.frame_id) {
    store.selectSlot('frame')
  }
})

function activateStep(index: number): void {
  activeStepIndex.value = index
  const firstSlot = ASSEMBLY_STEPS[index]?.slots[0]
  if (firstSlot) {
    store.selectSlot(firstSlot)
    store.selectMount(null)
  }
}

function stepStatus(step: AssemblyStep) {
  if (!store.aircraft) return 'pending' as const
  return getStepStatus(step, store.aircraft, store.validation)
}

function availableComponents(slot: AssemblySlot): Component[] {
  return slotComponents(store.components, slot)
}

function installedId(slot: AssemblySlot): number | null {
  return store.aircraft ? installedComponentId(store.aircraft, slot) : null
}

function candidateFor(slot: AssemblySlot): number | null {
  return candidateSelections[slot] ?? installedId(slot)
}

function chooseCandidate(slot: AssemblySlot, componentId: number): void {
  candidateSelections[slot] = componentId
  store.selectSlot(slot)
  store.selectMount(null)
}

async function install(slot: AssemblySlot, componentId: number): Promise<void> {
  chooseCandidate(slot, componentId)
  await store.installComponent(slot, componentId)
  candidateSelections[slot] = componentId
}

async function begin3dAssembly(slot: AssemblySlot, componentId: number): Promise<void> {
  chooseCandidate(slot, componentId)
  await store.beginMountAssembly(slot, componentId)
  candidateSelections[slot] = componentId
}

async function installAtMount(mountId: string): Promise<void> {
  await store.installAtMount(mountId)
}
function updateSpatialDiagnostics(diagnostics: SpatialDiagnostic[]): void {
  spatialDiagnostics.value = diagnostics
}


async function remove(slot: AssemblySlot): Promise<void> {
  await store.removeComponent(slot)
  delete candidateSelections[slot]
}

function isOptionalSlot(slot: AssemblySlot): boolean {
  return slot === 'gnss' || slot === 'payload'
}

function isSlotPhysicallyComplete(slot: AssemblySlot): boolean {
  const completion = store.completionForSlot(slot)
  return completion.installed >= completion.total
}

function completionText(slot: AssemblySlot): string {
  const completion = store.completionForSlot(slot)
  return `${completion.installed} / ${completion.total} Mount`
}

function cardActionLabel(slot: AssemblySlot): string {
  if (store.componentForSlot(slot)) return '快速更换'
  if (slot === 'motor' || slot === 'esc' || slot === 'propeller') return '快速配置 ×4'
  return '快速配置'
}

function selectSceneSlot(slot: AssemblySlot): void {
  store.selectSlot(slot)
  const stepIndex = ASSEMBLY_STEPS.findIndex(step => step.slots.includes(slot))
  if (stepIndex >= 0) activeStepIndex.value = stepIndex
}

function selectSceneMount(mountId: string, slot: AssemblySlot): void {
  store.selectMount(mountId)
  selectSceneSlot(slot)
}

function focusIssue(issue: AssemblyIssue): void {
  const mountId = issue.affected_mount_ids?.[0]
  if (mountId) {
    store.selectMount(mountId)
    const slot = mountId.split(':', 1)[0] as AssemblySlot
    selectSceneSlot(slot)
    return
  }
  const slot = issue.affected_slots?.[0] as AssemblySlot | undefined
  if (slot) selectSceneSlot(slot)
}

function focusSpatialDiagnostic(diagnostic: SpatialDiagnostic): void {
  const mountId = diagnostic.mountIds[0]
  if (mountId) {
    store.selectMount(mountId)
    const slot = mountId.split(':', 1)[0] as AssemblySlot
    selectSceneSlot(slot)
    return
  }
  const slot = diagnostic.slots[0] as AssemblySlot | undefined
  if (slot) selectSceneSlot(slot)
}

async function saveAsCopy(): Promise<void> {
  if (!store.aircraft) return
  if (!store.canCreateAircraft) {
    globalThis.alert?.(`每个账号最多保存 ${store.aircraftLimit} 架飞机。`)
    return
  }
  const suggested = `${store.aircraft.name} - 副本`
  const name = globalThis.prompt?.('另存为新的飞机设计', suggested)
  if (name === null) return
  try {
    await store.duplicateActive(name?.trim() || suggested)
  } catch (error) {
    globalThis.alert?.(error instanceof Error ? error.message : '另存为失败')
  }
}

function componentTypeLabel(type: ComponentType): string {
  return typeLabels[type]
}

function numberParameter(component: Component, key: string): number | null {
  const value = component.parameters_json[key]
  return typeof value === 'number' ? value : null
}

function componentSpecs(component: Component): string[] {
  const p = component.parameters_json
  switch (component.type) {
    case 'frame': {
      const diagonal = numberParameter(component, 'motor_diagonal_m')
      return [
        diagonal ? `轴距 ${(diagonal * 1000).toFixed(0)} mm` : '轴距未定义',
        `质量 ${(component.mass_kg * 1000).toFixed(0)} g`,
      ]
    }
    case 'motor': {
      const profiles = Array.isArray(p.profiles) ? p.profiles.length : 0
      return [`${numberParameter(component, 'kv')?.toFixed(0) ?? '?'} KV`, `${profiles} 组性能曲线`]
    }
    case 'esc':
      return [`${numberParameter(component, 'max_current_a')?.toFixed(0) ?? '?'} A`, `${numberParameter(component, 'voltage_max_v')?.toFixed(0) ?? '?'} V max`]
    case 'propeller':
      return [`${numberParameter(component, 'diameter_in')?.toFixed(0) ?? '?'} in`, `桨距 ${numberParameter(component, 'pitch_in')?.toFixed(1) ?? '?'}`]
    case 'battery':
      return [`${numberParameter(component, 'cell_count')?.toFixed(0) ?? '?'}S`, `${numberParameter(component, 'capacity_mah')?.toFixed(0) ?? '?'} mAh`]
    case 'power_module':
      return [`${numberParameter(component, 'max_current_a')?.toFixed(0) ?? '?'} A`, `${numberParameter(component, 'voltage_max_v')?.toFixed(0) ?? '?'} V max`]
    case 'flight_controller':
      return ['飞控', `${numberParameter(component, 'voltage_max_v')?.toFixed(0) ?? '?'} V max`]
    case 'gnss':
      return ['GNSS / 罗盘', `${numberParameter(component, 'voltage_max_v')?.toFixed(1) ?? '?'} V max`]
    case 'payload':
      return [`挂载 ${String(p.mount ?? '未定义')}`, `${(component.mass_kg * 1000).toFixed(0)} g`]
  }
}

function formatNestedValue(value: unknown): string {
  if (Array.isArray(value)) return `${value.length} 组`
  if (value && typeof value === 'object') {
    const item = value as Record<string, unknown>
    if (
      typeof item.x === 'number' &&
      typeof item.y === 'number' &&
      typeof item.z === 'number'
    ) {
      return `X ${formatMillimeters(item.x)} · Y ${formatMillimeters(item.y)} · Z ${formatMillimeters(item.z)}`
    }
    return '已配置'
  }
  return String(value)
}

function displayParameters(component: Component) {
  return Object.entries(component.parameters_json)
    .filter(([key]) => key !== 'source' && key !== 'points' && key !== '_visual')
    .map(([key, value]) => ({
      label: parameterLabels[key] ?? key,
      value: formatNestedValue(value),
    }))
}

function formatMillimeters(meters: number): string {
  const millimeters = meters * 1000
  const prefix = millimeters > 0 ? '+' : ''
  return `${prefix}${millimeters.toFixed(0)} mm`
}

function formatPower(watts: number): string {
  return watts >= 1000 ? `${(watts / 1000).toFixed(2)} kW` : `${watts.toFixed(0)} W`
}
</script>

<style scoped>
.component-card-slot {
  padding: 10px;
}
.component-card-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}
.component-list-empty {
  padding: 14px 8px;
  border: 1px dashed #d8e1ed;
  border-radius: 7px;
  color: #748197;
  text-align: center;
  font-size: 10px;
}
.component-remove-action {
  width: 100%;
  margin-top: 9px;
}
.slot-picker-head > div {
  min-width: 0;
  display: grid;
  gap: 2px;
}
.mount-completion {
  color: #718096;
  font-size: 8px;
  font-weight: 700;
}
.assembly-session-card {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
  margin: 8px 0;
  padding: 8px 9px;
  border: 1px solid #a9caf5;
  border-radius: 8px;
  background: linear-gradient(180deg, #f3f8ff, #edf5ff);
}
.session-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #2b82ee;
  box-shadow: 0 0 0 4px rgba(43, 130, 238, .12);
}
.assembly-session-card div {
  min-width: 0;
  display: grid;
  gap: 2px;
}
.assembly-session-card b {
  color: #20578f;
  font-size: 10px;
}
.assembly-session-card small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #6d8299;
  font-size: 8px;
}
.assembly-session-card button {
  border: 0;
  background: transparent;
  color: #627890;
  font-size: 9px;
  cursor: pointer;
}
.stage-live-state .assembly-dot,
.assembly-dot {
  background: #2f80ed;
  box-shadow: 0 0 0 4px rgba(47, 128, 237, .12);
}
.component-state.pending {
  background: #f2f5f8;
  color: #77859a;
}
.mount-inspector {
  display: grid;
  gap: 7px;
  margin-bottom: 10px;
  padding: 9px;
  border: 1px solid #dbe6f3;
  border-radius: 8px;
  background: #f8fbff;
}
.mount-id-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: 9px;
  color: #6e7d91;
}
.mount-id-row code {
  color: #245da5;
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-weight: 700;
}
.mount-position {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.mount-position span {
  padding: 3px 5px;
  border-radius: 5px;
  background: #edf3fa;
  color: #52657c;
  font-size: 8px;
}
.mount-remove-button {
  width: 100%;
  margin-top: 9px;
  padding: 7px;
  border: 1px solid #e3b9b4;
  border-radius: 7px;
  background: #fff8f7;
  color: #a83c32;
  font-size: 9px;
  font-weight: 800;
  cursor: pointer;
}
.spatial-ok {
  display: grid;
  gap: 3px;
  padding: 9px;
  border: 1px solid #cfe7d8;
  border-radius: 8px;
  background: #f4fbf7;
}
.spatial-ok b {
  color: #28734c;
  font-size: 10px;
}
.spatial-ok span {
  color: #708479;
  font-size: 8px;
}
.diagnostic-button {
  width: 100%;
  text-align: left;
  cursor: pointer;
}

.stage-title-actions {
  display: flex;
  align-items: center;
  gap: 7px;
}
.assembly-save-state {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: #66778d;
  font-size: 8px;
  font-weight: 800;
}
.assembly-save-state i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #42b77d;
}
.assembly-save-state.saving i { background: #4f91e6; }
.assembly-save-state.error { color: #ae443b; }
.assembly-save-state.error i { background: #e16056; }
.stage-library-link,
.stage-copy-button {
  border: 1px solid #cedaea;
  border-radius: 7px;
  background: #fff;
  color: #42617f;
  padding: 6px 8px;
  text-decoration: none;
  font-size: 8px;
  font-weight: 800;
}
.stage-copy-button { cursor: pointer; }
.stage-copy-button:disabled { opacity: .5; cursor: not-allowed; }
</style>
