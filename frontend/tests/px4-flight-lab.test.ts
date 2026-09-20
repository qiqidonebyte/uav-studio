import { describe, expect, it } from 'vitest'
import type { Px4Telemetry } from '../src/api/px4'
import { px4FlightMode, px4TelemetryToFrame } from '../src/utils/px4Flight'

function telemetry(overrides: Partial<Px4Telemetry> = {}): Px4Telemetry {
  return {
    dependency_available: true,
    running: true,
    connected: true,
    connection_url: 'udpin:0.0.0.0:14540',
    heartbeat_age_s: 0.1,
    system_id: 1,
    component_id: 1,
    mode: 'AUTO_TAKEOFF',
    armed: true,
    last_error: '',
    uptime_s: 1,
    landed_state: 3,
    attitude: { roll: 0.1, pitch: 0.2, yaw: 0.3, rollspeed: 1, pitchspeed: 2, yawspeed: 3 },
    local_position: { x: 4, y: 5, z: 2, vx: 1, vy: 2, vz: .3 },
    global_position: { lat_deg: 1, lon_deg: 2, relative_alt_m: 2, alt_amsl_m: 502 },
    gps: { fix_type: 3, satellites: 10, eph: .8 },
    battery: { voltage_v: 22.2, current_a: 5, remaining: 80 },
    motors: { outputs: [.2, .3, .4, .5] },
    estimator: { flags: 1, ok: true },
    statustext: '',
    prearm_ok: true,
    ...overrides,
  }
}

describe('PX4 flight telemetry adapter', () => {
  it('maps PX4 NED east into UAV Studio left-axis coordinates', () => {
    const frame = px4TelemetryToFrame(telemetry(), 3, null)
    expect(frame.position).toEqual({ x: 4, y: -5, z: 2 })
    expect(frame.velocity).toEqual({ x: 1, y: -2, z: .3 })
    expect(frame.attitude.roll).toBeCloseTo(.1)
    expect(frame.attitude.pitch).toBeCloseTo(-.2)
    expect(frame.attitude.yaw).toBeCloseTo(-.3)
  })

  it('uses PX4 landed state to derive flight phase', () => {
    expect(px4FlightMode(telemetry({ landed_state: 3 }))).toBe('TAKING_OFF')
    expect(px4FlightMode(telemetry({ landed_state: 4, mode: 'AUTO_LAND' }))).toBe('LANDING')
    expect(px4FlightMode(telemetry({ landed_state: 2, mode: 'POSCTL' }))).toBe('HOVERING')
    expect(px4FlightMode(telemetry({ landed_state: 1, mode: 'MANUAL' }))).toBe('ARMED')
  })

  it('normalizes PX4 battery percent to TelemetryFrame 0-1', () => {
    const frame = px4TelemetryToFrame(telemetry(), 1, null)
    expect(frame.power.battery_remaining).toBeCloseTo(.8)
    expect(frame.power.estimated_power_w).toBeCloseTo(111)
  })
})
