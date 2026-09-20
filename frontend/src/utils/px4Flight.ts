import type { Px4Telemetry } from '../api/px4'
import type { AircraftEngineeringSummary } from '../types/aircraft'
import type { FlightMode, MotorVector, TelemetryFrame } from '../types/telemetry'

export interface Px4FlightVisualizationOptions {
  windSpeedMps?: number
  windDirectionDeg?: number
}

function finite(value: number | null | undefined, fallback = 0): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback
}

function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value))
}

function motorVector(values: number[] | undefined): MotorVector {
  return [
    clamp01(finite(values?.[0])),
    clamp01(finite(values?.[1])),
    clamp01(finite(values?.[2])),
    clamp01(finite(values?.[3])),
  ]
}

export function px4FlightMode(telemetry: Px4Telemetry): FlightMode {
  const mode = (telemetry.mode || '').toUpperCase()

  if (!telemetry.armed) return 'IDLE'
  if (telemetry.landed_state === 3 || mode.includes('TAKEOFF')) return 'TAKING_OFF'
  if (telemetry.landed_state === 4 || mode.includes('LAND')) return 'LANDING'
  if (telemetry.landed_state === 1) return 'ARMED'

  const altitude = Math.max(0, finite(telemetry.local_position?.z))
  if (telemetry.landed_state === 2 || altitude > 0.25) return 'HOVERING'
  return 'ARMED'
}

/**
 * Convert PX4 NED/FRD telemetry into UAV Studio's simulation convention:
 *   UAV Studio: X forward/north, Y left/west, Z up.
 *   PX4 local NED: X north, Y east, Z down (Bridge already exposes Z as up).
 *
 * The Bridge already inverts LOCAL_POSITION_NED z/vz. We invert east -> left
 * here and apply the corresponding attitude sign conversion.
 */
export function px4TelemetryToFrame(
  telemetry: Px4Telemetry,
  elapsedS: number,
  engineering: AircraftEngineeringSummary | null | undefined,
  options: Px4FlightVisualizationOptions = {},
): TelemetryFrame {
  const outputs = motorVector(telemetry.motors?.outputs)
  const maxThrust = finite(engineering?.max_thrust_per_motor_n)
  const thrusts = outputs.map(output => output * maxThrust) as MotorVector
  const mass = finite(engineering?.total_mass_kg)
  const voltage = finite(telemetry.battery?.voltage_v)
  const current = Math.max(0, finite(telemetry.battery?.current_a))
  const remainingRaw = telemetry.battery?.remaining
  const batteryRemaining = typeof remainingRaw === 'number' && Number.isFinite(remainingRaw)
    ? clamp01(remainingRaw / 100)
    : 1

  return {
    t: Math.max(0, elapsedS),
    position: {
      x: finite(telemetry.local_position?.x),
      y: -finite(telemetry.local_position?.y),
      z: Math.max(0, finite(telemetry.local_position?.z)),
    },
    velocity: {
      x: finite(telemetry.local_position?.vx),
      y: -finite(telemetry.local_position?.vy),
      z: finite(telemetry.local_position?.vz),
    },
    attitude: {
      roll: finite(telemetry.attitude?.roll),
      pitch: -finite(telemetry.attitude?.pitch),
      yaw: -finite(telemetry.attitude?.yaw),
    },
    angular_velocity: {
      p: finite(telemetry.attitude?.rollspeed),
      q: -finite(telemetry.attitude?.pitchspeed),
      r: -finite(telemetry.attitude?.yawspeed),
    },
    center_of_gravity: engineering?.center_of_gravity_m
      ? { ...engineering.center_of_gravity_m }
      : { x: 0, y: 0, z: 0 },
    motors: {
      outputs,
      thrusts_n: thrusts,
    },
    forces: {
      gravity_n: mass * 9.80665,
      total_thrust_n: thrusts.reduce((sum, value) => sum + value, 0),
    },
    wind: {
      speed_mps: Math.max(0, finite(options.windSpeedMps)),
      direction_deg: finite(options.windDirectionDeg),
    },
    power: {
      estimated_power_w: voltage * current,
      battery_remaining: batteryRemaining,
      voltage_v: voltage,
      current_a: current,
    },
    armed: Boolean(telemetry.armed),
    flight_mode: px4FlightMode(telemetry),
  }
}

export function px4IsAirborne(telemetry: Px4Telemetry | null | undefined): boolean {
  if (!telemetry) return false
  if (telemetry.landed_state === 2 || telemetry.landed_state === 3 || telemetry.landed_state === 4) return true
  return Math.max(0, finite(telemetry.local_position?.z)) > 0.25
}

export function landedStateText(state: number | null | undefined): string {
  if (state === 1) return '地面'
  if (state === 2) return '空中'
  if (state === 3) return '起飞中'
  if (state === 4) return '降落中'
  return '未知'
}
