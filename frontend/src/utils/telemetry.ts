import type {
  FlightMode,
  SimulationStatus,
  TelemetryFrame,
} from '../types/telemetry'

export const SIMULATION_STATUS_LABELS: Record<SimulationStatus, string> = {
  STOPPED: '已停止',
  RUNNING: '运行中',
  PAUSED: '已暂停',
}

export const FLIGHT_MODE_LABELS: Record<FlightMode, string> = {
  IDLE: '待机',
  ARMED: '已解锁',
  TAKING_OFF: '起飞中',
  HOVERING: '悬停',
  LANDING: '降落中',
}

export function recentTelemetry(
  history: TelemetryFrame[],
  latestTime: number,
  seconds = 60,
): TelemetryFrame[] {
  const cutoff = latestTime - seconds
  return history.filter(frame => frame.t >= cutoff).slice(-1200)
}
