import { describe, expect, it } from 'vitest'
import { calculateDebugScore, resolveMotorResponse } from '../src/utils/debugging'

describe('debugging workbench teaching scenarios', () => {
  it('injects the M1 -> M3 mapping fault before repair', () => {
    expect(resolveMotorResponse('mapping', false, 'M1')).toBe('M3')
    expect(resolveMotorResponse('mapping', false, 'M2')).toBe('M2')
  })

  it('restores the correct motor response after repair', () => {
    expect(resolveMotorResponse('mapping', true, 'M1')).toBe('M1')
  })

  it('scores unresolved faults and assembly blockers', () => {
    expect(calculateDebugScore('standard', false, true)).toBe(100)
    expect(calculateDebugScore('mapping', false, true)).toBe(78)
    expect(calculateDebugScore('mapping', true, true)).toBe(100)
    expect(calculateDebugScore('failsafe', false, false)).toBe(64)
  })
})
