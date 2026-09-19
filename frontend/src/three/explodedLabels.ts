import type { Component } from '../types/aircraft'
import type { AssemblySlot } from '../utils/assembly'
import { SLOT_LABELS } from '../utils/assembly'

export interface ExplodedPartLike {
  slot: AssemblySlot
  componentId: number | null
  installed: boolean
  currentPosition: { x: number; y: number; z: number }
}

export interface ExplodedLabelDescriptor {
  key: AssemblySlot
  slot: AssemblySlot
  componentId: number
  title: string
  meta: string
  count: number
}

function compactName(value: string, maxLength = 28): string {
  const text = value.trim()
  if (text.length <= maxLength) return text
  return `${text.slice(0, maxLength - 1)}…`
}

/**
 * One compact label per component category, not one label per repeated part.
 * This keeps the exploded view readable: motor/ESC/propeller become ×4 labels.
 */
export function buildExplodedLabelDescriptors(
  components: Component[],
  parts: ExplodedPartLike[],
): ExplodedLabelDescriptor[] {
  const byId = new Map(components.map(component => [component.id, component]))
  const grouped = new Map<AssemblySlot, ExplodedPartLike[]>()

  for (const part of parts) {
    if (!part.installed || part.componentId === null) continue
    const component = byId.get(part.componentId)
    if (!component) continue
    const group = grouped.get(part.slot) ?? []
    group.push(part)
    grouped.set(part.slot, group)
  }

  return [...grouped.entries()].map(([slot, group]) => {
    const componentId = group[0].componentId
    const component = componentId === null ? undefined : byId.get(componentId)
    if (!component || componentId === null) {
      throw new Error(`Exploded label component missing for slot ${slot}`)
    }
    const count = group.length
    return {
      key: slot,
      slot,
      componentId,
      title: compactName(component.name),
      meta: `${SLOT_LABELS[slot]}${count > 1 ? ` ×${count}` : ''}`,
      count,
    }
  })
}
