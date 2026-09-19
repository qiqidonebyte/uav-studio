import type { Vector3Value } from './aircraft'

export type FlightMode = 'IDLE' | 'ARMED' | 'TAKING_OFF' | 'HOVERING' | 'LANDING'
export type SimulationStatus = 'STOPPED' | 'RUNNING' | 'PAUSED'
export type MotorVector = [number, number, number, number]

export interface TelemetryFrame {
  t: number
  position: Vector3Value
  velocity: Vector3Value
  attitude: { roll: number; pitch: number; yaw: number } // rad
  angular_velocity: { p: number; q: number; r: number } // rad/s
  center_of_gravity: Vector3Value
  motors: {
    outputs: MotorVector
    thrusts_n: MotorVector
  }
  forces: { gravity_n: number; total_thrust_n: number }
  wind: { speed_mps: number; direction_deg: number }
  power: {
    estimated_power_w: number
    battery_remaining: number
    voltage_v: number
    current_a: number
  }
  armed: boolean
  flight_mode: FlightMode
}

export interface SimulationSnapshot {
  id: number
  status: SimulationStatus
  telemetry: TelemetryFrame
  target_position: { x: number; y: number; z: number }
  waypoints: Array<{ x: number; y: number; z: number }>
  boundary_m: number
}

export interface ExperimentSummary {
  id: number
  aircraft_id: number
  aircraft_name: string
  started_at: string
  ended_at: string
  duration_s: number
  max_altitude_m: number
  status: 'COMPLETED' | 'STOPPED'
  frame_count: number
}

export interface ExperimentReplay {
  experiment: ExperimentSummary
  aircraft: import('./aircraft').AircraftDefinition
  components: import('./aircraft').Component[]
  frames: TelemetryFrame[]
  target_position: { x: number; y: number; z: number }
  waypoints: Array<{ x: number; y: number; z: number }>
  boundary_m: number
}
