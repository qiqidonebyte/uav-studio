import type { ComponentType, ComponentVisual } from './aircraft'

export interface LibraryMetadata {
  notes: string
  tags: string[]
}

export interface CompatibilityGroup {
  label: string
  component_ids: number[]
  note: string
}

export interface LibraryComponent {
  id: number
  name: string
  type: ComponentType
  mass_kg: number
  parameters_json: Record<string, unknown>
  visual?: ComponentVisual | null
  library: LibraryMetadata
  compatibility: CompatibilityGroup[]
}

export interface LibraryComponentUpdate {
  name: string
  mass_kg: number
  parameters_json: Record<string, unknown>
  notes: string
  tags: string[]
}
