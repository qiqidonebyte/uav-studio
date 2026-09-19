export type ComponentType = 'frame' | 'motor' | 'esc' | 'propeller' | 'battery' | 'power_module' | 'flight_controller' | 'gnss' | 'payload'

export interface Vector3Value { x: number; y: number; z: number }

export interface Component {
  id: number
  name: string
  type: ComponentType
  mass_kg: number
  parameters_json: Record<string, unknown>
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
