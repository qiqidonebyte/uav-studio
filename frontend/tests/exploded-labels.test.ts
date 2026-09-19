import { describe, expect, it } from 'vitest'
import type { Component } from '../src/types/aircraft'
import { buildExplodedLabelDescriptors } from '../src/three/explodedLabels'
import { layoutExplodedLabels, placementsOverlap } from '../src/three/explodedLabelLayout'

const components = [
  { id: 1, name: 'EduFrame-650', type: 'frame', mass_kg: 0.8, parameters_json: {} },
  { id: 10, name: 'EduMotor-5010-360KV', type: 'motor', mass_kg: 0.18, parameters_json: {} },
] as Component[]

describe('exploded labels', () => {
  it('groups repeated propulsion parts into one compact ×4 label', () => {
    const parts = [
      { slot: 'motor', componentId: 10, installed: true, currentPosition: { x: 1, y: 0, z: 1 } },
      { slot: 'motor', componentId: 10, installed: true, currentPosition: { x: 1, y: 0, z: -1 } },
      { slot: 'motor', componentId: 10, installed: true, currentPosition: { x: -1, y: 0, z: 1 } },
      { slot: 'motor', componentId: 10, installed: true, currentPosition: { x: -1, y: 0, z: -1 } },
    ] as const

    const labels = buildExplodedLabelDescriptors(components, [...parts])
    expect(labels).toHaveLength(1)
    expect(labels[0].title).toBe('EduMotor-5010-360KV')
    expect(labels[0].meta).toBe('电机 ×4')
    expect(labels[0].count).toBe(4)
  })

  it('does not create labels for uninstalled ghost parts', () => {
    const labels = buildExplodedLabelDescriptors(components, [
      { slot: 'frame', componentId: null, installed: false, currentPosition: { x: 0, y: 0, z: 0 } },
    ])
    expect(labels).toEqual([])
  })

  it('packs overlapping anchors into non-overlapping edge labels', () => {
    const placements = layoutExplodedLabels([
      { key: 'a', x: 700, y: 220, preferredSide: 'right' },
      { key: 'b', x: 710, y: 222, preferredSide: 'right' },
      { key: 'c', x: 705, y: 224, preferredSide: 'right' },
    ], 1200, 650)

    for (let i = 0; i < placements.length; i += 1) {
      const item = placements[i]
      expect(item.left).toBeGreaterThanOrEqual(0)
      expect(item.top).toBeGreaterThanOrEqual(0)
      expect(item.left + item.width).toBeLessThanOrEqual(1200)
      expect(item.top + item.height).toBeLessThanOrEqual(650)
      for (let j = i + 1; j < placements.length; j += 1) {
        expect(placementsOverlap(item, placements[j], 2)).toBe(false)
      }
    }
  })
})
