<template>
  <div class="charts-panel">
    <div class="chart-tabs">
      <button
        v-for="tab in tabs"
        :key="tab"
        :class="['chart-tab', { active: active === tab }]"
        @click="active = tab"
      >
        {{ tab }}
      </button>
      <div class="chart-live">
        <span :class="['dot', { paused: !live }]"></span>
        {{ live ? `实时 ${telemetry.t.toFixed(1)} s` : '遥测未连接' }}
      </div>
    </div>
    <div class="charts-grid">
      <div ref="firstEl" class="chart-box"></div>
      <div ref="secondEl" class="chart-box"></div>
      <div ref="thirdEl" class="chart-box"></div>
      <div ref="fourthEl" class="chart-box"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import * as echarts from 'echarts'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { TelemetryFrame } from '../types/telemetry'
import { recentTelemetry } from '../utils/telemetry'

const props = defineProps<{
  telemetry: TelemetryFrame
  history: TelemetryFrame[]
  live?: boolean
}>()

const tabs = ['飞行状态', '姿态', '电机', '动力', '轨迹', '实验结果'] as const
const active = ref<(typeof tabs)[number]>('飞行状态')
const firstEl = ref<HTMLDivElement | null>(null)
const secondEl = ref<HTMLDivElement | null>(null)
const thirdEl = ref<HTMLDivElement | null>(null)
const fourthEl = ref<HTMLDivElement | null>(null)
let charts: echarts.ECharts[] = []

const live = computed(() => props.live ?? props.history.length > 0)

function baseOption(title: string, times: string[]) {
  return {
    animation: false,
    title: {
      text: title,
      left: 10,
      top: 8,
      textStyle: { fontSize: 12, fontWeight: 600, color: '#22324a' },
    },
    grid: { left: 45, right: 14, top: 42, bottom: 28 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      axisLabel: { fontSize: 10 },
      data: times,
    },
    yAxis: {
      type: 'value',
      axisLabel: { fontSize: 10 },
      splitLine: { lineStyle: { color: '#eef2f7' } },
    },
    tooltip: { trigger: 'axis' },
  }
}

function line(name: string, data: number[], color?: string) {
  return {
    name,
    type: 'line',
    showSymbol: false,
    data,
    ...(color ? { lineStyle: { color }, itemStyle: { color } } : {}),
  }
}

function setChart(
  index: number,
  title: string,
  times: string[],
  series: unknown[],
  yBounds?: { min?: number; max?: number },
) {
  const option = baseOption(title, times)
  charts[index].setOption(
    {
      ...option,
      yAxis: { ...option.yAxis, ...yBounds },
      legend: {
        top: 9,
        right: 8,
        textStyle: { fontSize: 9 },
      },
      series,
    },
    true,
  )
}

function render() {
  if (charts.length !== 4) return
  const frames = recentTelemetry(props.history, props.telemetry.t, 60)
  const times = frames.map(frame => frame.t.toFixed(1))
  if (frames.length === 0) {
    for (let index = 0; index < 4; index += 1) {
      charts[index].clear()
    }
    return
  }

  const degrees = (radians: number) => (radians * 180) / Math.PI
  if (active.value === '飞行状态') {
    setChart(0, '高度 (m)', times, [line('高度', frames.map(frame => frame.position.z))])
    setChart(1, '垂直速度 (m/s)', times, [line('VZ', frames.map(frame => frame.velocity.z))])
    setChart(2, '水平速度 (m/s)', times, [
      line('水平速度', frames.map(frame => Math.hypot(frame.velocity.x, frame.velocity.y))),
    ])
    setChart(3, '总推力 (N)', times, [
      line('总推力', frames.map(frame => frame.forces.total_thrust_n)),
    ])
  } else if (active.value === '姿态') {
    setChart(0, '姿态角 (°)', times, [
      line('横滚', frames.map(frame => degrees(frame.attitude.roll))),
      line('俯仰', frames.map(frame => degrees(frame.attitude.pitch))),
      line('偏航', frames.map(frame => degrees(frame.attitude.yaw))),
    ])
    setChart(1, '角速度 (rad/s)', times, [
      line('P', frames.map(frame => frame.angular_velocity.p)),
      line('Q', frames.map(frame => frame.angular_velocity.q)),
      line('R', frames.map(frame => frame.angular_velocity.r)),
    ])
    setChart(2, '速度分量 (m/s)', times, [
      line('VX', frames.map(frame => frame.velocity.x)),
      line('VY', frames.map(frame => frame.velocity.y)),
      line('VZ', frames.map(frame => frame.velocity.z)),
    ])
    setChart(3, '位置 (m)', times, [
      line('X', frames.map(frame => frame.position.x)),
      line('Y', frames.map(frame => frame.position.y)),
      line('Z', frames.map(frame => frame.position.z)),
    ])
  } else if (active.value === '电机') {
    setChart(0, '电机输出 (%)', times, [0, 1, 2, 3].map(index =>
      line(`M${index + 1}`, frames.map(frame => frame.motors.outputs[index] * 100)),
    ), { min: 0, max: 100 })
    setChart(1, '电机推力 (N)', times, [0, 1, 2, 3].map(index =>
      line(`M${index + 1}`, frames.map(frame => frame.motors.thrusts_n[index])),
    ))
    setChart(2, '输出差 (百分点)', times, [
      line(
        '最大输出差',
        frames.map(frame => {
          const values = frame.motors.outputs.map(value => value * 100)
          return Math.max(...values) - Math.min(...values)
        }),
      ),
    ])
    setChart(3, '推力差 (N)', times, [
      line(
        '最大推力差',
        frames.map(frame => {
          const values = frame.motors.thrusts_n
          return Math.max(...values) - Math.min(...values)
        }),
      ),
    ])
  } else if (active.value === '动力') {
    setChart(0, '估算功率 (W)', times, [
      line('功率', frames.map(frame => frame.power.estimated_power_w)),
    ])
    setChart(1, '电流 (A)', times, [
      line('电流', frames.map(frame => frame.power.current_a)),
    ])
    setChart(2, '电压 (V)', times, [
      line('电压', frames.map(frame => frame.power.voltage_v)),
    ])
    setChart(3, '剩余电量 (%)', times, [
      line('电量', frames.map(frame => frame.power.battery_remaining * 100)),
    ], { min: 0, max: 100 })
  } else if (active.value === '轨迹') {
    setChart(0, 'X 位置 (m)', times, [line('X', frames.map(frame => frame.position.x))])
    setChart(1, 'Y 位置 (m)', times, [line('Y', frames.map(frame => frame.position.y))])
    setChart(2, '水平位移 (m)', times, [
      line('水平位移', frames.map(frame => Math.hypot(frame.position.x, frame.position.y))),
    ])
    setChart(3, '高度 (m)', times, [line('高度', frames.map(frame => frame.position.z))])
  } else {
    const maxAltitude = Math.max(...frames.map(frame => frame.position.z))
    const maxHorizontal = Math.max(
      ...frames.map(frame => Math.hypot(frame.position.x, frame.position.y)),
    )
    const maxMotorSpread = Math.max(
      ...frames.map(frame => {
        const values = frame.motors.thrusts_n
        return Math.max(...values) - Math.min(...values)
      }),
    )
    setChart(0, '实验结果概览', ['最大高度', '最大水平位移', '最大推力差', '当前电量'], [
      line('结果', [
        maxAltitude,
        maxHorizontal,
        maxMotorSpread,
        frames[frames.length - 1].power.battery_remaining * 100,
      ]),
    ])
    setChart(1, '风向 (度)', times, [
      line('风向', frames.map(frame => frame.wind.direction_deg)),
    ])
    setChart(2, '风速 (m/s)', times, [
      line('风速', frames.map(frame => frame.wind.speed_mps)),
    ])
    setChart(3, '总推力 / 重力 (N)', times, [
      line('总推力', frames.map(frame => frame.forces.total_thrust_n)),
      line('重力', frames.map(frame => frame.forces.gravity_n)),
    ])
  }
}

function resize() {
  charts.forEach(chart => chart.resize())
}

onMounted(async () => {
  await nextTick()
  charts = [firstEl, secondEl, thirdEl, fourthEl].map(element =>
    echarts.init(element.value!),
  )
  render()
  window.addEventListener('resize', resize)
})

watch(
  () => [props.telemetry.t, props.history.length, active.value],
  render,
)

onBeforeUnmount(() => {
  window.removeEventListener('resize', resize)
  charts.forEach(chart => chart.dispose())
})
</script>
