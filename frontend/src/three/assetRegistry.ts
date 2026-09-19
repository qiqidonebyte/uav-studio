import type { Component, ComponentType } from '../types/aircraft'

export type RotorDirection = 'CW' | 'CCW'

export interface ComponentVisualAsset {
  type: ComponentType
  file?: string
  cwFile?: string
  ccwFile?: string
  thumbnail?: string
  label: string
  propOffsetY?: number
}

export const UAV_ASSET_BASE = '/models/uav/v1_1/'

const ASSETS: Record<number, ComponentVisualAsset> = {
  1: { type: 'frame', file: 'frame_650.glb', thumbnail: 'thumbnails/frame_650.png', label: '650 四旋翼机架' },
  2: { type: 'frame', file: 'frame_450.glb', thumbnail: 'thumbnails/frame_450.png', label: '450 四旋翼机架' },
  10: { type: 'motor', file: 'motor_5010_360kv.glb', thumbnail: 'thumbnails/motor_5010.png', label: '5010 360KV 电机', propOffsetY: 0.070 },
  11: { type: 'motor', file: 'motor_4008_500kv.glb', thumbnail: 'thumbnails/motor_4008.png', label: '4008 500KV 电机', propOffsetY: 0.058 },
  20: { type: 'esc', file: 'esc_30a.glb', thumbnail: 'thumbnails/esc_30a.png', label: '30A 电调' },
  21: { type: 'esc', file: 'esc_40a.glb', thumbnail: 'thumbnails/esc_40a.png', label: '40A 电调' },
  30: { type: 'propeller', cwFile: 'prop_15_cw.glb', ccwFile: 'prop_15_ccw.glb', thumbnail: 'thumbnails/prop_15.png', label: '15×5 桨' },
  31: { type: 'propeller', cwFile: 'prop_14_cw.glb', ccwFile: 'prop_14_ccw.glb', thumbnail: 'thumbnails/prop_14.png', label: '14×4.8 桨' },
  40: { type: 'battery', file: 'battery_6s_10000.glb', thumbnail: 'thumbnails/battery_10000.png', label: '6S 10000mAh 电池' },
  41: { type: 'battery', file: 'battery_6s_16000.glb', thumbnail: 'thumbnails/battery_16000.png', label: '6S 16000mAh 电池' },
  50: { type: 'power_module', file: 'power_120a.glb', thumbnail: 'thumbnails/power_120.png', label: '120A 电源模块' },
  51: { type: 'power_module', file: 'power_160a.glb', thumbnail: 'thumbnails/power_160.png', label: '160A 电源模块' },
  60: { type: 'flight_controller', file: 'fc_v1.glb', thumbnail: 'thumbnails/fc_v1.png', label: 'EduFC-V1' },
  61: { type: 'flight_controller', file: 'fc_v2.glb', thumbnail: 'thumbnails/fc_v2.png', label: 'EduFC-V2' },
  70: { type: 'gnss', file: 'gnss_m8n.glb', thumbnail: 'thumbnails/gnss_m8n.png', label: 'M8N GNSS' },
  80: { type: 'payload', file: 'payload_camera_300g.glb', thumbnail: 'thumbnails/payload_camera.png', label: '300g 云台相机' },
}

const DEFAULT_ID_BY_TYPE: Record<ComponentType, number> = {
  frame: 1,
  motor: 10,
  esc: 20,
  propeller: 30,
  battery: 40,
  power_module: 50,
  flight_controller: 60,
  gnss: 70,
  payload: 80,
}

export const MOTOR_DIRECTIONS = {
  M1: 'CCW',
  M2: 'CW',
  M3: 'CCW',
  M4: 'CW',
} as const satisfies Record<'M1' | 'M2' | 'M3' | 'M4', RotorDirection>

export function assetForComponent(component: Component | null | undefined, fallbackType: ComponentType): ComponentVisualAsset {
  if (component && ASSETS[component.id]) return ASSETS[component.id]
  return ASSETS[DEFAULT_ID_BY_TYPE[fallbackType]]
}

export function assetUrl(asset: ComponentVisualAsset, direction?: RotorDirection): string {
  const file = direction === 'CW' ? asset.cwFile : direction === 'CCW' ? asset.ccwFile : asset.file
  if (!file) throw new Error(`3D asset file missing for ${asset.label}`)
  return `${UAV_ASSET_BASE}${file}`
}

export function thumbnailForComponent(component: Component): string | null {
  const spec = ASSETS[component.id]
  return spec?.thumbnail ? `${UAV_ASSET_BASE}${spec.thumbnail}` : null
}

export function propellerAssetUrl(component: Component | null | undefined, direction: RotorDirection): string {
  return assetUrl(assetForComponent(component, 'propeller'), direction)
}

export function propellerOffsetY(component: Component | null | undefined): number {
  return assetForComponent(component, 'motor').propOffsetY ?? 0.064
}

export function knownAssetIds(): number[] {
  return Object.keys(ASSETS).map(Number).sort((a, b) => a - b)
}
