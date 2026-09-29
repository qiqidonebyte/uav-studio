import { describe, expect, it } from 'vitest'
import { aircraftFingerprint, isTeacherDemoSnapshot, loadPreflightSnapshot, preflightScore, savePreflightSnapshot, type PreflightCheckRecord, type PreflightSnapshot } from '../src/utils/preflight'

describe('preflight gate', () => {
  it('scores six passing gates at 100', () => {
    const checks: PreflightCheckRecord[] = Array.from({ length: 6 }, (_, i) => ({ key: String(i), title: String(i), state: 'pass', summary: 'ok' }))
    expect(preflightScore(checks)).toBe(100)
  })

  it('penalizes blockers', () => {
    const checks: PreflightCheckRecord[] = [
      { key: 'assembly', title: 'assembly', state: 'pass', summary: 'ok' },
      { key: 'power', title: 'power', state: 'block', summary: 'not tested' },
    ]
    expect(preflightScore(checks)).toBe(80)
  })

  it('fingerprint changes when aircraft configuration changes', () => {
    expect(aircraftFingerprint({ id: 1, motor_id: 2 })).not.toBe(aircraftFingerprint({ id: 1, motor_id: 3 }))
  })

  it('only enables the local demo permit for a passed teacher demo snapshot', () => {
    const snapshot: PreflightSnapshot = {
      version: 1,
      aircraft_id: 1,
      aircraft_fingerprint: '{}',
      passed: true,
      score: 100,
      checked_at: new Date().toISOString(),
      bridge_mode: 'demo',
      scenario: 'teacher_demo',
      checks: [],
    }

    expect(isTeacherDemoSnapshot(snapshot, 'teacher')).toBe(true)
    expect(isTeacherDemoSnapshot(snapshot, 'student')).toBe(false)
    expect(isTeacherDemoSnapshot({ ...snapshot, bridge_mode: 'live' }, 'teacher')).toBe(false)
    expect(isTeacherDemoSnapshot({ ...snapshot, passed: false }, 'teacher')).toBe(false)
    expect(isTeacherDemoSnapshot({ ...snapshot, scenario: 'standard' }, 'teacher')).toBe(false)
  })
})
