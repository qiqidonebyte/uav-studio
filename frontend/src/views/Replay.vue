<template>
  <div class="workbench-grid replay-grid">
    <aside class="panel left-panel">
      <section class="panel-section">
        <h3>Replay 控制</h3>
        <div class="button-grid">
          <button class="primary-blue" :disabled="!store.document || store.playing" @click="store.play">
            播放
          </button>
          <button :disabled="!store.document || !store.playing" @click="store.pause">
            暂停
          </button>
        </div>
        <button class="secondary-action replay-reset" :disabled="!store.document" @click="store.reset">
          复位
        </button>
        <label class="replay-slider">
          <span>{{ store.currentTime.toFixed(1) }} s / {{ store.duration.toFixed(1) }} s</span>
          <input
            type="range"
            min="0"
            :max="Math.max(store.duration, 0.01)"
            step="0.05"
            :value="store.currentTime"
            @input="seek"
          />
        </label>
        <label class="field-row replay-speed">
          <span>播放速度</span>
          <select v-model.number="store.playbackRate">
            <option :value="0.5">0.5 倍</option>
            <option :value="1">1 倍</option>
            <option :value="2">2 倍</option>
          </select>
        </label>
      </section>

      <section v-if="documentInfo" class="panel-section">
        <h3>实验详情</h3>
        <dl class="replay-metadata">
          <div><dt>飞机</dt><dd>{{ documentInfo.experiment.aircraft_name }}</dd></div>
          <div><dt>开始时间</dt><dd>{{ formatDate(documentInfo.experiment.started_at) }}</dd></div>
          <div><dt>持续时间</dt><dd>{{ documentInfo.experiment.duration_s.toFixed(1) }} s</dd></div>
          <div><dt>最大高度</dt><dd>{{ documentInfo.experiment.max_altitude_m.toFixed(2) }} m</dd></div>
          <div><dt>总帧数</dt><dd>{{ documentInfo.frames.length }}</dd></div>
          <div><dt>航点数量</dt><dd>{{ documentInfo.waypoints.length }}</dd></div>
        </dl>
      </section>
    </aside>

    <main class="stage-panel flight-stage">
      <div class="view-switch">
        <button :class="{ active: viewMode === '3d' }" @click="viewMode = '3d'">三维回放</button>
        <button :class="{ active: viewMode === 'map' }" @click="viewMode = 'map'">轨迹回放</button>
        <button :class="{ active: viewMode === 'split' }" @click="viewMode = 'split'">分屏</button>
      </div>

      <template v-if="documentInfo && currentFrame">
        <DroneScene
          v-if="viewMode === '3d'"
          :telemetry="currentFrame"
          :aircraft="documentInfo.aircraft"
          :components="documentInfo.components"
        />
        <LocalFlightMap
          v-else-if="viewMode === 'map'"
          :telemetry="currentFrame"
          :history="store.history"
          :target-position="documentInfo.target_position"
          :waypoints="documentInfo.waypoints"
          :boundary-m="documentInfo.boundary_m"
        />
        <div v-else class="split-stage">
          <div class="split-pane">
            <DroneScene
              :telemetry="currentFrame"
              :aircraft="documentInfo.aircraft"
              :components="documentInfo.components"
            />
          </div>
          <div class="split-pane">
            <LocalFlightMap
              :telemetry="currentFrame"
              :history="store.history"
              :target-position="documentInfo.target_position"
              :waypoints="documentInfo.waypoints"
              :boundary-m="documentInfo.boundary_m"
            />
          </div>
        </div>
      </template>
      <div v-else class="stage-loading">正在读取实验回放…</div>
    </main>

    <aside class="panel inspector-panel">
      <section v-if="store.error" class="inspector-section command-error">
        {{ store.error }}
      </section>
      <template v-if="currentFrame">
        <section class="inspector-section">
          <h3>当前回放帧</h3>
          <dl>
            <div><dt>时间</dt><dd>{{ currentFrame.t.toFixed(2) }} s</dd></div>
            <div><dt>模式</dt><dd>{{ flightModeLabel(currentFrame.flight_mode) }}</dd></div>
            <div><dt>解锁</dt><dd>{{ currentFrame.armed ? '已解锁' : '未解锁' }}</dd></div>
            <div><dt>位置</dt><dd>{{ currentFrame.position.x.toFixed(1) }} / {{ currentFrame.position.y.toFixed(1) }} / {{ currentFrame.position.z.toFixed(1) }} m</dd></div>
          </dl>
        </section>
        <section class="inspector-section">
          <h3>姿态</h3>
          <dl>
            <div><dt>横滚 / 俯仰</dt><dd>{{ degrees(currentFrame.attitude.roll) }}° / {{ degrees(currentFrame.attitude.pitch) }}°</dd></div>
            <div><dt>偏航</dt><dd>{{ degrees(currentFrame.attitude.yaw) }}°</dd></div>
            <div><dt>P / Q / R</dt><dd>{{ currentFrame.angular_velocity.p.toFixed(3) }} / {{ currentFrame.angular_velocity.q.toFixed(3) }} / {{ currentFrame.angular_velocity.r.toFixed(3) }}</dd></div>
          </dl>
        </section>
        <section class="inspector-section">
          <h3>动力 / 电源</h3>
          <dl>
            <div><dt>总推力</dt><dd>{{ currentFrame.forces.total_thrust_n.toFixed(2) }} N</dd></div>
            <div><dt>功率</dt><dd>{{ currentFrame.power.estimated_power_w.toFixed(0) }} W</dd></div>
            <div><dt>电压</dt><dd>{{ currentFrame.power.voltage_v.toFixed(2) }} V</dd></div>
            <div><dt>电流</dt><dd>{{ currentFrame.power.current_a.toFixed(2) }} A</dd></div>
            <div><dt>电量</dt><dd>{{ (currentFrame.power.battery_remaining * 100).toFixed(1) }}%</dd></div>
          </dl>
        </section>
        <section class="inspector-section motor-section">
          <h3>四电机回放</h3>
          <table>
            <thead><tr><th>电机</th><th>输出</th><th>推力</th></tr></thead>
            <tbody>
              <tr v-for="(_, index) in currentFrame.motors.outputs" :key="index">
                <td>M{{ index + 1 }}</td>
                <td>{{ (currentFrame.motors.outputs[index] * 100).toFixed(1) }}%</td>
                <td>{{ currentFrame.motors.thrusts_n[index].toFixed(2) }} N</td>
              </tr>
            </tbody>
          </table>
        </section>
      </template>
    </aside>

    <section class="bottom-panel">
      <RealtimeCharts
        v-if="currentFrame"
        :telemetry="currentFrame"
        :history="store.history"
        :live="false"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import DroneScene from '../components/DroneScene.vue'
import LocalFlightMap from '../components/LocalFlightMap.vue'
import RealtimeCharts from '../components/RealtimeCharts.vue'
import { useReplayStore } from '../stores/replay'
import { FLIGHT_MODE_LABELS } from '../utils/telemetry'
import type { FlightMode } from '../types/telemetry'

const route = useRoute()
const store = useReplayStore()
const viewMode = ref<'3d' | 'map' | 'split'>('split')
const documentInfo = computed(() => store.document)
const currentFrame = computed(() => store.currentFrame)

onMounted(() => {
  const id = route.params.id
  if (typeof id === 'string') void store.load(id)
})

onBeforeUnmount(() => {
  store.dispose()
})

function seek(event: Event): void {
  store.seek(Number((event.target as HTMLInputElement).value))
}

function degrees(radians: number): string {
  return ((radians * 180) / Math.PI).toFixed(2)
}

function flightModeLabel(mode: FlightMode): string {
  return FLIGHT_MODE_LABELS[mode]
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}
</script>
