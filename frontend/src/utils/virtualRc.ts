export type VirtualStickSide = 'left' | 'right'
export type VirtualRcRole = 'roll' | 'pitch' | 'throttle' | 'yaw'

export interface VirtualStickPoint {
  x: number
  y: number
}

export interface StickBounds {
  left: number
  top: number
  width: number
  height: number
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

const virtualRcFallbackChannels: Record<VirtualRcRole, number> = {
  roll: 1,
  pitch: 2,
  throttle: 3,
  yaw: 4,
}

export function resolvedVirtualRcChannel(role: VirtualRcRole, configuredChannel: number): number {
  const channel = Number(configuredChannel)
  return Number.isInteger(channel) && channel >= 1 && channel <= 18
    ? channel
    : virtualRcFallbackChannels[role]
}

export function virtualStickPoint(clientX: number, clientY: number, bounds: StickBounds): VirtualStickPoint {
  if (bounds.width <= 0 || bounds.height <= 0) return { x: 0, y: 0 }
  return {
    x: clamp(((clientX - bounds.left) / bounds.width) * 2 - 1, -1, 1),
    y: clamp(1 - ((clientY - bounds.top) / bounds.height) * 2, -1, 1),
  }
}

export function centeredPwm(value: number): number {
  return Math.round(1500 + clamp(value, -1, 1) * 500)
}

export function throttlePwm(value: number): number {
  return Math.round(1000 + ((clamp(value, -1, 1) + 1) / 2) * 1000)
}

export function releasedStickValues(side: VirtualStickSide, throttle: number): Record<string, number> {
  return side === 'left'
    ? { yaw: 1500, throttle: clamp(Math.round(throttle), 1000, 2000) }
    : { roll: 1500, pitch: 1500 }
}
