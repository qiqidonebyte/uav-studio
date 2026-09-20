export type PreflightCheckState = 'pass' | 'warn' | 'block'

export interface PreflightCheckRecord {
  key: string
  title: string
  state: PreflightCheckState
  summary: string
}

export interface PreflightSnapshot {
  version: 1
  aircraft_id: number | null
  aircraft_fingerprint: string
  passed: boolean
  score: number
  checked_at: string
  bridge_mode: 'demo' | 'live'
  scenario: string
  checks: PreflightCheckRecord[]
}

const PREFIX = 'uavstudio.preflight.v1'
export const PREFLIGHT_MAX_AGE_MS = 60 * 60 * 1000

export function aircraftFingerprint(aircraft: unknown): string {
  try { return JSON.stringify(aircraft ?? null) } catch { return String(aircraft ?? '') }
}

export function preflightStorageKey(aircraftId: number | null | undefined): string {
  return `${PREFIX}:${aircraftId ?? 'none'}`
}

export function savePreflightSnapshot(snapshot: PreflightSnapshot): void {
  try { globalThis.localStorage?.setItem(preflightStorageKey(snapshot.aircraft_id), JSON.stringify(snapshot)) } catch { /* optional */ }
}

export function clearPreflightSnapshot(aircraftId: number | null | undefined): void {
  try { globalThis.localStorage?.removeItem(preflightStorageKey(aircraftId)) } catch { /* optional */ }
}

export function loadPreflightSnapshot(
  aircraftId: number | null | undefined,
  fingerprint: string,
  nowMs = Date.now(),
): PreflightSnapshot | null {
  try {
    const raw = globalThis.localStorage?.getItem(preflightStorageKey(aircraftId))
    if (!raw) return null
    const parsed = JSON.parse(raw) as PreflightSnapshot
    if (parsed.version !== 1 || !parsed.passed) return null
    if (parsed.aircraft_id !== (aircraftId ?? null)) return null
    if (parsed.aircraft_fingerprint !== fingerprint) return null
    const checkedAt = Date.parse(parsed.checked_at)
    if (!Number.isFinite(checkedAt) || nowMs - checkedAt > PREFLIGHT_MAX_AGE_MS) return null
    return parsed
  } catch {
    return null
  }
}

export function preflightScore(checks: PreflightCheckRecord[]): number {
  const penalty = checks.reduce((sum, item) => sum + (item.state === 'block' ? 20 : item.state === 'warn' ? 6 : 0), 0)
  return Math.max(0, 100 - penalty)
}
