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
    const guide = pageLearningGuide(route('/debugging', { run: '9', scenario: 'F01_COMPASS' }), 'student')
    expect(guide.title).toContain('证据')
    expect(guide.steps).toContain('提出故障原因')
    expect(guide.completion).toContain('诊断工作单')
  })
})
