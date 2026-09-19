import { describe, expect, it } from 'vitest'
import {
  displacementMagnitude,
  explodedPosition,
  explosionOffsetForPart,
} from '../src/three/explodedView'

describe('exploded view geometry', () => {
  it('keeps the frame fixed as the assembly datum', () => {
    expect(
      explosionOffsetForPart({
        slot: 'frame',
        basePosition: { x: 0, y: 0, z: 0 },
      }),
    ).toEqual({ x: 0, y: 0, z: 0 })
  })

  it('moves propulsion groups outward and separates propeller above motor above ESC', () => {
    const base = { x: 0.25, y: 0.06, z: -0.25 }
    const motor = explosionOffsetForPart({ slot: 'motor', basePosition: base, motorName: 'M1' })
    const esc = explosionOffsetForPart({ slot: 'esc', basePosition: base, motorName: 'M1' })
    const prop = explosionOffsetForPart({ slot: 'propeller', basePosition: base, motorName: 'M1' })

    expect(motor.x).toBeGreaterThan(0)
    expect(motor.z).toBeLessThan(0)
    expect(esc.y).toBeLessThan(motor.y)
    expect(prop.y).toBeGreaterThan(motor.y)
    expect(displacementMagnitude(prop)).toBeGreaterThan(displacementMagnitude(motor))
  })

  it('separates avionics upward and power / payload downward', () => {
    const origin = { x: 0, y: 0, z: 0 }
    const gnss = explosionOffsetForPart({ slot: 'gnss', basePosition: origin })
    const fc = explosionOffsetForPart({ slot: 'flight_controller', basePosition: origin })
    const battery = explosionOffsetForPart({ slot: 'battery', basePosition: origin })
    const payload = explosionOffsetForPart({ slot: 'payload', basePosition: origin })

    expect(gnss.y).toBeGreaterThan(fc.y)
    expect(fc.y).toBeGreaterThan(0)
    expect(battery.y).toBeLessThan(0)
    expect(payload.y).toBeLessThan(battery.y)
  })

  it('interpolates and clamps explosion progress', () => {
    const base = { x: 1, y: 2, z: 3 }
    const offset = { x: 2, y: -4, z: 6 }

    expect(explodedPosition(base, offset, 0)).toEqual(base)
    expect(explodedPosition(base, offset, 0.5)).toEqual({ x: 2, y: 0, z: 6 })
    expect(explodedPosition(base, offset, 1)).toEqual({ x: 3, y: -2, z: 9 })
    expect(explodedPosition(base, offset, 9)).toEqual({ x: 3, y: -2, z: 9 })
    expect(explodedPosition(base, offset, -9)).toEqual(base)
  })
})
