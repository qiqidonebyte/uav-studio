import { describe, expect, it } from 'vitest'
import { aircraftFingerprint, loadPreflightSnapshot, preflightScore, savePreflightSnapshot, type PreflightCheckRecord } from '../src/utils/preflight'

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
})
