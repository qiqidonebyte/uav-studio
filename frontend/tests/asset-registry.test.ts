import { describe, expect, it } from 'vitest'
import type { Component } from '../src/types/aircraft'
import {
  MOTOR_DIRECTIONS,
  assetForComponent,
  assetUrl,
  knownAssetIds,
  propellerAssetUrl,
  thumbnailForComponent,
} from '../src/three/assetRegistry'

const component = (id: number, type: Component['type']): Component => ({
  id,
  name: `C${id}`,
  type,
  mass_kg: 0.1,
  parameters_json: {},
})

describe('3D asset registry', () => {
  it('covers every current seed component id', () => {
    expect(knownAssetIds()).toEqual([1, 2, 10, 11, 20, 21, 30, 31, 40, 41, 50, 51, 60, 61, 70, 80])
  })

  it('keeps the frozen Quad-X rotor direction contract', () => {
    expect(MOTOR_DIRECTIONS).toEqual({ M1: 'CCW', M2: 'CW', M3: 'CCW', M4: 'CW' })
  })

  it('maps known components to GLB and thumbnail resources', () => {
    const motor = component(10, 'motor')
    expect(assetUrl(assetForComponent(motor, 'motor'))).toContain('motor_5010_360kv.glb')
    expect(thumbnailForComponent(motor)).toContain('motor_5010.png')
  })

  it('uses different CW and CCW propeller assets', () => {
    const prop = component(30, 'propeller')
    expect(propellerAssetUrl(prop, 'CW')).not.toBe(propellerAssetUrl(prop, 'CCW'))
  })
})
