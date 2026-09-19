import { describe, expect, it } from 'vitest'
import { flightControlAvailability } from '../src/utils/flightControlGuards'

const base = {
  assemblyReady: true,
  busy: false,
  simulationId: null as number | null,
  simulationStatus: 'STOPPED' as const,
  armed: false,
  flightMode: 'IDLE' as const,
  airborne: false,
}

describe('Flight Lab command state machine', () => {
  it('initially allows Start only, while Arm/Takeoff/Land are disabled', () => {
    const state = flightControlAvailability(base)

    expect(state.canStart).toBe(true)
    expect(state.canPause).toBe(false)
    expect(state.canArm).toBe(false)
    expect(state.canTakeoff).toBe(false)
    expect(state.canLand).toBe(false)
  })

  it('after Start, enables Arm but keeps Takeoff disabled', () => {
    const state = flightControlAvailability({
      ...base,
      simulationId: 1,
      simulationStatus: 'RUNNING',
    })

    expect(state.canStart).toBe(false)
    expect(state.canPause).toBe(true)
    expect(state.canArm).toBe(true)
    expect(state.canTakeoff).toBe(false)
    expect(state.canLand).toBe(false)
  })

  it('after Arm, disables Arm and enables Takeoff only', () => {
    const state = flightControlAvailability({
      ...base,
      simulationId: 1,
      simulationStatus: 'RUNNING',
      armed: true,
      flightMode: 'ARMED',
    })

    expect(state.canArm).toBe(false)
    expect(state.canTakeoff).toBe(true)
    expect(state.canLand).toBe(false)
  })

  it('during takeoff/hover, disables Takeoff and enables Land', () => {
    for (const flightMode of ['TAKING_OFF', 'HOVERING'] as const) {
      const state = flightControlAvailability({
        ...base,
        simulationId: 1,
        simulationStatus: 'RUNNING',
        armed: true,
        flightMode,
        airborne: true,
      })

      expect(state.canArm).toBe(false)
      expect(state.canTakeoff).toBe(false)
      expect(state.canLand).toBe(true)
    }
  })

  it('pause locks flight commands even if telemetry still says armed', () => {
    const state = flightControlAvailability({
      ...base,
      simulationId: 1,
      simulationStatus: 'PAUSED',
      armed: true,
      flightMode: 'ARMED',
    })

    expect(state.canStart).toBe(true)
    expect(state.canArm).toBe(false)
    expect(state.canTakeoff).toBe(false)
    expect(state.canLand).toBe(false)
  })

  it('assembly failure disables Start', () => {
    const state = flightControlAvailability({
      ...base,
      assemblyReady: false,
    })
    expect(state.canStart).toBe(false)
  })
})
