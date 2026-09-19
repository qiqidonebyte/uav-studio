import { describe, expect, it } from 'vitest'
import type { Component, ComponentType, ComponentVisual } from '../src/types/aircraft'
import {
  MOTOR_DIRECTIONS,
  assetForComponent,
  assetUrl,
  propellerAssetUrl,
  thumbnailForComponent,
} from '../src/three/assetRegistry'

function visualFor(type: ComponentType): ComponentVisual {
  if (type === 'propeller') {
    return {
      asset_key: 'propeller:test',
      cw_file: 'prop_cw.glb',
      ccw_file: 'prop_ccw.glb',
      thumbnail: 'thumbnails/prop.png',
      scale: 1,
    }
  }
  return {
    asset_key: `${type}:test`,
    file: `${type}.glb`,
    thumbnail: `thumbnails/${type}.png`,
    scale: 1,
  }
}

const component = (id: number, type: ComponentType): Component => ({
  id,
  name: `C${id}`,
  type,
  mass_kg: 0.1,
  parameters_json: {},
  visual: visualFor(type),
})

describe('3D asset registry', () => {
  it('keeps the frozen Quad-X rotor direction contract', () => {
    expect(MOTOR_DIRECTIONS).toEqual({ M1: 'CCW', M2: 'CW', M3: 'CCW', M4: 'CW' })
  })

  it('uses Component.visual instead of numeric component-id mapping', () => {
    const motor = component(999, 'motor')
    expect(assetUrl(assetForComponent(motor, 'motor'))).toContain('motor.glb')
    expect(thumbnailForComponent(motor)).toContain('thumbnails/motor.png')
  })

  it('uses different CW and CCW propeller assets', () => {
    const prop = component(30, 'propeller')
    expect(propellerAssetUrl(prop, 'CW')).not.toBe(propellerAssetUrl(prop, 'CCW'))
  })

  it('fails loudly for an installed component without visual metadata', () => {
    const broken: Component = {
      id: 1234,
      name: 'Broken Motor',
      type: 'motor',
      mass_kg: 0.1,
      parameters_json: {},
    }
    expect(() => assetForComponent(broken, 'motor')).toThrow(/no visual metadata/i)
  })
})
