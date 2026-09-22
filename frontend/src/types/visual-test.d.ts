import type { AssemblySlot } from '../utils/assembly'
import type { MotorName, PropellerDirection } from './aircraft'

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

export interface ExplodedVisualPart {
  mountId: string
  slot: AssemblySlot
  componentId: number | null
  motorName?: MotorName
  installed: boolean
  basePosition: VisualVector3
  currentPosition: VisualVector3
  offset: VisualVector3
}

export interface ExplodedVisualLabel {
  key: string
  slot: AssemblySlot
  title: string
  meta: string
  left: number
  top: number
  selected: boolean
  issue: boolean
}

export interface AssemblyMountVisual {
  id: string
  slot: AssemblySlot
  label: string
  position: VisualVector3
  required: boolean
  motorName?: MotorName
}

export interface PartInstanceVisual extends ExplodedVisualPart {
  installProgress: number
}

export interface SpatialDiagnosticVisual {
  code: string
  severity: 'error' | 'warning'
  message: string
  slots: AssemblySlot[]
  mountIds: string[]
}

export interface UavVisualTestProbe {
  version: '1.0' | '1.1' | '1.2'
  sceneReady: boolean
  pixelRatio: number
  cameraMode: 'follow' | 'top' | 'side' | 'free'
  selectedSlot: AssemblySlot | null
  issueSlots: AssemblySlot[]
  issueMounts: MotorName[]
  propellerDirections: Record<MotorName, PropellerDirection> | null
  loadedAssets: LoadedVisualAsset[]
  aircraftBounds: VisualBounds
  partBounds: Partial<Record<AssemblySlot, VisualBounds>>
  mounts: {
    M1: VisualVector3
    M2: VisualVector3
    M3: VisualVector3
    M4: VisualVector3
  }
  assemblyViewMode: 'assembled' | 'exploded'
  explosionProgress: number
  grounded: boolean
  groundedRestOffset: [number, number, number]
  directionLabelsVisible: boolean
  explodedParts: ExplodedVisualPart[]
  explodedLabels: ExplodedVisualLabel[]
  mountPoints: AssemblyMountVisual[]
  partInstances: PartInstanceVisual[]
  pendingInstall: { slot: AssemblySlot; componentId: number } | null
  hoveredMountId: string | null
  selectedMountId: string | null
  spatialDiagnostics: SpatialDiagnosticVisual[]
  activeInstallation: { mountId: string; progress: number; serial: number; mode: 'install' | 'remove' } | null
}
