export type ComponentType = 'frame' | 'motor' | 'esc' | 'propeller' | 'battery' | 'power_module' | 'flight_controller' | 'gnss' | 'payload'

export type MotorName = 'M1' | 'M2' | 'M3' | 'M4'
export type PropellerDirection = 'CW' | 'CCW'
export type RotorDirection = PropellerDirection

export interface Vector3Value { x: number; y: number; z: number }

export interface FrameMountPoints {
  motor_m1: Vector3Value
  motor_m2: Vector3Value
  motor_m3: Vector3Value
  motor_m4: Vector3Value
  esc_m1: Vector3Value
  esc_m2: Vector3Value
  esc_m3: Vector3Value
  esc_m4: Vector3Value
  battery: Vector3Value
  power_module: Vector3Value
  flight_controller: Vector3Value
  gnss: Vector3Value
  payload_front: Vector3Value
  payload_bottom: Vector3Value
}

export interface ComponentVisual {
  asset_key: string
  file?: string | null
  cw_file?: string | null
  ccw_file?: string | null
  thumbnail?: string | null
  scale: number
}

export interface Component {
  id: number
  name: string
  type: ComponentType
  mass_kg: number
  parameters_json: Record<string, unknown>
  visual?: ComponentVisual | null
}

export interface AssemblyInstance {
  mount_id: string
  slot: ComponentType
  component_id: number
}

export interface AircraftDefinition {
  id?: number
  name: string
  frame_id?: number | null
  motor_id?: number | null
  esc_id?: number | null
  propeller_id?: number | null
  battery_id?: number | null
  power_module_id?: number | null
  flight_controller_id?: number | null
  gnss_id?: number | null
  payload_id?: number | null
  gnss_position_m?: Vector3Value | null
  payload_position_m?: Vector3Value | null
  propeller_directions?: Record<MotorName, PropellerDirection> | null
  /**
   * Physical 3D assembly state. Legacy aircraft without this field are treated
   * as fully assembled from their slot-level component IDs.
   */
  assembly_instances?: AssemblyInstance[]
}

export interface InertiaEstimate {
  ixx: number
  iyy: number
  izz: number
}

export interface AssemblyIssue {
  code: string
  severity: 'error' | 'warning'
  message: string
  affected_slots?: ComponentType[]
  affected_mounts?: MotorName[]
  affected_mount_ids?: string[]
}

export interface AssemblyValidationResult {
  passed: boolean
  blocking_errors: AssemblyIssue[]
  warnings: AssemblyIssue[]
}

export interface AircraftEngineeringSummary {
  total_mass_kg: number
  center_of_gravity_m: Vector3Value
  inertia_kg_m2: InertiaEstimate
  max_thrust_per_motor_n: number
  max_total_thrust_n: number
  thrust_weight_ratio: number
  hover_throttle: number
  hover_thrust_per_motor_n: number
  hover_current_a: number
  max_current_a: number
  hover_power_w: number
  max_power_w: number
  battery_continuous_margin_a: number
  esc_current_margin_a: number
  power_module_current_margin_a: number
  payload_mass_fraction: number
  estimated_flight_time_min: number
  validation: AssemblyValidationResult
  estimation_note: 'Educational Estimation'
}

export interface AssemblyState {
  aircraft: AircraftDefinition
  engineering: AircraftEngineeringSummary | null
  validation: AssemblyValidationResult
}


export interface AircraftLibraryItem {
  aircraft: AircraftDefinition
  engineering: AircraftEngineeringSummary | null
  validation: AssemblyValidationResult
  description: string
  created_at: string
  updated_at: string
  experiment_count: number
}

export interface AircraftTemplate {
  key: string
  name: string
  description: string
  aircraft: AircraftDefinition
}

export interface AircraftMetadataUpdate {
  name?: string
  description?: string
}
