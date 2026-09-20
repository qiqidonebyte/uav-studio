import { describe, expect, it } from 'vitest'
import {
  calculateSafetyScore,
  recommendedSafetyProfile,
  unsafeDemoSafetyProfile,
  validateSafetyDraft,
} from '../src/utils/safety'

describe('safety settings workbench', () => {
  it('accepts the teaching recommended profile', () => {
    expect(validateSafetyDraft({ ...recommendedSafetyProfile })).toEqual([])
    expect(calculateSafetyScore({ ...recommendedSafetyProfile })).toBe(100)
  })

  it('detects battery threshold ordering errors', () => {
    const profile = { ...recommendedSafetyProfile, BAT_LOW_THR: 0.08, BAT_CRIT_THR: 0.10 }
    const issues = validateSafetyDraft(profile)
    expect(issues.some(issue => issue.code === 'BATTERY_ORDER' && issue.level === 'error')).toBe(true)
  })

  it('detects RTL altitude and geofence conflicts', () => {
    const profile = { ...recommendedSafetyProfile, RTL_RETURN_ALT: 40, GF_MAX_VER_DIST: 30 }
    const issues = validateSafetyDraft(profile)
    expect(issues.some(issue => issue.code === 'RTL_GEOFENCE' && issue.level === 'error')).toBe(true)
  })

  it('marks the failsafe training profile as unsafe until repaired', () => {
    const issues = validateSafetyDraft({ ...unsafeDemoSafetyProfile })
    expect(issues.length).toBeGreaterThan(0)
    expect(calculateSafetyScore({ ...unsafeDemoSafetyProfile }, true)).toBeLessThan(90)
  })
})
