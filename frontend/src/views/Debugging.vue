<template>
  <main class="debug-page">
    <section class="hero-card">
      <div>
        <p class="eyebrow">SYSTEM COMMISSIONING · 教学工作台</p>
        <h1>无人机系统调试</h1>
        <p class="hero-copy">
          对当前数字样机完成传感器、动力、电源、控制链路与起飞前检查，形成“装配 → 调试 → 飞行验证”的连续实训流程。
        </p>
      </div>
      <div class="hero-aircraft">
        <span>当前飞机</span>
        <strong>{{ assemblyStore.aircraftName }}</strong>
        <small>{{ assemblyStore.validation.passed ? '装配基础检查已通过' : '装配存在阻断项，请先修正' }}</small>
      </div>
    </section>

    <section class="status-grid">
      <article :class="['status-card', readinessClass]">
        <span>调试结论</span>
        <strong>{{ readinessZh }}</strong>
        <small>{{ readinessHint }}</small>
      </article>
      <article class="status-card">
        <span>调试得分</span>
        <strong>{{ evaluation.score }}</strong>
        <small>{{ evaluation.passCount }} 通过 · {{ evaluation.warningCount }} 警告 · {{ evaluation.errorCount }} 阻断</small>
      </article>
      <article class="status-card">
        <span>工程推重比</span>
        <strong>{{ engineeringValue('thrust_weight_ratio', 2) }}</strong>
        <small>课程推荐：≥ 1.80</small>
      </article>
      <article class="status-card">
        <span>预计续航</span>
        <strong>{{ engineeringValue('estimated_flight_time_min', 1, ' min') }}</strong>
        <small>来自当前飞机工程模型</small>
      </article>
    </section>

    <section class="scenario-card">
      <div class="section-heading">
        <div>
          <p class="eyebrow">TRAINING PRESETS</p>
          <h2>调试训练场景</h2>
        </div>
        <button class="ghost-button" type="button" @click="resetNormal">恢复标准状态</button>
      </div>
      <div class="scenario-list">
        <button
          v-for="scenario in scenarios"
          :key="scenario.key"
          type="button"
          :class="['scenario-item', { active: state.scenarioKey === scenario.key }]"
          @click="selectScenario(scenario.key)"
        >
          <span>{{ scenario.index }}</span>
          <div>
            <strong>{{ scenario.title }}</strong>
            <small>{{ scenario.description }}</small>
          </div>
        </button>
      </div>
    </section>

    <div class="workspace-grid">
      <section class="commissioning-panel">
        <div class="section-heading compact-heading">
          <div>
            <p class="eyebrow">COMMISSIONING WORKFLOW</p>
            <h2>系统调试工作台</h2>
          </div>
          <span class="autosave-note">当前飞机自动保存调试状态</span>
        </div>

        <div class="debug-section">
          <div class="debug-section-title">
            <span class="step-index">01</span>
            <div><strong>飞控与导航传感器</strong><small>确认姿态与定位基准可用</small></div>
            <span :class="['group-state', groupSeverity('sensors')]">{{ groupSummary('sensors') }}</span>
          </div>
          <div class="control-grid">
            <label class="toggle-row">
              <span><b>IMU 校准</b><small>加速度计 / 陀螺仪</small></span>
              <input v-model="state.imuCalibrated" type="checkbox" />
            </label>
            <label class="toggle-row">
              <span><b>罗盘校准</b><small>航向基准</small></span>
              <input v-model="state.compassCalibrated" type="checkbox" />
            </label>
            <label class="field-row">
              <span><b>GNSS 卫星数</b><small>课程起飞前检查</small></span>
              <input v-model.number="state.gpsSatellites" type="number" min="0" max="40" step="1" />
            </label>
            <label class="field-row">
              <span><b>GNSS HDOP</b><small>水平精度因子</small></span>
              <input v-model.number="state.gpsHdop" type="number" min="0.5" max="10" step="0.1" />
            </label>
          </div>
        </div>

        <div class="debug-section">
          <div class="debug-section-title">
            <span class="step-index">02</span>
            <div><strong>动力与电源系统</strong><small>执行电机响应、旋向与上电状态检查</small></div>
            <span :class="['group-state', groupSeverity('propulsion')]">{{ groupSummary('propulsion') }}</span>
          </div>
          <div class="motor-grid">
            <article v-for="motor in motorNames" :key="motor" class="motor-card">
              <div><strong>{{ motor }}</strong><small>电机输出测试</small></div>
              <label>
                <span>响应</span>
                <input v-model="state.motors[motor].responding" type="checkbox" />
              </label>
              <label>
                <span>旋向</span>
                <select v-model="state.motors[motor].direction">
                  <option value="CW">CW</option>
                  <option value="CCW">CCW</option>
                </select>
              </label>
            </article>
          </div>
          <div class="control-grid power-grid">
            <label class="field-row">
              <span><b>实测电池电压</b><small>{{ batteryRangeText }}</small></span>
              <input v-model.number="state.batteryVoltageV" type="number" min="0" max="60" step="0.1" />
              <em>V</em>
            </label>
            <div class="read-only-row">
              <span><b>最小电流裕量</b><small>ESC / 电池 / 电源模块</small></span>
              <strong>{{ minimumCurrentMargin }}</strong>
            </div>
          </div>
        </div>

        <div class="debug-section">
          <div class="debug-section-title">
            <span class="step-index">03</span>
            <div><strong>遥控链路与安全保护</strong><small>检查控制链路、失控保护与电量阈值</small></div>
            <span :class="['group-state', groupSeverity('link')]">{{ groupSummary('link') }}</span>
          </div>
          <div class="control-grid">
            <label class="toggle-row">
              <span><b>遥控器校准</b><small>通道中位 / 行程 / 方向</small></span>
              <input v-model="state.rcCalibrated" type="checkbox" />
            </label>
            <label class="field-row">
              <span><b>控制链路质量</b><small>接收机信号模拟值</small></span>
              <input v-model.number="state.rcSignalPercent" type="number" min="0" max="100" step="1" />
              <em>%</em>
            </label>
            <label class="field-row">
              <span><b>失控保护</b><small>课程场景策略</small></span>
              <select v-model="state.failsafeMode">
                <option value="RTH">RTH 返航</option>
                <option value="LAND">LAND 降落</option>
                <option value="HOLD">HOLD 保持</option>
              </select>
            </label>
            <label class="field-row">
              <span><b>返航高度</b><small>结合训练场障碍物设置</small></span>
              <input v-model.number="state.rthAltitudeM" type="number" min="5" max="120" step="1" />
              <em>m</em>
            </label>
            <label class="field-row">
              <span><b>低电量阈值</b><small>一级保护</small></span>
              <input v-model.number="state.lowBatteryPercent" type="number" min="5" max="60" step="1" />
              <em>%</em>
            </label>
            <label class="field-row">
              <span><b>严重低电量</b><small>二级保护</small></span>
              <input v-model.number="state.criticalBatteryPercent" type="number" min="5" max="50" step="1" />
              <em>%</em>
            </label>
          </div>
        </div>

        <div class="debug-section">
          <div class="debug-section-title">
            <span class="step-index">04</span>
            <div><strong>起飞前系统检查</strong><small>虚拟调试结束前完成最终确认</small></div>
            <span :class="['group-state', groupSeverity('preflight')]">{{ groupSummary('preflight') }}</span>
          </div>
          <div class="control-grid preflight-grid">
            <label class="toggle-row">
              <span><b>螺旋桨已检查</b><small>型号、旋向与紧固</small></span>
              <input v-model="state.propellersSecured" type="checkbox" />
            </label>
            <label class="toggle-row">
              <span><b>线束与接插件已检查</b><small>极性、锁止与干涉</small></span>
              <input v-model="state.wiringSecured" type="checkbox" />
            </label>
            <label class="toggle-row">
              <span><b>测试环境已确认</b><small>桨盘区域与人员防护</small></span>
              <input v-model="state.environmentClear" type="checkbox" />
            </label>
          </div>
        </div>
      </section>

      <aside class="diagnosis-panel">
        <div class="section-heading compact-heading">
          <div>
            <p class="eyebrow">AUTO CHECK</p>
            <h2>自动检查结果</h2>
          </div>
          <span class="score-badge">{{ evaluation.score }}</span>
        </div>

        <div class="check-list">
          <article v-for="item in evaluation.checks" :key="item.key" :class="['check-item', item.severity]">
            <span class="check-dot"></span>
            <div>
              <strong>{{ item.title }}</strong>
              <small>{{ item.value }}</small>
              <p v-if="item.severity !== 'pass'">{{ item.recommendation }}</p>
            </div>
          </article>
        </div>

        <div class="action-stack">
          <button class="primary-button" type="button" @click="recordCheckpoint">记录本次调试结果</button>
          <button class="secondary-button" type="button" @click="exportReport">导出调试报告</button>
          <button v-if="evaluation.readiness === 'READY'" class="success-button" type="button" @click="goFlight">进入飞行验证</button>
          <button v-else class="danger-button" type="button" @click="goAssembly">返回装配处理问题</button>
        </div>

        <div v-if="checkpoints.length" class="history-box">
          <div class="history-title"><strong>调试记录</strong><small>最近 {{ checkpoints.length }} 次</small></div>
          <div v-for="item in checkpoints.slice(0, 5)" :key="item.id" class="history-item">
            <span :class="['history-state', item.readiness.toLowerCase()]">{{ readinessText(item.readiness) }}</span>
            <div><b>{{ item.score }} 分</b><small>{{ formatTime(item.createdAt) }}</small></div>
          </div>
        </div>

        <p class="teaching-note">
          本模块用于课程教学和虚拟调试训练，阈值为教学场景规则，不替代具体飞控厂商手册、实体机检查规程或真实飞行安全要求。
        </p>
      </aside>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAssemblyStore } from '../stores/assembly'
import { useAuthStore } from '../stores/auth'
import type { Component, MotorName } from '../types/aircraft'
import type {
  DebugGroup,
  DebugReadiness,
  DebuggingBenchState,
  DebuggingCheckpoint,
  DebuggingContext,
} from '../types/debugging'
import {
  applyDebuggingScenario,
  defaultDebuggingBenchState,
  evaluateDebugging,
} from '../utils/debugging'

const router = useRouter()
const assemblyStore = useAssemblyStore()
const authStore = useAuthStore()
const motorNames: MotorName[] = ['M1', 'M2', 'M3', 'M4']

const scenarios = [
  { key: 'normal', index: 'A', title: '标准调试', description: '所有系统处于课程推荐状态，用于熟悉完整流程。' },
  { key: 'gps', index: 'B', title: 'GNSS 定位异常', description: '卫星数不足、HDOP 偏高，训练导航系统排查。' },
  { key: 'motor', index: 'C', title: '动力系统异常', description: '包含电机旋向与输出响应问题。' },
  { key: 'failsafe', index: 'D', title: '安全保护异常', description: '控制链路偏弱、失控策略与返航高度不合理。' },
  { key: 'exam', index: 'E', title: '综合考核', description: '混合多个调试问题，适合学生独立排查。' },
]

function numericParameter(component: Component | null, key: string): number | null {
  const value = component?.parameters_json?.[key]
  return typeof value === 'number' && Number.isFinite(value) ? value : null
}

const batteryComponent = computed(() => assemblyStore.componentForSlot('battery'))
const batteryMin = computed(() => numericParameter(batteryComponent.value, 'voltage_min_v'))
const batteryNominal = computed(() => numericParameter(batteryComponent.value, 'nominal_voltage_v'))
const batteryMax = computed(() => numericParameter(batteryComponent.value, 'voltage_max_v'))

const state = ref<DebuggingBenchState>(defaultDebuggingBenchState())
const checkpoints = ref<DebuggingCheckpoint[]>([])
let loadingWorkspace = false

const storageKey = computed(() => `uavstudio.debugging:${authStore.user?.id ?? 0}:${assemblyStore.activeAircraftId ?? 0}`)

const context = computed<DebuggingContext>(() => {
  const engineering = assemblyStore.engineering
  const cg = engineering?.center_of_gravity_m
  const horizontalCg = cg ? Math.sqrt(cg.x * cg.x + cg.y * cg.y) : null
  return {
    validationPassed: assemblyStore.validation.passed,
    blockingErrorCount: assemblyStore.validation.blocking_errors.length,
    warningCount: assemblyStore.validation.warnings.length,
    engineeringAvailable: engineering !== null,
    thrustWeightRatio: engineering?.thrust_weight_ratio ?? null,
    cgHorizontalM: horizontalCg,
    escCurrentMarginA: engineering?.esc_current_margin_a ?? null,
    batteryContinuousMarginA: engineering?.battery_continuous_margin_a ?? null,
    powerModuleCurrentMarginA: engineering?.power_module_current_margin_a ?? null,
    batteryMinVoltageV: batteryMin.value,
    batteryNominalVoltageV: batteryNominal.value,
    batteryMaxVoltageV: batteryMax.value,
  }
})

const evaluation = computed(() => evaluateDebugging(state.value, context.value))
const readinessClass = computed(() => evaluation.value.readiness.toLowerCase())
const readinessZh = computed(() => readinessText(evaluation.value.readiness))
const readinessHint = computed(() => {
  if (evaluation.value.readiness === 'READY') return '全部课程调试项通过，可进入飞行验证'
  if (evaluation.value.readiness === 'CONDITIONAL') return '无阻断项，但仍有警告需要复核'
  return '存在阻断项，暂不建议进入下一阶段'
})

const batteryRangeText = computed(() => {
  if (batteryMin.value === null || batteryMax.value === null) return '当前电池未提供电压范围'
  return `组件范围 ${batteryMin.value.toFixed(1)}–${batteryMax.value.toFixed(1)} V`
})

const minimumCurrentMargin = computed(() => {
  const engineering = assemblyStore.engineering
  if (!engineering) return '—'
  return `${Math.min(
    engineering.esc_current_margin_a,
    engineering.battery_continuous_margin_a,
    engineering.power_module_current_margin_a,
  ).toFixed(1)} A`
})

function engineeringValue(key: 'thrust_weight_ratio' | 'estimated_flight_time_min', digits: number, suffix = ''): string {
  const value = assemblyStore.engineering?.[key]
  return typeof value === 'number' ? `${value.toFixed(digits)}${suffix}` : '—'
}

function groupChecks(group: DebugGroup) {
  return evaluation.value.checks.filter(item => item.group === group)
}

function groupSeverity(group: DebugGroup): 'pass' | 'warning' | 'error' {
  const items = groupChecks(group)
  if (items.some(item => item.severity === 'error')) return 'error'
  if (items.some(item => item.severity === 'warning')) return 'warning'
  return 'pass'
}

function groupSummary(group: DebugGroup): string {
  const severity = groupSeverity(group)
  if (severity === 'pass') return '通过'
  if (severity === 'warning') return '需复核'
  return '有异常'
}

function readinessText(value: DebugReadiness): string {
  if (value === 'READY') return '调试完成'
  if (value === 'CONDITIONAL') return '条件通过'
  return '禁止起飞'
}

function formatTime(value: string): string {
  return new Date(value).toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  })
}

function normalizedState(raw: unknown): DebuggingBenchState {
  const base = defaultDebuggingBenchState(batteryNominal.value ?? 22.2)
  if (!raw || typeof raw !== 'object') return base
  const value = raw as Partial<DebuggingBenchState>
  return {
    ...base,
    ...value,
    motors: {
      M1: { ...base.motors.M1, ...value.motors?.M1 },
      M2: { ...base.motors.M2, ...value.motors?.M2 },
      M3: { ...base.motors.M3, ...value.motors?.M3 },
      M4: { ...base.motors.M4, ...value.motors?.M4 },
    },
  }
}

function loadWorkspace(): void {
  loadingWorkspace = true
  try {
    const raw = globalThis.localStorage?.getItem(storageKey.value)
    if (!raw) {
      state.value = defaultDebuggingBenchState(batteryNominal.value ?? 22.2)
      checkpoints.value = []
      return
    }
    const parsed = JSON.parse(raw) as { state?: unknown; checkpoints?: DebuggingCheckpoint[] }
    state.value = normalizedState(parsed.state)
    checkpoints.value = Array.isArray(parsed.checkpoints) ? parsed.checkpoints.slice(0, 20) : []
  } catch {
    state.value = defaultDebuggingBenchState(batteryNominal.value ?? 22.2)
    checkpoints.value = []
  } finally {
    loadingWorkspace = false
  }
}

function persistWorkspace(): void {
  if (loadingWorkspace || !assemblyStore.activeAircraftId || !authStore.user) return
  try {
    globalThis.localStorage?.setItem(storageKey.value, JSON.stringify({
      state: state.value,
      checkpoints: checkpoints.value.slice(0, 20),
    }))
  } catch {
    // Local persistence is intentionally best-effort; the aircraft itself remains stored by the backend.
  }
}

function selectScenario(key: string): void {
  const base = defaultDebuggingBenchState(batteryNominal.value ?? 22.2)
  state.value = applyDebuggingScenario(key, base)
}

function resetNormal(): void {
  selectScenario('normal')
}

function recordCheckpoint(): void {
  const result = evaluation.value
  checkpoints.value.unshift({
    id: `${Date.now()}`,
    createdAt: new Date().toISOString(),
    scenarioKey: state.value.scenarioKey,
    readiness: result.readiness,
    score: result.score,
    failedKeys: result.checks.filter(item => item.severity === 'error').map(item => item.key),
    warningKeys: result.checks.filter(item => item.severity === 'warning').map(item => item.key),
  })
  checkpoints.value = checkpoints.value.slice(0, 20)
  persistWorkspace()
}

function exportReport(): void {
  const result = evaluation.value
  const report = {
    exported_at: new Date().toISOString(),
    aircraft: assemblyStore.aircraftName,
    aircraft_id: assemblyStore.activeAircraftId,
    scenario: state.value.scenarioKey,
    readiness: result.readiness,
    score: result.score,
    bench_state: state.value,
    engineering_context: context.value,
    checks: result.checks,
  }
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `uav-debug-${assemblyStore.activeAircraftId ?? 'aircraft'}-${Date.now()}.json`
  link.click()
  URL.revokeObjectURL(url)
}

function goAssembly(): void { void router.push('/assembly') }
function goFlight(): void { void router.push('/flight') }

watch(state, persistWorkspace, { deep: true })
watch(checkpoints, persistWorkspace, { deep: true })
watch(() => assemblyStore.activeAircraftId, () => loadWorkspace())
watch(() => batteryNominal.value, (value, oldValue) => {
  if (value !== null && (oldValue === null || state.value.batteryVoltageV === 22.2)) {
    state.value.batteryVoltageV = value
  }
})

onMounted(async () => {
  await assemblyStore.initialize()
  loadWorkspace()
})
</script>

<style scoped>
.debug-page{min-height:calc(100vh - 60px);padding:22px;background:linear-gradient(180deg,#07111f 0%,#091626 55%,#07111f 100%);color:#eaf4ff}.hero-card,.scenario-card,.commissioning-panel,.diagnosis-panel,.status-card{border:1px solid rgba(125,161,202,.16);background:linear-gradient(145deg,rgba(16,34,55,.96),rgba(9,24,42,.92));box-shadow:0 16px 50px rgba(0,0,0,.16)}.hero-card{display:flex;justify-content:space-between;gap:30px;padding:24px 26px;border-radius:18px}.eyebrow{margin:0 0 6px;color:#65d8f5;font-size:10px;font-weight:800;letter-spacing:.16em}.hero-card h1,.section-heading h2{margin:0;color:#f5fbff}.hero-card h1{font-size:28px;letter-spacing:-.03em}.hero-copy{max-width:760px;margin:8px 0 0;color:#9eb3ca;font-size:13px;line-height:1.7}.hero-aircraft{min-width:260px;display:flex;flex-direction:column;justify-content:center;padding:14px 18px;border-radius:14px;background:rgba(75,151,197,.08);border:1px solid rgba(101,216,245,.12)}.hero-aircraft span,.status-card span{color:#7f9ab5;font-size:10px}.hero-aircraft strong{margin:4px 0;color:#eaf8ff;font-size:17px}.hero-aircraft small{color:#7ec7a0;font-size:10px}.status-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:12px}.status-card{padding:15px 17px;border-radius:14px}.status-card strong{display:block;margin:5px 0 3px;color:#f5fbff;font-size:23px}.status-card small{color:#8199b0;font-size:9px}.status-card.ready{border-color:rgba(74,222,128,.26)}.status-card.conditional{border-color:rgba(250,204,21,.26)}.status-card.blocked{border-color:rgba(248,113,113,.30)}.scenario-card{margin-top:12px;padding:18px;border-radius:16px}.section-heading{display:flex;align-items:center;justify-content:space-between;gap:14px}.section-heading h2{font-size:16px}.compact-heading{margin-bottom:14px}.scenario-list{display:grid;grid-template-columns:repeat(5,1fr);gap:9px;margin-top:14px}.scenario-item{display:flex;align-items:center;gap:10px;min-height:70px;padding:11px;border:1px solid rgba(132,160,191,.15);border-radius:12px;background:rgba(255,255,255,.025);color:inherit;text-align:left;cursor:pointer}.scenario-item:hover,.scenario-item.active{border-color:rgba(101,216,245,.34);background:rgba(37,143,178,.10)}.scenario-item>span{display:grid;place-items:center;width:30px;height:30px;border-radius:9px;background:rgba(101,216,245,.10);color:#79e7ff;font-weight:800}.scenario-item div{display:grid;gap:3px}.scenario-item strong{font-size:11px}.scenario-item small{color:#7e96ad;font-size:8px;line-height:1.4}.ghost-button,.primary-button,.secondary-button,.success-button,.danger-button{border-radius:9px;font-weight:750;cursor:pointer}.ghost-button{height:30px;padding:0 12px;border:1px solid rgba(132,160,191,.18);background:rgba(255,255,255,.04);color:#adc1d5;font-size:9px}.workspace-grid{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:12px;margin-top:12px}.commissioning-panel,.diagnosis-panel{border-radius:16px;padding:18px}.autosave-note{color:#6f8da8;font-size:9px}.debug-section{padding:15px 0;border-top:1px solid rgba(121,152,185,.10)}.debug-section:first-of-type{border-top:0}.debug-section-title{display:grid;grid-template-columns:34px 1fr auto;align-items:center;gap:10px;margin-bottom:12px}.step-index{display:grid;place-items:center;width:32px;height:32px;border-radius:9px;background:rgba(82,190,221,.09);color:#66d8f5;font-size:10px;font-weight:800}.debug-section-title div{display:grid;gap:2px}.debug-section-title strong{font-size:12px}.debug-section-title small{color:#7890a7;font-size:8px}.group-state{padding:4px 8px;border-radius:999px;font-size:8px;font-weight:800}.group-state.pass{background:rgba(74,222,128,.10);color:#86efac}.group-state.warning{background:rgba(250,204,21,.10);color:#fde68a}.group-state.error{background:rgba(248,113,113,.10);color:#fca5a5}.control-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}.toggle-row,.field-row,.read-only-row{position:relative;display:flex;align-items:center;justify-content:space-between;gap:10px;min-height:54px;padding:9px 11px;border:1px solid rgba(128,155,186,.11);border-radius:10px;background:rgba(255,255,255,.022)}.toggle-row span,.field-row span,.read-only-row span{display:grid;gap:2px}.toggle-row b,.field-row b,.read-only-row b{font-size:10px}.toggle-row small,.field-row small,.read-only-row small{color:#7189a1;font-size:8px}.toggle-row input{width:17px;height:17px;accent-color:#2eb8dd}.field-row input,.field-row select,.motor-card select{width:88px;height:30px;padding:0 8px;border:1px solid rgba(126,158,191,.18);border-radius:7px;background:#0b1b2d;color:#dceeff;font-size:10px;outline:none}.field-row em{position:absolute;right:18px;color:#7691aa;font-size:8px;font-style:normal}.field-row input+em{pointer-events:none}.field-row:has(em) input{padding-right:25px}.motor-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:8px}.motor-card{padding:10px;border:1px solid rgba(128,155,186,.11);border-radius:10px;background:rgba(255,255,255,.022)}.motor-card>div{display:grid;margin-bottom:8px}.motor-card strong{font-size:12px}.motor-card small{color:#7189a1;font-size:8px}.motor-card label{display:flex;align-items:center;justify-content:space-between;min-height:30px;color:#829bb3;font-size:8px}.motor-card input{accent-color:#2eb8dd}.power-grid{grid-template-columns:1fr 1fr}.read-only-row>strong{color:#d7f6ff;font-size:13px}.preflight-grid{grid-template-columns:repeat(3,1fr)}.diagnosis-panel{align-self:start;position:sticky;top:76px;max-height:calc(100vh - 92px);overflow:auto}.score-badge{display:grid;place-items:center;width:42px;height:42px;border-radius:12px;background:rgba(101,216,245,.10);color:#89edff;font-size:16px;font-weight:900}.check-list{display:grid;gap:6px}.check-item{display:grid;grid-template-columns:10px 1fr;gap:8px;padding:9px;border-radius:9px;background:rgba(255,255,255,.02);border:1px solid rgba(128,155,186,.09)}.check-dot{width:7px;height:7px;margin-top:4px;border-radius:50%}.check-item.pass .check-dot{background:#4ade80}.check-item.warning .check-dot{background:#facc15}.check-item.error .check-dot{background:#f87171}.check-item div{display:grid;grid-template-columns:1fr auto;gap:2px 8px}.check-item strong{font-size:9px}.check-item small{color:#8ea6bd;font-size:8px}.check-item p{grid-column:1/-1;margin:3px 0 0;color:#9ab0c5;font-size:8px;line-height:1.45}.action-stack{display:grid;gap:7px;margin-top:14px}.primary-button,.secondary-button,.success-button,.danger-button{height:34px;border:1px solid transparent;font-size:9px}.primary-button{background:#1f9fc3;color:white}.secondary-button{border-color:rgba(128,155,186,.18);background:rgba(255,255,255,.035);color:#b8cadb}.success-button{background:rgba(34,197,94,.14);border-color:rgba(74,222,128,.22);color:#a7f3d0}.danger-button{background:rgba(248,113,113,.10);border-color:rgba(248,113,113,.22);color:#fecaca}.history-box{margin-top:14px;padding-top:12px;border-top:1px solid rgba(128,155,186,.10)}.history-title,.history-item{display:flex;align-items:center;justify-content:space-between}.history-title{margin-bottom:7px}.history-title strong{font-size:9px}.history-title small{color:#7189a1;font-size:8px}.history-item{padding:6px 0;border-top:1px solid rgba(128,155,186,.06)}.history-item div{display:flex;gap:8px;align-items:center}.history-item b{font-size:9px}.history-item small{color:#6f879d;font-size:7px}.history-state{padding:3px 6px;border-radius:999px;font-size:7px;font-weight:800}.history-state.ready{background:rgba(74,222,128,.10);color:#86efac}.history-state.conditional{background:rgba(250,204,21,.10);color:#fde68a}.history-state.blocked{background:rgba(248,113,113,.10);color:#fca5a5}.teaching-note{margin:13px 0 0;padding:10px;border-radius:9px;background:rgba(250,204,21,.035);color:#8199b0;font-size:8px;line-height:1.55}
@media(max-width:1250px){.scenario-list{grid-template-columns:repeat(3,1fr)}.workspace-grid{grid-template-columns:1fr}.diagnosis-panel{position:static;max-height:none}.status-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:800px){.debug-page{padding:12px}.hero-card{flex-direction:column}.status-grid,.control-grid,.preflight-grid,.motor-grid,.scenario-list{grid-template-columns:1fr}.hero-aircraft{min-width:0}.workspace-grid{display:block}.diagnosis-panel{margin-top:12px}}
</style>
