<template>
  <div ref="host" class="drone-scene asset-scene" :style="{ cursor }" @pointerleave="cursor = 'default'">
    <div class="scene-toolbar asset-toolbar">
      <span class="scene-chip scene-chip-active">三维视图</span>
      <button :class="['scene-chip', { active: cameraMode === 'follow' }]" @click="setCameraMode('follow')">跟随</button>
      <button :class="['scene-chip', { active: cameraMode === 'top' }]" @click="setCameraMode('top')">俯视</button>
      <button :class="['scene-chip', { active: cameraMode === 'side' }]" @click="setCameraMode('side')">侧视</button>
      <button :class="['scene-chip', { active: cameraMode === 'free' }]" @click="setCameraMode('free')">自由</button>
    </div>

    <div class="asset-badge" :class="{ loading: loadingAssets, failed: Boolean(assetError) }">
      <span></span>
      {{ assetError ? '3D 资产异常' : loadingAssets ? '正在加载模型' : 'GLB 教学模型' }}
    </div>

    <div v-if="assetError" class="asset-error" data-testid="asset-error">
      <b>3D 资产加载失败</b>
      <span>{{ assetError }}</span>
    </div>

    <div v-if="telemetry" class="scene-readout">
      <div><span>时间</span><b>{{ telemetry.t.toFixed(1) }} s</b></div>
      <div><span>高度</span><b>{{ telemetry.position.z.toFixed(1) }} m</b></div>
      <div><span>位置</span><b>({{ telemetry.position.x.toFixed(1) }}, {{ telemetry.position.y.toFixed(1) }}, {{ telemetry.position.z.toFixed(1) }}) m</b></div>
    </div>

    <div v-if="telemetry" class="wind-readout">风场 {{ telemetry.wind.speed_mps.toFixed(1) }} m/s</div>

    <div v-if="assemblyMode" :class="['scene-selection', { issue: issueSlots.length > 0 }]">
      <b>{{ selectedSlot ? SLOT_LABELS[selectedSlot] : '选择部件' }}</b>
      <span v-if="issueSlots.length > 0">红色高亮为当前工程检查问题</span>
      <span v-else>{{ selectedSlot ? '蓝色高亮为当前检查部件' : '点击机架、电机、桨、电池等模型查看详情' }}</span>
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
import { AircraftRenderer } from '../three/AircraftRenderer'
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
  },
)

const emit = defineEmits<{
  (event: 'select-slot', slot: AssemblySlot): void
}>()

const host = ref<HTMLDivElement | null>(null)
const cursor = ref('default')
const loadingAssets = ref(true)
const assetError = ref('')
const cameraMode = ref<'follow' | 'top' | 'side' | 'free'>('free')
const assemblyMode = computed(() => props.interactive)
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
  canvas.width = 280
  canvas.height = 54
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.fillStyle = 'rgba(255,255,255,.88)'
  ctx.roundRect(2, 4, 274, 44, 8)
  ctx.fill()
  ctx.strokeStyle = 'rgba(120,145,175,.45)'
  ctx.stroke()
  ctx.fillStyle = color
  ctx.font = '600 21px Microsoft YaHei, sans-serif'
  ctx.fillText(text, 12, 33)
  const texture = new THREE.CanvasTexture(canvas)
  texture.colorSpace = THREE.SRGBColorSpace
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false })
  const sprite = new THREE.Sprite(material)
  sprite.scale.set(0.74, 0.145, 1)
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
    const direction = directions?.[name] ?? (index % 2 === 0 ? 'CCW' : 'CW')
    addLabelSprite(
      `${name} ${direction === 'CCW' ? '逆时针' : '顺时针'}`,
      p.clone().add(new THREE.Vector3(0, 0.34, 0)),
      props.issueMounts.includes(name) ? '#b42318' : '#1f4f8f',
    )
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
  applyAssemblyState()
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
    buildOverlay()
    applyAssemblyState()
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
  )
  const display = settingsStore.settings.display_3d
  thrustArrows.forEach(arrow => { arrow.visible = display.show_thrust_vectors && !assemblyMode.value })
  if (gravityArrow) gravityArrow.visible = display.show_gravity_vector && !assemblyMode.value
  if (windArrow) windArrow.visible = display.show_wind_vector && !assemblyMode.value
  if (trajectoryLine) trajectoryLine.visible = display.show_trajectory && !assemblyMode.value

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

function ingestTelemetryFrame(frame: TelemetryFrame): void {
  if (!vehicleGroup || !overlayGroup) return
  const pose = simulationPoseToThree(frame.position, frame.attitude)

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
  flightSmoothing.targetThrusts = [...frame.motors.thrusts_n]
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
  }

  addTrajectoryPoint(pose.position.clone())
}

function advanceSmoothedFlight(dt: number): void {
  if (!props.telemetry || !flightSmoothing.initialized) return

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

function setPointer(event: PointerEvent): void {
  const canvas = renderer?.domElement
  if (!canvas) return
  const rect = canvas.getBoundingClientRect()
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
}

function sceneSlotAtPointer(event: PointerEvent): AssemblySlot | null {
  if (!props.interactive || !aircraftRenderer) return null
  setPointer(event)
  raycaster.setFromCamera(pointer, camera)
  const hit = raycaster.intersectObjects(aircraftRenderer.raycastMeshes(), false)[0]
  return hit ? aircraftRenderer.slotForObject(hit.object) : null
}

function onPointerDown(event: PointerEvent): void {
  const slot = sceneSlotAtPointer(event)
  if (slot) emit('select-slot', slot)
}

function onPointerMove(event: PointerEvent): void {
  cursor.value = sceneSlotAtPointer(event) ? 'pointer' : 'default'
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
  advanceSmoothedFlight(dt)
  const rotorInputs = props.telemetry ? flightSmoothing.renderedThrusts : undefined
  aircraftRenderer?.rotateRotors(
    rotorInputs?.map(output => output * Math.min(1.35, dt * 60)),
  )
  updateManagedCamera(dt)
  controls?.update()
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

  setCameraMode(settingsStore.settings.display_3d.default_camera)
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
  () => [props.selectedSlot, props.issueSlots, props.issueMounts, props.engineering, props.aircraft] as const,
  () => {
    applyAssemblyState()
    buildOverlay()
  },
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
.asset-badge {
  position: absolute;
  z-index: 4;
  top: 12px;
  right: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 9px;
  border-radius: 999px;
  border: 1px solid rgba(190,205,222,.9);
  background: rgba(255,255,255,.84);
  color: #526176;
  font-size: 10px;
  pointer-events: none;
  box-shadow: 0 10px 25px rgba(9, 20, 42, 0.08);
}
.asset-badge span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #16a34a;
}
.asset-badge.loading span {
  background: #d97706;
  animation: assetPulse 1s infinite ease-in-out;
}
.asset-badge.failed {
  border-color: #efc5c0;
  color: #b42318;
}
.asset-badge.failed span {
  background: #dc2626;
  animation: none;
}
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
@keyframes assetPulse { 50% { opacity: .3; } }
</style>
