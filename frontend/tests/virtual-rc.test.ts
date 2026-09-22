import { describe, expect, it } from 'vitest'
import {
  centeredPwm,
  releasedStickValues,
  resolvedVirtualRcChannel,
  throttlePwm,
  virtualStickPoint,
} from '../src/utils/virtualRc'

describe('interactive virtual RC transmitter', () => {
  it('maps pointer position to clamped stick axes', () => {
    const bounds = { left: 100, top: 50, width: 200, height: 100 }
    expect(virtualStickPoint(200, 100, bounds)).toEqual({ x: 0, y: 0 })
    expect(virtualStickPoint(300, 50, bounds)).toEqual({ x: 1, y: 1 })
    expect(virtualStickPoint(0, 300, bounds)).toEqual({ x: -1, y: -1 })
  })

  it('maps centered axes and throttle to standard PWM values', () => {
    expect(centeredPwm(-1)).toBe(1000)
    expect(centeredPwm(0)).toBe(1500)
    expect(centeredPwm(1)).toBe(2000)
    expect(throttlePwm(-1)).toBe(1000)
    expect(throttlePwm(0)).toBe(1500)
    expect(throttlePwm(1)).toBe(2000)
  })

  it('centers spring axes while preserving Mode 2 throttle on release', () => {
    expect(releasedStickValues('right', 1730)).toEqual({ roll: 1500, pitch: 1500 })
    expect(releasedStickValues('left', 1730)).toEqual({ yaw: 1500, throttle: 1730 })
    expect(releasedStickValues('left', 2500).throttle).toBe(2000)
  })

  it('keeps virtual teaching sticks usable when PX4 has no RC mapping', () => {
    expect(resolvedVirtualRcChannel('roll', 0)).toBe(1)
    expect(resolvedVirtualRcChannel('pitch', 0)).toBe(2)
    expect(resolvedVirtualRcChannel('throttle', 0)).toBe(3)
    expect(resolvedVirtualRcChannel('yaw', 0)).toBe(4)
    expect(resolvedVirtualRcChannel('roll', 7)).toBe(7)
  })
})
