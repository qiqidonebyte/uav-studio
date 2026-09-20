export interface PlainVector3 {
  x: number
  y: number
  z: number
}

function clamp01(value: number): number {
  return Math.max(0, Math.min(1, value))
}

/**
 * Compose all visual transforms from one immutable datum.
 *
 * final = base
 *       + explosionOffset * explosionProgress
 *       + installOffset * (1 - installProgress)
 *
 * This prevents assembly animation, exploded view and the engineering datum
 * from drifting into separate coordinate systems.
 */
export function composeAssemblyPosition(
  base: PlainVector3,
  explosionOffset: PlainVector3,
  explosionProgress: number,
  installOffset: PlainVector3,
  installProgress: number,
): PlainVector3 {
  const exploded = clamp01(explosionProgress)
  const installed = clamp01(installProgress)
  const approach = 1 - installed
  return {
    x: base.x + explosionOffset.x * exploded + installOffset.x * approach,
    y: base.y + explosionOffset.y * exploded + installOffset.y * approach,
    z: base.z + explosionOffset.z * exploded + installOffset.z * approach,
  }
}
