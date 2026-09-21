<template>
  <div class="workbench-grid flight-grid">
    <aside class="panel left-panel flight-control-panel">
      <section class="panel-section">
        <h3>{{ px4Mode ? 'PX4 飞行验证' : '实验控制' }}</h3>
        <div v-if="assignedRunId" :class="['course-flight-banner', { passed: flightValidationReported }]">
          <b>{{ flightValidationReported ? '课程飞行验证已记录' : '课程实训 · 飞行验证阶段' }}</b>
          <small>{{ flightValidationMessage || '按 解锁 → 起飞 → 悬停 → 降落 完成闭环，系统将自动回写 TrainingRun。' }}</small>
          <button v-if="flightLandCommanded && !flightValidationReported" :disabled="flightValidationReporting" @click="maybeReportFlightValidation">{{ flightValidationReporting ? '同步中…' : '重新同步飞行结果' }}</button>
        </div>

        <div class="control-block">
          <span class="control-label">{{ px4Mode ? '数据源' : '仿真' }}</span>

          <template v-if="px4Mode">
            <div class="source-banner" :class="{ live: px4Connected }">
              <span class="source-dot"></span>
              <div>
                <b>{{ px4Connected ? 'PX4 SIH · MAVLink' : 'PX4 SIH · 等待连接' }}</b>
                <small>{{ px4ConnectionDetail }}</small>
              </div>
            </div>
            <div class="button-grid">
              <button
                data-testid="px4-flight-connect"
                class="primary-blue"
                :disabled="busy || !flightReady"
                @click="performPx4(connectPx4)"
              >
                {{ px4Connected ? '刷新连接' : '连接 PX4' }}
              </button>
              <button
                :disabled="busy || !px4Connected"
                @click="performPx4(requestPx4Streams)"
              >
                请求遥测
              </button>
            </div>
            <div class="command-state">
              <span>Heartbeat</span>
              <b :class="px4Connected ? 'ok-text' : 'warn-text'">{{ heartbeatText }}</b>
            </div>
          </template>

          <template v-else>
            <div class="button-grid">
              <button data-testid="flight-start" class="primary-blue" :disabled="!demoControls.canStart" @click="performDemo(store.start)">开始</button>
              <button data-testid="flight-pause" :disabled="!demoControls.canPause" @click="performDemo(store.pause)">暂停</button>
              <button data-testid="flight-reset" :disabled="!demoControls.canReset" @click="performDemo(store.reset)">复位</button>
              <button data-testid="flight-stop" class="danger-button" :disabled="!demoControls.canStop" @click="performDemo(store.stop)">停止</button>
            </div>
            <div class="command-state"><span>仿真状态</span><b>{{ store.simulationStatusZh }}</b></div>
          </template>
        </div>

        <div class="control-block">
          <span class="control-label">飞行</span>

          <template v-if="px4Mode">
            <button
              data-testid="flight-arm"
              class="secondary-action"
              :disabled="!px4ArmButtonEnabled"
              @click="performPx4(togglePx4Arm)"
            >
              {{ activeTelemetry.armed ? '上锁' : '解锁' }}
            </button>
            <label class="field-row">
              <span>相对起飞高度</span>
              <div><input v-model.number="store.targetAltitude" type="number" min="0.5" max="30" step="0.5"/><em>m</em></div>
            </label>
            <div class="button-grid">
              <button
                data-testid="flight-takeoff"
                class="primary-blue"
                :disabled="!px4CanTakeoff"
                @click="performPx4(takeoffPx4)"
              >
                起飞
              </button>
              <button
                data-testid="flight-land"
                :disabled="!px4CanLand"
                @click="performPx4(landPx4)"
              >
                降落
              </button>
            </div>
          </template>

          <template v-else>
            <button data-testid="flight-arm" class="secondary-action" :disabled="!demoControls.canArm" @click="performDemo(store.arm)">{{ store.telemetry.armed ? '已解锁' : '解锁' }}</button>
            <label class="field-row"><span>目标高度</span><div><input v-model.number="store.targetAltitude" type="number" min="0.5" max="120" step="0.5"/><em>m</em></div></label>
            <div class="button-grid">
              <button data-testid="flight-takeoff" class="primary-blue" :disabled="!demoControls.canTakeoff" @click="performDemo(takeoffDemo)">起飞</button>
              <button data-testid="flight-land" :disabled="!demoControls.canLand" @click="performDemo(landDemo)">降落</button>
            </div>
          </template>

          <p class="flight-command-hint" data-testid="flight-command-hint">{{ flightCommandHint }}</p>
        </div>

        <div class="control-block">
          <span class="control-label">环境</span>
          <label class="field-row"><span>风速</span><div><input v-model.number="store.windSpeed" type="number" min="0" max="30" step="0.5"/><em>m/s</em></div></label>
          <label class="field-row"><span>风向</span><div><input v-model.number="store.windDirection" type="number" min="0" max="360" step="1"/><em>°</em></div></label>
          <button
            class="secondary-action"
            :disabled="px4Mode ? (!px4Connected || busy) : !demoControls.canApplyWind"
            @click="px4Mode ? performPx4(applyPx4Wind) : performDemo(store.applyWind)"
          >
            {{ px4Mode ? '写入 SIH 风场' : '应用风场' }}
          </button>
          <small v-if="px4Mode" class="control-note">PX4 模式写入 SIH_WIND_N / SIH_WIND_E；不再调用 UAV-Studio 自研动力学。</small>
        </div>

        <div v-if="!px4Mode" class="control-block">
          <span class="control-label">目标与航点</span>
          <p class="waypoint-hint">{{ pendingTarget ? `待应用目标：X ${pendingTarget.x.toFixed(1)} m / Y ${pendingTarget.y.toFixed(1)} m` : '在地图上点击可选取目标点' }}</p>
          <div class="button-grid">
            <button :disabled="!pendingTarget || !demoControls.canSetTarget" @click="performDemo(applyPendingTarget)">设为目标点</button>
            <button :disabled="!pendingTarget || store.simulationId === null || busy" @click="performDemo(addWaypoint)">添加航点</button>
          </div>
          <button class="ghost-action waypoint-clear" :disabled="store.waypoints.length === 0 || busy" @click="performDemo(clearWaypoints)">清空航点</button>
        </div>

        <div v-else class="control-block px4-scope">
          <span class="control-label">本阶段验证范围</span>
          <b>Arm → Takeoff → Hover → Land</b>
          <small>当前闭环只验证装调检修后的基础飞行能力。目标点与航点控制暂不伪装支持，后续再按教学任务扩展。</small>
        </div>
      </section>

      <section class="panel-section aircraft-summary">
        <h3>当前飞机</h3>
        <dl>
          <div><dt>名称</dt><dd>{{ assemblyStore.aircraftName }}</dd></div>
          <div><dt>构型</dt><dd>四旋翼 X 型</dd></div>
          <div><dt>总质量</dt><dd>{{ massText }}</dd></div>
          <div><dt>装配状态</dt><dd :class="assemblyReady ? 'ok-text' : 'warn-text'">{{ assemblyReady ? '已通过' : '未通过' }}</dd></div>
          <div><dt>起飞前检查</dt><dd :class="preflightReady ? 'ok-text' : 'warn-text'">{{ preflightReady ? '已通过' : '未通过' }}</dd></div>
          <div><dt>飞行数据源</dt><dd>{{ dataSourceText }}</dd></div>
          <div><dt>遥测连接</dt><dd :class="connectionText.includes('已连接') ? 'ok-text' : ''">{{ connectionText }}</dd></div>
        </dl>
      </section>
    </aside>

    <main class="stage-panel flight-stage">
      <div class="view-switch">
        <button :class="{ active: viewMode === '3d' }" @click="viewMode = '3d'">三维视图</button>
        <button :class="{ active: viewMode === 'map' }" @click="viewMode = 'map'">基础地图</button>
        <button :class="{ active: viewMode === 'split' }" @click="viewMode = 'split'">分屏</button>
        <span v-if="px4Mode" class="px4-live-chip" :class="{ connected: px4Connected }">
          <i></i>{{ px4Connected ? 'PX4 LIVE' : 'PX4 OFFLINE' }}
        </span>
      </div>

      <DroneScene
        v-if="viewMode === '3d'"
        :telemetry="activeTelemetry"
        :aircraft="assemblyStore.aircraft"
        :components="assemblyStore.components"
        :engineering="assemblyStore.engineering"
      />
      <LocalFlightMap
        v-else-if="viewMode === 'map'"
        :telemetry="activeTelemetry"
        :history="activeHistory"
        :target-position="px4Mode ? null : store.targetPosition"
        :waypoints="px4Mode ? [] : store.waypoints"
        :pending-target="px4Mode ? null : pendingTarget"
        :boundary-m="activeBoundaryM"
        :interactive="!px4Mode"
        @select-target="selectPendingTarget"
      />
      <div v-else class="split-stage">
        <div class="split-pane">
          <DroneScene
            :telemetry="activeTelemetry"
            :aircraft="assemblyStore.aircraft"
            :components="assemblyStore.components"
            :engineering="assemblyStore.engineering"
          />
        </div>
        <div class="split-pane">
          <LocalFlightMap
            :telemetry="activeTelemetry"
            :history="activeHistory"
            :target-position="px4Mode ? null : store.targetPosition"
            :waypoints="px4Mode ? [] : store.waypoints"
            :pending-target="px4Mode ? null : pendingTarget"
            :boundary-m="activeBoundaryM"
            :interactive="!px4Mode"
            @select-target="selectPendingTarget"
          />
        </div>
      </div>

      <div v-if="!assemblyReady && !assemblyStore.loading" class="stage-blocker">
        <b>装配检查未通过</b>
        <span>请返回无人机装配页处理阻断错误后再进行飞行实验。</span>
        <RouterLink to="/assembly">返回无人机装配</RouterLink>
      </div>
      <div v-else-if="!preflightReady && !assemblyStore.loading" class="stage-blocker preflight-blocker">
        <b>起飞前检查未通过或许可已失效</b>
        <span>飞行实验要求先完成飞控传感器、遥控、动力、安全设置与 Pre-Arm 六项门禁。</span>
        <RouterLink to="/debugging">返回系统调试 / 起飞前检查</RouterLink>
      </div>
      <div v-else-if="px4Mode && !px4Connected" class="stage-status-banner">
        <b>正在等待 PX4 SIH Heartbeat</b>
        <span>启动 PX4 SIH 与 Bridge 后，本页不会退回旧模拟器；连接成功后 Three.js 会直接跟随 PX4 遥测。</span>
      </div>
    </main>

    <aside class="panel inspector-panel">
      <section v-if="activeError" class="inspector-section command-error">{{ activeError }}</section>

      <section v-if="px4Mode" class="inspector-section px4-source-section">
        <h3>PX4 数据源</h3>
        <dl>
          <div><dt>System ID</dt><dd>{{ px4Telemetry?.system_id ?? '—' }}</dd></div>
          <div><dt>飞控模式</dt><dd>{{ px4Telemetry?.mode || '—' }}</dd></div>
          <div><dt>着陆状态</dt><dd>{{ landedText }}</dd></div>
          <div><dt>GPS</dt><dd>{{ px4Telemetry?.gps?.satellites ?? '—' }} 星</dd></div>
          <div><dt>AMSL</dt><dd>{{ amslText }}</dd></div>
          <div><dt>STATUSTEXT</dt><dd class="status-text">{{ px4Telemetry?.statustext || '—' }}</dd></div>
        </dl>
      </section>

      <section class="inspector-section">
        <h3>飞行状态</h3>
        <dl>
          <div><dt>模式</dt><dd>{{ activeFlightModeText }}</dd></div>
          <div><dt>解锁</dt><dd>{{ activeTelemetry.armed ? '已解锁' : '未解锁' }}</dd></div>
          <div><dt>高度</dt><dd>{{ activeTelemetry.position.z.toFixed(2) }} m</dd></div>
          <div><dt>垂向速度</dt><dd>{{ activeTelemetry.velocity.z.toFixed(2) }} m/s</dd></div>
          <div><dt>总推力</dt><dd>{{ activeTelemetry.forces.total_thrust_n.toFixed(1) }} N</dd></div>
          <div><dt>重力</dt><dd>{{ activeTelemetry.forces.gravity_n.toFixed(1) }} N</dd></div>
        </dl>
      </section>

      <section class="inspector-section">
        <h3>位置 / 速度</h3>
        <dl>
          <div><dt>X / Y</dt><dd>{{ activeTelemetry.position.x.toFixed(2) }} / {{ activeTelemetry.position.y.toFixed(2) }} m</dd></div>
          <div><dt>VX / VY</dt><dd>{{ activeTelemetry.velocity.x.toFixed(2) }} / {{ activeTelemetry.velocity.y.toFixed(2) }} m/s</dd></div>
          <div><dt>水平速度</dt><dd>{{ horizontalSpeed.toFixed(2) }} m/s</dd></div>
        </dl>
      </section>

      <section class="inspector-section">
        <h3>姿态</h3>
        <dl>
          <div><dt>横滚</dt><dd>{{ deg(activeTelemetry.attitude.roll) }}°</dd></div>
          <div><dt>俯仰</dt><dd>{{ deg(activeTelemetry.attitude.pitch) }}°</dd></div>
          <div><dt>偏航</dt><dd>{{ deg(activeTelemetry.attitude.yaw) }}°</dd></div>
          <div><dt>P / Q / R</dt><dd>{{ activeTelemetry.angular_velocity.p.toFixed(3) }} / {{ activeTelemetry.angular_velocity.q.toFixed(3) }} / {{ activeTelemetry.angular_velocity.r.toFixed(3) }}</dd></div>
        </dl>
      </section>

      <section class="inspector-section">
        <h3>动力 / 电源</h3>
        <dl>
          <div><dt>剩余电量</dt><dd>{{ batteryPercent }}%</dd></div>
          <div><dt>电压</dt><dd>{{ activeTelemetry.power.voltage_v.toFixed(2) }} V</dd></div>
          <div><dt>电流</dt><dd>{{ activeTelemetry.power.current_a.toFixed(2) }} A</dd></div>
          <div><dt>估算功率</dt><dd>{{ powerText }}</dd></div>
        </dl>
      </section>

      <section class="inspector-section motor-section">
        <h3>四电机</h3>
        <table>
          <thead><tr><th>电机</th><th>输出</th><th>推力估计</th></tr></thead>
          <tbody>
            <tr v-for="(_, index) in activeTelemetry.motors.outputs" :key="index">
              <td><span :class="['motor-dot', `m${index + 1}`]"></span>M{{ index + 1 }}</td>
              <td>{{ (activeTelemetry.motors.outputs[index] * 100).toFixed(1) }}%</td>
              <td>{{ activeTelemetry.motors.thrusts_n[index].toFixed(2) }} N</td>
            </tr>
          </tbody>
        </table>
      </section>
    </aside>

    <section class="bottom-panel">
      <RealtimeCharts
        :telemetry="activeTelemetry"
        :history="activeHistory"
        :window-seconds="settingsStore.settings.flight.chart_window_seconds"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import DroneScene from '../components/DroneScene.vue'
import LocalFlightMap from '../components/LocalFlightMap.vue'
import RealtimeCharts from '../components/RealtimeCharts.vue'
import { px4Api, type Px4CommandResult, type Px4Telemetry } from '../api/px4'
import { studentTrainingApi } from '../api/teacher'
import { useAssemblyStore } from '../stores/assembly'
import { useSimulationStore } from '../stores/simulation'
import { useSettingsStore } from '../stores/settings'
import type { TelemetryFrame } from '../types/telemetry'
import { flightControlAvailability } from '../utils/flightControlGuards'
import { aircraftFingerprint, loadPreflightSnapshot, type PreflightSnapshot } from '../utils/preflight'
import { landedStateText, px4IsAirborne, px4TelemetryToFrame } from '../utils/px4Flight'
import { flightValidationReady } from '../utils/trainingFlow'

const route = useRoute()
const assemblyStore = useAssemblyStore()
const store = useSimulationStore()
const settingsStore = useSettingsStore()

const viewMode = ref<'3d' | 'map' | 'split'>(settingsStore.settings.flight.default_view)
const busy = ref(false)
const pendingTarget = ref<{ x: number; y: number } | null>(null)
const preflightSnapshot = ref<PreflightSnapshot | null>(null)

const px4Telemetry = ref<Px4Telemetry | null>(null)
const px4History = ref<TelemetryFrame[]>([])
const px4Frame = ref<TelemetryFrame>(blankTelemetry())
const px4Error = ref('')
const px4SessionStartedAt = ref<number | null>(null)
const px4StreamsRequested = ref(false)
let px4PollTimer: number | null = null
let px4Polling = false

const assignedRunId = computed(() => {
  const raw = Array.isArray(route.query.run) ? route.query.run[0] : route.query.run
  const value = Number(raw)
  return Number.isInteger(value) && value > 0 ? value : null
})
const flightTakeoffObserved = ref(false)
const flightHoverObserved = ref(false)
const flightLandCommanded = ref(false)
const flightValidationReported = ref(false)
const flightValidationReporting = ref(false)
const flightValidationMessage = ref('')

const assemblyReady = computed(() => assemblyStore.validation.passed && assemblyStore.engineering !== null)
const preflightReady = computed(() => Boolean(preflightSnapshot.value?.passed))
const flightReady = computed(() => assemblyReady.value && preflightReady.value)
const px4Mode = computed(() => preflightSnapshot.value?.bridge_mode === 'live')
const px4Connected = computed(() => Boolean(px4Telemetry.value?.connected))
const px4Airborne = computed(() => px4IsAirborne(px4Telemetry.value))
const activeAirborne = computed(() => px4Mode.value ? px4Airborne.value : store.airborne)

const demoControls = computed(() => flightControlAvailability({
  assemblyReady: flightReady.value,
  busy: busy.value,
  simulationId: store.simulationId,
  simulationStatus: store.simulationStatus,
  armed: store.telemetry.armed,
  flightMode: store.telemetry.flight_mode,
  airborne: store.airborne,
}))

const activeTelemetry = computed(() => px4Mode.value ? px4Frame.value : store.telemetry)
const activeHistory = computed(() => px4Mode.value ? px4History.value : store.history)
const activeBoundaryM = computed(() => px4Mode.value ? 25 : store.boundaryM)
const activeError = computed(() => px4Mode.value ? px4Error.value : store.error)
const activeFlightModeText = computed(() => px4Mode.value
  ? (px4Telemetry.value?.mode || flightModeFallback(activeTelemetry.value.flight_mode))
  : store.flightModeZh,
)

const px4ArmButtonEnabled = computed(() => {
  if (!flightReady.value || !px4Connected.value || busy.value) return false
  if (activeTelemetry.value.armed && px4Airborne.value) return false
  return true
})
const px4CanTakeoff = computed(() =>
  flightReady.value
  && px4Connected.value
  && !busy.value
  && activeTelemetry.value.armed
  && !px4Airborne.value,
)
const px4CanLand = computed(() =>
  flightReady.value
  && px4Connected.value
  && !busy.value
  && activeTelemetry.value.armed
  && px4Airborne.value,
)

const flightCommandHint = computed(() => {
  if (!assemblyReady.value) return '先通过装配检查，才能进行飞行验证。'
  if (!preflightReady.value) return '先完成系统调试页的起飞前检查并生成飞行许可。'

  if (px4Mode.value) {
    if (!px4Connected.value) return '当前许可来自真实 PX4 调试流程：请启动 PX4 SIH 与 Bridge，等待 Heartbeat。'
    if (!activeTelemetry.value.armed) return 'PX4 已连接：先解锁，再执行起飞。'
    if (!px4Airborne.value) return 'PX4 已解锁：设置相对高度后执行 Takeoff。'
    if (activeTelemetry.value.flight_mode === 'LANDING') return 'PX4 正在执行降落，等待着陆状态返回地面。'
    return 'PX4 飞行验证进行中：Three.js、地图和曲线均来自 MAVLink 遥测。'
  }

  if (store.simulationStatus !== 'RUNNING') return '先点击“开始”启动教学仿真，再进行解锁。'
  if (!store.telemetry.armed) return '仿真已运行：请先“解锁”，解锁后“起飞”才会启用。'
  if (store.telemetry.flight_mode === 'ARMED') return '已解锁：可以设置目标高度并起飞。'
  if (store.telemetry.flight_mode === 'TAKING_OFF') return '正在起飞：起飞按钮锁定，可执行降落。'
  if (store.telemetry.flight_mode === 'HOVERING') return '正在悬停：可调整环境、目标点，或执行降落。'
  if (store.telemetry.flight_mode === 'LANDING') return '正在降落：等待返回待机并自动上锁。'
  return '按 开始 → 解锁 → 起飞 → 降落 的顺序操作。'
})

const massText = computed(() => assemblyStore.engineering ? `${assemblyStore.engineering.total_mass_kg.toFixed(3)} kg` : '等待工程计算')
const horizontalSpeed = computed(() => Math.hypot(activeTelemetry.value.velocity.x, activeTelemetry.value.velocity.y))
const powerText = computed(() => activeTelemetry.value.power.estimated_power_w >= 1000
  ? `${(activeTelemetry.value.power.estimated_power_w / 1000).toFixed(2)} kW`
  : `${activeTelemetry.value.power.estimated_power_w.toFixed(0)} W`)
const batteryPercent = computed(() => Math.round(activeTelemetry.value.power.battery_remaining * 100))
const dataSourceText = computed(() => px4Mode.value ? 'PX4 SIH / MAVLink' : 'UAV-Studio Simple Simulator')
const connectionText = computed(() => {
  if (px4Mode.value) return px4Connected.value ? 'PX4 已连接' : 'PX4 未连接'
  return store.connectionStatus === 'CONNECTED' ? '已连接' : store.connectionStatus === 'CONNECTING' ? '连接中' : '未连接'
})
const heartbeatText = computed(() => {
  const age = px4Telemetry.value?.heartbeat_age_s
  if (!px4Connected.value || typeof age !== 'number') return '等待'
  return `${age.toFixed(2)} s`
})
const px4ConnectionDetail = computed(() => {
  if (px4Connected.value) return `${px4Telemetry.value?.connection_url || 'MAVLink'} · SYSID ${px4Telemetry.value?.system_id ?? '—'}`
  return px4Error.value || '不会回退到旧模拟器'
})
const landedText = computed(() => landedStateText(px4Telemetry.value?.landed_state))
const amslText = computed(() => {
  const value = px4Telemetry.value?.global_position?.alt_amsl_m
  return typeof value === 'number' && Number.isFinite(value) ? `${value.toFixed(1)} m` : '—'
})

onMounted(async () => {
  await Promise.all([assemblyStore.initialize(), settingsStore.initialize()])
  preflightSnapshot.value = loadPreflightSnapshot(
    assemblyStore.activeAircraftId,
    aircraftFingerprint(assemblyStore.aircraft),
  )
  viewMode.value = settingsStore.settings.flight.default_view

  if (assignedRunId.value) {
    try {
      const detail = await studentTrainingApi.runDetail(assignedRunId.value)
      flightValidationReported.value = detail.run.flight_validation_passed
      flightValidationMessage.value = detail.run.flight_validation_passed
        ? `已通过 · 当前课程成绩 ${detail.run.score ?? '—'}`
        : `当前阶段：${detail.run.stage}`
    } catch (error) {
      flightValidationMessage.value = error instanceof Error ? error.message : String(error)
    }
  }

  if (px4Mode.value) {
    store.targetAltitude = 2
    store.windSpeed = 0
    store.windDirection = 0
    await connectPx4().catch(() => { /* actionable error is displayed in page */ })
    return
  }

  if (store.simulationId === null) {
    store.targetAltitude = settingsStore.settings.flight.default_altitude_m
    store.windSpeed = settingsStore.settings.flight.default_wind_speed_mps
    store.windDirection = settingsStore.settings.flight.default_wind_direction_deg
    if (settingsStore.settings.flight.auto_create_simulation && flightReady.value) {
      try { await store.createSimulation() } catch { /* store exposes the error */ }
    }
  }
})

onBeforeUnmount(async () => {
  stopPx4Polling()
  if (!px4Mode.value) {
    if (store.simulationStatus === 'RUNNING') {
      try { await store.pause() } catch { /* closing */ }
    }
    store.disconnectTelemetry()
  }
})

function blankTelemetry(): TelemetryFrame {
  return {
    t: 0,
    position: { x: 0, y: 0, z: 0 },
    velocity: { x: 0, y: 0, z: 0 },
    attitude: { roll: 0, pitch: 0, yaw: 0 },
    angular_velocity: { p: 0, q: 0, r: 0 },
    center_of_gravity: { x: 0, y: 0, z: 0 },
    motors: { outputs: [0, 0, 0, 0], thrusts_n: [0, 0, 0, 0] },
    forces: { gravity_n: 0, total_thrust_n: 0 },
    wind: { speed_mps: 0, direction_deg: 0 },
    power: { estimated_power_w: 0, battery_remaining: 1, voltage_v: 0, current_a: 0 },
    armed: false,
    flight_mode: 'IDLE',
  }
}

function flightModeFallback(mode: TelemetryFrame['flight_mode']): string {
  const labels: Record<TelemetryFrame['flight_mode'], string> = {
    IDLE: '待机',
    ARMED: '已解锁',
    TAKING_OFF: '起飞中',
    HOVERING: '空中',
    LANDING: '降落中',
  }
  return labels[mode]
}

async function performDemo(action: () => Promise<void>): Promise<void> {
  if (busy.value) return
  busy.value = true
  try { await action() } catch { /* store exposes */ } finally { busy.value = false }
}

async function performPx4(action: () => Promise<void>): Promise<void> {
  if (busy.value) return
  busy.value = true
  px4Error.value = ''
  try {
    await action()
  } catch (error) {
    px4Error.value = error instanceof Error ? error.message : String(error)
  } finally {
    busy.value = false
  }
}

function ensureAccepted(result: Px4CommandResult, action: string): void {
  if (result.accepted === false) {
    if (result.timeout) throw new Error(`${action}超时，PX4 未返回 COMMAND_ACK`)
    throw new Error(`${action}被 PX4 拒绝（result=${String(result.result ?? 'unknown')}）`)
  }
}

async function connectPx4(): Promise<void> {
  px4Error.value = ''
  let status
  try {
    status = await px4Api.status()
  } catch {
    // Bridge may be running but not initialized yet; use connect for a single retry.
    status = await px4Api.connect()
  }

  if (!status.running || !status.connected) {
    try { await px4Api.connect() } catch { /* polling below reports the current state */ }
  }

  startPx4Polling()
  await delay(350)
  await pollPx4()

  if (px4Telemetry.value?.connected) {
    await requestPx4Streams()
  } else {
    px4Error.value = px4Telemetry.value?.last_error || 'Bridge 已启动，但尚未收到 PX4 Heartbeat'
  }
}

async function requestPx4Streams(): Promise<void> {
  if (!px4Connected.value) throw new Error('PX4 尚未连接，无法请求遥测流')
  await px4Api.requestStreams()
  px4StreamsRequested.value = true
  await pollPx4()
}

function startPx4Polling(): void {
  if (px4PollTimer !== null) return
  px4PollTimer = window.setInterval(() => { void pollPx4() }, 100)
}

function stopPx4Polling(): void {
  if (px4PollTimer !== null) {
    window.clearInterval(px4PollTimer)
    px4PollTimer = null
  }
}

async function pollPx4(): Promise<void> {
  if (px4Polling) return
  px4Polling = true
  try {
    const telemetry = await px4Api.telemetry()
    px4Telemetry.value = telemetry

    if (telemetry.connected && px4SessionStartedAt.value === null) {
      px4SessionStartedAt.value = performance.now()
      px4History.value = []
    }

    if (telemetry.connected && !px4StreamsRequested.value) {
      void px4Api.requestStreams()
        .then(() => { px4StreamsRequested.value = true })
        .catch(() => { /* next poll will keep trying via manual action */ })
    }

    const startedAt = px4SessionStartedAt.value ?? performance.now()
    const elapsedS = Math.max(0, (performance.now() - startedAt) / 1000)
    const frame = px4TelemetryToFrame(
      telemetry,
      elapsedS,
      assemblyStore.engineering,
      { windSpeedMps: store.windSpeed, windDirectionDeg: store.windDirection },
    )
    px4Frame.value = frame

    const last = px4History.value[px4History.value.length - 1]
    if (!last || frame.t - last.t >= 0.08 || frame.t < last.t) {
      px4History.value.push(frame)
      if (px4History.value.length > 2400) {
        px4History.value.splice(0, px4History.value.length - 2400)
      }
    }

    if (telemetry.connected) px4Error.value = ''
  } catch (error) {
    px4Error.value = error instanceof Error ? error.message : String(error)
  } finally {
    px4Polling = false
  }
}

async function togglePx4Arm(): Promise<void> {
  if (activeTelemetry.value.armed) {
    if (px4Airborne.value) throw new Error('飞机仍处于空中，禁止直接上锁；请先执行降落')
    const result = await px4Api.disarm()
    ensureAccepted(result, 'PX4 上锁')
  } else {
    const result = await px4Api.arm()
    ensureAccepted(result, 'PX4 解锁')
  }
  await delay(300)
  await pollPx4()
}

async function takeoffPx4(): Promise<void> {
  const altitude = Number(store.targetAltitude)
  if (!Number.isFinite(altitude) || altitude < 0.5 || altitude > 30) {
    throw new Error('PX4 相对起飞高度必须在 0.5-30 m')
  }
  const result = await px4Api.takeoff(altitude)
  ensureAccepted(result, 'PX4 起飞')
  await delay(350)
  await pollPx4()
}

async function landPx4(): Promise<void> {
  const result = await px4Api.land()
  ensureAccepted(result, 'PX4 降落')
  flightLandCommanded.value = true
  await delay(350)
  await pollPx4()
}

async function applyPx4Wind(): Promise<void> {
  const speed = Math.max(0, Number(store.windSpeed) || 0)
  const direction = ((Number(store.windDirection) || 0) % 360 + 360) % 360
  const radians = direction * Math.PI / 180
  const north = speed * Math.cos(radians)
  const east = speed * Math.sin(radians)
  await px4Api.setParameter('SIH_WIND_N', north)
  await px4Api.setParameter('SIH_WIND_E', east)
  await pollPx4()
}

async function takeoffDemo(): Promise<void> {
  await store.takeoff()
}

async function landDemo(): Promise<void> {
  await store.land()
  flightLandCommanded.value = true
}

async function maybeReportFlightValidation(): Promise<void> {
  if (!assignedRunId.value || flightValidationReported.value || flightValidationReporting.value) return
  const ready = flightValidationReady({
    takeoffObserved: flightTakeoffObserved.value,
    hoverObserved: flightHoverObserved.value,
    landCommanded: flightLandCommanded.value,
    airborne: activeAirborne.value,
    landedState: px4Mode.value ? px4Telemetry.value?.landed_state : null,
    armed: activeTelemetry.value.armed,
  })
  if (!ready) return
  flightValidationReporting.value = true
  try {
    const run = await studentTrainingApi.flightValidation(
      assignedRunId.value,
      true,
      `${px4Mode.value ? 'PX4 SIH' : '教学模拟'}：起飞 → 悬停 → 降落验证完成`,
    )
    flightValidationReported.value = true
    flightValidationMessage.value = `闭环完成 · 最终课程成绩 ${run.score ?? '—'}/100`
  } catch (error) {
    flightValidationMessage.value = `飞行结果回写失败：${error instanceof Error ? error.message : String(error)}`
  } finally {
    flightValidationReporting.value = false
  }
}

watch(activeAirborne, airborne => {
  if (airborne) flightTakeoffObserved.value = true
  void maybeReportFlightValidation()
})
watch(() => activeTelemetry.value.flight_mode, mode => {
  if (mode === 'HOVERING') flightHoverObserved.value = true
  void maybeReportFlightValidation()
})
watch(() => activeTelemetry.value.armed, () => { void maybeReportFlightValidation() })

async function applyPendingTarget(): Promise<void> {
  if (pendingTarget.value) await store.setTarget(pendingTarget.value.x, pendingTarget.value.y)
}

function selectPendingTarget(target: { x: number; y: number }): void {
  if (!px4Mode.value) pendingTarget.value = target
}

async function addWaypoint(): Promise<void> {
  if (!pendingTarget.value) return
  await store.setWaypoints([
    ...store.waypoints,
    { x: pendingTarget.value.x, y: pendingTarget.value.y, z: store.targetAltitude },
  ])
}

async function clearWaypoints(): Promise<void> {
  await store.setWaypoints([])
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => window.setTimeout(resolve, ms))
}

function deg(radians: number): string {
  return ((radians * 180) / Math.PI).toFixed(2)
}
</script>

<style scoped>
.course-flight-banner {
  display:grid; gap:3px; margin:0 0 9px; padding:9px 10px; border:1px solid #e6c978;
  border-radius:8px; background:#fff9e8; color:#7c5b12;
}
.course-flight-banner.passed { border-color:#b9dfc8; background:#effaf4; color:#247148; }
.course-flight-banner b { font-size:9px; }
.course-flight-banner small { font-size:8px; line-height:1.45; }
.course-flight-banner button { justify-self:start; margin-top:3px; border:1px solid currentColor; border-radius:6px; background:transparent; color:inherit; padding:4px 7px; font-size:7px; cursor:pointer; }
.flight-control-panel button:disabled {
  cursor:not-allowed!important;
  opacity:1!important;
  color:#98a4b3!important;
  background:#edf1f5!important;
  border-color:#d8e0ea!important;
  box-shadow:none!important;
  filter:none!important;
  transform:none!important;
}
.flight-control-panel .primary-blue:disabled,
.flight-control-panel .danger-button:disabled,
.flight-control-panel .secondary-action:disabled {
  color:#98a4b3!important;
  background:#edf1f5!important;
  border-color:#d8e0ea!important;
}
.flight-command-hint {
  margin:8px 0 0;
  min-height:30px;
  padding:7px 9px;
  border:1px solid #e1e7ef;
  border-radius:6px;
  background:#f8fafc;
  color:#64748b;
  font-size:10px;
  line-height:1.45;
}
.preflight-blocker { background:rgba(255,250,245,.96); }
.source-banner {
  display:flex;
  align-items:center;
  gap:9px;
  margin-bottom:8px;
  padding:8px 9px;
  border:1px solid #e0e7ef;
  border-radius:8px;
  background:#f8fafc;
}
.source-banner.live { border-color:#bfe7ce; background:#f3fbf6; }
.source-dot {
  width:8px;
  height:8px;
  flex:0 0 auto;
  border-radius:50%;
  background:#f0ad4e;
  box-shadow:0 0 0 4px rgba(240,173,78,.12);
}
.source-banner.live .source-dot {
  background:#22a45d;
  box-shadow:0 0 0 4px rgba(34,164,93,.12);
}
.source-banner div { min-width:0; display:grid; gap:2px; }
.source-banner b { color:#26364d; font-size:10px; }
.source-banner small { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#728197; font-size:8px; }
.control-note, .px4-scope small { display:block; margin-top:6px; color:#728197; font-size:9px; line-height:1.45; }
.px4-scope { display:grid; gap:5px; }
.px4-scope b { color:#24476d; font-size:10px; }
.px4-live-chip {
  display:inline-flex;
  align-items:center;
  gap:5px;
  margin-left:auto;
  height:25px;
  padding:0 8px;
  border:1px solid rgba(212,159,54,.28);
  border-radius:999px;
  background:rgba(245,185,62,.08);
  color:#986c16;
  font-size:8px;
  font-weight:800;
}
.px4-live-chip.connected { border-color:rgba(48,168,100,.28); background:rgba(48,168,100,.08); color:#1d8150; }
.px4-live-chip i { width:6px; height:6px; border-radius:50%; background:currentColor; }
.stage-status-banner {
  position:absolute;
  z-index:9;
  left:50%;
  bottom:18px;
  transform:translateX(-50%);
  display:grid;
  gap:3px;
  width:min(560px,calc(100% - 40px));
  padding:9px 12px;
  border:1px solid #f0d49b;
  border-radius:10px;
  background:rgba(255,251,237,.94);
  color:#805f1b;
  box-shadow:0 8px 20px rgba(86,64,19,.08);
  pointer-events:none;
}
.stage-status-banner b { font-size:11px; }
.stage-status-banner span { font-size:9px; line-height:1.4; }
.px4-source-section { border-color:#cde8da; }
.status-text { max-width:150px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
</style>
