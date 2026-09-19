<template>
  <div class="workbench-grid assembly-grid">
    <aside class="panel left-panel">
      <section class="panel-section">
        <h3>装配流程</h3>
        <button
          v-for="(step, index) in ASSEMBLY_STEPS"
          :key="step.id"
          :class="['assembly-step', { active: index === activeStepIndex }]"
          @click="activeStepIndex = index"
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
            class="slot-picker"
            :class="{ selected: store.selectedSlot === slot }"
            @click="store.selectSlot(slot)"
          >
            <div class="slot-picker-head">
              <b>{{ SLOT_LABELS[slot] }}</b>
              <span :class="store.componentForSlot(slot) ? 'installed' : 'empty'">
                {{ store.componentForSlot(slot)?.name ?? '未安装' }}
              </span>
            </div>
            <select
              :value="selectionFor(slot)"
              @change="updateSelection(slot, $event)"
            >
              <option :value="null">请选择{{ SLOT_LABELS[slot] }}</option>
              <option
                v-for="component in availableComponents(slot)"
                :key="component.id"
                :value="component.id"
              >
                {{ component.name }} · {{ component.mass_kg.toFixed(3) }} kg
              </option>
            </select>
            <div class="slot-actions">
              <button
                class="primary-action compact"
                :disabled="!selectionFor(slot) || store.saving"
                @click.stop="install(slot)"
              >
                {{ store.componentForSlot(slot) ? '更换组件' : installLabel(slot) }}
              </button>
              <button
                v-if="isOptionalSlot(slot)"
                class="ghost-action"
                :disabled="!store.componentForSlot(slot) || store.saving"
                @click.stop="remove(slot)"
              >
                移除
              </button>
            </div>
          </div>
        </template>

        <p v-if="store.error" class="inline-error">{{ store.error }}</p>
      </section>
    </aside>

    <main class="stage-panel assembly-stage">
      <div class="stage-titlebar">
        <div>
          <b>{{ store.aircraftName }}</b>
          <span>四旋翼 X 型数字母机</span>
        </div>
        <div class="stage-live-state">
          <span :class="store.validation.passed ? 'ok-dot' : 'pending-dot'"></span>
          {{ store.validation.passed ? '装配有效' : '装配未完成' }}
        </div>
      </div>
      <DroneScene
        :aircraft="store.aircraft"
        :components="store.components"
        :selected-slot="store.selectedSlot"
        :engineering="store.engineering"
        interactive
        @select-slot="selectSceneSlot"
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
            <h3>部件检查器</h3>
            <p>{{ store.selectedSlot ? SLOT_LABELS[store.selectedSlot] : '尚未选择部件' }}</p>
          </div>
          <span v-if="selectedComponent" class="component-state">已安装</span>
        </div>
        <dl v-if="selectedComponent" class="component-properties">
          <div><dt>名称</dt><dd>{{ selectedComponent.name }}</dd></div>
          <div><dt>类别</dt><dd>{{ componentTypeLabel(selectedComponent.type) }}</dd></div>
          <div><dt>质量</dt><dd>{{ selectedComponent.mass_kg.toFixed(3) }} kg</dd></div>
          <div
            v-for="parameter in displayParameters(selectedComponent)"
            :key="parameter.label"
          >
            <dt>{{ parameter.label }}</dt>
            <dd>{{ parameter.value }}</dd>
          </div>
        </dl>
        <div v-else class="empty-inspector">
          <b>点击 3D 部件</b>
          <span>可查看组件属性和当前安装位置。</span>
        </div>
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
            <p>结果由后端工程计算生成</p>
          </div>
          <span :class="['check-badge', store.validation.passed ? 'ok' : 'error']">
            {{ store.validation.passed ? '通过' : '阻断' }}
          </span>
        </div>

        <div
          v-for="issue in store.validation.blocking_errors"
          :key="issue.code"
          class="validation-item error"
        >
          <b>阻断错误</b>
          <span>{{ issue.message }}</span>
        </div>
        <div
          v-for="issue in store.validation.warnings"
          :key="issue.code"
          class="validation-item warning"
        >
          <b>警告</b>
          <span>{{ issue.message }}</span>
        </div>
        <p v-if="store.validation.passed && store.validation.warnings.length === 0" class="check-ok">
          所有必需组件、动力和电气检查均已通过。
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
        <b>当前教学重点：</b>
        按真实四旋翼装调顺序完成系统级装配；中央模型持续显示组件位置、M1-M4 旋向和重心。
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
import DroneScene from '../components/DroneScene.vue'
import { useAssemblyStore } from '../stores/assembly'
import type { Component, ComponentType } from '../types/aircraft'
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
const selections = reactive<Partial<Record<AssemblySlot, number | null>>>({})
const stateText = {
  done: '已配置',
  warning: '警告',
  error: '错误',
  pending: '未配置',
} as const

const activeStep = computed(() => ASSEMBLY_STEPS[activeStepIndex.value])
const selectedComponent = computed(() =>
  store.selectedSlot ? store.componentForSlot(store.selectedSlot) : null,
)
const completedStepCount = computed(() =>
  ASSEMBLY_STEPS.filter(step => {
    const status = stepStatus(step)
    return status === 'done' || status === 'warning'
  }).length,
)

const parameterLabels: Record<string, string> = {
  motor_diagonal_m: '电机对角轴距',
  battery_position_m: '电池安装位置',
  power_module_position_m: '电源模块位置',
  flight_controller_position_m: '飞控安装位置',
  gnss_mount_position_m: 'GNSS 安装位置',
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

function stepStatus(step: AssemblyStep) {
  if (!store.aircraft) return 'pending' as const
  return getStepStatus(step, store.aircraft, store.validation)
}

function availableComponents(slot: AssemblySlot): Component[] {
  return slotComponents(store.components, slot)
}

function selectionFor(slot: AssemblySlot): number | null {
  if (Object.prototype.hasOwnProperty.call(selections, slot)) {
    return selections[slot] ?? null
  }
  return store.aircraft ? installedComponentId(store.aircraft, slot) : null
}

function updateSelection(slot: AssemblySlot, event: Event): void {
  const value = (event.target as HTMLSelectElement).value
  selections[slot] = value ? Number(value) : null
}

async function install(slot: AssemblySlot): Promise<void> {
  const componentId = selectionFor(slot)
  if (!componentId) return
  await store.installComponent(slot, componentId)
}

async function remove(slot: AssemblySlot): Promise<void> {
  await store.removeComponent(slot)
  selections[slot] = null
}

function isOptionalSlot(slot: AssemblySlot): boolean {
  return slot === 'gnss' || slot === 'payload'
}

function installLabel(slot: AssemblySlot): string {
  if (slot === 'motor' || slot === 'esc' || slot === 'propeller') {
    return '安装到 4 个机臂'
  }
  return '安装组件'
}

function selectSceneSlot(slot: AssemblySlot): void {
  store.selectSlot(slot)
  const stepIndex = ASSEMBLY_STEPS.findIndex(step => step.slots.includes(slot))
  if (stepIndex >= 0) activeStepIndex.value = stepIndex
}

function componentTypeLabel(type: ComponentType): string {
  return typeLabels[type]
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
    .filter(([key]) => key !== 'source' && key !== 'points')
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
