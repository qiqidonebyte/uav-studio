import { createHash } from 'node:crypto'
import { existsSync, readFileSync, statSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import type { Component, ComponentType } from '../src/types/aircraft'
import {
  assetForComponent,
  assetUrl,
  propellerAssetUrl,
  thumbnailForComponent,
} from '../src/three/assetRegistry'

const modelDir = resolve(process.cwd(), 'public/models/uav/v1_1')
const manifestPath = resolve(modelDir, 'asset_manifest.json')
const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8')) as {
  assetVersion: string
  units: string
  axes: Record<string, string>
  componentMap: Record<string, {
    type: ComponentType
    file?: string
    cw?: string
    ccw?: string
    thumbnail?: string
  }>
}

function component(id: number, type: ComponentType): Component {
  return {
    id,
    name: `Component-${id}`,
    type,
    mass_kg: 0.1,
    parameters_json: {},
  }
}

function sha256(relativePath: string): string {
  return createHash('sha256')
    .update(readFileSync(resolve(modelDir, relativePath)))
    .digest('hex')
}

function referencedFiles(): string[] {
  const refs = new Set<string>()
  for (const item of Object.values(manifest.componentMap)) {
    for (const key of ['file', 'cw', 'ccw', 'thumbnail'] as const) {
      const value = item[key]
      if (value) refs.add(value)
    }
  }
  return [...refs]
}

describe('P0 Asset Contract', () => {
  it('P0-ASSET-001 manifest exists and declares meter units', () => {
    expect(existsSync(manifestPath)).toBe(true)
    expect(manifest.assetVersion).toBe('1.1.0')
    expect(manifest.units).toBe('meter')
  })

  it('P0-ASSET-002 current seed component ids all exist in manifest', () => {
    const ids = Object.keys(manifest.componentMap).map(Number).sort((a, b) => a - b)
    expect(ids).toEqual([1, 2, 10, 11, 20, 21, 30, 31, 40, 41, 50, 51, 60, 61, 70, 80])
  })

  it('P0-ASSET-003 every manifest resource exists on disk', () => {
    for (const relativePath of referencedFiles()) {
      expect(existsSync(resolve(modelDir, relativePath)), relativePath).toBe(true)
    }
  })

  it('P0-ASSET-004 every GLB is binary glTF v2 and non-trivial', () => {
    for (const relativePath of referencedFiles().filter(path => path.endsWith('.glb'))) {
      const fullPath = resolve(modelDir, relativePath)
      const bytes = readFileSync(fullPath)
      expect(bytes.subarray(0, 4).toString('ascii'), relativePath).toBe('glTF')
      expect(bytes.readUInt32LE(4), relativePath).toBe(2)
      expect(statSync(fullPath).size, relativePath).toBeGreaterThan(1024)
    }
  })

  it('P0-ASSET-005 every thumbnail is a real PNG and non-trivial', () => {
    const pngSignature = '89504e470d0a1a0a'
    for (const relativePath of referencedFiles().filter(path => path.endsWith('.png'))) {
      const fullPath = resolve(modelDir, relativePath)
      const bytes = readFileSync(fullPath)
      expect(bytes.subarray(0, 8).toString('hex'), relativePath).toBe(pngSignature)
      expect(statSync(fullPath).size, relativePath).toBeGreaterThan(1024)
    }
  })

  it('P0-ASSET-006 650 and 450 frames use different geometry assets', () => {
    const a = manifest.componentMap['1'].file!
    const b = manifest.componentMap['2'].file!
    expect(a).not.toBe(b)
    expect(sha256(a)).not.toBe(sha256(b))
  })

  it('P0-ASSET-007 5010 and 4008 motors use different geometry assets', () => {
    const a = manifest.componentMap['10'].file!
    const b = manifest.componentMap['11'].file!
    expect(a).not.toBe(b)
    expect(sha256(a)).not.toBe(sha256(b))
  })

  it('P0-ASSET-008 10000 and 16000 batteries use different geometry assets', () => {
    const a = manifest.componentMap['40'].file!
    const b = manifest.componentMap['41'].file!
    expect(a).not.toBe(b)
    expect(sha256(a)).not.toBe(sha256(b))
  })

  it('P0-ASSET-009 CW and CCW propellers are distinct assets', () => {
    for (const id of [30, 31]) {
      const item = manifest.componentMap[String(id)]
      expect(item.cw).toBeTruthy()
      expect(item.ccw).toBeTruthy()
      expect(item.cw).not.toBe(item.ccw)
      expect(sha256(item.cw!)).not.toBe(sha256(item.ccw!))
    }
  })

  it('P0-ASSET-010 runtime registry agrees with manifest for current components', () => {
    for (const [idText, item] of Object.entries(manifest.componentMap)) {
      const id = Number(idText)
      const c = component(id, item.type)
      if (item.type === 'propeller') {
        expect(propellerAssetUrl(c, 'CW')).toContain(item.cw!)
        expect(propellerAssetUrl(c, 'CCW')).toContain(item.ccw!)
      } else {
        expect(assetUrl(assetForComponent(c, item.type))).toContain(item.file!)
      }
      if (item.thumbnail) expect(thumbnailForComponent(c)).toContain(item.thumbnail)
    }
  })

  it('P0-ASSET-011 unknown component must fail loudly instead of silently showing a default model', () => {
    const unknown = component(9999, 'motor')
    expect(() => assetForComponent(unknown, 'motor')).toThrow()
  })

  it('P0-ASSET-012 Component data contract owns visual metadata instead of relying only on numeric frontend ids', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/types/aircraft.ts'), 'utf-8')
    expect(source).toMatch(/\bvisual\s*\??\s*:/)
  })
})
