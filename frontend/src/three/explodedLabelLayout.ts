export type LabelSide = 'left' | 'right'

export interface LabelAnchor {
  key: string
  x: number
  y: number
  preferredSide?: LabelSide
}

export interface LabelPlacement extends LabelAnchor {
  side: LabelSide
  left: number
  top: number
  width: number
  height: number
}

export interface LabelLayoutOptions {
  labelWidth?: number
  labelHeight?: number
  gap?: number
  margin?: number
  topInsetLeft?: number
  topInsetRight?: number
  bottomInset?: number
}

const DEFAULTS = {
  labelWidth: 164,
  labelHeight: 26,
  gap: 5,
  margin: 12,
  topInsetLeft: 64,
  topInsetRight: 126,
  bottomInset: 74,
} as const

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

function resolveColumn(
  items: LabelPlacement[],
  viewportHeight: number,
  topInset: number,
  bottomInset: number,
  gap: number,
): void {
  if (items.length === 0) return
  const lowerBoundary = viewportHeight - bottomInset
  items.sort((a, b) => a.top - b.top)

  // Pack forward without clamping to the lower boundary first. Clamping each
  // item independently would collapse several labels onto the same bottom Y.
  let cursor = topInset
  for (const item of items) {
    item.top = Math.max(item.top, cursor)
    cursor = item.top + item.height + gap
  }

  // If the forward pack crosses the reserved bottom area, pack backward from
  // the lower boundary. This preserves spacing without collapsing labels onto
  // one Y coordinate or dragging an early top label out of the viewport.
  if (items[items.length - 1].top + items[items.length - 1].height > lowerBoundary) {
    let bottomCursor = lowerBoundary
    for (let index = items.length - 1; index >= 0; index -= 1) {
      const item = items[index]
      item.top = Math.min(item.top, bottomCursor - item.height)
      bottomCursor = item.top - gap
    }
  }

  // Real UAV Studio has at most five labels per side. If a future model exceeds
  // the available height, clamp as a defensive fallback rather than escaping
  // the scene bounds.
  if (items[0].top < topInset) {
    cursor = topInset
    for (const item of items) {
      item.top = cursor
      cursor += item.height + gap
    }
  }
}

/**
 * Keeps compact labels at the left/right edges of the scene, away from the
 * central aircraft. Vertical positions still track the projected component
 * anchor, then a collision pass prevents label-label overlap.
 */
export function layoutExplodedLabels(
  anchors: LabelAnchor[],
  viewportWidth: number,
  viewportHeight: number,
  options: LabelLayoutOptions = {},
): LabelPlacement[] {
  const cfg = { ...DEFAULTS, ...options }
  const width = Math.max(1, viewportWidth)
  const height = Math.max(1, viewportHeight)
  const leftX = cfg.margin
  const rightX = Math.max(cfg.margin, width - cfg.margin - cfg.labelWidth)

  const placements: LabelPlacement[] = anchors.map(anchor => {
    const side: LabelSide = anchor.preferredSide ?? (anchor.x < width / 2 ? 'left' : 'right')
    const topInset = side === 'left' ? cfg.topInsetLeft : cfg.topInsetRight
    const maxTop = Math.max(topInset, height - cfg.bottomInset - cfg.labelHeight)
    return {
      ...anchor,
      side,
      left: side === 'left' ? leftX : rightX,
      top: clamp(anchor.y - cfg.labelHeight / 2, topInset, maxTop),
      width: cfg.labelWidth,
      height: cfg.labelHeight,
    }
  })

  resolveColumn(
    placements.filter(item => item.side === 'left'),
    height,
    cfg.topInsetLeft,
    cfg.bottomInset,
    cfg.gap,
  )
  resolveColumn(
    placements.filter(item => item.side === 'right'),
    height,
    cfg.topInsetRight,
    cfg.bottomInset,
    cfg.gap,
  )
  return placements
}

export function placementsOverlap(
  a: Pick<LabelPlacement, 'left' | 'top' | 'width' | 'height'>,
  b: Pick<LabelPlacement, 'left' | 'top' | 'width' | 'height'>,
  padding = 0,
): boolean {
  return !(
    a.left + a.width + padding <= b.left ||
    b.left + b.width + padding <= a.left ||
    a.top + a.height + padding <= b.top ||
    b.top + b.height + padding <= a.top
  )
}
