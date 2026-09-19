import type { MotorName } from '../types/aircraft'
import type { AssemblySlot } from '../utils/assembly'

export type AssemblyViewMode = 'assembled' | 'exploded'

export interface PlainVector3 {
  x: number
  y: number
  z: number
}

export interface ExplodedPartDescriptor {
  slot: AssemblySlot
  basePosition: PlainVector3
  motorName?: MotorName
}

export interface ExplodedPartPosition extends ExplodedPartDescriptor {
  offset: PlainVector3
  currentPosition: PlainVector3
}

const ZERO: PlainVector3 = { x: 0, y: 0, z: 0 }

function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value))
}

function radialDirection(
  basePosition: PlainVector3,
  motorName?: MotorName,
): PlainVector3 {
  const length = Math.hypot(basePosition.x, basePosition.z)
  if (length > 1e-6) {
    return {
      x: basePosition.x / length,
      y: 0,
      z: basePosition.z / length,
    }
  }

  const fallback: Record<MotorName, PlainVector3> = {
    M1: { x: 0.7071, y: 0, z: -0.7071 },
    M2: { x: 0.7071, y: 0, z: 0.7071 },
    M3: { x: -0.7071, y: 0, z: 0.7071 },
    M4: { x: -0.7071, y: 0, z: -0.7071 },
  }
  return motorName ? fallback[motorName] : { x: 1, y: 0, z: 0 }
}

function radialOffset(
  basePosition: PlainVector3,
  distance: number,
  vertical: number,
  motorName?: MotorName,
): PlainVector3 {
  const radial = radialDirection(basePosition, motorName)
  return {
    x: radial.x * distance,
    y: vertical,
    z: radial.z * distance,
  }
}

/**
 * Defines the teaching exploded-view hierarchy.
 *
 * Three.js Y is vertical in UAV Studio:
 * - navigation / flight controller move upward,
 * - propulsion groups move outward by arm,
 * - battery / payload move downward,
 * - frame stays fixed as the assembly datum.
 */
export function explosionOffsetForPart(
  descriptor: ExplodedPartDescriptor,
): PlainVector3 {
  switch (descriptor.slot) {
    case 'frame':
      return { ...ZERO }
    case 'propeller':
      return radialOffset(descriptor.basePosition, 0.24, 0.30, descriptor.motorName)
    case 'motor':
      return radialOffset(descriptor.basePosition, 0.17, 0.11, descriptor.motorName)
    case 'esc':
      return radialOffset(descriptor.basePosition, 0.11, -0.055, descriptor.motorName)
    case 'gnss':
      return { x: 0, y: 0.36, z: 0 }
    case 'flight_controller':
      return { x: 0, y: 0.22, z: 0 }
    case 'power_module':
      return { x: -0.20, y: -0.14, z: 0.04 }
    case 'battery':
      return { x: 0, y: -0.31, z: 0 }
    case 'payload':
      return { x: 0.10, y: -0.38, z: 0.12 }
  }
}

export function explodedPosition(
  basePosition: PlainVector3,
  offset: PlainVector3,
  progress: number,
): PlainVector3 {
  const t = clamp01(progress)
  return {
    x: basePosition.x + offset.x * t,
    y: basePosition.y + offset.y * t,
    z: basePosition.z + offset.z * t,
  }
}

export function displacementMagnitude(offset: PlainVector3): number {
  return Math.hypot(offset.x, offset.y, offset.z)
}
