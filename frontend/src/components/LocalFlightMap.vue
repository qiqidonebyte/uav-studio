<template>
  <div class="local-map">
    <div class="map-title">基础飞行地图 <small>局部 X/Y · m</small></div>
    <div class="map-boundary-label">飞行边界 ±{{ boundaryM.toFixed(0) }} m</div>
    <svg
      class="map-svg"
      :class="{ interactive: interactive }"
      viewBox="0 0 800 520"
      preserveAspectRatio="xMidYMid meet"
      @click="onMapClick"
    >
      <defs>
        <pattern id="smallGrid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#e8edf4" stroke-width="1"/>
        </pattern>
        <marker id="windHead" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
          <path d="M0,0 L8,4 L0,8 Z" fill="#2f80ed"/>
        </marker>
      </defs>
      <rect width="800" height="520" fill="#fbfcfe"/>
      <rect width="800" height="520" fill="url(#smallGrid)"/>
      <rect
        :x="boundaryRect.x"
        :y="boundaryRect.y"
        :width="boundaryRect.width"
        :height="boundaryRect.height"
        fill="rgba(37,99,235,.025)"
        stroke="#8fb3e8"
        stroke-width="2"
        stroke-dasharray="8 6"
      />
      <line x1="400" y1="0" x2="400" y2="520" stroke="#c7d1df"/>
      <line x1="0" y1="260" x2="800" y2="260" stroke="#c7d1df"/>
      <text x="410" y="18" class="axis-text">+Y 左</text>
      <text x="742" y="250" class="axis-text">+X 前</text>

      <polyline
        v-if="trackPoints"
        :points="trackPoints"
        fill="none"
        stroke="#5b8def"
        stroke-width="3"
        stroke-linecap="round"
        stroke-linejoin="round"
      />

      <g v-for="(waypoint, index) in waypoints" :key="`${index}-${waypoint.x}-${waypoint.y}`">
        <circle :cx="project(waypoint.x, waypoint.y).x" :cy="project(waypoint.x, waypoint.y).y" r="8" fill="#f59e0b"/>
        <text
          :x="project(waypoint.x, waypoint.y).x + 11"
          :y="project(waypoint.x, waypoint.y).y + 4"
          class="waypoint-label"
        >
          航点 {{ index + 1 }}
        </text>
      </g>

      <g v-if="targetPosition">
        <circle :cx="target.x" :cy="target.y" r="11" fill="none" stroke="#dc2626" stroke-width="3"/>
        <line :x1="target.x - 16" :y1="target.y" :x2="target.x + 16" :y2="target.y" stroke="#dc2626" stroke-width="2"/>
        <line :x1="target.x" :y1="target.y - 16" :x2="target.x" :y2="target.y + 16" stroke="#dc2626" stroke-width="2"/>
        <text :x="target.x + 15" :y="target.y - 13" class="target-label">
          目标点
        </text>
      </g>

      <g v-if="pendingTarget">
        <circle :cx="pending.x" :cy="pending.y" r="7" fill="#fbbf24" stroke="#b45309" stroke-width="2"/>
        <text :x="pending.x + 11" :y="pending.y - 10" class="target-label">待应用目标</text>
      </g>

      <circle :cx="home.x" :cy="home.y" r="9" fill="#16a34a"/>
      <text :x="home.x + 13" :y="home.y - 9" class="label">起点 (0,0)</text>

      <g :transform="`translate(${drone.x} ${drone.y}) rotate(${headingDeg})`">
        <polygon points="16,0 -11,-9 -7,0 -11,9" fill="#ef4444"/>
        <circle r="4" fill="#ffffff"/>
      </g>
      <text :x="drone.x + 14" :y="drone.y + 22" class="label">无人机</text>

      <line x1="92" y1="72" :x2="windEnd.x" :y2="windEnd.y" stroke="#2f80ed" stroke-width="4" marker-end="url(#windHead)"/>
      <text x="92" y="54" class="wind-text">
        风 {{ telemetry.wind.speed_mps.toFixed(1) }} m/s · {{ telemetry.wind.direction_deg.toFixed(0) }}°
      </text>

      <line :x1="scale.x1" y1="470" :x2="scale.x2" y2="470" stroke="#475569" stroke-width="3"/>
      <line :x1="scale.x1" y1="464" :x2="scale.x1" y2="476" stroke="#475569"/>
      <line :x1="scale.x2" y1="464" :x2="scale.x2" y2="476" stroke="#475569"/>
      <text :x="(scale.x1 + scale.x2) / 2 - 8" y="494" class="axis-text">{{ scale.meters }} m</text>
    </svg>
    <div class="map-readout">
      X {{ telemetry.position.x.toFixed(2) }} m · Y {{ telemetry.position.y.toFixed(2) }} m · 高度 {{ telemetry.position.z.toFixed(2) }} m
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TelemetryFrame } from '../types/telemetry'
import type { Vector3Value } from '../types/aircraft'
import {
  isInsideFlightBoundary,
  projectLocalPoint,
  unprojectMapPoint,
} from '../utils/flightMap'

const props = withDefaults(
  defineProps<{
    telemetry: TelemetryFrame
    history: TelemetryFrame[]
    targetPosition?: Vector3Value | null
    waypoints?: Vector3Value[]
    pendingTarget?: { x: number; y: number } | null
    boundaryM?: number
    interactive?: boolean
  }>(),
  {
    targetPosition: null,
    waypoints: () => [],
    pendingTarget: null,
    boundaryM: 25,
    interactive: false,
  },
)

const emit = defineEmits<{
  (event: 'select-target', target: { x: number; y: number }): void
}>()

const rangeM = computed(() => props.boundaryM * 1.15)
const scaleMeters = 5
const home = computed(() => project(0, 0))
const drone = computed(() =>
  project(props.telemetry.position.x, props.telemetry.position.y),
)
const target = computed(() =>
  props.targetPosition ? project(props.targetPosition.x, props.targetPosition.y) : { x: 0, y: 0 },
)
const pending = computed(() =>
  props.pendingTarget ? project(props.pendingTarget.x, props.pendingTarget.y) : { x: 0, y: 0 },
)
const headingDeg = computed(
  () => (-props.telemetry.attitude.yaw * 180) / Math.PI,
)
const trackPoints = computed(() =>
  props.history
    .slice(-1200)
    .map(frame => {
      const point = project(frame.position.x, frame.position.y)
      return `${point.x},${point.y}`
    })
    .join(' '),
)
const boundaryRect = computed(() => {
  const min = project(-props.boundaryM, props.boundaryM)
  const max = project(props.boundaryM, -props.boundaryM)
  return {
    x: min.x,
    y: min.y,
    width: max.x - min.x,
    height: max.y - min.y,
  }
})
const windEnd = computed(() => {
  const radians = (props.telemetry.wind.direction_deg * Math.PI) / 180
  return {
    x: 92 + Math.cos(radians) * 90,
    y: 72 - Math.sin(radians) * 90,
  }
})
const scale = computed(() => {
  const start = project(0, 0).x
  const end = project(scaleMeters, 0).x
  return {
    meters: scaleMeters,
    x1: 625,
    x2: 625 + (end - start),
  }
})

function project(x: number, y: number) {
  return projectLocalPoint(x, y, 800, 520, rangeM.value)
}

function onMapClick(event: MouseEvent): void {
  if (!props.interactive) return
  const svg = event.currentTarget as SVGSVGElement
  const rect = svg.getBoundingClientRect()
  const pixelX = ((event.clientX - rect.left) / rect.width) * 800
  const pixelY = ((event.clientY - rect.top) / rect.height) * 520
  const targetPoint = unprojectMapPoint(
    pixelX,
    pixelY,
    800,
    520,
    rangeM.value,
  )
  if (
    !isInsideFlightBoundary(
      targetPoint.x,
      targetPoint.y,
      props.boundaryM,
    )
  ) {
    return
  }
  emit('select-target', {
    x: Number(targetPoint.x.toFixed(2)),
    y: Number(targetPoint.y.toFixed(2)),
  })
}
</script>
