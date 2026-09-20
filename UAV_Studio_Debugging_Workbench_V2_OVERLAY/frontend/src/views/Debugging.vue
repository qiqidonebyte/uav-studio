<template>
  <div class="debug-page">
    <aside class="debug-sidebar">
      <section class="side-section">
        <div class="side-title">调试流程</div>
        <button
          v-for="(step, index) in steps"
          :key="step.key"
          :class="['flow-step', { active: activeSection === step.key }]"
          @click="activeSection = step.key"
        >
          <span class="step-no">{{ index + 1 }}</span>
          <span class="step-icon">{{ step.icon }}</span>
          <span class="step-copy">
            <b>{{ step.title }}</b>
            <small>{{ step.subtitle }}</small>
          </span>
        </button>
      </section>

      <section class="side-section scenarios">
        <div class="side-title">训练场景</div>
        <button
          v-for="item in scenarios"
          :key="item.key"
          :class="['scenario-card', { active: scenario === item.key }]"
          @click="switchScenario(item.key)"
        >
          <span>{{ item.icon }}</span>
          <div><b>{{ item.title }}</b><small>{{ item.subtitle }}</small></div>
        </button>
      </section>

      <div class="practice-mark">
        <b>PRACTICE</b>
        <span>MAKE BETTER PILOTS</span>
      </div>
    </aside>

    <main class="debug-main">
      <div class="section-tabs">
        <button
          v-for="tab in topTabs"
          :key="tab.key"
          :class="{ active: activeSection === tab.key }"
          @click="activeSection = tab.key"
        >{{ tab.title }}</button>
      </div>

      <template v-if="activeSection === 'power'">
        <div class="power-layout">
          <section class="surface scene-surface">
            <div class="surface-heading">
              <div>
                <span class="heading-icon">▣</span>
                <b>四旋翼无人机 3D 视图</b>
              </div>
              <span class="heading-note">当前飞机：{{ assemblyStore.aircraftName }}</span>
            </div>

            <div class="scene-and-controls">
              <DebugMotorScene
                :telemetry="debugTelemetry"
                :aircraft="assemblyStore.aircraft"
                :components="assemblyStore.components"
                :engineering="assemblyStore.engineering"
                :commanded-motor="commandedMotor"
                :actual-motor="actualMotor"
                :fault-motor="faultMotor"
              />

              <div class="motor-test-stack">
                <button
                  v-for="motor in motorNames"
                  :key="motor"
                  :class="['motor-test', { active: commandedMotor === motor }]"
                  :disabled="motorTestBusy"
                  @click="testMotor(motor)"
                >
                  <span>▶</span> 测试 {{ motor }}
                </button>
                <button class="stop-all" @click="stopAllMotors"><span>■</span> 全部停止</button>
              </div>
            </div>
          </section>

          <section class="surface parameter-surface">
            <div class="surface-heading">
              <div><span class="heading-icon">▤</span><b>动力系统参数</b></div>
            </div>
            <div class="metric-grid">
              <div class="metric-card"><span>▥</span><small>电池</small><b>{{ batteryText }}</b></div>
              <div class="metric-card"><span>▥</span><small>推重比</small><b>{{ thrustRatioText }}</b></div>
              <div class="metric-card"><span>◔</span><small>悬停油门</small><b>{{ hoverThrottleText }}</b></div>
              <div class="metric-card"><span>ϟ</span><small>最大电流</small><b>{{ maxCurrentText }}</b></div>
              <div class="metric-card good"><span>✓</span><small>ESC 裕量</small><b>{{ escMarginText }}</b></div>
              <div class="metric-card good"><span>♡</span><small>电池状态</small><b>{{ batteryHealthText }}</b></div>
            </div>
            <div class="safety-tip">ⓘ 教学演示模式仅驱动数字旋翼；接入 PX4 后再发送真实执行机构测试指令。</div>
          </section>
        </div>

        <div class="lower-grid">
          <section class="surface actuator-surface">
            <div class="surface-heading"><div><span class="heading-icon">⚙</span><b>执行机构状态</b></div></div>
            <div class="actuator-list">
              <div v-for="(motor, index) in motorNames" :key="motor" class="actuator-row">
                <b>{{ motor }}</b><span>输出</span>
                <div class="output-bar"><i :style="{ width: `${Math.round(motorOutputs[index] * 100)}%` }"></i></div>
                <strong>{{ Math.round(motorOutputs[index] * 100) }}%</strong>
              </div>
            </div>
          </section>

          <section class="surface mapping-surface">
            <div class="surface-heading"><div><span class="heading-icon">⚙</span><b>旋向与映射</b></div></div>
            <table>
              <thead><tr><th>电机</th><th>位置</th><th>理论旋向</th><th>当前响应</th></tr></thead>
              <tbody>
                <tr v-for="row in motorRows" :key="row.motor">
                  <td>{{ row.motor }}</td><td>{{ row.position }}</td><td>{{ row.direction }}</td>
                  <td :class="row.responseClass">{{ row.response }}</td>
                </tr>
              </tbody>
            </table>
            <div v-if="mappingFaultVisible" class="fault-banner">
              <span>!</span>
              <div>
                <b>检测到：M1 指令触发后实际 M3 响应</b>
                <small>疑似执行机构映射错误。可在教学场景中执行修复。</small>
              </div>
              <button @click="repairMotorMapping">修复映射</button>
            </div>
            <div v-else class="pass-banner"><span>✓</span> 电机响应与理论映射一致</div>
          </section>
        </div>
      </template>

      <section v-else class="surface module-placeholder">
        <div class="module-icon">{{ currentStep.icon }}</div>
        <div>
          <h2>{{ currentStep.title }}</h2>
          <p>{{ currentModuleDescription }}</p>
          <div class="placeholder-actions">
            <button class="primary-action" @click="appendLog(`进入${currentStep.title}调试`)" >开始教学调试</button>
            <button @click="activeSection = 'power'">返回动力系统</button>
          </div>
        </div>
      </section>
    </main>

    <aside class="debug-rightbar">
      <section class="surface telemetry-surface">
        <div class="surface-heading"><div><span class="heading-icon">▥</span><b>实时状态 / 遥测</b></div></div>
        <div class="status-grid">
          <div><span>飞控</span><b>{{ bridgeMode === 'live' ? 'PX4 SITL' : '教学模拟' }}</b></div>
          <div><span>电池</span><b>{{ batteryVoltageText }}</b></div>
          <div><span>模式</span><b class="standby">STANDBY</b></div>
          <div><span>EKF</span><b class="ok">{{ scenario === 'compass' ? '异常' : '正常' }}</b></div>
          <div><span>GPS</span><b class="ok">{{ gpsStatus }}</b></div>
          <div><span>Arming</span><b class="bad">禁止</b></div>
          <div><span>IMU</span><b class="ok">正常</b></div>
          <div><span>Bridge</span><b :class="bridgeMode === 'live' ? 'ok' : 'warn'">{{ bridgeMode === 'live' ? '在线' : '待接入' }}</b></div>
        </div>
        <div class="prearm-alert">
          <span>!</span>
          <div><b>Pre-Arm Check {{ prearmPassed ? 'Passed' : 'Failed' }}</b><small>{{ prearmMessage }}</small></div>
        </div>
      </section>

      <section class="surface bridge-surface">
        <div class="bridge-row">
          <span class="dot" :class="bridgeMode === 'live' ? 'online' : 'demo'"></span>
          <div><b>PX4 SITL</b><small>{{ bridgeMode === 'live' ? 'MAVLink Bridge 已连接' : '接口已预留 · 当前教学模拟' }}</small></div>
          <strong>{{ bridgeMode === 'live' ? '已连接' : '待接入' }}</strong>
        </div>
        <div class="bridge-row">
          <span class="dot demo"></span>
          <div><b>Gazebo</b><small>物理环境 / 传感器仿真节点</small></div>
          <strong>待接入</strong>
        </div>
      </section>

      <section class="surface log-surface">
        <div class="surface-heading">
          <div><span class="heading-icon">▤</span><b>调试记录</b></div>
          <button class="clear-log" @click="logs = []">清空记录</button>
        </div>
        <div class="timeline">
          <div v-for="item in logs" :key="item.id" :class="['log-item', item.level]">
            <span class="timeline-dot"></span>
            <time>{{ item.time }}</time>
            <div><b>{{ item.title }}</b><small>{{ item.detail }}</small></div>
          </div>
          <div v-if="logs.length === 0" class="empty-log">尚无调试记录</div>
        </div>
      </section>

      <section class="surface score-surface">
        <span class="trophy">♛</span>
        <div><small>当前调试得分</small><b>{{ score }}<em>/100</em></b></div>
        <div class="remaining"><span>未完成项：</span><b>{{ remainingTasks }}</b></div>
      </section>

      <div class="right-actions">
        <button @click="saveDebugReport">▣ 保存调试记录</button>
        <RouterLink class="flight-action" to="/flight">➤ 进入飞行验证</RouterLink>
      </div>
    </aside>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import DebugMotorScene from '../components/DebugMotorScene.vue'
import { useAssemblyStore } from '../stores/assembly'
import type { MotorName } from '../types/aircraft'
import type { MotorVector, TelemetryFrame } from '../types/telemetry'
import { calculateDebugScore, resolveMotorResponse, type DebugScenario } from '../utils/debugging'

type SectionKey = 'sensors' | 'rc' | 'power' | 'safety' | 'preflight'
type ScenarioKey = DebugScenario
type LogLevel = 'info' | 'warn' | 'error' | 'success'

interface DebugLog {
  id: number
  time: string
  title: string
  detail: string
  level: LogLevel
}

const assemblyStore = useAssemblyStore()
const activeSection = ref<SectionKey>('power')
const scenario = ref<ScenarioKey>('mapping')
const bridgeMode = ref<'demo' | 'live'>('demo')
const commandedMotor = ref<MotorName | null>(null)
const actualMotor = ref<MotorName | null>(null)
const mappingRepaired = ref(false)
const motorOutputs = ref<MotorVector>([0, 0, 0, 0])
const motorTestBusy = ref(false)
const clockTick = ref(0)
const logs = ref<DebugLog[]>([])
let timer: number | undefined
let stopTimer: number | undefined
let logId = 0

const motorNames: MotorName[] = ['M1', 'M2', 'M3', 'M4']
const motorIndex: Record<MotorName, number> = { M1: 0, M2: 1, M3: 2, M4: 3 }
const motorMeta: Record<MotorName, { position: string; direction: string }> = {
  M1: { position: '右前', direction: 'CCW（逆时针）' },
  M2: { position: '右后', direction: 'CW（顺时针）' },
  M3: { position: '左后', direction: 'CCW（逆时针）' },
  M4: { position: '左前', direction: 'CW（顺时针）' },
}

const steps = [
  { key: 'sensors' as const, icon: '▦', title: '飞控与传感器', subtitle: '检查飞控、IMU、指南针等' },
  { key: 'rc' as const, icon: '⌁', title: '遥控系统', subtitle: '验证遥控器与接收机' },
  { key: 'power' as const, icon: '✤', title: '动力系统', subtitle: '电机 / ESC / 桨叶测试' },
  { key: 'safety' as const, icon: '◇', title: '安全设置', subtitle: 'Failsafe 与安全策略' },
  { key: 'preflight' as const, icon: '☑', title: '起飞前检查', subtitle: '完成整机检查' },
]
const topTabs = steps.slice(0, 4)
const scenarios = [
  { key: 'standard' as const, icon: '◇', title: '标准调试', subtitle: '基础功能调试流程' },
  { key: 'mapping' as const, icon: '△', title: '电机映射故障', subtitle: '模拟电机映射错误' },
  { key: 'compass' as const, icon: '◉', title: '罗盘异常', subtitle: '模拟指南针数据异常' },
  { key: 'failsafe' as const, icon: '⌘', title: 'Failsafe 异常', subtitle: '模拟失控保护触发' },
]

const currentStep = computed(() => steps.find(item => item.key === activeSection.value) ?? steps[2])
const currentModuleDescription = computed(() => ({
  sensors: '用于飞控状态、IMU、磁罗盘、GNSS 与 EKF 的教学化校准和状态观察。后续接入 PX4 SITL 后，此处直接读取真实 MAVLink 状态。',
  rc: '用于通道映射、中位、行程、正反向、链路质量与失控保护的调试。',
  power: '',
  safety: '用于低电量保护、失控保护、返航高度和解锁条件等安全参数教学。',
  preflight: '汇总装配、调试、参数与系统状态，形成进入飞行验证前的最后检查。',
}[activeSection.value]))

const engineering = computed(() => assemblyStore.engineering)
const massKg = computed(() => engineering.value?.total_mass_kg ?? 2.8)
const gravityN = computed(() => massKg.value * 9.80665)
const maxThrustPerMotor = computed(() => engineering.value?.max_thrust_per_motor_n ?? 17.5)
const totalThrustN = computed(() => motorOutputs.value.reduce((sum, item) => sum + item * maxThrustPerMotor.value, 0))
const batteryComponent = computed(() => assemblyStore.componentForSlot('battery'))
const batteryVoltage = computed(() => {
  const raw = batteryComponent.value?.parameters_json.nominal_voltage_v
  return typeof raw === 'number' ? raw : 22.2
})
const batteryCells = computed(() => {
  const raw = batteryComponent.value?.parameters_json.cell_count
  return typeof raw === 'number' ? raw : 6
})
const batteryText = computed(() => `${batteryCells.value}S / ${batteryVoltage.value.toFixed(1)}V`)
const batteryVoltageText = computed(() => `${(batteryVoltage.value + .2).toFixed(1)} V`)
const thrustRatioText = computed(() => engineering.value ? engineering.value.thrust_weight_ratio.toFixed(2) : '—')
const hoverThrottleText = computed(() => engineering.value ? `${Math.round(engineering.value.hover_throttle * 100)}%` : '—')
const maxCurrentText = computed(() => engineering.value ? `${engineering.value.max_current_a.toFixed(0)}A` : '—')
const escMarginText = computed(() => !engineering.value ? '待计算' : engineering.value.esc_current_margin_a >= 0 ? '通过' : '不足')
const batteryHealthText = computed(() => !engineering.value ? '待计算' : engineering.value.battery_continuous_margin_a >= 0 ? '良好' : '风险')

const faultMotor = computed<MotorName | null>(() => mappingFaultVisible.value ? 'M3' : null)
const mappingFaultVisible = computed(() => scenario.value === 'mapping' && !mappingRepaired.value)
const gpsStatus = computed(() => scenario.value === 'compass' ? '定位受限' : '7 星')
const prearmPassed = computed(() => scenario.value === 'standard' || (scenario.value === 'mapping' && mappingRepaired.value))
const prearmMessage = computed(() => {
  if (scenario.value === 'mapping' && !mappingRepaired.value) return '执行机构映射未通过，请完成 M1–M4 单电机测试。'
  if (scenario.value === 'compass') return '磁罗盘/EKF 状态异常，请进入飞控与传感器调试。'
  if (scenario.value === 'failsafe') return '安全保护参数异常，请检查 Failsafe 设置。'
  return '当前教学场景的前置检查已通过。'
})

const score = computed(() => calculateDebugScore(
  scenario.value,
  mappingRepaired.value,
  assemblyStore.validation.passed,
))
const remainingTasks = computed(() => score.value >= 95 ? '起飞前验证' : '故障修复、安全检查')

const motorRows = computed(() => motorNames.map(motor => {
  const isCommanded = commandedMotor.value === motor
  const actual = actualMotor.value
  const response = isCommanded
    ? actual === motor ? '响应正确' : actual ? `实际 ${actual} 响应` : '待测试'
    : '—'
  return {
    motor,
    position: motorMeta[motor].position,
    direction: motorMeta[motor].direction,
    response,
    responseClass: isCommanded && actual && actual !== motor ? 'response-fault' : isCommanded && actual === motor ? 'response-ok' : '',
  }
}))

const debugTelemetry = computed<TelemetryFrame>(() => ({
  t: clockTick.value / 10,
  position: { x: 0, y: 0, z: 0 },
  velocity: { x: 0, y: 0, z: 0 },
  attitude: { roll: 0, pitch: 0, yaw: 0 },
  angular_velocity: { p: 0, q: 0, r: 0 },
  center_of_gravity: engineering.value?.center_of_gravity_m ?? { x: 0, y: 0, z: 0 },
  motors: {
    outputs: [...motorOutputs.value] as MotorVector,
    thrusts_n: motorOutputs.value.map(item => item * maxThrustPerMotor.value) as MotorVector,
  },
  forces: { gravity_n: gravityN.value, total_thrust_n: totalThrustN.value },
  wind: { speed_mps: 0, direction_deg: 0 },
  power: {
    estimated_power_w: engineering.value?.hover_power_w ?? 0,
    battery_remaining: .86,
    voltage_v: batteryVoltage.value + .2,
    current_a: motorOutputs.value.reduce((sum, item) => sum + item * 7.5, 0),
  },
  armed: false,
  flight_mode: 'IDLE',
}))

function nowText(): string {
  return new Date().toLocaleTimeString('zh-CN', { hour12: false })
}

function appendLog(title: string, detail = '教学调试操作', level: LogLevel = 'info'): void {
  logs.value.push({ id: ++logId, time: nowText(), title, detail, level })
  if (logs.value.length > 12) logs.value = logs.value.slice(-12)
}

function switchScenario(next: ScenarioKey): void {
  scenario.value = next
  mappingRepaired.value = false
  stopAllMotors()
  appendLog(`切换训练场景：${scenarios.find(item => item.key === next)?.title ?? next}`, '场景状态已重新初始化', 'info')
}


function testMotor(command: MotorName): void {
  if (motorTestBusy.value) return
  motorTestBusy.value = true
  commandedMotor.value = command
  const actual = resolveMotorResponse(scenario.value, mappingRepaired.value, command)
  actualMotor.value = actual
  const outputs: MotorVector = [0, 0, 0, 0]
  outputs[motorIndex[actual]] = .62
  motorOutputs.value = outputs
  appendLog(`执行 ${command} 单电机测试`, `发送 ${command} 测试指令（教学输出 62%）`, 'info')

  if (actual !== command) {
    appendLog(`检测到 ${actual} 异常响应`, `${command} 指令触发后，实际 ${actual} 数字旋翼转动`, 'error')
  } else {
    appendLog(`${command} 响应正确`, `${command} 编号与当前映射一致`, 'success')
  }

  if (stopTimer) window.clearTimeout(stopTimer)
  stopTimer = window.setTimeout(() => {
    motorOutputs.value = [0, 0, 0, 0]
    actualMotor.value = null
    motorTestBusy.value = false
  }, 1800)
}

function stopAllMotors(): void {
  if (stopTimer) window.clearTimeout(stopTimer)
  motorOutputs.value = [0, 0, 0, 0]
  actualMotor.value = null
  motorTestBusy.value = false
}

function repairMotorMapping(): void {
  mappingRepaired.value = true
  stopAllMotors()
  appendLog('学生修改电机映射参数', '将 M1–M4 映射恢复为理论顺序', 'warn')
  window.setTimeout(() => {
    commandedMotor.value = 'M1'
    actualMotor.value = 'M1'
    motorOutputs.value = [.45, 0, 0, 0]
    appendLog('二次测试通过', 'M1 响应正常，电机映射恢复正确', 'success')
    stopTimer = window.setTimeout(() => {
      motorOutputs.value = [0, 0, 0, 0]
      actualMotor.value = null
    }, 1400)
  }, 300)
}

function saveDebugReport(): void {
  const report = {
    generated_at: new Date().toISOString(),
    aircraft: assemblyStore.aircraftName,
    scenario: scenario.value,
    bridge_mode: bridgeMode.value,
    score: score.value,
    engineering: assemblyStore.engineering,
    logs: logs.value,
  }
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `uav-debug-${assemblyStore.activeAircraftId ?? 'aircraft'}-${Date.now()}.json`
  anchor.click()
  URL.revokeObjectURL(url)
  appendLog('保存调试记录', '已生成本次教学调试 JSON 报告', 'success')
}

onMounted(async () => {
  await assemblyStore.initialize()
  timer = window.setInterval(() => { clockTick.value += 1 }, 100)
  appendLog('进入动力系统调试', '当前使用教学模拟执行机构；PX4 Bridge 接口已预留', 'info')
  if (scenario.value === 'mapping') {
    appendLog('载入电机映射故障', 'M1 指令将被教学场景映射到 M3', 'warn')
  }
})

onBeforeUnmount(() => {
  if (timer) window.clearInterval(timer)
  if (stopTimer) window.clearTimeout(stopTimer)
})
</script>

<style scoped>
.debug-page {
  --bg:#071321;
  --panel:#0b1b2b;
  --panel2:#0d2134;
  --line:rgba(99, 145, 186, .22);
  --line-strong:rgba(67, 170, 244, .4);
  --text:#d9e8f6;
  --muted:#7897b5;
  --blue:#28a8ff;
  --cyan:#55d9ff;
  --green:#48df8b;
  --red:#ff5e57;
  --amber:#f0bd45;
  display:grid;
  grid-template-columns: 258px minmax(700px, 1fr) 420px;
  gap:0;
  height:calc(100vh - 58px);
  min-height:720px;
  overflow:hidden;
  background:
    radial-gradient(circle at 50% 20%, rgba(31, 103, 154, .12), transparent 35%),
    linear-gradient(180deg, #081523, #06111e);
  color:var(--text);
}
button, a { font:inherit; }
.debug-sidebar, .debug-rightbar { background:rgba(6, 18, 31, .88); }
.debug-sidebar { position:relative; overflow:auto; border-right:1px solid var(--line); padding:16px 14px 72px; }
.debug-main { min-width:0; overflow:auto; padding:16px 12px 22px; }
.debug-rightbar { overflow:auto; border-left:1px solid var(--line); padding:16px 14px; }
.side-section + .side-section { margin-top:18px; padding-top:15px; border-top:1px solid rgba(102,147,188,.14); }
.side-title { margin:0 6px 10px; color:#dbeeff; font-size:13px; font-weight:800; letter-spacing:.03em; }
.flow-step, .scenario-card { width:100%; border:1px solid transparent; background:transparent; color:var(--text); cursor:pointer; }
.flow-step { display:grid; grid-template-columns:30px 34px 1fr; align-items:center; min-height:66px; padding:7px 8px; border-radius:9px; text-align:left; position:relative; }
.flow-step:not(:last-child)::after { content:""; position:absolute; left:22px; top:52px; width:1px; height:28px; border-left:1px dashed rgba(72, 139, 190, .38); }
.flow-step:hover { background:rgba(46, 139, 202, .08); }
.flow-step.active { border-color:rgba(47,171,255,.46); background:linear-gradient(90deg, rgba(23,126,198,.2), rgba(18,57,91,.2)); box-shadow:inset 3px 0 #2aa8ff; }
.step-no { width:22px;height:22px;display:grid;place-items:center;border-radius:50%;border:1px solid rgba(57,164,238,.6);color:#9edcff;background:#102c43;font-size:10px; }
.step-icon { font-size:22px;color:#b8ddf6; }
.step-copy { display:grid;gap:2px; }
.step-copy b { font-size:12px; }
.step-copy small { color:var(--muted);font-size:9px; }
.scenario-card { display:flex;align-items:center;gap:10px;padding:10px;border-radius:8px;text-align:left;border-color:rgba(105,149,186,.13);background:rgba(255,255,255,.018);margin-bottom:7px; }
.scenario-card > span { width:26px;color:#b9d6ed;font-size:18px; }
.scenario-card div { display:grid;gap:2px; }
.scenario-card b { font-size:11px; }
.scenario-card small { font-size:8px;color:var(--muted); }
.scenario-card.active { border-color:#258fd3;background:rgba(17,109,171,.22);box-shadow:0 0 18px rgba(21,132,205,.14); }
.practice-mark { position:absolute;left:20px;bottom:18px;display:grid;color:#506f8b;letter-spacing:.12em;font-size:9px; }
.practice-mark span { font-size:7px; }
.section-tabs { height:44px;display:grid;grid-template-columns:repeat(4,1fr);border:1px solid var(--line);border-radius:8px;background:rgba(8,24,39,.72);margin-bottom:12px;overflow:hidden; }
.section-tabs button { position:relative;border:0;border-right:1px solid rgba(90,140,180,.18);background:transparent;color:#8ca8c0;cursor:pointer;font-size:11px; }
.section-tabs button.active { color:#43c1ff;background:linear-gradient(180deg,rgba(17,93,145,.1),rgba(17,93,145,.04)); }
.section-tabs button.active::after { content:"";position:absolute;left:14%;right:14%;bottom:0;height:2px;background:#26b2ff;box-shadow:0 0 8px #26b2ff; }
.power-layout { display:grid;grid-template-columns:minmax(520px,1.8fr) minmax(260px,.82fr);gap:12px; }
.surface { border:1px solid var(--line);border-radius:9px;background:linear-gradient(180deg,rgba(12,31,49,.94),rgba(8,24,39,.94));box-shadow:0 12px 30px rgba(0,0,0,.12); }
.surface-heading { height:42px;display:flex;align-items:center;justify-content:space-between;padding:0 13px;border-bottom:1px solid rgba(91,139,178,.16); }
.surface-heading > div { display:flex;align-items:center;gap:8px; }
.surface-heading b { font-size:12px; }
.heading-icon { color:#35b9ff;font-size:15px; }
.heading-note { color:#6686a2;font-size:8px; }
.scene-surface { min-width:0;overflow:hidden; }
.scene-and-controls { height:470px;display:grid;grid-template-columns:minmax(0,1fr) 126px;gap:8px;padding:8px; }
.motor-test-stack { display:flex;flex-direction:column;gap:9px;padding-top:58px; }
.motor-test, .stop-all { min-height:43px;border-radius:6px;border:1px solid rgba(92,145,185,.32);background:linear-gradient(180deg,#102a41,#0b1c2c);color:#bad5e9;cursor:pointer;font-size:10px; }
.motor-test:hover,.motor-test.active { border-color:#2dabff;background:linear-gradient(180deg,#1789d0,#116aa5);color:white;box-shadow:0 0 16px rgba(36,161,239,.25); }
.stop-all { margin-top:3px;border-color:rgba(255,88,82,.52);color:#ff807a;background:rgba(118,35,34,.16); }
.parameter-surface { padding-bottom:10px; }
.metric-grid { display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:12px; }
.metric-card { min-height:87px;display:grid;grid-template-columns:30px 1fr;grid-template-rows:1fr 1fr;align-items:center;padding:10px;border:1px solid rgba(91,141,180,.16);border-radius:8px;background:rgba(8,27,44,.78); }
.metric-card > span { grid-row:1/3;color:#3bb6ff;font-size:20px; }
.metric-card small { color:#7493ae;font-size:9px;align-self:end; }
.metric-card b { color:#d9efff;font-size:13px;align-self:start; }
.metric-card.good b,.metric-card.good > span { color:var(--green); }
.safety-tip { margin:3px 12px 2px;padding:8px 9px;border:1px solid rgba(87,142,184,.15);border-radius:6px;color:#6f8eaa;font-size:8px;background:rgba(7,22,36,.72); }
.lower-grid { display:grid;grid-template-columns:.92fr 1fr;gap:12px;margin-top:12px; }
.actuator-list { padding:12px;display:grid;gap:14px; }
.actuator-row { display:grid;grid-template-columns:28px 38px 1fr 42px;gap:8px;align-items:center;font-size:10px; }
.actuator-row > span { color:#7592ac; }
.actuator-row strong { font-size:11px;text-align:right; }
.output-bar { height:11px;border-radius:999px;background:#1a3249;overflow:hidden;box-shadow:inset 0 0 0 1px rgba(93,142,180,.08); }
.output-bar i { display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,#177ee8,#37c4ff);box-shadow:0 0 10px rgba(44,176,255,.28);transition:width .12s linear; }
.mapping-surface { overflow:hidden; }
table { width:calc(100% - 24px);margin:10px 12px 8px;border-collapse:collapse;font-size:9px;text-align:center; }
th,td { padding:7px 5px;border:1px solid rgba(82,132,172,.17); }
th { color:#7f9bb4;font-weight:600;background:rgba(12,35,54,.6); }
td:first-child { color:#45baff;font-weight:800; }
.response-fault { color:#ff7a72!important; }.response-ok { color:#55df91!important; }
.fault-banner,.pass-banner { margin:8px 12px 12px;min-height:47px;display:flex;align-items:center;gap:9px;padding:7px 9px;border-radius:7px;font-size:9px; }
.fault-banner { border:1px solid rgba(255,80,71,.46);background:rgba(126,34,31,.22);color:#ff9b96; }
.fault-banner > span { width:23px;height:23px;display:grid;place-items:center;border-radius:50%;background:#c4423c;color:white;font-weight:900; }
.fault-banner div { display:grid;gap:2px;flex:1; }.fault-banner small { color:#b87f7c; }
.fault-banner button { border:1px solid rgba(255,126,117,.5);border-radius:5px;background:rgba(145,48,43,.35);color:#ffd0cc;padding:6px 9px;cursor:pointer;font-size:8px; }
.pass-banner { border:1px solid rgba(66,215,134,.3);background:rgba(35,124,78,.15);color:#70e5a2; }
.module-placeholder { min-height:550px;display:flex;align-items:center;justify-content:center;gap:28px;padding:50px; }
.module-icon { width:84px;height:84px;display:grid;place-items:center;border-radius:24px;border:1px solid rgba(44,171,255,.28);background:rgba(21,103,158,.12);color:#5fcaff;font-size:38px; }
.module-placeholder h2 { margin:0 0 12px;font-size:24px; }.module-placeholder p { max-width:660px;color:#809bb5;line-height:1.7;font-size:12px; }
.placeholder-actions { display:flex;gap:10px;margin-top:18px; }.placeholder-actions button { border:1px solid var(--line);background:#0c263c;color:#a9c9e1;border-radius:6px;padding:9px 14px;cursor:pointer; }.placeholder-actions .primary-action { border-color:#279ddd;background:#126da6;color:white; }
.debug-rightbar { display:flex;flex-direction:column;gap:10px; }
.status-grid { display:grid;grid-template-columns:1fr 1fr;gap:7px;padding:10px; }
.status-grid > div { display:flex;justify-content:space-between;align-items:center;min-height:36px;padding:0 9px;border:1px solid rgba(86,137,177,.14);border-radius:6px;background:rgba(7,25,40,.62);font-size:9px; }
.status-grid span { color:#7995ad; }.status-grid b { color:#dbeeff;font-size:10px; }.status-grid .ok { color:#54e492; }.status-grid .bad { color:#ff746e; }.status-grid .warn { color:#efba51; }.status-grid .standby { color:#f1c457;background:rgba(133,97,23,.22);padding:2px 5px;border-radius:4px; }
.prearm-alert { margin:0 10px 10px;display:flex;gap:10px;align-items:center;padding:9px;border:1px solid rgba(255,83,74,.48);border-radius:6px;background:rgba(128,31,29,.22); }
.prearm-alert > span { width:23px;height:23px;display:grid;place-items:center;border-radius:50%;background:#ef4b43;color:white;font-weight:900; }.prearm-alert div { display:grid;gap:2px; }.prearm-alert b { color:#ff766e;font-size:10px; }.prearm-alert small { color:#a87976;font-size:8px; }
.bridge-surface { padding:5px 10px; }
.bridge-row { display:grid;grid-template-columns:12px 1fr auto;align-items:center;gap:8px;padding:8px 2px; }.bridge-row + .bridge-row { border-top:1px solid rgba(89,138,178,.12); }.bridge-row .dot { width:7px;height:7px;border-radius:50%; }.dot.online { background:#43df84;box-shadow:0 0 10px #43df84; }.dot.demo { background:#e6b64d;box-shadow:0 0 8px rgba(230,182,77,.4); }.bridge-row div { display:grid;gap:1px; }.bridge-row b { font-size:9px; }.bridge-row small { color:#6e8da9;font-size:7px; }.bridge-row strong { color:#87a4bc;font-size:8px; }
.log-surface { flex:1;min-height:270px; }.clear-log { border:0;background:transparent;color:#6686a1;font-size:7px;cursor:pointer; }
.timeline { padding:8px 10px 12px;max-height:330px;overflow:auto; }.log-item { position:relative;display:grid;grid-template-columns:58px 1fr;gap:7px;padding:7px 3px 7px 18px;border-left:1px solid rgba(57,132,185,.34);margin-left:4px; }.timeline-dot { position:absolute;left:-4px;top:14px;width:7px;height:7px;border-radius:50%;background:#268ddd;box-shadow:0 0 8px rgba(38,141,221,.5); }.log-item.error .timeline-dot { background:#ff4f48; }.log-item.success .timeline-dot { background:#46d985; }.log-item.warn .timeline-dot { background:#ecb84f; }.log-item time { color:#809cb4;font-size:8px; }.log-item div { display:grid;gap:2px; }.log-item b { font-size:9px; }.log-item small { color:#6e8ba4;font-size:7px;line-height:1.4; }.empty-log { color:#597892;text-align:center;padding:30px 0;font-size:9px; }
.score-surface { display:grid;grid-template-columns:40px 112px 1fr;align-items:center;padding:12px; }.trophy { color:#f3c443;font-size:27px; }.score-surface > div { display:grid; }.score-surface small { color:#8aa4bb;font-size:8px; }.score-surface b { font-size:28px;color:#ffd163;line-height:1; }.score-surface b em { font-size:12px;color:#92aabe;font-style:normal;margin-left:3px; }.remaining { padding-left:12px;border-left:1px solid rgba(94,141,178,.18); }.remaining span { color:#7894ad;font-size:8px; }.remaining b { color:#94aec4;font-size:9px;line-height:1.4;margin-top:3px; }
.right-actions { display:grid;grid-template-columns:1fr 1fr;gap:8px; }.right-actions button,.flight-action { min-height:42px;display:grid;place-items:center;border-radius:6px;text-decoration:none;cursor:pointer;font-size:9px; }.right-actions button { border:1px solid rgba(110,155,193,.5);background:#10263a;color:#b7d2e8; }.flight-action { border:1px solid #2baeff;background:linear-gradient(180deg,#159eea,#0871b8);color:white;box-shadow:0 0 18px rgba(35,164,241,.17); }
@media(max-width:1450px){ .debug-page{grid-template-columns:220px minmax(620px,1fr) 350px}.scene-and-controls{grid-template-columns:minmax(0,1fr) 108px}.metric-grid{gap:7px;padding:9px}.debug-rightbar{padding:12px 9px}.debug-sidebar{padding-left:9px;padding-right:9px} }
@media(max-width:1180px){ .debug-page{grid-template-columns:190px minmax(590px,1fr)}.debug-rightbar{display:none}.power-layout{grid-template-columns:1fr}.parameter-surface{display:none}.lower-grid{grid-template-columns:1fr}.debug-sidebar{font-size:90%} }
</style>
