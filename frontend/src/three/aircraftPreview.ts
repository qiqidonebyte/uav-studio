import * as THREE from 'three'
import type { AircraftDefinition, Component } from '../types/aircraft'
import { AircraftRenderer } from './AircraftRenderer'

const WIDTH = 480
const HEIGHT = 270

let renderer: THREE.WebGLRenderer | null = null
let scene: THREE.Scene | null = null
let camera: THREE.PerspectiveCamera | null = null
let aircraftRenderer: AircraftRenderer | null = null
let queue: Promise<unknown> = Promise.resolve()

const previewCache = new Map<string, Promise<string>>()

function previewKey(
  aircraft: AircraftDefinition,
  components: Component[],
): string {
  const instances = aircraft.assembly_instances
    ?.map(item => `${item.mount_id}:${item.component_id}`)
    .sort()
    .join(',') ?? 'legacy'
  const componentVisuals = components
    .map(item => `${item.id}:${item.visual?.asset_key ?? ''}`)
    .join('|')
  return [
    aircraft.id ?? 'template',
    aircraft.name,
    aircraft.frame_id ?? '-',
    aircraft.motor_id ?? '-',
    aircraft.esc_id ?? '-',
    aircraft.propeller_id ?? '-',
    aircraft.battery_id ?? '-',
    aircraft.power_module_id ?? '-',
    aircraft.flight_controller_id ?? '-',
    aircraft.gnss_id ?? '-',
    aircraft.payload_id ?? '-',
    instances,
    componentVisuals,
  ].join('::')
}

function ensureRenderer(): void {
  if (renderer && scene && camera && aircraftRenderer) return

  renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true,
    preserveDrawingBuffer: true,
    powerPreference: 'low-power',
  })
  renderer.setPixelRatio(1)
  renderer.setSize(WIDTH, HEIGHT, false)
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.05
  renderer.shadowMap.enabled = false

  scene = new THREE.Scene()
  camera = new THREE.PerspectiveCamera(32, WIDTH / HEIGHT, 0.01, 20)

  scene.add(new THREE.HemisphereLight(0xeaf4ff, 0x52616f, 2.4))
  const key = new THREE.DirectionalLight(0xffffff, 3.1)
  key.position.set(2.2, 3.2, 2.4)
  scene.add(key)
  const rim = new THREE.DirectionalLight(0xbfdcff, 1.6)
  rim.position.set(-2.4, 1.4, -2.0)
  scene.add(rim)

  aircraftRenderer = new AircraftRenderer()
  scene.add(aircraftRenderer.root)
}

function fitCamera(): void {
  if (!aircraftRenderer || !camera) return
  const bounds = new THREE.Box3().setFromObject(aircraftRenderer.root)
  if (bounds.isEmpty()) {
    camera.position.set(0.75, 0.58, 0.82)
    camera.lookAt(0, 0, 0)
    return
  }

  const center = new THREE.Vector3()
  const size = new THREE.Vector3()
  bounds.getCenter(center)
  bounds.getSize(size)
  const radius = Math.max(size.x, size.y, size.z, 0.2)

  camera.position.set(
    center.x + radius * 1.08,
    center.y + radius * 0.72,
    center.z + radius * 1.12,
  )
  camera.lookAt(center.x, center.y + size.y * 0.03, center.z)
  camera.near = Math.max(0.01, radius / 100)
  camera.far = radius * 12
  camera.updateProjectionMatrix()
}

async function renderPreview(
  aircraft: AircraftDefinition,
  components: Component[],
): Promise<string> {
  ensureRenderer()
  if (!renderer || !scene || !camera || !aircraftRenderer) {
    throw new Error('3D preview renderer unavailable')
  }

  await aircraftRenderer.rebuild(aircraft, components)
  aircraftRenderer.root.position.set(0, 0, 0)
  aircraftRenderer.root.rotation.set(0, -0.34, 0)
  aircraftRenderer.root.scale.set(1, 1, 1)
  aircraftRenderer.applyAssemblyState(aircraft, null)
  fitCamera()

  renderer.setClearColor(0xffffff, 0)
  renderer.render(scene, camera)
  return renderer.domElement.toDataURL('image/webp', 0.86)
}

/**
 * Generate an actual aircraft 3D thumbnail using a single shared WebGL context.
 *
 * Design-library cards receive ordinary <img> data URLs, avoiding the browser
 * WebGL-context limit when a teacher/student accumulates many saved designs.
 */
export function aircraftPreviewDataUrl(
  aircraft: AircraftDefinition,
  components: Component[],
): Promise<string> {
  const key = previewKey(aircraft, components)
  const cached = previewCache.get(key)
  if (cached) return cached

  const task = queue.then(() => renderPreview(aircraft, components))
  queue = task.then(
    () => undefined,
    () => undefined,
  )
  previewCache.set(key, task)

  task.catch(() => {
    if (previewCache.get(key) === task) previewCache.delete(key)
  })
  return task
}

export function clearAircraftPreviewCache(): void {
  previewCache.clear()
}
