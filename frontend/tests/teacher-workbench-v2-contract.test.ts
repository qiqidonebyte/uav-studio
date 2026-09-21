import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

function source(relative: string): string {
  return readFileSync(new URL(relative, import.meta.url), 'utf8')
}

describe('Teacher Workbench V2 view integration contracts', () => {
  it('persists Debugging progress and diagnosis submission into TrainingRun', () => {
    const text = source('../src/views/Debugging.vue')
    expect(text).toContain('studentTrainingApi.progressRun')
    expect(text).toContain('studentTrainingApi.submitRun')
    expect(text).toContain('assignedScenarioId')
    expect(text).toContain(':to="flightRoute"')
  })

  it('writes the completed takeoff-hover-land cycle back from FlightLab', () => {
    const text = source('../src/views/FlightLab.vue')
    expect(text).toContain('flightTakeoffObserved')
    expect(text).toContain('flightHoverObserved')
    expect(text).toContain('flightLandCommanded')
    expect(text).toContain('studentTrainingApi.flightValidation')
  })

  it('exposes gradebook, class analytics and CSV export in the teacher UI', () => {
    const text = source('../src/views/TeacherWorkbench.vue')
    expect(text).toContain("activeTab === 'grades'")
    expect(text).toContain('teacherApi.gradebook')
    expect(text).toContain('teacherApi.analytics')
    expect(text).toContain('teacherApi.exportGradebook')
  })
})
