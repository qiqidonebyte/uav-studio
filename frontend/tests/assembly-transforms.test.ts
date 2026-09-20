import { describe, expect, it } from 'vitest'
import { composeAssemblyPosition } from '../src/three/assemblyTransforms'

describe('unified assembly transform', () => {
  it('keeps datum unchanged when assembled and not exploded', () => {
    expect(
      composeAssemblyPosition(
        { x: 1, y: 2, z: 3 },
        { x: 4, y: 0, z: 0 },
        0,
        { x: 0, y: 5, z: 0 },
        1,
      ),
    ).toEqual({ x: 1, y: 2, z: 3 })
  })

  it('starts installation from approach offset and eases to the datum', () => {
    expect(
      composeAssemblyPosition(
        { x: 1, y: 2, z: 3 },
        { x: 0, y: 0, z: 0 },
        0,
        { x: 0.2, y: 0.1, z: 0.3 },
        0,
      ),
    ).toEqual({ x: 1.2, y: 2.1, z: 3.3 })

    expect(
      composeAssemblyPosition(
        { x: 1, y: 2, z: 3 },
        { x: 0, y: 0, z: 0 },
        0,
        { x: 0.2, y: 0.1, z: 0.3 },
        1,
      ),
    ).toEqual({ x: 1, y: 2, z: 3 })
  })

  it('composes exploded and installation transforms from the same datum', () => {
    const value = composeAssemblyPosition(
      { x: 0, y: 0, z: 0 },
      { x: 1, y: 0, z: 0 },
      0.5,
      { x: 0, y: 2, z: 0 },
      0.25,
    )
    expect(value).toEqual({ x: 0.5, y: 1.5, z: 0 })
  })

  it('clamps progress inputs to 0..1', () => {
    expect(
      composeAssemblyPosition(
        { x: 0, y: 0, z: 0 },
        { x: 1, y: 0, z: 0 },
        9,
        { x: 0, y: 2, z: 0 },
        -4,
      ),
    ).toEqual({ x: 1, y: 2, z: 0 })
  })
})
