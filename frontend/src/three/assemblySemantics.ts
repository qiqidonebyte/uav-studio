import type {
  AircraftDefinition,
  AssemblyInstance,
  Component,
  ComponentType,
  MotorName,
  Vector3Value,
} from '../types/aircraft'

export type MountId = string

export interface MountPoint {
  id: MountId
  slot: ComponentType
  label: string
  position: Vector3Value
  install_offset: Vector3Value
  snap_radius_m: number
  required: boolean
  motorName?: MotorName
}

export interface SpatialDiagnostic {
  code: string
  severity: 'error' | 'warning'
  message: string
  slots: ComponentType[]
  mountIds: string[]
}

export interface BatteryBayFitResult {
  fits: boolean
  bay: Vector3Value
  battery: Vector3Value
  excess: Vector3Value
}

export const MOUNT_IDS_BY_SLOT: Record<ComponentType, readonly string[]> = {
  frame: ['frame:main'],
  motor: ['motor:M1', 'motor:M2', 'motor:M3', 'motor:M4'],
  esc: ['esc:M1', 'esc:M2', 'esc:M3', 'esc:M4'],
  propeller: ['propeller:M1', 'propeller:M2', 'propeller:M3', 'propeller:M4'],
  battery: ['battery:main'],
  power_module: ['power_module:main'],
  flight_controller: ['flight_controller:main'],
  gnss: ['gnss:main'],
  payload: ['payload:main'],
}

const SLOT_FIELD: Record<ComponentType, keyof AircraftDefinition> = {
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

const SLOT_LABEL: Record<ComponentType, string> = {
  frame: '机架基准',
  motor: '电机',
  esc: '电调',
  propeller: '螺旋桨',
  battery: '电池',
  power_module: '电源模块',
  flight_controller: '飞控',
  gnss: 'GNSS',
  payload: '任务载荷',
}

const REQUIRED_SLOTS = new Set<ComponentType>([
  'frame',
  'motor',
  'esc',
  'propeller',
  'battery',
  'power_module',
  'flight_controller',
])

function numberParam(component: Component | null, key: string, fallback: number): number {
  const value = component?.parameters_json[key]
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback
}

function vectorParam(
  component: Component | null,
  key: string,
  fallback: Vector3Value,
): Vector3Value {
  const raw = component?.parameters_json[key]
  if (!raw || typeof raw !== 'object') return { ...fallback }
  const value = raw as Record<string, unknown>
  if (
    typeof value.x !== 'number' ||
    typeof value.y !== 'number' ||
    typeof value.z !== 'number'
  ) return { ...fallback }
  return { x: value.x, y: value.y, z: value.z }
}

function rawMount(
  frame: Component | null,
  key: string,
): Vector3Value | null {
  const raw = frame?.parameters_json.mount_points
  if (!raw || typeof raw !== 'object') return null
  const value = (raw as Record<string, unknown>)[key]
  if (!value || typeof value !== 'object') return null
  const point = value as Record<string, unknown>
  if (
    typeof point.x !== 'number' ||
    typeof point.y !== 'number' ||
    typeof point.z !== 'number'
  ) return null
  return { x: point.x, y: point.y, z: point.z }
}

export function selectedComponentId(
  aircraft: AircraftDefinition,
  slot: ComponentType,
): number | null {
  const value = aircraft[SLOT_FIELD[slot]]
  return typeof value === 'number' ? value : null
}

export function componentById(
  components: Component[],
  componentId: number | null | undefined,
): Component | null {
  if (!componentId) return null
  return components.find(component => component.id === componentId) ?? null
}

function motorFallbacks(diagonal: number): Record<MotorName, Vector3Value> {
  const horizontal = diagonal / 2 / Math.sqrt(2)
  const vertical = 0.066 * (diagonal / 0.65)
  return {
    M1: { x: horizontal, y: horizontal, z: vertical },
    M2: { x: horizontal, y: -horizontal, z: vertical },
    M3: { x: -horizontal, y: -horizontal, z: vertical },
    M4: { x: -horizontal, y: horizontal, z: vertical },
  }
}

function outwardOffset(point: Vector3Value, distance: number, vertical = 0): Vector3Value {
  const length = Math.hypot(point.x, point.y)
  const nx = length > 1e-9 ? point.x / length : 1
  const ny = length > 1e-9 ? point.y / length : 0
  return { x: nx * distance, y: ny * distance, z: vertical }
}

function motorNameFromMount(id: string): MotorName | undefined {
  const name = id.split(':')[1]
  return name === 'M1' || name === 'M2' || name === 'M3' || name === 'M4'
    ? name
    : undefined
}

/**
 * Resolve the complete 3D installation contract from the currently selected
 * frame. Existing mount_points data wins; legacy projects get deterministic
 * derived mounts from motor_diagonal_m and the old single-part positions.
 */
export function buildMountPoints(
  aircraft: AircraftDefinition | null | undefined,
  components: Component[],
): MountPoint[] {
  const frame = componentById(components, aircraft?.frame_id)
  const diagonal = numberParam(frame, 'motor_diagonal_m', 0.65)
  const motors = motorFallbacks(diagonal)
  const scale = diagonal / 0.65

  ;(['M1', 'M2', 'M3', 'M4'] as MotorName[]).forEach(name => {
    const key = `motor_${name.toLowerCase()}`
    motors[name] = rawMount(frame, key) ?? motors[name]
  })

  const mounts: MountPoint[] = [
    {
      id: 'frame:main',
      slot: 'frame',
      label: '机架基准',
      position: { x: 0, y: 0, z: 0 },
      install_offset: { x: 0, y: 0, z: 0 },
      snap_radius_m: 0.08,
      required: true,
    },
  ]

  for (const name of ['M1', 'M2', 'M3', 'M4'] as MotorName[]) {
    const motor = motors[name]
    const esc = rawMount(frame, `esc_${name.toLowerCase()}`) ?? {
      x: motor.x * 0.64,
      y: motor.y * 0.64,
      z: motor.z * 0.58,
    }
    mounts.push(
      {
        id: `motor:${name}`,
        slot: 'motor',
        label: `${name} 电机`,
        motorName: name,
        position: motor,
        install_offset: {
          ...outwardOffset(motor, 0.18 * scale, 0.07 * scale),
        },
        snap_radius_m: 0.055 * scale,
        required: true,
      },
      {
        id: `esc:${name}`,
        slot: 'esc',
        label: `${name} 电调`,
        motorName: name,
        position: esc,
        install_offset: {
          ...outwardOffset(esc, 0.13 * scale, 0.045 * scale),
        },
        snap_radius_m: 0.05 * scale,
        required: true,
      },
      {
        id: `propeller:${name}`,
        slot: 'propeller',
        label: `${name} 螺旋桨`,
        motorName: name,
        position: {
          x: motor.x,
          y: motor.y,
          z: motor.z + 0.064,
        },
        install_offset: { x: 0, y: 0, z: 0.16 * scale },
        snap_radius_m: 0.07 * scale,
        required: true,
      },
    )
  }

  const battery = rawMount(frame, 'battery') ?? vectorParam(
    frame,
    'battery_position_m',
    { x: -0.03 * scale, y: 0, z: -0.10 * scale },
  )
  const power = rawMount(frame, 'power_module') ?? vectorParam(
    frame,
    'power_module_position_m',
    { x: 0, y: 0, z: 0.02 * scale },
  )
  const fc = rawMount(frame, 'flight_controller') ?? vectorParam(
    frame,
    'flight_controller_position_m',
    { x: 0, y: 0, z: 0.05 * scale },
  )
  const gnss = aircraft?.gnss_position_m
    ?? rawMount(frame, 'gnss')
    ?? vectorParam(
      frame,
      'gnss_mount_position_m',
      { x: -0.16 * scale, y: 0, z: 0.08 * scale },
    )

  const payloadComponent = componentById(components, aircraft?.payload_id)
  const payloadMode = payloadComponent?.parameters_json.mount
  const payload = aircraft?.payload_position_m
    ?? rawMount(frame, payloadMode === 'front' ? 'payload_front' : 'payload_bottom')
    ?? (
      payloadMode === 'front'
        ? { x: 0.18 * scale, y: 0, z: -0.02 * scale }
        : { x: 0.08 * scale, y: 0, z: -0.12 * scale }
    )

  mounts.push(
    {
      id: 'battery:main',
      slot: 'battery',
      label: '主电池',
      position: battery,
      install_offset: { x: 0, y: 0, z: -0.20 * scale },
      snap_radius_m: 0.08 * scale,
      required: true,
    },
    {
      id: 'power_module:main',
      slot: 'power_module',
      label: '电源模块',
      position: power,
      install_offset: { x: -0.16 * scale, y: 0, z: -0.08 * scale },
      snap_radius_m: 0.06 * scale,
      required: true,
    },
    {
      id: 'flight_controller:main',
      slot: 'flight_controller',
      label: '飞控',
      position: fc,
      install_offset: { x: 0, y: 0, z: 0.18 * scale },
      snap_radius_m: 0.055 * scale,
      required: true,
    },
    {
      id: 'gnss:main',
      slot: 'gnss',
      label: 'GNSS',
      position: gnss,
      install_offset: { x: 0, y: 0, z: 0.24 * scale },
      snap_radius_m: 0.06 * scale,
      required: false,
    },
    {
      id: 'payload:main',
      slot: 'payload',
      label: '任务载荷',
      position: payload,
      install_offset: { x: 0.10 * scale, y: 0, z: -0.24 * scale },
      snap_radius_m: 0.08 * scale,
      required: false,
    },
  )
  return mounts
}

export function legacyAssemblyInstances(
  aircraft: AircraftDefinition,
): AssemblyInstance[] {
  const result: AssemblyInstance[] = []
  for (const slot of Object.keys(MOUNT_IDS_BY_SLOT) as ComponentType[]) {
    const componentId = selectedComponentId(aircraft, slot)
    if (componentId === null) continue
    for (const mountId of MOUNT_IDS_BY_SLOT[slot]) {
      result.push({ mount_id: mountId, slot, component_id: componentId })
    }
  }
  return result
}

export function assemblyInstancesFor(
  aircraft: AircraftDefinition | null | undefined,
): AssemblyInstance[] {
  if (!aircraft) return []
  if (Array.isArray(aircraft.assembly_instances)) {
    return aircraft.assembly_instances
  }
  return legacyAssemblyInstances(aircraft)
}

export function instanceAtMount(
  aircraft: AircraftDefinition | null | undefined,
  mountId: string,
): AssemblyInstance | null {
  return assemblyInstancesFor(aircraft).find(item => item.mount_id === mountId) ?? null
}

export function isMountInstalled(
  aircraft: AircraftDefinition | null | undefined,
  mountId: string,
): boolean {
  return instanceAtMount(aircraft, mountId) !== null
}

export function componentIdAtMount(
  aircraft: AircraftDefinition | null | undefined,
  mount: MountPoint,
): number | null {
  return instanceAtMount(aircraft, mount.id)?.component_id ?? null
}

export function mountsForSlot(
  mounts: MountPoint[],
  slot: ComponentType,
): MountPoint[] {
  return mounts.filter(mount => mount.slot === slot)
}

export function clearSlotInstances(
  aircraft: AircraftDefinition,
  slot: ComponentType,
): AssemblyInstance[] {
  return assemblyInstancesFor(aircraft).filter(item => item.slot !== slot)
}

export function replaceSlotInstances(
  aircraft: AircraftDefinition,
  mounts: MountPoint[],
  slot: ComponentType,
  componentId: number,
): AssemblyInstance[] {
  return [
    ...clearSlotInstances(aircraft, slot),
    ...mountsForSlot(mounts, slot).map(mount => ({
      mount_id: mount.id,
      slot,
      component_id: componentId,
    })),
  ]
}

export function installInstance(
  aircraft: AircraftDefinition,
  mount: MountPoint,
  componentId: number,
): AssemblyInstance[] {
  return [
    ...assemblyInstancesFor(aircraft).filter(item => item.mount_id !== mount.id),
    {
      mount_id: mount.id,
      slot: mount.slot,
      component_id: componentId,
    },
  ]
}

export function removeInstance(
  aircraft: AircraftDefinition,
  mountId: string,
): AssemblyInstance[] {
  return assemblyInstancesFor(aircraft).filter(item => item.mount_id !== mountId)
}

export function slotCompletion(
  aircraft: AircraftDefinition | null | undefined,
  slot: ComponentType,
): { installed: number; total: number } {
  const ids = MOUNT_IDS_BY_SLOT[slot]
  const installedSet = new Set(assemblyInstancesFor(aircraft).map(item => item.mount_id))
  return {
    installed: ids.filter(id => installedSet.has(id)).length,
    total: ids.length,
  }
}

export function missingMountsForSlot(
  aircraft: AircraftDefinition | null | undefined,
  mounts: MountPoint[],
  slot: ComponentType,
): MountPoint[] {
  const installed = new Set(assemblyInstancesFor(aircraft).map(item => item.mount_id))
  return mounts.filter(mount => mount.slot === slot && !installed.has(mount.id))
}

export function rotorDiscDiagnostics(
  aircraft: AircraftDefinition | null | undefined,
  components: Component[],
  mounts: MountPoint[],
): SpatialDiagnostic[] {
  if (!aircraft) return []
  const propeller = componentById(components, aircraft.propeller_id)
  const diameterIn = propeller?.parameters_json.diameter_in
  if (typeof diameterIn !== 'number' || diameterIn <= 0) return []

  const diameterM = diameterIn * 0.0254
  const installed = new Set(assemblyInstancesFor(aircraft).map(item => item.mount_id))
  const props = mounts.filter(
    mount => mount.slot === 'propeller' && installed.has(mount.id),
  )

  const collisions: string[] = []
  const affected = new Set<string>()
  for (let i = 0; i < props.length; i += 1) {
    for (let j = i + 1; j < props.length; j += 1) {
      const a = props[i]
      const b = props[j]
      const distance = Math.hypot(
        a.position.x - b.position.x,
        a.position.y - b.position.y,
      )
      const overlap = diameterM - distance
      if (overlap > 0.001) {
        collisions.push(
          `${a.motorName ?? a.id}↔${b.motorName ?? b.id} ${(overlap * 1000).toFixed(1)} mm`,
        )
        affected.add(a.id)
        affected.add(b.id)
      }
    }
  }

  if (collisions.length === 0) return []
  return [{
    code: 'ROTOR_DISC_COLLISION',
    severity: 'error',
    message: `旋翼盘空间干涉：${collisions.join('；')}`,
    slots: ['frame', 'propeller'],
    mountIds: [...affected],
  }]
}

export function batteryBayDimensions(motorDiagonalM: number): Vector3Value {
  return {
    x: motorDiagonalM * 0.40,
    y: motorDiagonalM * 0.18,
    z: motorDiagonalM * 0.14,
  }
}

/**
 * Visual bounds arrive in Three.js axes: X horizontal, Y vertical, Z horizontal.
 * Convert them back to body-space X/Y/Z before comparing to the teaching bay.
 */
export function batteryBayFit(
  motorDiagonalM: number,
  batteryThreeSize: Vector3Value,
): BatteryBayFitResult {
  const bay = batteryBayDimensions(motorDiagonalM)
  const battery = {
    x: batteryThreeSize.x,
    y: batteryThreeSize.z,
    z: batteryThreeSize.y,
  }
  const excess = {
    x: Math.max(0, battery.x - bay.x),
    y: Math.max(0, battery.y - bay.y),
    z: Math.max(0, battery.z - bay.z),
  }
  return {
    fits: excess.x <= 0.001 && excess.y <= 0.001 && excess.z <= 0.001,
    bay,
    battery,
    excess,
  }
}

export function batteryEnvelopeDiagnostic(
  aircraft: AircraftDefinition | null | undefined,
  components: Component[],
  batteryThreeSize: Vector3Value | null,
): SpatialDiagnostic[] {
  if (!aircraft || !batteryThreeSize || !aircraft.battery_id) return []
  const frame = componentById(components, aircraft.frame_id)
  const diagonal = numberParam(frame, 'motor_diagonal_m', 0.65)
  const fit = batteryBayFit(diagonal, batteryThreeSize)
  if (fit.fits) return []
  const excessMm = Math.max(fit.excess.x, fit.excess.y, fit.excess.z) * 1000
  return [{
    code: 'BATTERY_ENVELOPE_EXCEEDED',
    severity: 'warning',
    message: `电池超出教学电池舱包络约 ${excessMm.toFixed(1)} mm，建议检查安装空间。`,
    slots: ['frame', 'battery'],
    mountIds: ['battery:main'],
  }]
}

export function mountLabel(mountId: string): string {
  const slot = mountId.split(':', 1)[0] as ComponentType
  const motor = motorNameFromMount(mountId)
  return motor ? `${motor} ${SLOT_LABEL[slot]}` : SLOT_LABEL[slot] ?? mountId
}

export function isRequiredSlot(slot: ComponentType): boolean {
  return REQUIRED_SLOTS.has(slot)
}
