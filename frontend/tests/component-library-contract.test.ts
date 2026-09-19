import { describe, expect, it } from 'vitest'
import type { LibraryComponent } from '../src/types/componentLibrary'

function fixture(): LibraryComponent {
  return {
    id: 10,
    name: 'EduMotor-5010-360KV',
    type: 'motor',
    mass_kg: 0.18,
    parameters_json: { kv: 360 },
    visual: {
      asset_key: 'motor:10',
      file: 'motor_5010_360kv.glb',
      thumbnail: 'thumbnails/motor_5010.png',
      scale: 1,
    },
    library: { notes: '', tags: [] },
    compatibility: [{ label: '螺旋桨', component_ids: [30, 31], note: '来自性能曲线' }],
  }
}

describe('component library contract', () => {
  it('carries engineering, visual and compatibility data together', () => {
    const item = fixture()
    expect(item.parameters_json.kv).toBe(360)
    expect(item.visual?.file).toBe('motor_5010_360kv.glb')
    expect(item.compatibility[0].component_ids).toEqual([30, 31])
  })
})
