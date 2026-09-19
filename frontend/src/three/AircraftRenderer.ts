import * as THREE from 'three'
import type {
  AircraftDefinition,
  Component,
  ComponentType,
  ComponentVisual,
  MotorName,
  Vector3Value,
} from '../types/aircraft'
import type { AssemblySlot } from '../utils/assembly'
import { isSlotInstalled } from '../utils/assembly'
import { motorPositionsToThree, simulationVectorToThree } from './coordinates'
import {
  assetForComponent,
  assetUrl,
  MOTOR_DIRECTIONS,
  propellerAssetUrl,
  propellerOffsetY,
} from './assetRegistry'
import { loadModel } from './modelLoader'

interface MaterialSnapshot {
  opacity: number
  transparent: boolean
  depthWrite: boolean
  color?: number
  emissive?: number
  emissiveIntensity?: number
}

interface PartRecord {
  slot: AssemblySlot
  object: THREE.Object3D
  meshes: THREE.Mesh[]
  installed: boolean
  componentId: number | null
  url: string
  direction?: 'CW' | 'CCW'
  motorName?: MotorName
}

export interface VisualBoundsSnapshot {
  width: number
  height: number
  depth: number
}

export interface LoadedAssetSnapshot {
  slot: AssemblySlot
  componentId: number | null
  url: string
  direction?: 'CW' | 'CCW'
}

const SLOT_FIELD: Record<AssemblySlot, keyof AircraftDefinition> = {
  frame: 'frame_id',
  motor: 'motor_id',
  esc: 'esc_id',
  propeller: 'propeller_id',
  battery: 'battery_id',
  power_module: 'power_module_id',
  flight_controller: 'flight_controller_id',
  gnss: 'gnss_id',
  payload: 'payload_id',
}

function componentById(
  components: Component[],
  id: number | null | undefined,
): Component | null {
  if (!id) return null
  return components.find(component => component.id === id) ?? null
}

function componentForSlot(
  aircraft: AircraftDefinition | null | undefined,
  components: Component[],
  slot: AssemblySlot,
): Component | null {
  if (!aircraft) return null
  const id = aircraft[SLOT_FIELD[slot]]
  return typeof id === 'number' ? componentById(components, id) : null
}

function parameterVector(
  component: Component | null,
  key: string,
): THREE.Vector3 | null {
  const raw = component?.parameters_json[key]
  if (!raw || typeof raw !== 'object') return null
  const value = raw as Record<string, unknown>
  if (
    typeof value.x !== 'number' ||
    typeof value.y !== 'number' ||
    typeof value.z !== 'number'
  ) return null
  return simulationVectorToThree({ x: value.x, y: value.y, z: value.z })
}

function materialSnapshot(material: THREE.Material): MaterialSnapshot {
  const standard = material as THREE.MeshStandardMaterial
  return {
    opacity: material.opacity,
    transparent: material.transparent,
    depthWrite: material.depthWrite,
    color: standard.color?.getHex(),
    emissive: standard.emissive?.getHex(),
    emissiveIntensity: standard.emissiveIntensity,
  }
}

function applyMaterialState(
  mesh: THREE.Mesh,
  installed: boolean,
  selected: boolean,
  issue: boolean,
): void {
  const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material]
  materials.forEach(material => {
    if (!material) return
    const snapshot = material.userData.uavBaseMaterial as MaterialSnapshot | undefined
    const base = snapshot ?? materialSnapshot(material)
    if (!snapshot) material.userData.uavBaseMaterial = base

    const standard = material as THREE.MeshStandardMaterial
    material.transparent = !installed || base.transparent
    material.opacity = installed ? base.opacity : selected ? 0.34 : 0.14
    material.depthWrite = installed

    if (standard.color) {
      standard.color.setHex(installed ? (base.color ?? 0xffffff) : 0x9aa8b7)
    }
    if (standard.emissive) {
      standard.emissive.setHex(issue ? 0xb42318 : selected ? 0x2563eb : (base.emissive ?? 0x000000))
      standard.emissiveIntensity = issue
        ? 0.7
        : selected
          ? 0.75
        : (base.emissiveIntensity ?? 1)
    }
    material.needsUpdate = true
  })
}

function applyVisualScale(object: THREE.Object3D, visual: ComponentVisual): void {
  object.scale.setScalar(visual.scale ?? 1)
}

function dimensionsForObjects(objects: THREE.Object3D[]): VisualBoundsSnapshot {
  const box = new THREE.Box3()
  let hasObject = false
  objects.forEach(object => {
    object.updateMatrixWorld(true)
    const objectBox = new THREE.Box3().setFromObject(object)
    if (!objectBox.isEmpty()) {
      box.union(objectBox)
      hasObject = true
    }
  })
  if (!hasObject || box.isEmpty()) return { width: 0, height: 0, depth: 0 }
  const size = new THREE.Vector3()
  box.getSize(size)
  return { width: size.x, height: size.y, depth: size.z }
}

function simulationMotorMounts(diagonal: number): Record<MotorName, Vector3Value> {
  const offset = diagonal / 2 / Math.sqrt(2)
  return {
    M1: { x: offset, y: offset, z: 0 },
    M2: { x: offset, y: -offset, z: 0 },
    M3: { x: -offset, y: -offset, z: 0 },
    M4: { x: -offset, y: offset, z: 0 },
  }
}

export class AircraftRenderer {
  readonly root = new THREE.Group()
  private parts: PartRecord[] = []
  private rotorGroups: Array<{ group: THREE.Object3D; sign: number }> = []
  private generation = 0
  private lastMotorMounts: Record<MotorName, Vector3Value> = simulationMotorMounts(0.65)

  constructor() {
    this.root.name = 'uav-aircraft-root'
  }

  private clearParts(): void {
    this.root.traverse(object => {
      const mesh = object as THREE.Mesh
      if (!mesh.isMesh) return
      const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material]
      materials.forEach(material => material?.dispose())
    })
    this.root.clear()
    this.parts = []
    this.rotorGroups = []
  }

  private async loadRequired(url: string): Promise<THREE.Group> {
    // P0 rule: installed assets fail loudly. Missing GLBs must not silently turn
    // back into BoxGeometry/CylinderGeometry placeholders.
    return loadModel(url)
  }

  private register(
    slot: AssemblySlot,
    object: THREE.Object3D,
    installed: boolean,
    componentId: number | null,
    url: string,
    direction?: 'CW' | 'CCW',
    motorName?: MotorName,
  ): void {
    const meshes: THREE.Mesh[] = []
    object.traverse(child => {
      const mesh = child as THREE.Mesh
      if (!mesh.isMesh) return
      mesh.userData.slot = slot
      meshes.push(mesh)
    })
    this.parts.push({
      slot,
      object,
      meshes,
      installed,
      componentId,
      url,
      direction,
      motorName,
    })
    this.root.add(object)
  }

  private frameDiagonal(frame: Component | null): number {
    const raw = frame?.parameters_json.motor_diagonal_m
    return typeof raw === 'number' && raw > 0 ? raw : 0.65
  }

  async rebuild(
    aircraft: AircraftDefinition | null | undefined,
    components: Component[],
  ): Promise<void> {
    const generation = ++this.generation
    const oldPosition = this.root.position.clone()
    const oldRotation = this.root.rotation.clone()
    const oldScale = this.root.scale.clone()
    this.clearParts()

    const frame = componentForSlot(aircraft, components, 'frame')
    const motor = componentForSlot(aircraft, components, 'motor')
    const esc = componentForSlot(aircraft, components, 'esc')
    const propeller = componentForSlot(aircraft, components, 'propeller')
    const battery = componentForSlot(aircraft, components, 'battery')
    const power = componentForSlot(aircraft, components, 'power_module')
    const flightController = componentForSlot(aircraft, components, 'flight_controller')
    const gnss = componentForSlot(aircraft, components, 'gnss')
    const payload = componentForSlot(aircraft, components, 'payload')

    const diagonal = this.frameDiagonal(frame)
    const frameScale = diagonal / 0.65
    const mountY = 0.066 * frameScale
    const motorPositions = motorPositionsToThree(diagonal)
    this.lastMotorMounts = simulationMotorMounts(diagonal)

    const frameVisual = assetForComponent(frame, 'frame')
    const frameUrl = assetUrl(frameVisual)
    const frameObject = await this.loadRequired(frameUrl)
    if (generation !== this.generation) return
    applyVisualScale(frameObject, frameVisual)
    this.register('frame', frameObject, Boolean(frame), frame?.id ?? null, frameUrl)

    const motorVisual = assetForComponent(motor, 'motor')
    const motorUrl = assetUrl(motorVisual)
    const escVisual = assetForComponent(esc, 'esc')
    const escUrl = assetUrl(escVisual)
    const propVisual = assetForComponent(propeller, 'propeller')
    const propUrls = {
      CW: propellerAssetUrl(propeller, 'CW'),
      CCW: propellerAssetUrl(propeller, 'CCW'),
    }

    const motorPrototype = await this.loadRequired(motorUrl)
    const escPrototype = await this.loadRequired(escUrl)
    const propPrototypeCW = await this.loadRequired(propUrls.CW)
    const propPrototypeCCW = await this.loadRequired(propUrls.CCW)
    if (generation !== this.generation) return
    applyVisualScale(motorPrototype, motorVisual)
    applyVisualScale(escPrototype, escVisual)
    applyVisualScale(propPrototypeCW, propVisual)
    applyVisualScale(propPrototypeCCW, propVisual)

    ;(['M1', 'M2', 'M3', 'M4'] as MotorName[]).forEach((name, index) => {
      const p = motorPositions[name].clone()
      p.y = mountY

      const motorObject = index === 0 ? motorPrototype : motorPrototype.clone(true)
      motorObject.position.copy(p)
      this.register(
        'motor',
        motorObject,
        Boolean(motor),
        motor?.id ?? null,
        motorUrl,
        undefined,
        name,
      )

      const escObject = index === 0 ? escPrototype : escPrototype.clone(true)
      escObject.position.copy(p.clone().multiplyScalar(0.64))
      escObject.position.y = mountY * 0.58
      escObject.rotation.y = Math.atan2(-p.z, p.x)
      this.register('esc', escObject, Boolean(esc), esc?.id ?? null, escUrl)

      const direction = MOTOR_DIRECTIONS[name]
      const source = direction === 'CW' ? propPrototypeCW : propPrototypeCCW
      const propObject = source.clone(true)
      propObject.position.copy(p).add(new THREE.Vector3(0, propellerOffsetY(motor), 0))
      const propUrl = direction === 'CW' ? propUrls.CW : propUrls.CCW
      this.register(
        'propeller',
        propObject,
        Boolean(propeller),
        propeller?.id ?? null,
        propUrl,
        direction,
        name,
      )
      this.rotorGroups.push({ group: propObject, sign: direction === 'CW' ? -1 : 1 })
    })

    const frameForPositions = frame ?? componentById(components, aircraft?.frame_id)
    const batteryPosition = parameterVector(frameForPositions, 'battery_position_m')
      ?? new THREE.Vector3(-0.03, -0.10, 0)
    const powerPosition = parameterVector(frameForPositions, 'power_module_position_m')
      ?? new THREE.Vector3(0, 0.02, 0)
    const fcPosition = parameterVector(frameForPositions, 'flight_controller_position_m')
      ?? new THREE.Vector3(0, 0.05, 0)
    const gnssPosition = aircraft?.gnss_position_m
      ? simulationVectorToThree(aircraft.gnss_position_m)
      : parameterVector(frameForPositions, 'gnss_mount_position_m')
        ?? new THREE.Vector3(-0.16, 0.08, 0)
    const payloadPosition = aircraft?.payload_position_m
      ? simulationVectorToThree(aircraft.payload_position_m)
      : new THREE.Vector3(0.08, -0.12, 0)

    const singles: Array<[AssemblySlot, Component | null, THREE.Vector3]> = [
      ['battery', battery, batteryPosition],
      ['power_module', power, powerPosition],
      ['flight_controller', flightController, fcPosition],
      ['gnss', gnss, gnssPosition],
      ['payload', payload, payloadPosition],
    ]

    for (const [slot, component, position] of singles) {
      const type = slot as ComponentType
      const visual = assetForComponent(component, type)
      const url = assetUrl(visual)
      const object = await this.loadRequired(url)
      if (generation !== this.generation) return
      applyVisualScale(object, visual)
      object.position.copy(position)
      this.register(slot, object, Boolean(component), component?.id ?? null, url)
    }

    if (gnss || !aircraft || !isSlotInstalled(aircraft, 'gnss')) {
      const mastHeight = Math.max(0.08, gnssPosition.y - mountY)
      const mast = new THREE.Mesh(
        new THREE.CylinderGeometry(0.0035, 0.0035, mastHeight, 14),
        new THREE.MeshStandardMaterial({
          color: 0x20252b,
          metalness: 0.25,
          roughness: 0.55,
        }),
      )
      mast.position.set(
        gnssPosition.x,
        gnssPosition.y - mastHeight / 2,
        gnssPosition.z,
      )
      mast.castShadow = true
      // Mast is an engineering overlay/accessory, not a component asset. It is
      // intentionally excluded from loadedAssets by using the GNSS URL only for
      // the actual GNSS component above.
      mast.userData.slot = 'gnss'
      this.root.add(mast)
      const mastMeshes = [mast]
      this.parts.push({
        slot: 'gnss',
        object: mast,
        meshes: mastMeshes,
        installed: Boolean(gnss),
        componentId: null,
        url: 'procedural:gnss-mast',
      })
    }

    this.root.position.copy(oldPosition)
    this.root.rotation.copy(oldRotation)
    this.root.scale.copy(oldScale)
    this.applyAssemblyState(aircraft, null)
  }

  applyAssemblyState(
    aircraft: AircraftDefinition | null | undefined,
    selectedSlot: AssemblySlot | null,
    issueSlots: AssemblySlot[] = [],
    issueMounts: MotorName[] = [],
  ): void {
    this.parts.forEach(part => {
      const installed = aircraft ? isSlotInstalled(aircraft, part.slot) : part.installed
      const selected = selectedSlot === part.slot
      const issue = issueSlots.includes(part.slot)
        || Boolean(part.motorName && issueMounts.includes(part.motorName))
      part.meshes.forEach(mesh => applyMaterialState(mesh, installed, selected, issue))
      part.object.visible = true
    })
  }

  rotateRotors(outputs: number[] | undefined): void {
    this.rotorGroups.forEach((item, index) => {
      const output = outputs?.[index] ?? 0
      item.group.rotation.y += item.sign * output * 0.75
    })
  }

  raycastMeshes(): THREE.Mesh[] {
    return this.parts.flatMap(part => part.meshes)
  }

  slotForObject(object: THREE.Object3D): AssemblySlot | null {
    let current: THREE.Object3D | null = object
    while (current) {
      const slot = current.userData.slot as AssemblySlot | undefined
      if (slot) return slot
      current = current.parent
    }
    return null
  }

  loadedAssetsSnapshot(): LoadedAssetSnapshot[] {
    const result: LoadedAssetSnapshot[] = []
    const seen = new Set<string>()
    this.parts.forEach(part => {
      if (part.url.startsWith('procedural:')) return
      const key = `${part.slot}|${part.componentId}|${part.url}|${part.direction ?? ''}`
      if (seen.has(key)) return
      seen.add(key)
      result.push({
        slot: part.slot,
        componentId: part.componentId,
        url: part.url,
        ...(part.direction ? { direction: part.direction } : {}),
      })
    })
    return result
  }

  aircraftBoundsSnapshot(): VisualBoundsSnapshot {
    return dimensionsForObjects([this.root])
  }

  partBoundsSnapshot(): Partial<Record<AssemblySlot, VisualBoundsSnapshot>> {
    const slots: AssemblySlot[] = [
      'frame',
      'motor',
      'esc',
      'propeller',
      'battery',
      'power_module',
      'flight_controller',
      'gnss',
      'payload',
    ]
    const result: Partial<Record<AssemblySlot, VisualBoundsSnapshot>> = {}
    slots.forEach(slot => {
      const objects = this.parts
        .filter(part => part.slot === slot && !part.url.startsWith('procedural:'))
        .map(part => part.object)
      if (objects.length > 0) result[slot] = dimensionsForObjects(objects)
    })
    return result
  }

  motorMountsSnapshot(): Record<MotorName, Vector3Value> {
    return {
      M1: { ...this.lastMotorMounts.M1 },
      M2: { ...this.lastMotorMounts.M2 },
      M3: { ...this.lastMotorMounts.M3 },
      M4: { ...this.lastMotorMounts.M4 },
    }
  }

  setPose(position: THREE.Vector3, rotation: THREE.Euler): void {
    this.root.position.copy(position)
    this.root.rotation.copy(rotation)
  }

  localPoint(vector: Vector3Value): THREE.Vector3 {
    return simulationVectorToThree(vector)
  }

  dispose(): void {
    this.generation += 1
    this.clearParts()
  }
}
