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

    <div v-if="assemblyMode" class="scene-selection">
      <b>{{ selectedSlot ? SLOT_LABELS[selectedSlot] : '选择部件' }}</b>
      <span>{{ selectedSlot ? '蓝色高亮为当前检查部件' : '点击机架、电机、桨、电池等模型查看详情' }}</span>
    </div>

    <div :class="['scene-legend', { 'scene-legend-assembly': assemblyMode }]">
      <template v-if="assemblyMode">
        <span class="legend-green"></span>已安装
        <span class="legend-gray"></span>待安装
        <span class="legend-yellow"></span>重心
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
import type { AircraftDefinition, AircraftEngineeringSummary, Component } from '../types/aircraft'
import type { TelemetryFrame } from '../types/telemetry'
import { motorPositionsToThree, simulationPoseToThree, simulationVectorToThree } from '../three/coordinates'
import { AircraftRenderer } from '../three/AircraftRenderer'
import { SLOT_LABELS, type AssemblySlot } from '../utils/assembly'

const props = withDefaults(
  defineProps<{
    telemetry?: TelemetryFrame
    aircraft?: AircraftDefinition | null
    components?: Component[]
    selectedSlot?: AssemblySlot | null
    engineering?: AircraftEngineeringSummary | null
    interactive?: boolean
  }>(),
  {
    telemetry: undefined,
    aircraft: null,
    components: () => [],
    selectedSlot: null,
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
let trajectoryPoints: THREE.Vector3[] = []
let thrustArrows: THREE.ArrowHelper[] = []
let animationId = 0
let previousAnimationTime = performance.now()
let lastTelemetryTime = -1
let rebuildGeneration = 0
const raycaster = new THREE.Raycaster()
const pointer = new THREE.Vector2()

function frameComponent(): Component | null {
  if (!props.aircraft?.frame_id) return null
  return props.components.find(component => component.id === props.aircraft?.frame_id) ?? null
}

function motorDiagonal(): number {
  const value = frameComponent()?.parameters_json.motor_diagonal_m
  return typeof value === 'number' && value > 0 ? value : 0.65
}

function mountY(): number {
  return 0.066 * (motorDiagonal() / 0.65)
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
  const diagonal = motorDiagonal()
  const motors = motorPositionsToThree(diagonal)
  const y = mountY()
  const directions = ['逆时针', '顺时针', '逆时针', '顺时针']

  ;(['M1', 'M2', 'M3', 'M4'] as const).forEach((name, index) => {
    const p = motors[name].clone()
    p.y = y
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
    addLabelSprite(`${name} ${directions[index]}`, p.clone().add(new THREE.Vector3(0, 0.34, 0)))
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
    if (props.telemetry) updateFlightScene(props.telemetry)
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
  const key = new THREE.DirectionalLight(0xffffff, 2.0)
  key.position.set(3.8, 6.5, 4.8)
  key.castShadow = true
  key.shadow.mapSize.set(2048, 2048)
  key.shadow.camera.near = 0.1
  key.shadow.camera.far = 22
  key.shadow.camera.left = -5
  key.shadow.camera.right = 5
  key.shadow.camera.top = 5
  key.shadow.camera.bottom = -5
  scene.add(key)

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

  const grid = new THREE.GridHelper(18, 36, 0x9fb1c5, 0xd3dde8)
  grid.position.y = -0.158
  const gridMaterials = Array.isArray(grid.material) ? grid.material : [grid.material]
  gridMaterials.forEach(material => {
    material.opacity = 0.52
    material.transparent = true
  })
  scene.add(grid)

  const axes = new THREE.AxesHelper(0.62)
  axes.position.set(-2.15, -0.145, 1.45)
  scene.add(axes)

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
    new THREE.LineBasicMaterial({ color: 0x2563eb, transparent: true, opacity: 0.75 }),
  )
  scene.add(trajectoryLine)
}

function applyAssemblyState(): void {
  if (!aircraftRenderer || !overlayGroup) return
  aircraftRenderer.applyAssemblyState(props.aircraft, props.selectedSlot ?? null)
  thrustArrows.forEach(arrow => { arrow.visible = !assemblyMode.value })
  if (gravityArrow) gravityArrow.visible = !assemblyMode.value
  if (windArrow) windArrow.visible = !assemblyMode.value
  if (trajectoryLine) trajectoryLine.visible = !assemblyMode.value

  if (cgMarker) {
    cgMarker.visible = assemblyMode.value ? Boolean(props.engineering) : Boolean(props.telemetry)
    if (props.engineering) {
      cgMarker.position.copy(simulationVectorToThree(props.engineering.center_of_gravity_m))
    }
  }
  syncVisualTestProbe()
}

function updateFlightScene(frame: TelemetryFrame): void {
  if (!vehicleGroup || !overlayGroup) return
  const pose = simulationPoseToThree(frame.position, frame.attitude)
  vehicleGroup.position.copy(pose.position)
  vehicleGroup.rotation.copy(pose.rotation)

  if (cgMarker) {
    cgMarker.visible = true
    cgMarker.position.copy(simulationVectorToThree(frame.center_of_gravity))
  }
  frame.motors.thrusts_n.forEach((thrust, index) => {
    thrustArrows[index]?.setLength(0.16 + Math.min(1.0, thrust / 16), 0.095, 0.055)
  })
  gravityArrow?.setLength(0.30 + Math.min(0.68, frame.forces.gravity_n / 62), 0.10, 0.06)
  gravityArrow?.setRotationFromQuaternion(vehicleGroup.quaternion.clone().invert())

  const radians = (frame.wind.direction_deg * Math.PI) / 180
  windArrow?.setDirection(
    new THREE.Vector3(-Math.cos(radians), 0, Math.sin(radians)).normalize(),
  )
  windArrow?.setLength(0.42 + Math.min(1.5, frame.wind.speed_mps / 5), 0.14, 0.08)

  if (frame.t < lastTelemetryTime) {
    trajectoryPoints = []
    trajectoryLine.geometry.dispose()
    trajectoryLine.geometry = new THREE.BufferGeometry().setFromPoints([pose.position.clone()])
  }
  lastTelemetryTime = frame.t
  const point = pose.position.clone()
  const last = trajectoryPoints[trajectoryPoints.length - 1]
  if (!last || last.distanceTo(point) > 0.05) {
    trajectoryPoints.push(point)
    if (trajectoryPoints.length > 600) trajectoryPoints.shift()
    trajectoryLine.geometry.dispose()
    trajectoryLine.geometry = new THREE.BufferGeometry().setFromPoints(trajectoryPoints)
  }
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
  if (mode !== 'free') updateManagedCamera(true)
  syncVisualTestProbe()
}

function cameraTarget(): THREE.Vector3 {
  return vehicleGroup?.position.clone().add(new THREE.Vector3(0, 0.08, 0))
    ?? new THREE.Vector3(0, 0.08, 0)
}

function updateManagedCamera(immediate = false): void {
  if (cameraMode.value === 'free' || !camera || !controls) return
  const target = cameraTarget()
  let offset = new THREE.Vector3(2.2, 1.45, 2.7)
  if (cameraMode.value === 'top') offset = new THREE.Vector3(0.001, 4.2, 0.001)
  if (cameraMode.value === 'side') offset = new THREE.Vector3(0.05, 1.05, 3.6)
  const desired = target.clone().add(offset)
  if (immediate) {
    camera.position.copy(desired)
    controls.target.copy(target)
  } else {
    camera.position.lerp(desired, 0.07)
    controls.target.lerp(target, 0.09)
  }
}

function animate(now = performance.now()): void {
  animationId = requestAnimationFrame(animate)
  const dt = Math.min(0.05, Math.max(0, (now - previousAnimationTime) / 1000))
  previousAnimationTime = now
  aircraftRenderer?.rotateRotors(
    props.telemetry?.motors.outputs.map(output => output * Math.min(1.4, dt * 60)),
  )
  updateManagedCamera()
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

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(visualTestProbeEnabled ? 1 : Math.min(window.devicePixelRatio, 2))
  renderer.setClearColor(0x000000, 0)
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.0
  host.value.appendChild(renderer.domElement)

  pmrem = new THREE.PMREMGenerator(renderer)
  const environment = new RoomEnvironment()
  environmentTexture = pmrem.fromScene(environment, 0.04).texture

  buildWorld()
  scene.environment = environmentTexture

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08
  controls.minDistance = 0.65
  controls.maxDistance = 12
  controls.target.set(0, 0.05, 0)
  renderer.domElement.addEventListener('pointerdown', onPointerDown)
  renderer.domElement.addEventListener('pointermove', onPointerMove)

  resize()
  window.addEventListener('resize', resize)
  syncVisualTestProbe()
  await rebuildAircraftAssets()
  if (props.telemetry) updateFlightScene(props.telemetry)
  applyAssemblyState()
  previousAnimationTime = performance.now()
  animate()
})

watch(componentSignature, () => { void rebuildAircraftAssets() })
watch(() => props.telemetry, frame => { if (frame) updateFlightScene(frame) }, { deep: true })
watch(
  () => [props.selectedSlot, props.engineering, props.aircraft] as const,
  applyAssemblyState,
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
    radial-gradient(circle at 50% 36%, rgba(255,255,255,.98) 0%, rgba(239,246,253,.96) 42%, rgba(225,235,246,.98) 100%);
}
.asset-toolbar button.scene-chip {
  border: 0;
  background: transparent;
  cursor: pointer;
}
.asset-toolbar button.scene-chip:hover,
.asset-toolbar button.scene-chip.active {
  color: #1f6feb;
  background: #edf5ff;
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
  border-radius: 6px;
  border: 1px solid rgba(190,205,222,.9);
  background: rgba(255,255,255,.84);
  color: #526176;
  font-size: 10px;
  pointer-events: none;
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
  border-radius: 8px;
  background: rgba(255, 247, 246, .96);
  color: #9f2f25;
  box-shadow: 0 12px 30px rgba(110, 38, 31, .12);
  font-size: 11px;
}
.asset-error b {
  font-size: 13px;
}
@keyframes assetPulse { 50% { opacity: .3; } }
</style>
