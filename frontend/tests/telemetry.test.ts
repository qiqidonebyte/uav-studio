import { describe, expect, it } from 'vitest'
import type { TelemetryFrame } from '../src/types/telemetry'
import {
  FLIGHT_MODE_LABELS,
  SIMULATION_STATUS_LABELS,
  recentTelemetry,
} from '../src/utils/telemetry'

function frameAt(t: number): TelemetryFrame {
  return {
    t,
    position: { x: 0, y: 0, z: t },
    velocity: { x: 0, y: 0, z: 0 },
    attitude: { roll: 0, pitch: 0, yaw: 0 },
    angular_velocity: { p: 0, q: 0, r: 0 },
    center_of_gravity: { x: 0, y: 0, z: 0 },
    motors: { outputs: [0, 0, 0, 0], thrusts_n: [0, 0, 0, 0] },
    forces: { gravity_n: 0, total_thrust_n: 0 },
    wind: { speed_mps: 0, direction_deg: 0 },
    power: {
      estimated_power_w: 0,
      battery_remaining: 1,
      voltage_v: 22.2,
      current_a: 0,
    },
    armed: false,
    flight_mode: 'IDLE',
  }
}

describe('telemetry helpers', () => {
  it('keeps the latest 60 seconds for realtime charts', () => {
    const history = Array.from({ length: 200 }, (_, index) => frameAt(index * 0.5))

    const window = recentTelemetry(history, 99.5, 60)

    expect(window.length).toBe(121)
    expect(window[0].t).toBe(39.5)
    expect(window.at(-1)?.t).toBe(99.5)
  })

  it('exposes frozen Chinese status labels', () => {
    expect(SIMULATION_STATUS_LABELS.RUNNING).toBe('运行中')
    expect(SIMULATION_STATUS_LABELS.PAUSED).toBe('已暂停')
    expect(FLIGHT_MODE_LABELS.HOVERING).toBe('悬停')
    expect(FLIGHT_MODE_LABELS.LANDING).toBe('降落中')
  })
})
