import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import type { RouteLocationNormalizedLoaded } from 'vue-router'
import {
  learningStageForRoute,
  learningStageTarget,
  pageLearningGuide,
} from '../src/utils/learningGuide'

function route(path: string, query: Record<string, string> = {}): RouteLocationNormalizedLoaded {
  return { path, query, fullPath: path, hash: '', name: undefined, params: {}, matched: [], meta: {}, redirectedFrom: undefined } as unknown as RouteLocationNormalizedLoaded
}

function source(relative: string): string {
  return readFileSync(new URL(relative, import.meta.url), 'utf8')
}

describe('Learning Guide V1', () => {
  it('maps the full teaching path to the right stages', () => {
    expect(learningStageForRoute(route('/training'))).toBe('prepare')
    expect(learningStageForRoute(route('/assembly'))).toBe('assembly')
    expect(learningStageForRoute(route('/debugging'))).toBe('debug')
    expect(learningStageForRoute(route('/debugging', { guide: 'diagnosis' }))).toBe('diagnosis')
    expect(learningStageForRoute(route('/debugging', { run: '12', scenario: 'F06_INTEGRATED' }))).toBe('diagnosis')
    expect(learningStageForRoute(route('/debugging', { section: 'preflight' }))).toBe('preflight')
    expect(learningStageForRoute(route('/flight'))).toBe('flight')
    expect(learningStageForRoute(route('/review'))).toBe('review')
  })

  it('gives student, teacher and admin a role-aware entry point', () => {
    const current = route('/aircraft')
    expect(learningStageTarget('prepare', 'student', current)).toBe('/training')
    expect(learningStageTarget('prepare', 'teacher', current)).toBe('/teacher')
    expect(learningStageTarget('prepare', 'admin', current)).toBe('/teacher')
  })

  it('preserves a course run while moving through diagnosis, preflight and review', () => {
    const current = route('/debugging', { run: '33', scenario: 'F05_FAILSAFE', assignment: '8' })
    expect(learningStageTarget('preflight', 'student', current)).toEqual({
      path: '/debugging',
      query: { run: '33', scenario: 'F05_FAILSAFE', assignment: '8', section: 'preflight' },
    })
    expect(learningStageTarget('review', 'student', current)).toEqual({ path: '/review', query: { run: '33' } })
  })

  it('uses evidence-chain language for assigned diagnosis guidance', () => {
    const guide = pageLearningGuide(route('/debugging', { run: '9', scenario: 'F01_COMPASS', section: 'sensors' }), 'student')
    expect(guide.title).toContain('飞控与传感器')
    expect(guide.objective).toContain('证据链')
    expect(guide.steps.some(item => item.includes('GNSS Fix'))).toBe(true)
    expect(guide.observe?.some(item => item.includes('数据是否持续刷新'))).toBe(true)
    expect(guide.mistakes?.some(item => item.includes('校准命令已受理'))).toBe(true)
  })

  it('changes detailed guidance with every debugging subsection', () => {
    const sensors = pageLearningGuide(route('/debugging', { section: 'sensors' }), 'student')
    const rc = pageLearningGuide(route('/debugging', { section: 'rc' }), 'student')
    const power = pageLearningGuide(route('/debugging', { section: 'power' }), 'student')
    const safety = pageLearningGuide(route('/debugging', { section: 'safety' }), 'student')
    const preflight = pageLearningGuide(route('/debugging', { section: 'preflight' }), 'student')

    expect(sensors.currentTask).toContain('IMU')
    expect(rc.currentTask).toContain('Roll')
    expect(power.currentTask).toContain('M1–M4')
    expect(safety.currentTask).toContain('低电量')
    expect(preflight.title).toContain('六项门禁')
    expect(power.nextTo).toEqual({ path: '/debugging', query: { section: 'safety' } })
  })

  it('keeps the diagnosis worksheet task-based, collapsed and required on course submission', () => {
    const debugging = source('../src/views/Debugging.vue')
    const worksheet = source('../src/components/DiagnosisWorksheet.vue')

    expect(debugging).toContain('v-if="activeTrainingCase"')
    expect(debugging).toContain('v-show="diagnosisWorksheetExpanded"')
    expect(debugging).toContain("auth.user?.role === 'student' && assignedRunId.value && !worksheet?.isComplete()")
    expect(debugging).toContain('diagnosisWorksheetExpanded.value = true')
    expect(worksheet).toContain("(event: 'progress-change', completed: number)")
  })
})
