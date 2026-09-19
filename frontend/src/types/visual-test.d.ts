import type { AssemblySlot } from '../utils/assembly'

export {}

declare global {
  interface Window {
    __UAV_VISUAL_TEST__?: UavVisualTestProbe
  }
}

export interface VisualBounds {
  width: number
  height: number
  depth: number
}

export interface VisualVector3 {
  x: number
  y: number
  z: number
}

export interface LoadedVisualAsset {
  slot: AssemblySlot
  componentId: number | null
  url: string
  direction?: 'CW' | 'CCW'
}

export interface UavVisualTestProbe {
  version: '1.0'
  sceneReady: boolean
  pixelRatio: number
  cameraMode: 'follow' | 'top' | 'side' | 'free'
  selectedSlot: AssemblySlot | null
  loadedAssets: LoadedVisualAsset[]
  aircraftBounds: VisualBounds
  partBounds: Partial<Record<AssemblySlot, VisualBounds>>
  mounts: {
    M1: VisualVector3
    M2: VisualVector3
    M3: VisualVector3
    M4: VisualVector3
  }
}
