<template>
  <div ref="host" class="drone-scene" @pointerleave="cursor = 'default'">
    <div class="scene-toolbar">
      <span class="scene-chip scene-chip-active">三维视图</span>
      <span class="scene-chip">跟随</span>
      <span class="scene-chip">俯视</span>
      <span class="scene-chip">侧视</span>
      <span class="scene-chip">自由</span>
    </div>

    <div v-if="telemetry" class="scene-readout">
      <div><span>时间</span><b>{{ telemetry.t.toFixed(1) }} s</b></div>
      <div><span>高度</span><b>{{ telemetry.position.z.toFixed(1) }} m</b></div>
      <div><span>位置</span><b>({{ telemetry.position.x.toFixed(1) }}, {{ telemetry.position.y.toFixed(1) }}, {{ telemetry.position.z.toFixed(1) }}) m</b></div>
    </div>

    <div v-if="telemetry" class="wind-readout">风场示意 {{ telemetry.wind.speed_mps.toFixed(1) }} m/s</div>

    <div v-if="assemblyMode" class="scene-selection">
      <b>{{ selectedSlot ? SLOT_LABELS[selectedSlot] : '选择部件' }}</b>
      <span>{{ selectedSlot ? '点击其他部件可切换检查器' : '点击机身、电机或安装槽位查看详情' }}</span>
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
import type {
  AircraftDefinition,
  AircraftEngineeringSummary,
  Component,
} from '../types/aircraft'
import type { TelemetryFrame } from '../types/telemetry'
import {
  motorPositionsToThree,
  simulationPoseToThree,
  simulationVectorToThree,
} from '../three/coordinates'
import {
  assemblySlotFromScenePart,
  isSlotInstalled,
  SLOT_LABELS,
  type AssemblySlot,
} from '../utils/assembly'

interface ScenePart {
  mesh: THREE.Mesh
  slot: AssemblySlot
  color: number
  opacity: number
}

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
const assemblyMode = computed(() => props.interactive)

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let drone: THREE.Group
let cgMarker: THREE.Mesh
let gravityArrow: THREE.ArrowHelper
let windArrow: THREE.ArrowHelper
let trajectoryLine: THREE.Line
let trajectoryPoints: THREE.Vector3[] = []
let thrustArrows: THREE.ArrowHelper[] = []
let rotorMeshes: THREE.Mesh[] = []
let sceneParts: ScenePart[] = []
let animationId = 0
let lastFrameId: number | null | undefined
const raycaster = new THREE.Raycaster()
const pointer = new THREE.Vector2()

function addLabelSprite(
  text: string,
  position: THREE.Vector3,
  color = '#1f4f8f',
) {
  const canvas = document.createElement('canvas')
  canvas.width = 220
  canvas.height = 48
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  ctx.fillStyle = color
  ctx.font = 'bold 22px sans-serif'
  ctx.fillText(text, 8, 31)
  const texture = new THREE.CanvasTexture(canvas)
  const sprite = new THREE.Sprite(
    new THREE.SpriteMaterial({ map: texture, transparent: true }),
  )
  sprite.scale.set(0.72, 0.16, 1)
  sprite.position.copy(position)
  drone.add(sprite)
}

function frameComponent(): Component | null {
  if (!props.aircraft?.frame_id) return null
  return (
    props.components.find(component => component.id === props.aircraft?.frame_id) ??
    null
  )
}

function motorDiagonal(): number {
  const value = frameComponent()?.parameters_json.motor_diagonal_m
  return typeof value === 'number' && value > 0 ? value : 0.65
}

function frameMountPosition(key: string): THREE.Vector3 {
  const raw = frameComponent()?.parameters_json[key]
  if (raw && typeof raw === 'object') {
    const value = raw as Record<string, unknown>
    if (
      typeof value.x === 'number' &&
      typeof value.y === 'number' &&
      typeof value.z === 'number'
    ) {
      return simulationVectorToThree({
        x: value.x,
        y: value.y,
        z: value.z,
      })
    }
  }
  return new THREE.Vector3()
}

function payloadPosition(): THREE.Vector3 {
  return props.aircraft?.payload_position_m
    ? simulationVectorToThree(props.aircraft.payload_position_m)
    : new THREE.Vector3(0.12, -0.22, 0)
}

function registerPart(
  mesh: THREE.Mesh,
  slot: AssemblySlot,
  color: number,
  opacity = 1,
) {
  const material = new THREE.MeshStandardMaterial({
    color,
    metalness: 0.2,
    roughness: 0.55,
    transparent: opacity < 1,
    opacity,
  })
  mesh.material = material
  mesh.userData.slot = slot
  sceneParts.push({ mesh, slot, color, opacity })
  drone.add(mesh)
}

function buildDrone() {
  drone = new THREE.Group()
  sceneParts = []
  rotorMeshes = []
  thrustArrows = []
  const diagonal = motorDiagonal()
  const scale = diagonal / 0.65
  const motorPositions = motorPositionsToThree(diagonal)
  const armMaterial = new THREE.MeshStandardMaterial({ color: 0x36495f })

  const body = new THREE.Mesh(
    new THREE.BoxGeometry(0.55 * scale, 0.16 * scale, 0.38 * scale),
    armMaterial,
  )
  body.position.y = 0.02 * scale
  registerPart(body, 'frame', 0x25364b)

  const battery = new THREE.Mesh(
    new THREE.BoxGeometry(0.30 * scale, 0.16 * scale, 0.16 * scale),
    armMaterial,
  )
  battery.position.copy(frameMountPosition('battery_position_m'))
  registerPart(battery, 'battery', 0x1f6feb)

  const power = new THREE.Mesh(
    new THREE.BoxGeometry(0.13 * scale, 0.035 * scale, 0.11 * scale),
    armMaterial,
  )
  power.position.copy(frameMountPosition('power_module_position_m'))
  registerPart(power, 'power_module', 0xf59e0b)

  const fc = new THREE.Mesh(
    new THREE.BoxGeometry(0.14 * scale, 0.025 * scale, 0.14 * scale),
    armMaterial,
  )
  fc.position.copy(frameMountPosition('flight_controller_position_m'))
  registerPart(fc, 'flight_controller', 0x16a34a)

  const nose = new THREE.ArrowHelper(
    new THREE.Vector3(1, 0, 0),
    new THREE.Vector3(0, 0.19 * scale, 0),
    0.25 * scale,
    0x16a34a,
    0.07 * scale,
    0.04 * scale,
  )
  drone.add(nose)

  const gnssPosition = props.aircraft?.gnss_position_m
    ? simulationVectorToThree(props.aircraft.gnss_position_m)
    : frameMountPosition('gnss_mount_position_m')
  const gnss = new THREE.Mesh(
    new THREE.CylinderGeometry(
      0.07 * scale,
      0.07 * scale,
      0.025 * scale,
      24,
    ),
    armMaterial,
  )
  gnss.position.copy(gnssPosition)
  registerPart(gnss, 'gnss', 0xe5e7eb)

  const payload = new THREE.Mesh(
    new THREE.BoxGeometry(0.12 * scale, 0.12 * scale, 0.12 * scale),
    armMaterial,
  )
  payload.position.copy(payloadPosition())
  registerPart(payload, 'payload', 0x20242b)

  const directions = ['逆时针', '顺时针', '逆时针', '顺时针']
  ;(['M1', 'M2', 'M3', 'M4'] as const).forEach((motorName, index) => {
    const position = motorPositions[motorName]
    const arm = new THREE.Mesh(
      new THREE.BoxGeometry(position.length() * 0.92, 0.05 * scale, 0.06 * scale),
      armMaterial,
    )
    arm.position.copy(position.clone().multiplyScalar(0.5))
    arm.rotation.y = Math.atan2(-position.z, position.x)
    registerPart(arm, 'frame', 0x36495f)

    const esc = new THREE.Mesh(
      new THREE.BoxGeometry(0.13 * scale, 0.025 * scale, 0.07 * scale),
      armMaterial,
    )
    esc.position.copy(position.clone().multiplyScalar(0.64))
    esc.position.y = 0.01
    registerPart(esc, 'esc', 0xf59e0b)

    const motor = new THREE.Mesh(
      new THREE.CylinderGeometry(
        0.07 * scale,
        0.07 * scale,
        0.09 * scale,
        24,
      ),
      armMaterial,
    )
    motor.position.copy(position)
    registerPart(motor, 'motor', 0x27364a)

    const propeller = new THREE.Mesh(
      new THREE.CylinderGeometry(
        0.24 * scale,
        0.24 * scale,
        0.008,
        40,
      ),
      new THREE.MeshStandardMaterial({
        color: 0x111827,
        transparent: true,
        opacity: 0.32,
        side: THREE.DoubleSide,
      }),
    )
    propeller.position.copy(position).add(new THREE.Vector3(0, 0.065, 0))
    propeller.userData.rotorIndex = index
    registerPart(propeller, 'propeller', 0x111827, 0.32)
    rotorMeshes.push(propeller)

    const arrow = new THREE.ArrowHelper(
      new THREE.Vector3(0, 1, 0),
      position.clone().add(new THREE.Vector3(0, 0.09, 0)),
      0.4,
      0x3b82f6,
      0.11,
      0.06,
    )
    thrustArrows.push(arrow)
    drone.add(arrow)
    addLabelSprite(
      `${motorName} ${directions[index]}`,
      position.clone().add(new THREE.Vector3(0, 0.42 * scale, 0)),
    )
  })

  cgMarker = new THREE.Mesh(
    new THREE.SphereGeometry(0.045, 20, 20),
    new THREE.MeshStandardMaterial({ color: 0xf5c518 }),
  )
  drone.add(cgMarker)
  addLabelSprite('重心', new THREE.Vector3(0.04, 0.28 * scale, 0), '#a16207')

  gravityArrow = new THREE.ArrowHelper(
    new THREE.Vector3(0, -1, 0),
    new THREE.Vector3(0, -0.05, 0),
    0.6,
    0xef4444,
    0.12,
    0.07,
  )
  drone.add(gravityArrow)
  scene.add(drone)
}

function disposeDrone() {
  if (!drone) return
  scene.remove(drone)
  drone.traverse(object => {
    const mesh = object as THREE.Mesh
    mesh.geometry?.dispose()
    const material = mesh.material
    if (Array.isArray(material)) material.forEach(item => item.dispose())
    else material?.dispose()
  })
}

function rebuildDrone() {
  if (!scene) return
  disposeDrone()
  buildDrone()
  applyAssemblyState()
}

function buildWorld() {
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xeaf4ff)
  scene.add(new THREE.HemisphereLight(0xffffff, 0x738197, 1.3))
  const directional = new THREE.DirectionalLight(0xffffff, 1.2)
  directional.position.set(4, 7, 5)
  scene.add(directional)
  scene.add(new THREE.GridHelper(30, 30, 0xa8b4c4, 0xd4dce7))
  const axes = new THREE.AxesHelper(0.7)
  axes.position.set(-2.5, 0.02, 1.8)
  scene.add(axes)

  buildDrone()

  windArrow = new THREE.ArrowHelper(
    new THREE.Vector3(-1, 0, 0),
    new THREE.Vector3(2.8, 1.2, -0.2),
    1.5,
    0x2f80ed,
    0.18,
    0.1,
  )
  scene.add(windArrow)
  trajectoryLine = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0)]),
    new THREE.LineBasicMaterial({ color: 0x4f8cff }),
  )
  scene.add(trajectoryLine)
  applyAssemblyState()
}

function applyAssemblyState() {
  if (!drone) return
  thrustArrows.forEach(arrow => {
    arrow.visible = !assemblyMode.value
  })
  gravityArrow.visible = !assemblyMode.value
  windArrow.visible = !assemblyMode.value
  trajectoryLine.visible = !assemblyMode.value

  const aircraft = props.aircraft
  if (!aircraft) {
    sceneParts.forEach(part => {
      const material = part.mesh.material as THREE.MeshStandardMaterial
      material.opacity = part.opacity
      material.transparent = part.opacity < 1
      material.color.setHex(part.color)
      material.emissive.setHex(0x000000)
    })
    cgMarker.visible = assemblyMode.value
      ? Boolean(props.engineering)
      : Boolean(props.telemetry)
    return
  }

  sceneParts.forEach(part => {
    const installed = isSlotInstalled(aircraft, part.slot)
    const selected = props.selectedSlot === part.slot
    const material = part.mesh.material as THREE.MeshStandardMaterial
    material.color.setHex(installed ? part.color : 0xaeb8c5)
    material.transparent = !installed || part.opacity < 1
    material.opacity = installed ? part.opacity : 0.16
    material.emissive.setHex(selected ? 0x1d4ed8 : 0x000000)
    material.emissiveIntensity = selected ? 0.55 : 0
  })

  cgMarker.visible = props.engineering !== null
  if (props.engineering) {
    cgMarker.position.copy(
      simulationVectorToThree(props.engineering.center_of_gravity_m),
    )
  }
}

function updateFlightScene(frame: TelemetryFrame) {
  if (!drone) return
  const pose = simulationPoseToThree(frame.position, frame.attitude)
  drone.position.copy(pose.position)
  drone.rotation.copy(pose.rotation)
  cgMarker.visible = true
  cgMarker.position.copy(simulationVectorToThree(frame.center_of_gravity))
  frame.motors.thrusts_n.forEach((thrust, index) => {
    thrustArrows[index]?.setLength(0.18 + Math.min(1.15, thrust / 15), 0.11, 0.06)
  })
  gravityArrow.setLength(0.35 + Math.min(0.7, frame.forces.gravity_n / 60), 0.12, 0.07)
  gravityArrow.setRotationFromQuaternion(drone.quaternion.clone().invert())
  const radians = (frame.wind.direction_deg * Math.PI) / 180
  const windDirection = new THREE.Vector3(
    -Math.cos(radians),
    0,
    Math.sin(radians),
  ).normalize()
  windArrow.setDirection(windDirection)
  windArrow.setLength(0.45 + Math.min(1.6, frame.wind.speed_mps / 5), 0.18, 0.1)

  const point = simulationVectorToThree(frame.position)
  const last = trajectoryPoints[trajectoryPoints.length - 1]
  if (!last || last.distanceTo(point) > 0.05) {
    trajectoryPoints.push(point.clone())
    if (trajectoryPoints.length > 600) trajectoryPoints.shift()
    trajectoryLine.geometry.dispose()
    trajectoryLine.geometry = new THREE.BufferGeometry().setFromPoints(
      trajectoryPoints,
    )
  }
}

function setPointer(event: PointerEvent) {
  if (!host.value) return
  const rect = renderer.domElement.getBoundingClientRect()
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
}

function scenePartAtPointer(event: PointerEvent): ScenePart | null {
  if (!props.interactive) return null
  setPointer(event)
  raycaster.setFromCamera(pointer, camera)
  const hit = raycaster.intersectObjects(
    sceneParts.map(part => part.mesh),
    false,
  )[0]
  if (!hit) return null
  const slot = hit.object.userData.slot as AssemblySlot | undefined
  if (!slot) return null
  return sceneParts.find(part => part.slot === slot) ?? null
}

function onPointerDown(event: PointerEvent) {
  const part = scenePartAtPointer(event)
  if (part) emit('select-slot', part.slot)
}

function onPointerMove(event: PointerEvent) {
  cursor.value = scenePartAtPointer(event) ? 'pointer' : 'default'
}

function animate() {
  animationId = requestAnimationFrame(animate)
  rotorMeshes.forEach((mesh, index) => {
    const output = props.telemetry?.motors.outputs[index] ?? 0
    mesh.rotation.y += output * 0.9
  })
  controls?.update()
  renderer?.render(scene, camera)
}

function resize() {
  if (!host.value || !renderer || !camera) return
  const width = host.value.clientWidth
  const height = host.value.clientHeight
  renderer.setSize(width, height)
  camera.aspect = width / Math.max(1, height)
  camera.updateProjectionMatrix()
}

onMounted(() => {
  if (!host.value) return
  buildWorld()
  camera = new THREE.PerspectiveCamera(48, 1, 0.1, 100)
  camera.position.set(3.2, 2.2, 4.2)
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  host.value.appendChild(renderer.domElement)
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.target.set(0, 0.4, 0)
  renderer.domElement.addEventListener('pointerdown', onPointerDown)
  renderer.domElement.addEventListener('pointermove', onPointerMove)
  resize()
  if (props.telemetry) updateFlightScene(props.telemetry)
  applyAssemblyState()
  window.addEventListener('resize', resize)
  animate()
})

watch(
  () => props.telemetry,
  frame => {
    if (frame) updateFlightScene(frame)
  },
  { deep: true },
)

watch(
  () => [props.aircraft?.frame_id, props.components.length],
  () => {
    const frameId = props.aircraft?.frame_id
    if (!scene || frameId === lastFrameId) {
      applyAssemblyState()
      return
    }
    lastFrameId = frameId
    rebuildDrone()
  },
)

watch(
  () => [props.selectedSlot, props.engineering, props.aircraft],
  applyAssemblyState,
  { deep: true },
)

onBeforeUnmount(() => {
  cancelAnimationFrame(animationId)
  window.removeEventListener('resize', resize)
  renderer?.domElement.removeEventListener('pointerdown', onPointerDown)
  renderer?.domElement.removeEventListener('pointermove', onPointerMove)
  controls?.dispose()
  disposeDrone()
  renderer?.dispose()
  renderer?.domElement.remove()
})
</script>
