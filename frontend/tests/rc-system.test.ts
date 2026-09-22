import { describe, expect, it } from 'vitest'
import {
  defaultRcDraft,
  flattenRcDraft,
  normalizeRcInput,
  validateRcDraft,
} from '../src/utils/rc'
import { readFileSync } from 'node:fs'

describe('RC system workbench', () => {
  it('accepts the recommended four-channel mapping', () => {
    const draft = defaultRcDraft(18)
    expect(validateRcDraft(draft).filter(item => item.level === 'error')).toHaveLength(0)
  })

  it('detects duplicate and unassigned mappings', () => {
    const duplicate = defaultRcDraft(18)
    duplicate.mapping.pitch = 1
    expect(validateRcDraft(duplicate).some(item => item.code === 'MAP_DUPLICATE')).toBe(true)

    const unassigned = defaultRcDraft(18)
    unassigned.mapping.roll = 0
    expect(validateRcDraft(unassigned).some(item => item.code === 'MAP_RANGE')).toBe(true)
  })

  it('normalizes centered and throttle values', () => {
    const draft = defaultRcDraft(18)
    expect(normalizeRcInput(1500, draft.channels[1], false)).toBe(0)
    expect(normalizeRcInput(2000, draft.channels[1], false)).toBeCloseTo(1)
    expect(normalizeRcInput(1500, draft.channels[3], true)).toBeCloseTo(.5)
  })

  it('does not emit removed RCx_DZ parameters to PX4', () => {
    const flat = flattenRcDraft(defaultRcDraft(18))
    expect(flat.RC1_DZ).toBeUndefined()
    expect(flat.RC1_MIN).toBe(1000)
    expect(flat.RC1_REV).toBe(1)
  })

  it('renders a pointer-driven Mode 2 transmitter while keeping precise input optional', () => {
    const source = readFileSync(new URL('../src/views/Debugging.vue', import.meta.url), 'utf8')
    expect(source).toContain("startVirtualStick('left', $event)")
    expect(source).toContain("startVirtualStick('right', $event)")
    expect(source).toContain('左摇杆油门松手保持')
    expect(source).toContain('<details>')
    expect(source).toContain("setVirtualRolePwm('throttle', 1000)")
    expect(source).toContain('rc-transmitter-frsky-x9d.jpg')
    expect(source).toContain('@lostpointercapture="releaseVirtualStick')
    expect(source).toContain("window.addEventListener('blur', releaseActiveVirtualStick)")
  })
})
