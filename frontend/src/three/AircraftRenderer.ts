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
import { simulationVectorToThree } from './coordinates'
import {
  assetForComponent,
  assetUrl,
  MOTOR_DIRECTIONS,
  propellerAssetUrl,
} from './assetRegistry'
import { loadModel } from './modelLoader'
import {
  explosionOffsetForPart,
  type PlainVector3,
} from './explodedView'
import { composeAssemblyPosition } from './assemblyTransforms'
import {
  buildMountPoints,
  componentById,
  componentIdAtMount,
  isMountInstalled,
  selectedComponentId,
  type MountPoint,
} from './assemblySemantics'

interface MaterialSnapshot {
  opacity: number
  transparent: boolean
  depthWrite: boolean
  color?: number
  emissive?: number
  emissiveIntensity?: number
}

interface PartRecord {
  mountId: string
  slot: AssemblySlot
  object: THREE.Object3D
  meshes: THREE.Mesh[]
  installed: boolean
  componentId: number | null
  url: string
  direction?: 'CW' | 'CCW'
  motorName?: MotorName
  basePosition: THREE.Vector3
  explosionOffset: THREE.Vector3
  installOffset: THREE.Vector3
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

export interface ExplodedPartSnapshot {
  mountId: string
  slot: AssemblySlot
  componentId: number | null
  motorName?: MotorName
  installed: boolean
  basePosition: PlainVector3
  currentPosition: PlainVector3
  offset: PlainVector3
}

export interface PartInstanceSnapshot extends ExplodedPartSnapshot {
  installProgress: number
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
  pending: boolean,
  hovered: boolean,
): void {
  const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material]
  materials.forEach(material => {
    if (!material) return
    const snapshot = material.userData.uavBaseMaterial as MaterialSnapshot | undefined
    const base = snapshot ?? materialSnapshot(material)
    if (!snapshot) material.userData.uavBaseMaterial = base

    const standard = material as THREE.MeshStandardMaterial
    material.transparent = !installed || base.transparent
    material.opacity = installed
      ? base.opacity
      : hovered
        ? 0.42
        : pending
          ? 0.16
          : selected
            ? 0.28
            : 0.08
    material.depthWrite = installed

    if (standard.color) {
      standard.color.setHex(
        installed
          ? (base.color ?? 0xffffff)
          : hovered
            ? 0x69c6ff
            : pending
              ? 0x91bde8
              : 0xa6b5c7,
      )
    }
    if (standard.emissive) {
      standard.emissive.setHex(
        issue
          ? 0xb42318
          : hovered
            ? 0x0787d1
            : selected
              ? 0x2563eb
              : (base.emissive ?? 0x000000),
      )
      standard.emissiveIntensity = issue
        ? 0.78
        : hovered
          ? 0.95
          : selected
            ? 0.88
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

function vectorSnapshot(value: THREE.Vector3): PlainVector3 {
  return { x: value.x, y: value.y, z: value.z }
}

function mountFor(
  mounts: MountPoint[],
  id: string,
): MountPoint {
  const mount = mounts.find(item => item.id === id)
  if (!mount) throw new Error(`Assembly mount missing: ${id}`)
  return mount
}

function mountComponent(
  aircraft: AircraftDefinition | null | undefined,
  components: Component[],
  mount: MountPoint,
): Component | null {
  const mountedId = componentIdAtMount(aircraft, mount)
  const selectedId = aircraft
    ? selectedComponentId(aircraft, mount.slot)
    : null
  return componentById(components, mountedId ?? selectedId)
}

export class AircraftRenderer {
  readonly root = new THREE.Group()
  private parts: PartRecord[] = []
  private rotorGroups: Array<{ group: THREE.Object3D; sign: number; mountId: string }> = []
  private generation = 0
  private explodedProgress = 0
  private installationProgress = new Map<string, number>()
  private lastMotorMounts: Record<MotorName, Vector3Value> = {
    M1: { x: 0.23, y: 0.23, z: 0.066 },
    M2: { x: 0.23, y: -0.23, z: 0.066 },
    M3: { x: -0.23, y: -0.23, z: 0.066 },
    M4: { x: -0.23, y: 0.23, z: 0.066 },
  }

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
    return loadModel(url)
  }

  private explosionOffset(
    slot: AssemblySlot,
    object: THREE.Object3D,
    motorName?: MotorName,
  ): THREE.Vector3 {
    const offset = explosionOffsetForPart({
      slot,
      basePosition: vectorSnapshot(object.position),
      ...(motorName ? { motorName } : {}),
    })
    return new THREE.Vector3(offset.x, offset.y, offset.z)
  }

  private register(
    mount: MountPoint,
    object: THREE.Object3D,
    installed: boolean,
    componentId: number | null,
    url: string,
    direction?: 'CW' | 'CCW',
  ): void {
    const meshes: THREE.Mesh[] = []
    object.traverse(child => {
      const mesh = child as THREE.Mesh
      if (!mesh.isMesh) return
      mesh.userData.slot = mount.slot
      mesh.userData.mountId = mount.id
      meshes.push(mesh)
    })

    const basePosition = object.position.clone()
    const explosionOffset = this.explosionOffset(
      mount.slot,
      object,
      mount.motorName,
    )
    const installOffset = simulationVectorToThree(mount.install_offset)
    this.parts.push({
      mountId: mount.id,
      slot: mount.slot,
      object,
      meshes,
      installed,
      componentId,
      url,
      direction,
      motorName: mount.motorName,
      basePosition,
      explosionOffset,
      installOffset,
    })
    if (!installed || !this.installationProgress.has(mount.id)) {
      this.installationProgress.set(mount.id, 1)
    }
    this.root.add(object)
  }

  private applyTransforms(): void {
    this.parts.forEach(part => {
      const installProgress = this.installationProgress.get(part.mountId) ?? 1
      const next = composeAssemblyPosition(
        vectorSnapshot(part.basePosition),
        vectorSnapshot(part.explosionOffset),
        this.explodedProgress,
        vectorSnapshot(part.installOffset),
        installProgress,
      )
      part.object.position.set(next.x, next.y, next.z)
    })
    this.root.updateMatrixWorld(true)
  }

  async rebuild(
    aircraft: AircraftDefinition | null | undefined,
    components: Component[],
  ): Promise<void> {
    const generation = ++this.generation
    const oldPosition = this.root.position.clone()
    const oldRotation = this.root.rotation.clone()
    const oldScale = this.root.scale.clone()
    const explodedProgress = this.explodedProgress
    this.clearParts()

    const mounts = buildMountPoints(aircraft, components)
    for (const name of ['M1', 'M2', 'M3', 'M4'] as MotorName[]) {
      this.lastMotorMounts[name] = {
        ...mountFor(mounts, `motor:${name}`).position,
      }
    }

    // Frame datum
    {
      const mount = mountFor(mounts, 'frame:main')
      const component = mountComponent(aircraft, components, mount)
      const visual = assetForComponent(component, 'frame')
      const url = assetUrl(visual)
      const object = await this.loadRequired(url)
      if (generation !== this.generation) return
      applyVisualScale(object, visual)
      object.position.copy(simulationVectorToThree(mount.position))
      this.register(
        mount,
        object,
        isMountInstalled(aircraft, mount.id),
        component?.id ?? null,
        url,
      )
    }

    // Repeated propulsion instances are now true mount-scoped objects.
    for (const name of ['M1', 'M2', 'M3', 'M4'] as MotorName[]) {
      for (const slot of ['motor', 'esc', 'propeller'] as const) {
        const mount = mountFor(mounts, `${slot}:${name}`)
        const component = mountComponent(aircraft, components, mount)
        const visual = assetForComponent(component, slot)
        const direction = slot === 'propeller'
          ? (aircraft?.propeller_directions?.[name] ?? MOTOR_DIRECTIONS[name])
          : undefined
        const url = slot === 'propeller'
          ? propellerAssetUrl(component, direction!)
          : assetUrl(visual)
        const object = await this.loadRequired(url)
        if (generation !== this.generation) return
        applyVisualScale(object, visual)
        object.position.copy(simulationVectorToThree(mount.position))

        if (slot === 'esc') {
          const p = object.position
          object.rotation.y = Math.atan2(-p.z, p.x)
        }

        this.register(
          mount,
          object,
          isMountInstalled(aircraft, mount.id),
          component?.id ?? null,
          url,
          direction,
        )
        if (slot === 'propeller') {
          this.rotorGroups.push({
            group: object,
            sign: direction === 'CW' ? -1 : 1,
            mountId: mount.id,
          })
        }
      }
    }

    // Single-instance avionics / power / payload mounts.
    for (const slot of [
      'battery',
      'power_module',
      'flight_controller',
      'gnss',
      'payload',
    ] as ComponentType[]) {
      const mount = mountFor(mounts, `${slot}:main`)
      const component = mountComponent(aircraft, components, mount)
      const visual = assetForComponent(component, slot)
      const url = assetUrl(visual)
      const object = await this.loadRequired(url)
      if (generation !== this.generation) return
      applyVisualScale(object, visual)
      object.position.copy(simulationVectorToThree(mount.position))
      this.register(
        mount,
        object,
        isMountInstalled(aircraft, mount.id),
        component?.id ?? null,
        url,
      )
    }

    // GNSS mast is a structural teaching cue, not a catalog component.
    const gnssMount = mountFor(mounts, 'gnss:main')
    const gnssThree = simulationVectorToThree(gnssMount.position)
    const motorHeight = simulationVectorToThree(
      mountFor(mounts, 'motor:M1').position,
    ).y
    if (aircraft?.gnss_id || !aircraft) {
      const mastHeight = Math.max(0.08, gnssThree.y - motorHeight)
      const mast = new THREE.Mesh(
        new THREE.CylinderGeometry(0.0035, 0.0035, mastHeight, 14),
        new THREE.MeshStandardMaterial({
          color: 0x20252b,
          metalness: 0.25,
          roughness: 0.55,
        }),
      )
      // Make the mast a child of the GNSS part so install/explode transforms
      // remain unified instead of leaving the support behind in world space.
      mast.position.set(0, -mastHeight / 2, 0)
      mast.castShadow = true
      mast.userData.slot = 'gnss'
      mast.userData.mountId = 'gnss:main'
      const gnssPart = this.parts.find(item => item.mountId === 'gnss:main')
      gnssPart?.object.add(mast)
    }

    this.root.position.copy(oldPosition)
    this.root.rotation.copy(oldRotation)
    this.root.scale.copy(oldScale)
    this.explodedProgress = explodedProgress
    this.applyTransforms()
    this.applyAssemblyState(aircraft, null)
  }

  applyAssemblyState(
    aircraft: AircraftDefinition | null | undefined,
    selectedSlot: AssemblySlot | null,
    issueSlots: AssemblySlot[] = [],
    issueMounts: MotorName[] = [],
    selectedMountId: string | null = null,
    issueMountIds: string[] = [],
    pendingSlot: AssemblySlot | null = null,
    hoveredMountId: string | null = null,
  ): void {
    this.parts.forEach(part => {
      const installed = isMountInstalled(aircraft, part.mountId)
      part.installed = installed
      const pending = !installed && pendingSlot === part.slot
      const hovered = pending && hoveredMountId === part.mountId
      const selected = hovered || (
        selectedMountId
          ? selectedMountId === part.mountId
          : selectedSlot === part.slot
      )
      const issue = issueMountIds.includes(part.mountId)
        || issueSlots.includes(part.slot)
        || Boolean(part.motorName && issueMounts.includes(part.motorName))
      part.meshes.forEach(mesh =>
        applyMaterialState(mesh, installed, selected, issue, pending, hovered),
      )
      // Empty slots stay out of the way unless they are currently relevant.
      part.object.visible = installed || pending || selected || issue
    })
  }

  setExplodedProgress(progress: number): void {
    this.explodedProgress = Math.max(0, Math.min(1, progress))
    this.applyTransforms()
  }

  setInstallationProgress(mountId: string, progress: number): void {
    this.installationProgress.set(
      mountId,
      Math.max(0, Math.min(1, progress)),
    )
    this.applyTransforms()
  }

  installationProgressSnapshot(mountId: string): number {
    return this.installationProgress.get(mountId) ?? 1
  }

  explodedProgressSnapshot(): number {
    return this.explodedProgress
  }

  explodedPartsSnapshot(): ExplodedPartSnapshot[] {
    return this.parts.map(part => ({
      mountId: part.mountId,
      slot: part.slot,
      componentId: part.componentId,
      ...(part.motorName ? { motorName: part.motorName } : {}),
      installed: part.installed,
      basePosition: vectorSnapshot(part.basePosition),
      currentPosition: vectorSnapshot(part.object.position),
      offset: vectorSnapshot(part.explosionOffset),
    }))
  }

  partInstancesSnapshot(): PartInstanceSnapshot[] {
    return this.parts.map(part => ({
      mountId: part.mountId,
      slot: part.slot,
      componentId: part.componentId,
      ...(part.motorName ? { motorName: part.motorName } : {}),
      installed: part.installed,
      basePosition: vectorSnapshot(part.basePosition),
      currentPosition: vectorSnapshot(part.object.position),
      offset: vectorSnapshot(part.explosionOffset),
      installProgress: this.installationProgress.get(part.mountId) ?? 1,
    }))
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

  mountForObject(object: THREE.Object3D): string | null {
    let current: THREE.Object3D | null = object
    while (current) {
      const mountId = current.userData.mountId as string | undefined
      if (mountId) return mountId
      current = current.parent
    }
    return null
  }

  loadedAssetsSnapshot(): LoadedAssetSnapshot[] {
    const result: LoadedAssetSnapshot[] = []
    const seen = new Set<string>()
    this.parts.forEach(part => {
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
        .filter(part => part.slot === slot)
        .map(part => part.object)
      if (objects.length > 0) result[slot] = dimensionsForObjects(objects)
    })
    return result
  }

  boundsForMount(mountId: string): VisualBoundsSnapshot | null {
    const part = this.parts.find(item => item.mountId === mountId)
    return part ? dimensionsForObjects([part.object]) : null
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
