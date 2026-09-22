<template>
  <div ref="host" class="drone-scene asset-scene" :style="{ cursor }" @pointerleave="cursor = 'default'">
    <div class="scene-toolbar asset-toolbar">
      <template v-if="assemblyMode">
        <span class="scene-chip scene-chip-active">装配视图</span>
        <button
          data-testid="assembly-view-assembled"
          :class="['scene-chip', { active: assemblyViewMode === 'assembled' }]"
          @click="setAssemblyViewMode('assembled')"
        >
          整机
        </button>
        <button
          data-testid="assembly-view-exploded"
          :class="['scene-chip', { active: assemblyViewMode === 'exploded' }]"
          :disabled="Boolean(pendingInstall)"
          :title="pendingInstall ? '完成或取消当前 3D 装配后可进入爆炸视图' : ''"
          @click="setAssemblyViewMode('exploded')"
        >
          爆炸视图
        </button>
        <span class="scene-toolbar-divider"></span>
        <button :class="['scene-chip', { active: cameraMode === 'top' }]" @click="setCameraMode('top')">俯视</button>
        <button :class="['scene-chip', { active: cameraMode === 'side' }]" @click="setCameraMode('side')">侧视</button>
        <button :class="['scene-chip', { active: cameraMode === 'free' }]" @click="setCameraMode('free')">自由</button>
      </template>
      <template v-else>
        <span class="scene-chip scene-chip-active">三维视图</span>
        <button :class="['scene-chip', { active: cameraMode === 'follow' }]" @click="setCameraMode('follow')">跟随</button>
        <button :class="['scene-chip', { active: cameraMode === 'top' }]" @click="setCameraMode('top')">俯视</button>
        <button :class="['scene-chip', { active: cameraMode === 'side' }]" @click="setCameraMode('side')">侧视</button>
        <button :class="['scene-chip', { active: cameraMode === 'free' }]" @click="setCameraMode('free')">自由</button>
      </template>
    </div>

    <div v-if="assetError" class="asset-error" data-testid="asset-error">
      <b>3D 资产加载失败</b>
      <span>{{ assetError }}</span>
    </div>

    <div v-if="telemetry && !grounded" class="scene-readout">
      <div><span>时间</span><b>{{ telemetry.t.toFixed(1) }} s</b></div>
      <div><span>高度</span><b>{{ telemetry.position.z.toFixed(1) }} m</b></div>
      <div><span>位置</span><b>({{ telemetry.position.x.toFixed(1) }}, {{ telemetry.position.y.toFixed(1) }}, {{ telemetry.position.z.toFixed(1) }}) m</b></div>
    </div>

    <div v-if="telemetry && grounded" class="scene-readout grounded-readout" data-testid="grounded-test-state">
      <div><span>测试状态</span><b>地面固定</b></div>
      <div><span>机体运动</span><b>已锁定</b></div>
    </div>

    <div v-if="telemetry && !grounded" class="wind-readout">风场 {{ telemetry.wind.speed_mps.toFixed(1) }} m/s</div>

    <div v-if="assemblyMode" :class="['scene-selection', { issue: issueSlots.length > 0 }]">
      <b>{{ assemblyViewMode === 'exploded' ? '爆炸视图' : (selectedSlot ? SLOT_LABELS[selectedSlot] : '选择部件') }}</b>
      <span v-if="issueSlots.length > 0">红色高亮为当前工程检查问题</span>
      <span v-else-if="assemblyViewMode === 'exploded'">组件按装配层级展开，可直接点击任意部件查看详情</span>
      <span v-else>{{ selectedSlot ? '蓝色高亮为当前检查部件' : '点击机架、电机、桨、电池等模型查看详情' }}</span>
    </div>

    <div
      v-if="assemblyMode && pendingInstall"
      class="assembly-install-banner"
      data-testid="assembly-install-banner"
    >
      <span class="install-pulse"></span>
      <div>
        <b>3D 装配模式 · {{ SLOT_LABELS[pendingInstall.slot] }}</b>
        <small>选择蓝色安装点，Ghost 组件会自动吸附到真实 Mount Anchor</small>
      </div>
    </div>

    <div
      v-if="assemblyMode && pendingInstall && mountHotspots.length > 0"
      class="mount-hotspot-layer"
      data-testid="mount-hotspot-layer"
    >
      <button
        v-for="hotspot in mountHotspots"
        :key="hotspot.mountId"
        class="mount-hotspot"
        :class="{ hovered: hoveredMountId === hotspot.mountId }"
        :style="{ left: `${hotspot.left}px`, top: `${hotspot.top}px` }"
        :data-mount-id="hotspot.mountId"
        :aria-label="`安装到 ${hotspot.label}`"
        data-testid="assembly-mount-hotspot"
        @mouseenter="hoverMount(hotspot.mountId)"
        @mouseleave="leaveMount(hotspot.mountId)"
        @focus="hoverMount(hotspot.mountId)"
        @blur="leaveMount(hotspot.mountId)"
        @click.stop="installMount(hotspot.mountId)"
      >
        <span></span>
        <b>{{ hotspot.shortLabel }}</b>
      </button>
    </div>

    <div
      v-if="assemblyMode && spatialDiagnostics.length > 0"
      :class="['spatial-diagnostic-pill', { error: hasSpatialError }]"
      data-testid="spatial-diagnostic-pill"
    >
      <b>{{ hasSpatialError ? '空间干涉' : '空间提醒' }}</b>
      <span>{{ spatialDiagnostics[0].message }}</span>
    </div>

    <div
      v-if="assemblyMode && assemblyViewMode === 'exploded'"
      class="exploded-view-hint"
      data-testid="exploded-view-hint"
    >
      <b>装配层级</b>
      <span>上层：导航 / 飞控</span>
      <span>外侧：桨 / 电机 / 电调</span>
      <span>下层：电源 / 电池 / 载荷</span>
    </div>

    <div
      v-if="assemblyMode && assemblyViewMode === 'exploded' && explodedComponentLabels.length > 0"
      class="exploded-label-layer"
      data-testid="exploded-label-layer"
    >
      <div
        v-for="label in explodedComponentLabels"
        :key="label.key"
        :class="['exploded-component-label', { selected: label.selected, issue: label.issue }]"
        :data-label-slot="label.slot"
        data-testid="exploded-component-label"
        :style="{ left: `${label.left}px`, top: `${label.top}px` }"
      >
        <span class="exploded-label-type">{{ label.meta }}</span>
        <b :title="label.title">{{ label.title }}</b>
      </div>
    </div>

    <div :class="['scene-legend', { 'scene-legend-assembly': assemblyMode }]">
      <template v-if="assemblyMode">
        <span class="legend-green"></span>已安装
        <span class="legend-gray"></span>待安装
        <span class="legend-yellow"></span>重心
        <span class="legend-issue"></span>问题定位
      </template>
      <template v-else>
        <span class="legend-blue"></span>旋翼推力
        <span class="legend-red"></span>重力
        <span class="legend-yellow"></span>重心
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js'
import type { AircraftDefinition, AircraftEngineeringSummary, Component, MotorName } from '../types/aircraft'
import type { TelemetryFrame } from '../types/telemetry'
import { simulationPoseToThree, simulationVectorToThree } from '../three/coordinates'
import {
  batteryBayDimensions,
  batteryEnvelopeDiagnostic,
  buildMountPoints,
  componentById,
  isMountInstalled,
  missingMountsForSlot,
  rotorDiscDiagnostics,
  type MountPoint,
  type SpatialDiagnostic,
} from '../three/assemblySemantics'
import { AircraftRenderer } from '../three/AircraftRenderer'
import type { AssemblyViewMode } from '../three/explodedView'
import { buildExplodedLabelDescriptors } from '../three/explodedLabels'
import { layoutExplodedLabels } from '../three/explodedLabelLayout'
import { SLOT_LABELS, type AssemblySlot } from '../utils/assembly'
import { useSettingsStore } from '../stores/settings'

const props = withDefaults(
  defineProps<{
    telemetry?: TelemetryFrame
    aircraft?: AircraftDefinition | null
    components?: Component[]
    selectedSlot?: AssemblySlot | null
    issueSlots?: AssemblySlot[]
    issueMounts?: MotorName[]
    engineering?: AircraftEngineeringSummary | null
    interactive?: boolean
    pendingInstall?: { slot: AssemblySlot; componentId: number } | null
    selectedMountId?: string | null
    installAnimation?: { mountId: string; serial: number } | null
    removeAnimation?: { mountId: string; serial: number } | null
    issueMountIds?: string[]
    grounded?: boolean
  }>(),
  {
    telemetry: undefined,
    aircraft: null,
    components: () => [],
    selectedSlot: null,
    issueSlots: () => [],
    issueMounts: () => [],
    engineering: null,
    interactive: false,
    pendingInstall: null,
    selectedMountId: null,
    installAnimation: null,
    removeAnimation: null,
    issueMountIds: () => [],
    grounded: false,
  },
)

const emit = defineEmits<{
  (event: 'select-slot', slot: AssemblySlot): void
  (event: 'select-mount', mountId: string, slot: AssemblySlot): void
  (event: 'install-at-mount', mountId: string): void
  (event: 'spatial-diagnostics', diagnostics: SpatialDiagnostic[]): void
}>()

const host = ref<HTMLDivElement | null>(null)
const cursor = ref('default')
const loadingAssets = ref(true)
const assetError = ref('')
const cameraMode = ref<'follow' | 'top' | 'side' | 'free'>('free')
const assemblyViewMode = ref<AssemblyViewMode>('assembled')
const explosionProgress = ref(0)
type ExplodedComponentLabelView = {
  key: string
  slot: AssemblySlot
  title: string
  meta: string
  left: number
  top: number
  selected: boolean
  issue: boolean
}
const explodedComponentLabels = ref<ExplodedComponentLabelView[]>([])
type MountHotspotView = {
  mountId: string
  label: string
  shortLabel: string
  left: number
  top: number
}
const mountHotspots = ref<MountHotspotView[]>([])
const hoveredMountId = ref<string | null>(null)
const spatialDiagnostics = ref<SpatialDiagnostic[]>([])
const hasSpatialError = computed(
  () => spatialDiagnostics.value.some(item => item.severity === 'error'),
)
const resolvedMountPoints = computed(
  () => buildMountPoints(props.aircraft, props.components),
)
const assemblyMode = computed(() => props.interactive)
const directionLabelsVisible = computed(
  () =>
    assemblyMode.value &&
    assemblyViewMode.value === 'assembled' &&
    (props.selectedSlot === 'propeller' || props.issueMounts.length > 0),
)
const visualTestProbeEnabled = import.meta.env.DEV || import.meta.env.MODE === 'test'
const settingsStore = useSettingsStore()

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let pmrem: THREE.PMREMGenerator | null = null
let environmentTexture: THREE.Texture | null = null
let aircraftRenderer: AircraftRenderer
let vehicleGroup: THREE.Group
let overlayGroup: THREE.Group
let cgMarker: THREE.Mesh
let gravityArrow: THREE.ArrowHelper
let windArrow: THREE.ArrowHelper
let trajectoryLine: THREE.Line
let gridHelper: THREE.GridHelper
let axesHelper: THREE.AxesHelper
let keyLight: THREE.DirectionalLight
let trajectoryPoints: THREE.Vector3[] = []
let thrustArrows: THREE.ArrowHelper[] = []
let activeInstallation: {
  mountId: string
  progress: number
  serial: number
  mode: 'install' | 'remove'
} | null = null
let lastInstallationSerial = -1
let lastRemovalSerial = -1
let animationId = 0
let previousAnimationTime = performance.now()
let lastTelemetryTime = -1
let rebuildGeneration = 0
const raycaster = new THREE.Raycaster()
const pointer = new THREE.Vector2()
const cameraTargetState = new THREE.Vector3(0, 0.08, 0)

type SmoothFlightState = {
  initialized: boolean
  targetPosition: THREE.Vector3
  renderedPosition: THREE.Vector3
  targetQuaternion: THREE.Quaternion
  renderedQuaternion: THREE.Quaternion
  targetCg: THREE.Vector3
  renderedCg: THREE.Vector3
  targetThrusts: number[]
  renderedThrusts: number[]
  targetGravityN: number
  renderedGravityN: number
  targetWindVector: THREE.Vector3
  renderedWindVector: THREE.Vector3
}

const flightSmoothing: SmoothFlightState = {
  initialized: false,
  targetPosition: new THREE.Vector3(),
  renderedPosition: new THREE.Vector3(),
  targetQuaternion: new THREE.Quaternion(),
  renderedQuaternion: new THREE.Quaternion(),
  targetCg: new THREE.Vector3(),
  renderedCg: new THREE.Vector3(),
  targetThrusts: [0, 0, 0, 0],
  renderedThrusts: [0, 0, 0, 0],
  targetGravityN: 0,
  renderedGravityN: 0,
  targetWindVector: new THREE.Vector3(-1, 0, 0),
  renderedWindVector: new THREE.Vector3(-1, 0, 0),
}

function resetFlightSmoothing(): void {
  flightSmoothing.initialized = false
  flightSmoothing.targetPosition.set(0, 0, 0)
  flightSmoothing.renderedPosition.set(0, 0, 0)
  flightSmoothing.targetQuaternion.identity()
  flightSmoothing.renderedQuaternion.identity()
  flightSmoothing.targetCg.set(0, 0, 0)
  flightSmoothing.renderedCg.set(0, 0, 0)
  flightSmoothing.targetThrusts = [0, 0, 0, 0]
  flightSmoothing.renderedThrusts = [0, 0, 0, 0]
  flightSmoothing.targetGravityN = 0
  flightSmoothing.renderedGravityN = 0
  flightSmoothing.targetWindVector.set(-1, 0, 0)
  flightSmoothing.renderedWindVector.set(-1, 0, 0)
}

function disposeObject(root: THREE.Object3D): void {
  root.traverse(object => {
    const mesh = object as THREE.Mesh
    if (mesh.geometry && mesh.userData.overlayGeometry) mesh.geometry.dispose()
    const material = mesh.material
    if (Array.isArray(material)) {
      material.forEach(item => {
        const sprite = item as THREE.SpriteMaterial
        sprite.map?.dispose()
        item.dispose()
      })
    } else if (material) {
      const sprite = material as THREE.SpriteMaterial
      sprite.map?.dispose()
      material.dispose()
    }
  })
}

function addLabelSprite(text: string, position: THREE.Vector3, color = '#1f4f8f'): void {
  const canvas = document.createElement('canvas')
  canvas.width = 220
  canvas.height = 42
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.fillStyle = 'rgba(255,255,255,.88)'
  ctx.roundRect(2, 3, 216, 34, 7)
  ctx.fill()
  ctx.strokeStyle = 'rgba(120,145,175,.45)'
  ctx.stroke()
  ctx.fillStyle = color
  ctx.font = '600 16px Microsoft YaHei, sans-serif'
  ctx.fillText(text, 10, 27)
  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false })
  const sprite = new THREE.Sprite(material)
  sprite.scale.set(0.5, 0.096, 1)
  sprite.position.copy(position)
  sprite.renderOrder = 8
  overlayGroup.add(sprite)
}

function clearOverlay(): void {
  if (!overlayGroup) return
  disposeObject(overlayGroup)
  overlayGroup.clear()
  thrustArrows = []
}

function buildOverlay(): void {
  clearOverlay()
  const mounts = aircraftRenderer.motorMountsSnapshot()
  const directions = props.aircraft?.propeller_directions

  ;(['M1', 'M2', 'M3', 'M4'] as MotorName[]).forEach((name, index) => {
    const p = simulationVectorToThree(mounts[name])
    const arrow = new THREE.ArrowHelper(
      new THREE.Vector3(0, 1, 0),
      p.clone().add(new THREE.Vector3(0, 0.09, 0)),
      0.32,
      0x3b82f6,
      0.09,
      0.05,
    )
    thrustArrows.push(arrow)
    overlayGroup.add(arrow)
    if (directionLabelsVisible.value) {
      const direction = directions?.[name] ?? (index % 2 === 0 ? 'CCW' : 'CW')
      addLabelSprite(
        `${name} ${direction === 'CCW' ? '逆时针' : '顺时针'}`,
        p.clone().add(new THREE.Vector3(0, 0.34, 0)),
        props.issueMounts.includes(name) ? '#b42318' : '#1f4f8f',
      )
    }
  })

  cgMarker = new THREE.Mesh(
    new THREE.SphereGeometry(0.028, 18, 18),
    new THREE.MeshStandardMaterial({ color: 0xf5c518, emissive: 0x704d00, emissiveIntensity: 0.18 }),
  )
  cgMarker.userData.overlayGeometry = true
  overlayGroup.add(cgMarker)

  gravityArrow = new THREE.ArrowHelper(
    new THREE.Vector3(0, -1, 0),
    new THREE.Vector3(0, -0.04, 0),
    0.48,
    0xef4444,
    0.10,
    0.06,
  )
  overlayGroup.add(gravityArrow)

  const nose = new THREE.ArrowHelper(
    new THREE.Vector3(1, 0, 0),
    new THREE.Vector3(0, 0.11, 0),
    0.24,
    0x16a34a,
    0.06,
    0.035,
  )
  overlayGroup.add(nose)
  buildSpatialOverlay()
  applyAssemblyState()
}

function buildSpatialOverlay(): void {
  if (!overlayGroup || !props.aircraft) return
  const diagnostics = rotorDiscDiagnostics(
    props.aircraft,
    props.components,
    resolvedMountPoints.value,
  )
  const hasRotorCollision = diagnostics.some(item => item.code === 'ROTOR_DISC_COLLISION')
  const propeller = componentById(props.components, props.aircraft.propeller_id)
  const diameterIn = propeller?.parameters_json.diameter_in
  if (hasRotorCollision && typeof diameterIn === 'number') {
    const radius = diameterIn * 0.0254 / 2
    const installed = new Set(
      aircraftRenderer
        .partInstancesSnapshot()
        .filter(item => item.installed && item.slot === 'propeller')
        .map(item => item.mountId),
    )
    for (const mount of resolvedMountPoints.value.filter(item => item.slot === 'propeller')) {
      if (!installed.has(mount.id)) continue
      const disc = new THREE.Mesh(
        new THREE.CircleGeometry(radius, 64),
        new THREE.MeshBasicMaterial({
          color: 0xef4444,
          transparent: true,
          opacity: 0.16,
          side: THREE.DoubleSide,
          depthWrite: false,
        }),
      )
      disc.geometry.userData.overlayGeometry = true
      disc.userData.overlayGeometry = true
      disc.rotation.x = -Math.PI / 2
      disc.position.copy(simulationVectorToThree(mount.position))
      disc.position.y -= 0.002
      overlayGroup.add(disc)
    }
  }

  if (props.selectedSlot === 'battery' || spatialDiagnostics.value.some(item => item.code === 'BATTERY_ENVELOPE_EXCEEDED')) {
    const frame = componentById(props.components, props.aircraft.frame_id)
    const diagonalRaw = frame?.parameters_json.motor_diagonal_m
    const diagonal = typeof diagonalRaw === 'number' ? diagonalRaw : 0.65
    const bay = batteryBayDimensions(diagonal)
    const mount = resolvedMountPoints.value.find(item => item.id === 'battery:main')
    if (mount) {
      const box = new THREE.Mesh(
        new THREE.BoxGeometry(bay.x, bay.z, bay.y),
        new THREE.MeshBasicMaterial({
          color: spatialDiagnostics.value.some(item => item.code === 'BATTERY_ENVELOPE_EXCEEDED')
            ? 0xf59e0b
            : 0x3b82f6,
          wireframe: true,
          transparent: true,
          opacity: 0.55,
        }),
      )
      box.geometry.userData.overlayGeometry = true
      box.userData.overlayGeometry = true
      box.position.copy(simulationVectorToThree(mount.position))
      overlayGroup.add(box)
    }
  }
}

function refreshSpatialDiagnostics(): void {
  if (!aircraftRenderer) return
  const diagnostics: SpatialDiagnostic[] = [
    ...rotorDiscDiagnostics(
      props.aircraft,
      props.components,
      resolvedMountPoints.value,
    ),
  ]

  const batteryInstalled = isMountInstalled(props.aircraft, 'battery:main')
  const batteryBounds = batteryInstalled
    ? aircraftRenderer.boundsForMount('battery:main')
    : null
  diagnostics.push(
    ...batteryEnvelopeDiagnostic(
      props.aircraft,
      props.components,
      batteryBounds
        ? { x: batteryBounds.width, y: batteryBounds.height, z: batteryBounds.depth }
        : null,
    ),
  )
  spatialDiagnostics.value = diagnostics
  emit('spatial-diagnostics', diagnostics)
}

function errorText(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

function syncVisualTestProbe(): void {
  if (!visualTestProbeEnabled || !renderer || !aircraftRenderer) return
  window.__UAV_VISUAL_TEST__ = {
    version: '1.0',
    sceneReady: !loadingAssets.value && !assetError.value,
    pixelRatio: renderer.getPixelRatio(),
    cameraMode: cameraMode.value,
    selectedSlot: props.selectedSlot ?? null,
    issueSlots: [...props.issueSlots],
    issueMounts: [...props.issueMounts],
    propellerDirections: props.aircraft?.propeller_directions ?? null,
    loadedAssets: aircraftRenderer.loadedAssetsSnapshot(),
    aircraftBounds: aircraftRenderer.aircraftBoundsSnapshot(),
    partBounds: aircraftRenderer.partBoundsSnapshot(),
    mounts: aircraftRenderer.motorMountsSnapshot(),
    assemblyViewMode: assemblyViewMode.value,
    explosionProgress: explosionProgress.value,
    directionLabelsVisible: directionLabelsVisible.value,
    explodedParts: aircraftRenderer.explodedPartsSnapshot(),
    explodedLabels: explodedComponentLabels.value.map(label => ({
      key: label.key,
      slot: label.slot,
      title: label.title,
      meta: label.meta,
      left: label.left,
      top: label.top,
      selected: label.selected,
      issue: label.issue,
    })),
    mountPoints: resolvedMountPoints.value.map(mount => ({
      id: mount.id,
      slot: mount.slot,
      label: mount.label,
      position: { ...mount.position },
      required: mount.required,
      motorName: mount.motorName,
    })),
    partInstances: aircraftRenderer.partInstancesSnapshot(),
    pendingInstall: props.pendingInstall
      ? { ...props.pendingInstall }
      : null,
    hoveredMountId: hoveredMountId.value,
    selectedMountId: props.selectedMountId ?? null,
    spatialDiagnostics: spatialDiagnostics.value.map(item => ({
      ...item,
      slots: [...item.slots],
      mountIds: [...item.mountIds],
    })),
    activeInstallation: activeInstallation
      ? { ...activeInstallation }
      : null,
  }
}

async function rebuildAircraftAssets(): Promise<void> {
  if (!aircraftRenderer) return
  const generation = ++rebuildGeneration
  loadingAssets.value = true
  assetError.value = ''
  syncVisualTestProbe()
  try {
    await aircraftRenderer.rebuild(props.aircraft, props.components)
    if (generation !== rebuildGeneration) return
    aircraftRenderer.setExplodedProgress(explosionProgress.value)
    refreshSpatialDiagnostics()
    buildOverlay()
    updateExplodedComponentLabels()
    applyAssemblyState()
    startInstallationAnimationIfNeeded()
    updateMountHotspots()
    fitAircraftToView()
    resetFlightSmoothing()
    if (props.telemetry) ingestTelemetryFrame(props.telemetry)
  } catch (error) {
    if (generation !== rebuildGeneration) return
    assetError.value = errorText(error)
    console.error('[UAV Studio] 3D asset contract failed:', error)
  } finally {
    if (generation === rebuildGeneration) {
      loadingAssets.value = false
      syncVisualTestProbe()
    }
  }
}

function buildWorld(): void {
  scene = new THREE.Scene()
  vehicleGroup = new THREE.Group()
  vehicleGroup.name = 'vehicle-pose-root'
  scene.add(vehicleGroup)

  aircraftRenderer = new AircraftRenderer()
  vehicleGroup.add(aircraftRenderer.root)
  overlayGroup = new THREE.Group()
  overlayGroup.name = 'engineering-overlays'
  vehicleGroup.add(overlayGroup)

  scene.add(new THREE.HemisphereLight(0xffffff, 0x6f8095, 1.45))
  keyLight = new THREE.DirectionalLight(0xffffff, 1.9)
  keyLight.position.set(3.8, 6.5, 4.8)
  keyLight.castShadow = true
  keyLight.shadow.mapSize.set(2048, 2048)
  keyLight.shadow.camera.near = 0.1
  keyLight.shadow.camera.far = 22
  keyLight.shadow.camera.left = -5
  keyLight.shadow.camera.right = 5
  keyLight.shadow.camera.top = 5
  keyLight.shadow.camera.bottom = -5
  scene.add(keyLight)

  const fill = new THREE.DirectionalLight(0xb9d7ff, 0.65)
  fill.position.set(-4, 2.5, -3)
  scene.add(fill)

  const ground = new THREE.Mesh(
    new THREE.PlaneGeometry(24, 24),
    new THREE.ShadowMaterial({ color: 0x29425f, opacity: 0.12 }),
  )
  ground.rotation.x = -Math.PI / 2
  ground.position.y = -0.16
  ground.receiveShadow = true
  scene.add(ground)

  gridHelper = new THREE.GridHelper(18, 36, 0x9fb1c5, 0xd3dde8)
  gridHelper.position.y = -0.158
  const gridMaterials = Array.isArray(gridHelper.material) ? gridHelper.material : [gridHelper.material]
  gridMaterials.forEach(material => {
    material.opacity = 0.38
    material.transparent = true
  })
  scene.add(gridHelper)

  axesHelper = new THREE.AxesHelper(0.62)
  axesHelper.position.set(-2.15, -0.145, 1.45)
  scene.add(axesHelper)

  windArrow = new THREE.ArrowHelper(
    new THREE.Vector3(-1, 0, 0),
    new THREE.Vector3(2.1, 0.72, -0.3),
    1.05,
    0x2f80ed,
    0.14,
    0.08,
  )
  scene.add(windArrow)

  trajectoryLine = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0)]),
    new THREE.LineBasicMaterial({ color: 0x2563eb, transparent: true, opacity: 0.68 }),
  )
  scene.add(trajectoryLine)
}

function displayPixelRatio(): number {
  if (visualTestProbeEnabled) return 1
  const quality = settingsStore.settings.display_3d.quality
  if (quality === 'performance') return 1
  if (quality === 'high') return Math.min(window.devicePixelRatio, 2)
  return Math.min(window.devicePixelRatio, 1.5)
}

function shadowMapSize(): number {
  const quality = settingsStore.settings.display_3d.shadows
  if (quality === 'low') return 1024
  if (quality === 'high') return 4096
  return 2048
}

function applyDisplaySettings(): void {
  if (!renderer || !scene) return
  const settings = settingsStore.settings.display_3d
  renderer.setPixelRatio(displayPixelRatio())
  renderer.shadowMap.enabled = settings.shadows !== 'off'
  if (keyLight) {
    keyLight.castShadow = settings.shadows !== 'off'
    const size = shadowMapSize()
    keyLight.shadow.mapSize.set(size, size)
  }
  scene.environment = settings.environment_reflection ? environmentTexture : null
  if (gridHelper) gridHelper.visible = settings.show_grid
  if (axesHelper) axesHelper.visible = settings.show_axes
  if (cgMarker) cgMarker.visible = settings.show_cg && (assemblyMode.value ? Boolean(props.engineering) : Boolean(props.telemetry))
  thrustArrows.forEach(arrow => { arrow.visible = settings.show_thrust_vectors && !assemblyMode.value })
  if (gravityArrow) gravityArrow.visible = settings.show_gravity_vector && !assemblyMode.value
  if (windArrow) windArrow.visible = settings.show_wind_vector && !assemblyMode.value
  if (trajectoryLine) trajectoryLine.visible = settings.show_trajectory && !assemblyMode.value
  resize()
}

function applyAssemblyState(): void {
  if (!aircraftRenderer || !overlayGroup) return
  aircraftRenderer.applyAssemblyState(
    props.aircraft,
    props.selectedSlot ?? null,
    props.issueSlots,
    props.issueMounts,
    props.selectedMountId ?? null,
    props.issueMountIds,
    props.pendingInstall?.slot ?? null,
    hoveredMountId.value,
  )
  const display = settingsStore.settings.display_3d
  thrustArrows.forEach(arrow => { arrow.visible = display.show_thrust_vectors && !assemblyMode.value && !props.grounded })
  if (gravityArrow) gravityArrow.visible = display.show_gravity_vector && !assemblyMode.value && !props.grounded
  if (windArrow) windArrow.visible = display.show_wind_vector && !assemblyMode.value && !props.grounded
  if (trajectoryLine) trajectoryLine.visible = display.show_trajectory && !assemblyMode.value && !props.grounded

  if (cgMarker) {
    cgMarker.visible = display.show_cg && (assemblyMode.value ? Boolean(props.engineering) : Boolean(props.telemetry))
    if (props.engineering) {
      cgMarker.position.copy(simulationVectorToThree(props.engineering.center_of_gravity_m))
    }
  }
  syncVisualTestProbe()
}

function addTrajectoryPoint(point: THREE.Vector3): void {
  const last = trajectoryPoints[trajectoryPoints.length - 1]
  if (!last || last.distanceTo(point) > 0.05) {
    trajectoryPoints.push(point)
    const limit = Math.max(100, settingsStore.settings.display_3d.trajectory_points)
    while (trajectoryPoints.length > limit) trajectoryPoints.shift()
    trajectoryLine.geometry.dispose()
    trajectoryLine.geometry = new THREE.BufferGeometry().setFromPoints(trajectoryPoints)
  }
}

function restAircraftOnGround(): THREE.Vector3 {
  const bounds = new THREE.Box3().setFromObject(aircraftRenderer.root)
  const lowestPoint = Number.isFinite(bounds.min.y) ? bounds.min.y : -0.15
  // The scene ground is y=-0.16. A 5 mm visual clearance avoids mesh flicker
  // while keeping the lowest point of the aircraft visibly on the floor.
  return new THREE.Vector3(0, -0.155 - lowestPoint, 0)
}

function ingestTelemetryFrame(frame: TelemetryFrame): void {
  if (!vehicleGroup || !overlayGroup) return
  const pose = simulationPoseToThree(
    props.grounded ? { x: 0, y: 0, z: 0 } : frame.position,
    props.grounded ? { roll: 0, pitch: 0, yaw: 0 } : frame.attitude,
  )
  if (props.grounded) pose.position.copy(restAircraftOnGround())

  if (frame.t < lastTelemetryTime) {
    trajectoryPoints = []
    trajectoryLine.geometry.dispose()
    trajectoryLine.geometry = new THREE.BufferGeometry().setFromPoints([pose.position.clone()])
    resetFlightSmoothing()
  }
  lastTelemetryTime = frame.t

  flightSmoothing.targetPosition.copy(pose.position)
  flightSmoothing.targetQuaternion.setFromEuler(pose.rotation)
  flightSmoothing.targetCg.copy(simulationVectorToThree(frame.center_of_gravity))
  flightSmoothing.targetThrusts = props.grounded
    ? [...frame.motors.outputs]
    : [...frame.motors.thrusts_n]
  flightSmoothing.targetGravityN = frame.forces.gravity_n

  const radians = (frame.wind.direction_deg * Math.PI) / 180
  flightSmoothing.targetWindVector.set(-Math.cos(radians), 0, Math.sin(radians))
  if (flightSmoothing.targetWindVector.lengthSq() < 1e-6) {
    flightSmoothing.targetWindVector.set(-1, 0, 0)
  }
  flightSmoothing.targetWindVector.normalize().multiplyScalar(frame.wind.speed_mps)

  if (!flightSmoothing.initialized) {
    flightSmoothing.renderedPosition.copy(flightSmoothing.targetPosition)
    flightSmoothing.renderedQuaternion.copy(flightSmoothing.targetQuaternion)
    flightSmoothing.renderedCg.copy(flightSmoothing.targetCg)
    flightSmoothing.renderedThrusts = [...flightSmoothing.targetThrusts]
    flightSmoothing.renderedGravityN = flightSmoothing.targetGravityN
    flightSmoothing.renderedWindVector.copy(flightSmoothing.targetWindVector)
    vehicleGroup.position.copy(flightSmoothing.renderedPosition)
    vehicleGroup.quaternion.copy(flightSmoothing.renderedQuaternion)
    flightSmoothing.initialized = true
  } else if (props.grounded) {
    // A ground test bench must react immediately to Stop. Flight smoothing is
    // useful in the air, but would make a stopped propeller keep coasting.
    flightSmoothing.renderedPosition.copy(flightSmoothing.targetPosition)
    flightSmoothing.renderedQuaternion.copy(flightSmoothing.targetQuaternion)
    flightSmoothing.renderedThrusts = [...flightSmoothing.targetThrusts]
    vehicleGroup.position.copy(flightSmoothing.renderedPosition)
    vehicleGroup.quaternion.copy(flightSmoothing.renderedQuaternion)
  }

  if (!props.grounded) addTrajectoryPoint(pose.position.clone())
}

function advanceSmoothedFlight(dt: number): void {
  if (!props.telemetry || !flightSmoothing.initialized) return

  if (props.grounded) {
    vehicleGroup.position.copy(flightSmoothing.targetPosition)
    vehicleGroup.quaternion.copy(flightSmoothing.targetQuaternion)
    flightSmoothing.renderedThrusts = [...flightSmoothing.targetThrusts]
    return
  }

  const positionAlpha = 1 - Math.exp(-dt * 11)
  const rotationAlpha = 1 - Math.exp(-dt * 13)
  const scalarAlpha = 1 - Math.exp(-dt * 8)

  flightSmoothing.renderedPosition.lerp(flightSmoothing.targetPosition, positionAlpha)
  flightSmoothing.renderedQuaternion.slerp(flightSmoothing.targetQuaternion, rotationAlpha)
  flightSmoothing.renderedCg.lerp(flightSmoothing.targetCg, positionAlpha)
  flightSmoothing.renderedWindVector.lerp(flightSmoothing.targetWindVector, scalarAlpha)
  flightSmoothing.renderedGravityN += (flightSmoothing.targetGravityN - flightSmoothing.renderedGravityN) * scalarAlpha

  flightSmoothing.targetThrusts.forEach((target, index) => {
    const current = flightSmoothing.renderedThrusts[index] ?? 0
    flightSmoothing.renderedThrusts[index] = current + (target - current) * scalarAlpha
  })

  vehicleGroup.position.copy(flightSmoothing.renderedPosition)
  vehicleGroup.quaternion.copy(flightSmoothing.renderedQuaternion)

  if (cgMarker) {
    cgMarker.visible = true
    cgMarker.position.copy(flightSmoothing.renderedCg)
  }

  flightSmoothing.renderedThrusts.forEach((thrust, index) => {
    thrustArrows[index]?.setLength(0.16 + Math.min(1.0, thrust / 16), 0.095, 0.055)
  })

  gravityArrow?.setLength(0.30 + Math.min(0.68, flightSmoothing.renderedGravityN / 62), 0.10, 0.06)
  gravityArrow?.setRotationFromQuaternion(vehicleGroup.quaternion.clone().invert())

  const windSpeed = flightSmoothing.renderedWindVector.length()
  const windDirection = windSpeed > 1e-6
    ? flightSmoothing.renderedWindVector.clone().normalize()
    : new THREE.Vector3(-1, 0, 0)
  windArrow?.setDirection(windDirection)
  windArrow?.setLength(0.42 + Math.min(1.5, windSpeed / 5), 0.14, 0.08)
}

function preferredLabelSide(slot: AssemblySlot): 'left' | 'right' | undefined {
  if (slot === 'frame' || slot === 'battery' || slot === 'payload') return 'left'
  if (slot === 'flight_controller' || slot === 'gnss' || slot === 'power_module') return 'right'
  return undefined
}

function projectedPartPoint(
  point: { x: number; y: number; z: number },
): { x: number; y: number; visible: boolean } {
  if (!host.value || !camera || !aircraftRenderer) return { x: 0, y: 0, visible: false }
  const world = aircraftRenderer.root.localToWorld(new THREE.Vector3(point.x, point.y, point.z))
  const projected = world.project(camera)
  return {
    x: (projected.x * 0.5 + 0.5) * host.value.clientWidth,
    y: (-projected.y * 0.5 + 0.5) * host.value.clientHeight,
    visible: projected.z >= -1 && projected.z <= 1,
  }
}

function updateExplodedComponentLabels(): void {
  if (
    !host.value ||
    !aircraftRenderer ||
    !assemblyMode.value ||
    assemblyViewMode.value !== 'exploded' ||
    explosionProgress.value < 0.72
  ) {
    if (explodedComponentLabels.value.length > 0) explodedComponentLabels.value = []
    return
  }

  const parts = aircraftRenderer.explodedPartsSnapshot()
  const descriptors = buildExplodedLabelDescriptors(props.components, parts)
  const viewportWidth = host.value.clientWidth
  const viewportHeight = host.value.clientHeight
  const centerX = viewportWidth / 2
  const centerY = viewportHeight / 2

  const anchors = descriptors.flatMap(descriptor => {
    const candidates = parts
      .filter(part => part.slot === descriptor.slot && part.installed && part.componentId === descriptor.componentId)
      .map(part => projectedPartPoint(part.currentPosition))
      .filter(point => point.visible)
    if (candidates.length === 0) return []

    // Repeated propulsion components use the visually outermost instance as
    // the anchor, keeping their single ×4 label away from the aircraft center.
    const anchor = candidates.reduce((best, point) => {
      const bestDistance = Math.abs(best.x - centerX) + Math.abs(best.y - centerY) * 0.18
      const pointDistance = Math.abs(point.x - centerX) + Math.abs(point.y - centerY) * 0.18
      return pointDistance > bestDistance ? point : best
    })

    return [{
      key: descriptor.key,
      x: anchor.x,
      y: anchor.y,
      preferredSide: preferredLabelSide(descriptor.slot),
    }]
  })

  const placements = layoutExplodedLabels(anchors, viewportWidth, viewportHeight)
  const descriptorByKey = new Map(descriptors.map(descriptor => [descriptor.key, descriptor]))
  explodedComponentLabels.value = placements.flatMap(placement => {
    const descriptor = descriptorByKey.get(placement.key as AssemblySlot)
    if (!descriptor) return []
    const mountIssue = props.issueMounts.length > 0 && (
      descriptor.slot === 'motor' || descriptor.slot === 'propeller'
    )
    return [{
      key: descriptor.key,
      slot: descriptor.slot,
      title: descriptor.title,
      meta: descriptor.meta,
      left: placement.left,
      top: placement.top,
      selected: props.selectedSlot === descriptor.slot,
      issue: props.issueSlots.includes(descriptor.slot) || mountIssue,
    }]
  })
}

function mountShortLabel(mount: MountPoint): string {
  return mount.motorName ?? (
    mount.slot === 'battery' ? 'BAT'
      : mount.slot === 'flight_controller' ? 'FC'
        : mount.slot === 'power_module' ? 'PWR'
          : mount.slot === 'gnss' ? 'GNSS'
            : mount.slot === 'payload' ? 'PAY'
              : mount.slot.toUpperCase()
  )
}

function updateMountHotspots(): void {
  if (
    !host.value ||
    !aircraftRenderer ||
    !props.pendingInstall ||
    assemblyViewMode.value !== 'assembled'
  ) {
    if (mountHotspots.value.length > 0) mountHotspots.value = []
    return
  }

  const missing = missingMountsForSlot(
    props.aircraft,
    resolvedMountPoints.value,
    props.pendingInstall.slot,
  )
  mountHotspots.value = missing.flatMap(mount => {
    const point = projectedPartPoint(simulationVectorToThree(mount.position))
    if (!point.visible) return []
    return [{
      mountId: mount.id,
      label: mount.label,
      shortLabel: mountShortLabel(mount),
      left: point.x,
      top: point.y,
    }]
  })
}

function hoverMount(mountId: string): void {
  hoveredMountId.value = mountId
  applyAssemblyState()
  syncVisualTestProbe()
}

function leaveMount(mountId: string): void {
  if (hoveredMountId.value !== mountId) return
  hoveredMountId.value = null
  applyAssemblyState()
  syncVisualTestProbe()
}

function installMount(mountId: string): void {
  hoveredMountId.value = null
  applyAssemblyState()
  emit('install-at-mount', mountId)
}

function startInstallationAnimationIfNeeded(): void {
  const request = props.installAnimation
  if (!request || request.serial === lastInstallationSerial || !aircraftRenderer) return
  const exists = aircraftRenderer
    .partInstancesSnapshot()
    .some(item => item.mountId === request.mountId && item.installed)
  if (!exists) return
  lastInstallationSerial = request.serial
  activeInstallation = {
    mountId: request.mountId,
    progress: 0,
    serial: request.serial,
    mode: 'install',
  }
  aircraftRenderer.setInstallationProgress(request.mountId, 0)
  syncVisualTestProbe()
}

function startRemovalAnimationIfNeeded(): void {
  const request = props.removeAnimation
  if (!request || request.serial === lastRemovalSerial || !aircraftRenderer) return
  const exists = aircraftRenderer
    .partInstancesSnapshot()
    .some(item => item.mountId === request.mountId && item.installed)
  if (!exists) return
  lastRemovalSerial = request.serial
  activeInstallation = {
    mountId: request.mountId,
    progress: 1,
    serial: request.serial,
    mode: 'remove',
  }
  aircraftRenderer.setInstallationProgress(request.mountId, 1)
  syncVisualTestProbe()
}

function advanceInstallationAnimation(dt: number): void {
  if (!activeInstallation || !aircraftRenderer) return

  if (activeInstallation.mode === 'install') {
    activeInstallation.progress = Math.min(1, activeInstallation.progress + dt / 0.46)
    const t = activeInstallation.progress
    const eased = 1 - Math.pow(1 - t, 3)
    aircraftRenderer.setInstallationProgress(activeInstallation.mountId, eased)
    if (t >= 1) {
      aircraftRenderer.setInstallationProgress(activeInstallation.mountId, 1)
      activeInstallation = null
      syncVisualTestProbe()
    }
    return
  }

  activeInstallation.progress = Math.max(0, activeInstallation.progress - dt / 0.34)
  const t = activeInstallation.progress
  const eased = t * t * (3 - 2 * t)
  aircraftRenderer.setInstallationProgress(activeInstallation.mountId, eased)
  if (t <= 0) {
    aircraftRenderer.setInstallationProgress(activeInstallation.mountId, 0)
    activeInstallation = null
    syncVisualTestProbe()
  }
}

function setAssemblyViewMode(mode: AssemblyViewMode): void {
  if (!assemblyMode.value || assemblyViewMode.value === mode) return
  if (mode === 'exploded' && props.pendingInstall) return
  assemblyViewMode.value = mode
  if (cameraMode.value === 'follow') setCameraMode('free')
  buildOverlay()
  updateExplodedComponentLabels()
  syncVisualTestProbe()
}

let lastFittedExplosionTarget = -1

function advanceExplodedView(dt: number): void {
  if (!aircraftRenderer) return
  const target = assemblyMode.value && assemblyViewMode.value === 'exploded' ? 1 : 0
  const alpha = 1 - Math.exp(-dt * 6.5)
  let next = explosionProgress.value + (target - explosionProgress.value) * alpha
  if (Math.abs(target - next) < 0.0015) next = target

  if (Math.abs(next - explosionProgress.value) > 1e-6) {
    explosionProgress.value = next
    aircraftRenderer.setExplodedProgress(next)
    updateExplodedComponentLabels()
    syncVisualTestProbe()
  }

  if (next === target && lastFittedExplosionTarget !== target && !props.telemetry) {
    lastFittedExplosionTarget = target
    fitAircraftToView()
  }
}

function setPointer(event: PointerEvent): void {
  const canvas = renderer?.domElement
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
}

function sceneTargetAtPointer(
  event: PointerEvent,
): { slot: AssemblySlot; mountId: string | null } | null {
  if (!props.interactive || !aircraftRenderer) return null
  setPointer(event)
  raycaster.setFromCamera(pointer, camera)
  const hit = raycaster.intersectObjects(aircraftRenderer.raycastMeshes(), false)[0]
  if (!hit) return null
  const slot = aircraftRenderer.slotForObject(hit.object)
  if (!slot) return null
  return {
    slot,
    mountId: aircraftRenderer.mountForObject(hit.object),
  }
}

function onPointerDown(event: PointerEvent): void {
  const target = sceneTargetAtPointer(event)
  if (!target) return
  emit('select-slot', target.slot)
  if (target.mountId) emit('select-mount', target.mountId, target.slot)
}

function onPointerMove(event: PointerEvent): void {
  cursor.value = sceneTargetAtPointer(event) ? 'pointer' : 'default'
}


function setCameraMode(mode: typeof cameraMode.value): void {
  cameraMode.value = mode
  controls.enableRotate = true
  controls.enablePan = mode === 'free'
  if (mode !== 'free') updateManagedCamera(0.016, true)
  syncVisualTestProbe()
}

function fitAircraftToView(): void {
  if (!camera || !controls || !aircraftRenderer || props.telemetry) return
  const bounds = aircraftRenderer.aircraftBoundsSnapshot()
  const span = Math.max(bounds.width, bounds.height, bounds.depth, 0.45)
  const distance = Math.min(5.2, Math.max(1.55, span * 2.65))
  const target = new THREE.Vector3(0, 0.03, 0)
  controls.target.copy(target)
  cameraTargetState.copy(target)
  if (cameraMode.value === 'free') {
    camera.position.set(distance * 0.72, distance * 0.48, distance * 0.88)
  }
  camera.updateProjectionMatrix()
  controls.update()
}

function cameraTarget(): THREE.Vector3 {
  if (props.telemetry && flightSmoothing.initialized) {
    return flightSmoothing.renderedPosition.clone().add(new THREE.Vector3(0, 0.08, 0))
  }
  return vehicleGroup?.position.clone().add(new THREE.Vector3(0, 0.08, 0))
    ?? new THREE.Vector3(0, 0.08, 0)
}

function updateManagedCamera(dt: number, immediate = false): void {
  if (cameraMode.value === 'free' || !camera || !controls) return
  const target = cameraTarget()
  let offset = new THREE.Vector3(2.2, 1.45, 2.7)
  if (cameraMode.value === 'top') offset = new THREE.Vector3(0.001, 4.2, 0.001)
  if (cameraMode.value === 'side') offset = new THREE.Vector3(0.05, 1.05, 3.6)
  const desired = target.clone().add(offset)
  if (immediate) {
    camera.position.copy(desired)
    controls.target.copy(target)
    cameraTargetState.copy(target)
  } else {
    const cameraAlpha = 1 - Math.exp(-dt * 4.2)
    camera.position.lerp(desired, cameraAlpha)
    cameraTargetState.lerp(target, 1 - Math.exp(-dt * 5.2))
    controls.target.copy(cameraTargetState)
  }
}

function animate(now = performance.now()): void {
  animationId = requestAnimationFrame(animate)
  const dt = Math.min(0.05, Math.max(0, (now - previousAnimationTime) / 1000))
  previousAnimationTime = now
  advanceExplodedView(dt)
  advanceInstallationAnimation(dt)
  advanceSmoothedFlight(dt)
  const rotorInputs = props.telemetry ? flightSmoothing.renderedThrusts : undefined
  aircraftRenderer?.rotateRotors(
    rotorInputs?.map(output => output * Math.min(1.35, dt * 60)),
  )
  updateManagedCamera(dt)
  controls?.update()
  updateExplodedComponentLabels()
  updateMountHotspots()
  renderer?.render(scene, camera)
}

function resize(): void {
  if (!host.value || !renderer || !camera) return
  const width = host.value.clientWidth
  const height = host.value.clientHeight
  renderer.setSize(width, height, false)
  camera.aspect = width / Math.max(1, height)
  camera.updateProjectionMatrix()
}

const componentSignature = computed(() => {
  const aircraft = props.aircraft
  return [
    aircraft?.frame_id,
    aircraft?.motor_id,
    aircraft?.esc_id,
    aircraft?.propeller_id,
    aircraft?.propeller_directions?.M1,
    aircraft?.propeller_directions?.M2,
    aircraft?.propeller_directions?.M3,
    aircraft?.propeller_directions?.M4,
    aircraft?.battery_id,
    aircraft?.power_module_id,
    aircraft?.flight_controller_id,
    aircraft?.gnss_id,
    aircraft?.payload_id,
    aircraft?.assembly_instances
      ?.map(item => `${item.mount_id}:${item.component_id}`)
      .sort()
      .join(',') ?? 'LEGACY',
    props.components
      .map(component => `${component.id}:${component.visual?.asset_key ?? 'NO_VISUAL'}`)
      .join(','),
  ].join('|')
})

onMounted(async () => {
  if (!host.value) return
  camera = new THREE.PerspectiveCamera(44, 1, 0.03, 100)
  camera.position.set(2.4, 1.6, 3.0)

  await settingsStore.initialize()
  renderer = new THREE.WebGLRenderer({ antialias: settingsStore.settings.display_3d.antialias, alpha: true })
  renderer.setPixelRatio(displayPixelRatio())
  renderer.setClearColor(0x000000, 0)
  renderer.shadowMap.enabled = settingsStore.settings.display_3d.shadows !== 'off'
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.0
  host.value.appendChild(renderer.domElement)

  pmrem = new THREE.PMREMGenerator(renderer)
  const environment = new RoomEnvironment()
  environmentTexture = pmrem.fromScene(environment, 0.04).texture

  buildWorld()
  scene.environment = settingsStore.settings.display_3d.environment_reflection ? environmentTexture : null

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.06
  controls.minDistance = 0.65
  controls.maxDistance = 12
  controls.target.set(0, 0.05, 0)
  renderer.domElement.addEventListener('pointerdown', onPointerDown)
  renderer.domElement.addEventListener('pointermove', onPointerMove)

  const configuredCamera = settingsStore.settings.display_3d.default_camera
  setCameraMode(assemblyMode.value && configuredCamera === 'follow' ? 'free' : configuredCamera)
  applyDisplaySettings()
  resize()
  window.addEventListener('resize', resize)
  syncVisualTestProbe()
  await rebuildAircraftAssets()
  if (props.telemetry) ingestTelemetryFrame(props.telemetry)
  applyAssemblyState()
  previousAnimationTime = performance.now()
  animate()
})

watch(componentSignature, () => { void rebuildAircraftAssets() })
watch(() => settingsStore.settings.display_3d, () => { applyDisplaySettings() }, { deep: true })
watch(() => props.telemetry, frame => { if (frame) ingestTelemetryFrame(frame) }, { deep: true })
watch(
  () => [
    props.selectedSlot,
    props.selectedMountId,
    props.issueSlots,
    props.issueMounts,
    props.issueMountIds,
    props.engineering,
    props.aircraft,
  ] as const,
  () => {
    refreshSpatialDiagnostics()
    applyAssemblyState()
    buildOverlay()
    updateExplodedComponentLabels()
    updateMountHotspots()
  },
  { deep: true },
)
watch(
  () => props.pendingInstall,
  () => {
    if (props.pendingInstall) {
      assemblyViewMode.value = 'assembled'
    } else {
      hoveredMountId.value = null
    }
    updateMountHotspots()
    syncVisualTestProbe()
  },
  { deep: true },
)
watch(
  () => props.installAnimation,
  () => { startInstallationAnimationIfNeeded() },
  { deep: true },
)
watch(
  () => props.removeAnimation,
  () => { startRemovalAnimationIfNeeded() },
  { deep: true },
)

onBeforeUnmount(() => {
  rebuildGeneration += 1
  cancelAnimationFrame(animationId)
  window.removeEventListener('resize', resize)
  renderer?.domElement.removeEventListener('pointerdown', onPointerDown)
  renderer?.domElement.removeEventListener('pointermove', onPointerMove)
  controls?.dispose()
  aircraftRenderer?.dispose()
  clearOverlay()
  trajectoryLine?.geometry.dispose()
  ;(trajectoryLine?.material as THREE.Material | undefined)?.dispose()
  environmentTexture?.dispose()
  pmrem?.dispose()
  renderer?.dispose()
  renderer?.domElement.remove()
  if (visualTestProbeEnabled) delete window.__UAV_VISUAL_TEST__
})
</script>

<style scoped>
.asset-scene {
  background:
    radial-gradient(circle at 50% 26%, rgba(255,255,255,.98) 0%, rgba(237,244,255,.96) 38%, rgba(222,232,247,.98) 100%);
}
.asset-toolbar button.scene-chip {
  border: 0;
  background: transparent;
  cursor: pointer;
  transition: background .18s ease, color .18s ease, transform .18s ease;
}
.asset-toolbar button.scene-chip:hover,
.asset-toolbar button.scene-chip.active {
  color: #1f6feb;
  background: #edf5ff;
}
.asset-toolbar button.scene-chip:hover {
  transform: translateY(-1px);
}
.grounded-readout b { color:#18794e; }
.asset-error {
  position: absolute;
  z-index: 10;
  left: 50%;
  top: 50%;
  width: min(480px, calc(100% - 48px));
  transform: translate(-50%, -50%);
  display: grid;
  gap: 6px;
  padding: 14px 16px;
  border: 1px solid #efc5c0;
  border-radius: 12px;
  background: rgba(255, 247, 246, .96);
  color: #9f2f25;
  box-shadow: 0 12px 30px rgba(110, 38, 31, .12);
  font-size: 11px;
}
.asset-error b {
  font-size: 13px;
}
.scene-selection.issue { border-color:#efb2ac; background:rgba(255,247,246,.94); }
.scene-selection.issue b,.scene-selection.issue span { color:#9f2f25; }
.legend-issue { background:#dc2626; }

.scene-toolbar-divider {
  width: 1px;
  height: 20px;
  align-self: center;
  background: rgba(132, 151, 177, .28);
  margin: 0 2px;
}
.exploded-label-layer {
  position: absolute;
  inset: 0;
  z-index: 6;
  pointer-events: none;
}
.exploded-component-label {
  position: absolute;
  width: 164px;
  height: 26px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 7px;
  overflow: hidden;
  border: 1px solid rgba(105, 167, 219, .28);
  border-radius: 8px;
  background: rgba(9, 20, 35, .86);
  color: #edf6ff;
  box-shadow: 0 6px 14px rgba(5, 14, 28, .16);
  backdrop-filter: blur(7px);
}
.exploded-component-label.selected {
  border-color: rgba(96, 165, 250, .82);
  box-shadow: 0 0 0 1px rgba(37, 99, 235, .22), 0 6px 14px rgba(5, 14, 28, .16);
}
.exploded-component-label.issue {
  border-color: rgba(248, 113, 113, .82);
  background: rgba(52, 18, 23, .90);
}
.exploded-label-type {
  flex: 0 0 auto;
  color: #7dd3fc;
  font-size: 9px;
  font-weight: 750;
  white-space: nowrap;
}
.exploded-component-label.issue .exploded-label-type { color: #fca5a5; }
.exploded-component-label b {
  min-width: 0;
  overflow: hidden;
  color: #f8fbff;
  font-size: 10px;
  font-weight: 650;
  line-height: 1;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.exploded-view-hint {
  position: absolute;
  z-index: 4;
  top: 58px;
  right: 12px;
  display: grid;
  gap: 3px;
  min-width: 172px;
  padding: 9px 11px;
  border: 1px solid rgba(190, 205, 222, .92);
  border-radius: 12px;
  background: rgba(255,255,255,.88);
  color: #607087;
  font-size: 10px;
  pointer-events: none;
  box-shadow: 0 10px 25px rgba(9, 20, 42, 0.08);
  backdrop-filter: blur(10px);
}
.exploded-view-hint b {
  margin-bottom: 2px;
  color: #203047;
  font-size: 11px;
}


.asset-toolbar button.scene-chip:disabled {
  cursor: not-allowed;
  opacity: .42;
  transform: none;
}
.assembly-install-banner {
  position: absolute;
  z-index: 7;
  left: 50%;
  top: 58px;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 300px;
  max-width: min(520px, calc(100% - 260px));
  padding: 8px 12px;
  border: 1px solid rgba(78, 148, 239, .42);
  border-radius: 12px;
  background: rgba(244, 249, 255, .92);
  box-shadow: 0 8px 26px rgba(30, 82, 148, .12);
  backdrop-filter: blur(10px);
  pointer-events: none;
}
.assembly-install-banner .install-pulse {
  width: 9px;
  height: 9px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: #2583f7;
  box-shadow: 0 0 0 5px rgba(37, 131, 247, .13);
  animation: installPulse 1.35s ease-in-out infinite;
}
.assembly-install-banner div {
  min-width: 0;
  display: grid;
  gap: 1px;
}
.assembly-install-banner b {
  color: #164b85;
  font-size: 11px;
}
.assembly-install-banner small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #68809c;
  font-size: 9px;
}
.mount-hotspot-layer {
  position: absolute;
  inset: 0;
  z-index: 8;
  pointer-events: none;
}
.mount-hotspot {
  position: absolute;
  width: 42px;
  height: 42px;
  transform: translate(-50%, -50%);
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 50%;
  background: transparent;
  color: #165fae;
  cursor: pointer;
  pointer-events: auto;
}
.mount-hotspot > span {
  position: absolute;
  inset: 7px;
  border: 2px solid rgba(43, 137, 244, .88);
  border-radius: 50%;
  background: rgba(91, 174, 255, .10);
  box-shadow:
    0 0 0 5px rgba(59, 130, 246, .08),
    0 0 20px rgba(37, 99, 235, .20);
  animation: anchorPulse 1.45s ease-in-out infinite;
}
.mount-hotspot b {
  position: absolute;
  top: 36px;
  min-width: 30px;
  padding: 2px 5px;
  border: 1px solid rgba(141, 176, 218, .62);
  border-radius: 7px;
  background: rgba(255, 255, 255, .92);
  color: #285b95;
  font-size: 8px;
  line-height: 1;
  box-shadow: 0 3px 10px rgba(27, 62, 104, .08);
}
.mount-hotspot.hovered > span,
.mount-hotspot:hover > span,
.mount-hotspot:focus-visible > span {
  border-color: #00a7e8;
  background: rgba(0, 174, 239, .16);
  box-shadow:
    0 0 0 7px rgba(0, 167, 232, .10),
    0 0 26px rgba(0, 130, 210, .34);
  transform: scale(1.08);
}
.spatial-diagnostic-pill {
  position: absolute;
  z-index: 6;
  right: 12px;
  bottom: 48px;
  display: grid;
  gap: 2px;
  max-width: 270px;
  padding: 7px 9px;
  border: 1px solid #f0d49b;
  border-radius: 9px;
  background: rgba(255, 251, 237, .93);
  color: #8a6418;
  font-size: 9px;
  pointer-events: none;
}
.spatial-diagnostic-pill.error {
  border-color: #efb3ad;
  background: rgba(255, 246, 245, .94);
  color: #a7382f;
}
.spatial-diagnostic-pill b {
  font-size: 10px;
}
@keyframes anchorPulse {
  50% { transform: scale(1.12); opacity: .68; }
}
@keyframes installPulse {
  50% { transform: scale(.78); opacity: .62; }
}
</style>
