export type FlightSimulationStatus = 'STOPPED' | 'RUNNING' | 'PAUSED'
export type FlightMode = 'IDLE' | 'ARMED' | 'TAKING_OFF' | 'HOVERING' | 'LANDING'

export interface FlightControlContext {
  assemblyReady: boolean
  busy: boolean
  simulationId: number | null
  simulationStatus: FlightSimulationStatus
  armed: boolean
  flightMode: FlightMode
  airborne: boolean
}

export interface FlightControlAvailability {
  canStart: boolean
  canPause: boolean
  canReset: boolean
  canStop: boolean
  canArm: boolean
  canTakeoff: boolean
  canLand: boolean
  canApplyWind: boolean
  canSetTarget: boolean
}

/**
 * Single source of truth for the Flight Lab command state machine.
 *
 * Intended sequence:
 * assembly passed -> start simulation -> arm -> takeoff -> land.
 * A button is enabled only when the command is valid in the current state.
 */
export function flightControlAvailability(
  context: FlightControlContext,
): FlightControlAvailability {
  const {
    assemblyReady,
    busy,
    simulationId,
    simulationStatus,
    armed,
    flightMode,
    airborne,
  } = context

  const hasSimulation = simulationId !== null
  const running = simulationStatus === 'RUNNING'
  const stopped = simulationStatus === 'STOPPED'
  const idleOnGround = flightMode === 'IDLE' && !airborne
  const takeoffReady = flightMode === 'ARMED' && !airborne
  const landingReady = flightMode === 'TAKING_OFF' || flightMode === 'HOVERING'

  return {
    canStart: assemblyReady && !busy && !running,
    canPause: !busy && running,
    canReset: !busy && hasSimulation,
    canStop: !busy && hasSimulation && !stopped,
    canArm: !busy && running && !armed && idleOnGround,
    canTakeoff: !busy && running && armed && takeoffReady,
    canLand: !busy && running && armed && landingReady,
    canApplyWind: !busy && running && hasSimulation,
    canSetTarget: !busy && running && armed && flightMode !== 'LANDING',
  }
}
