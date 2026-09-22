import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

function source(relative: string): string {
  return readFileSync(new URL(relative, import.meta.url), 'utf8')
}

describe('UI Bugfix V2 regression contracts', () => {
  it('never substitutes an unrelated local worksheet for a server run', () => {
    const review = source('../src/views/LearningReview.vue')
    expect(review).not.toContain('?? loadLocalWorksheet()')
    expect(review).toContain('watch(runId')
    expect(review).toContain('reviewLoadGeneration')
  })

  it('falls back to the sensor page when a debugging section is missing', () => {
    const debugging = source('../src/views/Debugging.vue')
    expect(debugging).toContain("    : 'sensors'")
    expect(debugging).toContain('watch(() => route.query.section')
  })

  it('allows only one assignment transition at a time', () => {
    const training = source('../src/views/MyTraining.vue')
    expect(training).toContain(':disabled="startingId !== null"')
    expect(training).toContain('if (startingId.value !== null) return')
  })

  it('keeps the latest teacher filter response and reports request errors', () => {
    const teacher = source('../src/views/TeacherWorkbench.vue')
    expect(teacher).toContain('assignmentRequestGeneration')
    expect(teacher).toContain('runRequestGeneration')
    expect(teacher).toContain('studentRequestGeneration')
    expect(teacher).toContain('detailRequestGeneration')
    expect(teacher).toContain('gradeRequestGeneration')
    expect(teacher).toContain('const classId = gradeClassId.value')
    expect(teacher.match(/catch \(caught\) \{ showNotice\(apiError\(caught\)\) \}/g)?.length ?? 0).toBeGreaterThanOrEqual(7)
  })

  it('discards parameter reads started for an obsolete PX4 bridge mode', () => {
    const debugging = source('../src/views/Debugging.vue')
    expect(debugging).toContain('rcLoadGeneration')
    expect(debugging).toContain('safetyLoadGeneration')
    expect(debugging).toContain('bridgeMode.value !== requestedMode')
  })

  it('keeps top navigation reachable on narrower classroom screens', () => {
    const app = source('../src/App.vue')
    expect(app).toContain('@media(max-width:1200px)')
    expect(app).toContain('overflow-x:auto')
    expect(app).toContain('scrollbar-width:none')
  })
})
