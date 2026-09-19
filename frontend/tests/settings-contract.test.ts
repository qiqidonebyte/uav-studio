import { describe, expect, it } from 'vitest'
import { DEFAULT_USER_SETTINGS } from '../src/types/settings'
import { flightControlAvailability } from '../src/utils/flightControlGuards'

describe('settings contract', () => {
  it('keeps safe flight defaults and never introduces automatic arm/takeoff', () => {
    expect(DEFAULT_USER_SETTINGS.flight.default_altitude_m).toBe(5)
    expect(DEFAULT_USER_SETTINGS.flight.default_view).toBe('split')
    expect(DEFAULT_USER_SETTINGS.flight.auto_create_simulation).toBe(false)
    expect(DEFAULT_USER_SETTINGS.flight.auto_connect_telemetry).toBe(true)
    expect('auto_arm' in DEFAULT_USER_SETTINGS.flight).toBe(false)
    expect('auto_takeoff' in DEFAULT_USER_SETTINGS.flight).toBe(false)
  })

  it('still requires start then arm before takeoff', () => {
    const beforeStart = flightControlAvailability({
      assemblyReady: true,
      busy: false,
      simulationId: null,
      simulationStatus: 'STOPPED',
      armed: false,
      flightMode: 'IDLE',
      airborne: false,
    })
    expect(beforeStart.canArm).toBe(false)
    expect(beforeStart.canTakeoff).toBe(false)

    const runningDisarmed = flightControlAvailability({
      assemblyReady: true,
      busy: false,
      simulationId: 1,
      simulationStatus: 'RUNNING',
      armed: false,
      flightMode: 'IDLE',
      airborne: false,
    })
    expect(runningDisarmed.canArm).toBe(true)
    expect(runningDisarmed.canTakeoff).toBe(false)

    const armed = flightControlAvailability({
      assemblyReady: true,
      busy: false,
      simulationId: 1,
      simulationStatus: 'RUNNING',
      armed: true,
      flightMode: 'ARMED',
      airborne: false,
    })
    expect(armed.canTakeoff).toBe(true)
  })

  it('uses conservative 3D defaults', () => {
    expect(DEFAULT_USER_SETTINGS.display_3d.quality).toBe('balanced')
    expect(DEFAULT_USER_SETTINGS.display_3d.trajectory_points).toBe(600)
    expect(DEFAULT_USER_SETTINGS.display_3d.show_grid).toBe(true)
    expect(DEFAULT_USER_SETTINGS.display_3d.show_cg).toBe(true)
  })
})
