import { describe, expect, it } from 'vitest'
import {
  isInsideFlightBoundary,
  projectLocalPoint,
  unprojectMapPoint,
} from '../src/utils/flightMap'
import { replayFrameIndex } from '../src/utils/replay'

describe('local flight map', () => {
  it('projects the simulator X/Y origin to the map center', () => {
    const point = projectLocalPoint(0, 0, 800, 520, 25)

    expect(point.x).toBe(400)
    expect(point.y).toBe(260)
  })

  it('maps +X right and +Y up inside the flight boundary', () => {
    const point = projectLocalPoint(25, 25, 800, 520, 25)

    expect(point.x).toBeGreaterThan(400)
    expect(point.y).toBeLessThan(260)
    expect(point.x).toBeLessThan(800)
    expect(point.y).toBeGreaterThan(0)
  })

  it('detects points outside the square flight boundary', () => {
    expect(isInsideFlightBoundary(24.9, -24.9, 25)).toBe(true)
    expect(isInsideFlightBoundary(25.1, 0, 25)).toBe(false)
  })

  it('converts a clicked SVG point back into simulator X/Y coordinates', () => {
    const point = unprojectMapPoint(400, 260, 800, 520, 25)

    expect(point.x).toBeCloseTo(0)
    expect(point.y).toBeCloseTo(0)
  })
})

describe('replay timing', () => {
  it('finds the latest telemetry frame not after replay time', () => {
    const frames = [
      { t: 0.0 },
      { t: 0.5 },
      { t: 1.0 },
      { t: 1.5 },
    ]

    expect(replayFrameIndex(frames, 0.0)).toBe(0)
    expect(replayFrameIndex(frames, 0.8)).toBe(1)
    expect(replayFrameIndex(frames, 1.5)).toBe(3)
    expect(replayFrameIndex(frames, 9.0)).toBe(3)
  })
})
