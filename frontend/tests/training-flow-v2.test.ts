import { describe, expect, it } from 'vitest'
import { buildStudentTrainingRoute, flightValidationReady, trainingStatusText } from '../src/utils/trainingFlow'

describe('Teacher Workbench V2 training flow', () => {
  it('routes diagnosis-stage tasks back to Debugging with run context', () => {
    expect(buildStudentTrainingRoute({ runId: 12, assignmentId: 5, scenarioId: 'F06_INTEGRATED', status: 'in_progress' })).toEqual({
      path: '/debugging',
      query: { run: '12', scenario: 'F06_INTEGRATED', assignment: '5' },
    })
  })

  it('routes awaiting-flight tasks directly to FlightLab', () => {
    expect(buildStudentTrainingRoute({ runId: 12, assignmentId: 5, scenarioId: 'F06_INTEGRATED', status: 'awaiting_flight' }).path).toBe('/flight')
    expect(trainingStatusText('awaiting_flight')).toBe('等待飞行验证')
  })

  it('requires takeoff, hover and commanded landing before flight validation passes', () => {
    expect(flightValidationReady({ takeoffObserved: true, hoverObserved: false, landCommanded: true, airborne: false, landedState: 1, armed: false })).toBe(false)
    expect(flightValidationReady({ takeoffObserved: true, hoverObserved: true, landCommanded: false, airborne: false, landedState: 1, armed: false })).toBe(false)
    expect(flightValidationReady({ takeoffObserved: true, hoverObserved: true, landCommanded: true, airborne: true, landedState: 2, armed: true })).toBe(false)
    expect(flightValidationReady({ takeoffObserved: true, hoverObserved: true, landCommanded: true, airborne: false, landedState: 1, armed: false })).toBe(true)
  })
})
