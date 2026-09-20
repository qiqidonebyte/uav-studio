export interface Px4Status {
  dependency_available: boolean
  running: boolean
  connected: boolean
  connection_url: string
  heartbeat_age_s: number | null
  system_id: number | null
  component_id: number | null
  mode: string
  armed: boolean
  last_error: string
  uptime_s: number
}

export interface Px4Telemetry extends Px4Status {
  landed_state: number | null
  attitude: {
    roll: number
    pitch: number
    yaw: number
    rollspeed: number
    pitchspeed: number
    yawspeed: number
  }
  local_position: { x: number; y: number; z: number; vx: number; vy: number; vz: number }
  global_position: { lat_deg: number | null; lon_deg: number | null; relative_alt_m: number | null }
  gps: { fix_type: number | null; satellites: number | null; eph: number | null }
  battery: { voltage_v: number | null; current_a: number | null; remaining: number | null }
  motors: { outputs: number[] }
  estimator: { flags: number | null; ok: boolean | null }
  statustext: string
  prearm_ok: boolean
}

function defaultBridgeBase(): string {
  const explicit = import.meta.env.VITE_PX4_BRIDGE_URL as string | undefined
  if (explicit) return explicit.replace(/\/$/, '')
  if (typeof window === 'undefined') return 'http://127.0.0.1:8001/api/px4'
  return `${window.location.protocol}//${window.location.hostname}:8001/api/px4`
}

const base = defaultBridgeBase()

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${base}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = typeof body?.detail === 'string' ? body.detail : `PX4 Bridge HTTP ${response.status}`
    throw new Error(detail)
  }
  return body as T
}

export const px4Api = {
  status: () => request<Px4Status>('/status'),
  telemetry: () => request<Px4Telemetry>('/telemetry'),
  connect: (connectionUrl?: string) => request<Px4Status>('/connect', {
    method: 'POST',
    body: JSON.stringify({ connection_url: connectionUrl || null }),
  }),
  disconnect: () => request<Px4Status>('/disconnect', { method: 'POST' }),
  requestStreams: () => request<{ ok: boolean }>('/request-streams', { method: 'POST' }),
  arm: () => request<Record<string, unknown>>('/arm', { method: 'POST' }),
  disarm: () => request<Record<string, unknown>>('/disarm', { method: 'POST' }),
  takeoff: (altitudeM = 2) => request<Record<string, unknown>>('/takeoff', {
    method: 'POST',
    body: JSON.stringify({ altitude_m: altitudeM }),
  }),
  land: () => request<Record<string, unknown>>('/land', { method: 'POST' }),
  prearmCheck: () => request<Record<string, unknown>>('/prearm-check', { method: 'POST' }),
  testMotor: (motor: string, value = .2, timeoutS = 1.5) => request<Record<string, unknown>>(`/motors/${motor}/test`, {
    method: 'POST',
    body: JSON.stringify({ value, timeout_s: timeoutS }),
  }),
  getParameter: (name: string) => request<{ name: string; value: number; type: number }>(`/parameters/${encodeURIComponent(name)}`),
  setParameter: (name: string, value: number) => request<{ name: string; value: number; type: number }>(`/parameters/${encodeURIComponent(name)}`, {
    method: 'PUT',
    body: JSON.stringify({ value }),
  }),
}
