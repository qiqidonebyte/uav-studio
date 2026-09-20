import { describe, expect, it } from 'vitest'
import { scoreFaultTraining, type FaultTrainingCase } from '../src/utils/training'

const testCase: FaultTrainingCase = {
  id: 'F99_TEST',
  title: 'test',
  category: 'power',
  difficulty: 2,
  recommended_minutes: 10,
  icon: 'T',
  fault_source: 'test',
  legacy_scenario: 'mapping',
  initial_section: 'power',
  target_sections: ['power'],
  student_brief: { symptom: 'x', task: 'y' },
  injections: ['motor_mapping'],
  success_conditions: [
    { key: 'repair', group: 'repair' },
    { key: 'verify', group: 'validation' },
  ],
  hints: ['hint'],
}

describe('fault training score', () => {
  it('passes only when all success conditions are complete', () => {
    const result = scoreFaultTraining({
      trainingCase: testCase,
      conditionState: { repair: true, verify: true },
      visitedSections: ['power'],
      elapsedSeconds: 300,
      hintsUsed: 0,
      wrongOperations: 0,
    })
    expect(result.passed).toBe(true)
    expect(result.score).toBe(100)
  })

  it('penalizes hints and failed operations', () => {
    const result = scoreFaultTraining({
      trainingCase: testCase,
      conditionState: { repair: true, verify: true },
      visitedSections: ['power'],
      elapsedSeconds: 300,
      hintsUsed: 1,
      wrongOperations: 2,
    })
    expect(result.score).toBe(86)
  })

  it('keeps an incomplete repair from passing', () => {
    const result = scoreFaultTraining({
      trainingCase: testCase,
      conditionState: { repair: true, verify: false },
      visitedSections: ['power'],
      elapsedSeconds: 300,
      hintsUsed: 0,
      wrongOperations: 0,
    })
    expect(result.passed).toBe(false)
    expect(result.completedConditions).toBe(1)
  })
})
