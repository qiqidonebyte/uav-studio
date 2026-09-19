<template>
  <div class="workbench-grid flight-grid">
    <aside class="panel left-panel flight-control-panel">
      <section class="panel-section">
        <h3>实验控制</h3>
        <div class="control-block">
          <span class="control-label">仿真</span>
          <div class="button-grid">
            <button
              data-testid="flight-start"
              class="primary-blue"
              :disabled="!controls.canStart"
              @click="perform(store.start)"
            >
              开始
            </button>
            <button
              data-testid="flight-pause"
              :disabled="!controls.canPause"
              @click="perform(store.pause)"
            >
              暂停
            </button>
            <button
              data-testid="flight-reset"
              :disabled="!controls.canReset"
              @click="perform(store.reset)"
            >
              复位
            </button>
            <button
              data-testid="flight-stop"
              class="danger-button"
              :disabled="!controls.canStop"
              @click="perform(store.stop)"
            >
              停止
            </button>
          </div>
          <div class="command-state">
            <span>仿真状态</span>
            <b>{{ store.simulationStatusZh }}</b>
          </div>
        </div>

        <div class="control-block">
          <span class="control-label">飞行</span>
          <button
            data-testid="flight-arm"
            class="secondary-action"
            :disabled="!controls.canArm"
            @click="perform(store.arm)"
          >
            {{ store.telemetry.armed ? '已解锁' : '解锁' }}
          </button>
          <label class="field-row">
            <span>目标高度</span>
            <div><input v-model.number="store.targetAltitude" type="number" min="0.5" max="120" step="0.5"/><em>m</em></div>
          </label>
          <div class="button-grid">
            <button
              data-testid="flight-takeoff"
              class="primary-blue"
              :disabled="!controls.canTakeoff"
              @click="perform(store.takeoff)"
            >
              起飞
            </button>
            <button
              data-testid="flight-land"
              :disabled="!controls.canLand"
              @click="perform(store.land)"
            >
              降落
            </button>
          </div>
          <p class="flight-command-hint" data-testid="flight-command-hint">
            {{ flightCommandHint }}
          </p>
        </div>

        <div class="control-block">
          <span class="control-label">环境</span>
          <label class="field-row">
            <span>风速</span>
            <div><input v-model.number="store.windSpeed" type="number" min="0" max="30" step="0.5"/><em>m/s</em></div>
          </label>
          <label class="field-row">
            <span>风向</span>
            <div><input v-model.number="store.windDirection" type="number" min="0" max="360" step="1"/><em>°</em></div>
          </label>
          <button
            class="secondary-action"
            :disabled="!controls.canApplyWind"
            @click="perform(store.applyWind)"
          >
            应用风场
          </button>
        </div>

        <div class="control-block">
          <span class="control-label">目标与航点</span>
          <p class="waypoint-hint">
            {{ pendingTarget ? `待应用目标：X ${pendingTarget.x.toFixed(1)} m / Y ${pendingTarget.y.toFixed(1)} m` : '在地图上点击可选取目标点' }}
          </p>
          <div class="button-grid">
            <button
              :disabled="!pendingTarget || !controls.canSetTarget"
              @click="perform(applyPendingTarget)"
            >
              设为目标点
            </button>
            <button
              :disabled="!pendingTarget || store.simulationId === null || busy"
              @click="perform(addWaypoint)"
            >
              添加航点
            </button>
          </div>
          <button
            class="ghost-action waypoint-clear"
            :disabled="store.waypoints.length === 0 || busy"
            @click="perform(clearWaypoints)"
          >
            清空航点
          </button>
        </div>
      </section>

      <section class="panel-section aircraft-summary">
        <h3>当前飞机</h3>
        <dl>
          <div><dt>名称</dt><dd>{{ assemblyStore.aircraftName }}</dd></div>
          <div><dt>构型</dt><dd>四旋翼 X 型</dd></div>
          <div><dt>总质量</dt><dd>{{ massText }}</dd></div>
          <div><dt>装配状态</dt><dd :class="assemblyReady ? 'ok-text' : 'warn-text'">{{ assemblyReady ? '已通过' : '未通过' }}</dd></div>
          <div><dt>遥测连接</dt><dd>{{ connectionText }}</dd></div>
        </dl>
      </section>
    </aside>

    <main class="stage-panel flight-stage">
      <div class="view-switch">
        <button :class="{ active: viewMode === '3d' }" @click="viewMode = '3d'">三维视图</button>
        <button :class="{ active: viewMode === 'map' }" @click="viewMode = 'map'">基础地图</button>
        <button :class="{ active: viewMode === 'split' }" @click="viewMode = 'split'">分屏</button>
      </div>
      <DroneScene
        v-if="viewMode === '3d'"
        :telemetry="store.telemetry"
        :aircraft="assemblyStore.aircraft"
        :components="assemblyStore.components"
        :engineering="assemblyStore.engineering"
      />
      <LocalFlightMap
        v-else-if="viewMode === 'map'"
        :telemetry="store.telemetry"
        :history="store.history"
        :target-position="store.targetPosition"
        :waypoints="store.waypoints"
        :pending-target="pendingTarget"
        :boundary-m="store.boundaryM"
        interactive
        @select-target="selectPendingTarget"
      />
      <div v-else class="split-stage">
        <div class="split-pane">
          <DroneScene
            :telemetry="store.telemetry"
            :aircraft="assemblyStore.aircraft"
            :components="assemblyStore.components"
            :engineering="assemblyStore.engineering"
          />
        </div>
        <div class="split-pane">
          <LocalFlightMap
            :telemetry="store.telemetry"
            :history="store.history"
            :target-position="store.targetPosition"
            :waypoints="store.waypoints"
            :pending-target="pendingTarget"
            :boundary-m="store.boundaryM"
            interactive
            @select-target="selectPendingTarget"
          />
        </div>
      </div>
      <div v-if="!assemblyReady && !assemblyStore.loading" class="stage-blocker">
        <b>装配检查未通过</b>
        <span>请返回无人机装配页处理阻断错误后再进行飞行实验。</span>
        <RouterLink to="/assembly">返回无人机装配</RouterLink>
      </div>
    </main>

    <aside class="panel inspector-panel">
      <section v-if="store.error" class="inspector-section command-error">
        {{ store.error }}
      </section>

      <section class="inspector-section">
        <h3>飞行状态</h3>
        <dl>
          <div><dt>模式</dt><dd>{{ store.flightModeZh }}</dd></div>
          <div><dt>解锁</dt><dd>{{ store.telemetry.armed ? '已解锁' : '未解锁' }}</dd></div>
          <div><dt>高度</dt><dd>{{ store.telemetry.position.z.toFixed(2) }} m</dd></div>
          <div><dt>垂向速度</dt><dd>{{ store.telemetry.velocity.z.toFixed(2) }} m/s</dd></div>
          <div><dt>总推力</dt><dd>{{ store.telemetry.forces.total_thrust_n.toFixed(1) }} N</dd></div>
          <div><dt>重力</dt><dd>{{ store.telemetry.forces.gravity_n.toFixed(1) }} N</dd></div>
        </dl>
      </section>

      <section class="inspector-section">
        <h3>位置 / 速度</h3>
        <dl>
          <div><dt>X / Y</dt><dd>{{ store.telemetry.position.x.toFixed(2) }} / {{ store.telemetry.position.y.toFixed(2) }} m</dd></div>
          <div><dt>VX / VY</dt><dd>{{ store.telemetry.velocity.x.toFixed(2) }} / {{ store.telemetry.velocity.y.toFixed(2) }} m/s</dd></div>
          <div><dt>水平速度</dt><dd>{{ horizontalSpeed.toFixed(2) }} m/s</dd></div>
        </dl>
      </section>

      <section class="inspector-section">
        <h3>姿态</h3>
        <dl>
          <div><dt>横滚</dt><dd>{{ deg(store.telemetry.attitude.roll) }}°</dd></div>
          <div><dt>俯仰</dt><dd>{{ deg(store.telemetry.attitude.pitch) }}°</dd></div>
          <div><dt>偏航</dt><dd>{{ deg(store.telemetry.attitude.yaw) }}°</dd></div>
          <div><dt>P / Q / R</dt><dd>{{ store.telemetry.angular_velocity.p.toFixed(3) }} / {{ store.telemetry.angular_velocity.q.toFixed(3) }} / {{ store.telemetry.angular_velocity.r.toFixed(3) }}</dd></div>
        </dl>
      </section>

      <section class="inspector-section">
        <h3>动力 / 电源</h3>
        <dl>
          <div><dt>剩余电量</dt><dd>{{ store.batteryPercent }}%</dd></div>
          <div><dt>电压</dt><dd>{{ store.telemetry.power.voltage_v.toFixed(2) }} V</dd></div>
          <div><dt>电流</dt><dd>{{ store.telemetry.power.current_a.toFixed(2) }} A</dd></div>
          <div><dt>估算功率</dt><dd>{{ powerText }}</dd></div>
        </dl>
      </section>

      <section class="inspector-section motor-section">
        <h3>四电机</h3>
        <table>
          <thead><tr><th>电机</th><th>输出</th><th>推力</th></tr></thead>
          <tbody>
            <tr v-for="(_, index) in store.telemetry.motors.outputs" :key="index">
              <td><span :class="['motor-dot', `m${index + 1}`]"></span>M{{ index + 1 }}</td>
              <td>{{ (store.telemetry.motors.outputs[index] * 100).toFixed(1) }}%</td>
              <td>{{ store.telemetry.motors.thrusts_n[index].toFixed(2) }} N</td>
            </tr>
          </tbody>
        </table>
      </section>
    </aside>

    <section class="bottom-panel">
      <RealtimeCharts :telemetry="store.telemetry" :history="store.history" :window-seconds="settingsStore.settings.flight.chart_window_seconds" />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import DroneScene from '../components/DroneScene.vue'
import LocalFlightMap from '../components/LocalFlightMap.vue'
import RealtimeCharts from '../components/RealtimeCharts.vue'
import { useAssemblyStore } from '../stores/assembly'
import { useSimulationStore } from '../stores/simulation'
import { useSettingsStore } from '../stores/settings'
import { flightControlAvailability } from '../utils/flightControlGuards'

const assemblyStore = useAssemblyStore()
const store = useSimulationStore()
const settingsStore = useSettingsStore()
const viewMode = ref<'3d' | 'map' | 'split'>(settingsStore.settings.flight.default_view)
const busy = ref(false)
const pendingTarget = ref<{ x: number; y: number } | null>(null)

const assemblyReady = computed(
  () => assemblyStore.validation.passed && assemblyStore.engineering !== null,
)
const controls = computed(() =>
  flightControlAvailability({
    assemblyReady: assemblyReady.value,
    busy: busy.value,
    simulationId: store.simulationId,
    simulationStatus: store.simulationStatus,
    armed: store.telemetry.armed,
    flightMode: store.telemetry.flight_mode,
    airborne: store.airborne,
  }),
)
const flightCommandHint = computed(() => {
  if (!assemblyReady.value) return '先通过装配检查，才能开始飞行实验。'
  if (store.simulationStatus !== 'RUNNING') return '先点击“开始”启动仿真，再进行解锁。'
  if (!store.telemetry.armed) return '仿真已运行：请先“解锁”，解锁后“起飞”才会启用。'
  if (store.telemetry.flight_mode === 'ARMED') return '已解锁：可以设置目标高度并起飞。'
  if (store.telemetry.flight_mode === 'TAKING_OFF') return '正在起飞：起飞按钮锁定，可执行降落。'
  if (store.telemetry.flight_mode === 'HOVERING') return '正在悬停：可调整环境、目标点，或执行降落。'
  if (store.telemetry.flight_mode === 'LANDING') return '正在降落：等待返回待机并自动上锁。'
  return '按 开始 → 解锁 → 起飞 → 降落 的顺序操作。'
})
const massText = computed(() =>
  assemblyStore.engineering
    ? `${assemblyStore.engineering.total_mass_kg.toFixed(3)} kg`
    : '等待工程计算',
)
const horizontalSpeed = computed(() =>
  Math.hypot(store.telemetry.velocity.x, store.telemetry.velocity.y),
)
const powerText = computed(() =>
  store.telemetry.power.estimated_power_w >= 1000
    ? `${(store.telemetry.power.estimated_power_w / 1000).toFixed(2)} kW`
    : `${store.telemetry.power.estimated_power_w.toFixed(0)} W`,
)
const connectionText = computed(() => {
  if (store.connectionStatus === 'CONNECTED') return '已连接'
  if (store.connectionStatus === 'CONNECTING') return '连接中'
  return '未连接'
})

onMounted(async () => {
  await Promise.all([assemblyStore.initialize(), settingsStore.initialize()])
  if (store.simulationId === null) {
    store.targetAltitude = settingsStore.settings.flight.default_altitude_m
    store.windSpeed = settingsStore.settings.flight.default_wind_speed_mps
    store.windDirection = settingsStore.settings.flight.default_wind_direction_deg
    viewMode.value = settingsStore.settings.flight.default_view
    if (settingsStore.settings.flight.auto_create_simulation && assemblyReady.value) {
      try { await store.createSimulation() } catch { /* store exposes the error */ }
    }
  }
})

onBeforeUnmount(async () => {
  if (store.simulationStatus === 'RUNNING') {
    try {
      await store.pause()
    } catch {
      // The page is closing; the backend shutdown path still protects the task.
    }
  }
  store.disconnectTelemetry()
})

async function perform(action: () => Promise<void>): Promise<void> {
  if (busy.value) return
  busy.value = true
  try {
    await action()
  } catch {
    // The store exposes the user-facing error message.
  } finally {
    busy.value = false
  }
}

async function applyPendingTarget(): Promise<void> {
  if (!pendingTarget.value) return
  await store.setTarget(pendingTarget.value.x, pendingTarget.value.y)
}

function selectPendingTarget(target: { x: number; y: number }): void {
  pendingTarget.value = target
}

async function addWaypoint(): Promise<void> {
  if (!pendingTarget.value) return
  await store.setWaypoints([
    ...store.waypoints,
    {
      x: pendingTarget.value.x,
      y: pendingTarget.value.y,
      z: store.targetAltitude,
    },
  ])
}

async function clearWaypoints(): Promise<void> {
  await store.setWaypoints([])
}

function deg(radians: number): string {
  return ((radians * 180) / Math.PI).toFixed(2)
}
</script>

<style scoped>
.flight-control-panel button:disabled {
  cursor: not-allowed !important;
  opacity: 1 !important;
  color: #98a4b3 !important;
  background: #edf1f5 !important;
  border-color: #d8e0ea !important;
  box-shadow: none !important;
  filter: none !important;
  transform: none !important;
}

.flight-control-panel .primary-blue:disabled,
.flight-control-panel .danger-button:disabled,
.flight-control-panel .secondary-action:disabled {
  color: #98a4b3 !important;
  background: #edf1f5 !important;
  border-color: #d8e0ea !important;
}

.flight-command-hint {
  margin: 8px 0 0;
  min-height: 30px;
  padding: 7px 9px;
  border: 1px solid #e1e7ef;
  border-radius: 6px;
  background: #f8fafc;
  color: #64748b;
  font-size: 10px;
  line-height: 1.45;
}
</style>
