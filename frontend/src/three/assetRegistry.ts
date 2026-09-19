import type { Component, ComponentType, ComponentVisual } from '../types/aircraft'

export type RotorDirection = 'CW' | 'CCW'

export const UAV_ASSET_BASE = '/models/uav/v1_1/'

/**
 * Ghost models are only used when a slot is empty so the student can see the
 * installation location. Installed components MUST provide Component.visual.
 */
const GHOST_VISUALS: Record<ComponentType, ComponentVisual> = {
  frame: {
    asset_key: 'ghost:frame',
    file: 'frame_650.glb',
    thumbnail: 'thumbnails/frame_650.png',
    scale: 1,
  },
  motor: {
    asset_key: 'ghost:motor',
    file: 'motor_5010_360kv.glb',
    thumbnail: 'thumbnails/motor_5010.png',
    scale: 1,
  },
  esc: {
    asset_key: 'ghost:esc',
    file: 'esc_30a.glb',
    thumbnail: 'thumbnails/esc_30a.png',
    scale: 1,
  },
  propeller: {
    asset_key: 'ghost:propeller',
    cw_file: 'prop_15_cw.glb',
    ccw_file: 'prop_15_ccw.glb',
    thumbnail: 'thumbnails/prop_15.png',
    scale: 1,
  },
  battery: {
    asset_key: 'ghost:battery',
    file: 'battery_6s_10000.glb',
    thumbnail: 'thumbnails/battery_10000.png',
    scale: 1,
  },
  power_module: {
    asset_key: 'ghost:power_module',
    file: 'power_120a.glb',
    thumbnail: 'thumbnails/power_120.png',
    scale: 1,
  },
  flight_controller: {
    asset_key: 'ghost:flight_controller',
    file: 'fc_v1.glb',
    thumbnail: 'thumbnails/fc_v1.png',
    scale: 1,
  },
  gnss: {
    asset_key: 'ghost:gnss',
    file: 'gnss_m8n.glb',
    thumbnail: 'thumbnails/gnss_m8n.png',
    scale: 1,
  },
  payload: {
    asset_key: 'ghost:payload',
    file: 'payload_camera_300g.glb',
    thumbnail: 'thumbnails/payload_camera.png',
    scale: 1,
  },
}

export const MOTOR_DIRECTIONS = {
  M1: 'CCW',
  M2: 'CW',
  M3: 'CCW',
  M4: 'CW',
} as const satisfies Record<'M1' | 'M2' | 'M3' | 'M4', RotorDirection>

function assertVisualType(component: Component, expectedType: ComponentType): void {
  if (component.type !== expectedType) {
    throw new Error(
      `3D asset type mismatch: component ${component.id} is ${component.type}, expected ${expectedType}`,
    )
  }
}

export function assetForComponent(
  component: Component | null | undefined,
  fallbackType: ComponentType,
): ComponentVisual {
  if (!component) return GHOST_VISUALS[fallbackType]
  assertVisualType(component, fallbackType)
  if (!component.visual) {
    throw new Error(
      `Component ${component.id} (${component.name}) has no visual metadata. ` +
      'Add it to the 3D asset manifest / component data contract instead of silently reusing another model.',
    )
  }
  return component.visual
}

export function assetUrl(
  asset: ComponentVisual,
  direction?: RotorDirection,
): string {
  const file = direction === 'CW'
    ? asset.cw_file
    : direction === 'CCW'
      ? asset.ccw_file
      : asset.file

  if (!file) {
    throw new Error(
      `3D asset file missing for ${asset.asset_key}` +
      (direction ? ` (${direction})` : ''),
    )
  }
  return `${UAV_ASSET_BASE}${file}`
}

export function thumbnailForComponent(component: Component): string {
  if (!component.visual) {
    throw new Error(`Component ${component.id} (${component.name}) has no visual metadata`)
  }
  if (!component.visual.thumbnail) {
    throw new Error(`Component ${component.id} (${component.name}) has no thumbnail`)
  }
  return `${UAV_ASSET_BASE}${component.visual.thumbnail}`
}

export function propellerAssetUrl(
  component: Component | null | undefined,
  direction: RotorDirection,
): string {
  return assetUrl(assetForComponent(component, 'propeller'), direction)
}

/**
 * Current V1.1 motor models share a conservative propeller hub offset.
 * Mount offsets will move into the unified Frame Mount System in P0 Sprint 2.
 */
export function propellerOffsetY(_component: Component | null | undefined): number {
  return 0.064
}
