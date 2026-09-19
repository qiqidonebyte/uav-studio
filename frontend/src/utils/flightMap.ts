export interface MapPoint {
  x: number
  y: number
}

export function projectLocalPoint(
  xMeters: number,
  yMeters: number,
  width: number,
  height: number,
  rangeMeters: number,
): MapPoint {
  const usableWidth = width * 0.84
  const usableHeight = height * 0.84
  return {
    x: width / 2 + (xMeters / rangeMeters) * (usableWidth / 2),
    y: height / 2 - (yMeters / rangeMeters) * (usableHeight / 2),
  }
}

export function unprojectMapPoint(
  pixelX: number,
  pixelY: number,
  width: number,
  height: number,
  rangeMeters: number,
): { x: number; y: number } {
  const usableWidth = width * 0.84
  const usableHeight = height * 0.84
  return {
    x: ((pixelX - width / 2) / (usableWidth / 2)) * rangeMeters,
    y: (-(pixelY - height / 2) / (usableHeight / 2)) * rangeMeters,
  }
}

export function isInsideFlightBoundary(
  xMeters: number,
  yMeters: number,
  boundaryMeters: number,
): boolean {
  return (
    Math.abs(xMeters) <= boundaryMeters &&
    Math.abs(yMeters) <= boundaryMeters
  )
}
