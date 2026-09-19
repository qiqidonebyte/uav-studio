import * as THREE from 'three'
import type { Vector3Value } from '../types/aircraft'

// Simulator: X forward, Y left, Z up. Three.js: X right, Y up, Z toward viewer.
export function simulationVectorToThree(v: Vector3Value): THREE.Vector3 {
  return new THREE.Vector3(v.x, v.z, -v.y)
}

export function simulationPoseToThree(position: Vector3Value, attitude: { roll: number; pitch: number; yaw: number }) {
  const p = simulationVectorToThree(position)
  // This mapping is centralized by contract. Refine only with tests/visual verification; do not duplicate elsewhere.
  const euler = new THREE.Euler(attitude.roll, attitude.yaw, -attitude.pitch, 'XYZ')
  return { position: p, rotation: euler }
}

export function motorPositionsToThree(motorDiagonalM: number): Record<'M1' | 'M2' | 'M3' | 'M4', THREE.Vector3> {
  const offset = motorDiagonalM / 2 / Math.sqrt(2)
  return {
    M1: new THREE.Vector3(offset, 0, -offset),
    M2: new THREE.Vector3(offset, 0, offset),
    M3: new THREE.Vector3(-offset, 0, offset),
    M4: new THREE.Vector3(-offset, 0, -offset),
  }
}
