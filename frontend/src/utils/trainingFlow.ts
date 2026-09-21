export type TrainingRunStatus =
  | 'not_started'
  | 'in_progress'
  | 'awaiting_prearm'
  | 'awaiting_flight'
  | 'completed'
  | string

export interface TrainingRouteInput {
  runId: number
  assignmentId?: number | null
  scenarioId: string
  status: TrainingRunStatus
}

export interface TrainingRouteTarget {
  path: '/debugging' | '/flight'
  query: Record<string, string>
}

export function trainingStatusText(status: TrainingRunStatus): string {
  if (status === 'not_started') return '未开始'
  if (status === 'in_progress') return '诊断进行中'
  if (status === 'awaiting_prearm') return '等待 Pre-Arm'
  if (status === 'awaiting_flight') return '等待飞行验证'
  if (status === 'completed') return '已完成'
  return status || '未知'
}

export function buildStudentTrainingRoute(input: TrainingRouteInput): TrainingRouteTarget {
  const query: Record<string, string> = {
    run: String(input.runId),
    scenario: input.scenarioId,
  }
  if (input.assignmentId) query.assignment = String(input.assignmentId)
  return {
    path: input.status === 'awaiting_flight' ? '/flight' : '/debugging',
    query,
  }
}

export interface FlightValidationState {
  takeoffObserved: boolean
  hoverObserved: boolean
  landCommanded: boolean
  airborne: boolean
  landedState?: number | null
  armed?: boolean
}

export function flightValidationReady(state: FlightValidationState): boolean {
  if (!state.takeoffObserved || !state.hoverObserved || !state.landCommanded || state.airborne) return false
  // MAVLink EXTENDED_SYS_STATE: 1 = ON_GROUND. Some SIH builds may lag the
  // landed-state update, so a disarmed, non-airborne vehicle is also accepted.
  if (state.landedState === 1) return true
  return state.armed === false
}
