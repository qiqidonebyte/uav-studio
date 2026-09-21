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
  session_status?: 'unassigned' | 'queued' | 'starting' | 'ready' | 'active' | 'released' | 'failed'
  queue_position?: number
  slot_id?: number | null
  slot_port?: number
  run_id?: number
}

export type Px4SensorKey = 'gyro' | 'accelerometer' | 'compass' | 'barometer'

export interface Px4SensorHealthFlag {
  present: boolean | null
  enabled: boolean | null
  healthy: boolean | null
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
  global_position: {
    lat_deg: number | null
    lon_deg: number | null
    relative_alt_m: number | null
    alt_amsl_m?: number | null
  }
  gps: { fix_type: number | null; satellites: number | null; eph: number | null }
  battery: { voltage_v: number | null; current_a: number | null; remaining: number | null }
  imu?: {
    accel_m_s2: { x: number | null; y: number | null; z: number | null }
    gyro_rad_s: { x: number | null; y: number | null; z: number | null }
    temperature_c: number | null
    source: string | null
  }
  magnetometer?: {
    x_gauss: number | null
    y_gauss: number | null
    z_gauss: number | null
    field_strength_gauss: number | null
    heading_deg: number | null
  }
  barometer?: {
    absolute_pressure_hpa: number | null
    pressure_alt_m: number | null
    temperature_c: number | null
  }
  sensor_health?: {
    gyro: Px4SensorHealthFlag
    accelerometer: Px4SensorHealthFlag
    magnetometer: Px4SensorHealthFlag
    barometer: Px4SensorHealthFlag
    gps: Px4SensorHealthFlag
  }
  sensor_data_age_s?: {
    imu: number | null
    magnetometer: number | null
    barometer: number | null
  }
  rc?: {
    channel_count: number
    channels_us: Array<number | null>
    rssi_percent: number | null
    age_s: number | null
    manual_control: { x: number | null; y: number | null; z: number | null; r: number | null; buttons: number | null }
    manual_control_age_s: number | null
  }
  motors: { outputs: number[] }
  estimator: { flags: number | null; ok: boolean | null }
  statustext: string
  prearm_ok: boolean
}

export interface Px4CommandResult {
  accepted?: boolean
  timeout?: boolean
  command?: number
  result?: number
  progress?: number
  relative_altitude_m?: number
  home_altitude_amsl_m?: number
  target_altitude_amsl_m?: number
  [key: string]: unknown
}

function trainingRunId(): number | null {
  if (typeof window === 'undefined') return null
  const value = Number(new URLSearchParams(window.location.search).get('run'))
  return Number.isInteger(value) && value > 0 ? value : null
}

function apiBase(): string {
  const explicit = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '/api'
  return explicit.replace(/\/$/, '')
}

function defaultBridgeBase(): string {
  const explicit = import.meta.env.VITE_PX4_BRIDGE_URL as string | undefined
  if (explicit) return explicit.replace(/\/$/, '')
  if (typeof window === 'undefined') return 'http://127.0.0.1:8001/api/px4'
  return `${window.location.protocol}//${window.location.hostname}:8001/api/px4`
}

function endpointBase(): { base: string; training: boolean } {
  const runId = trainingRunId()
  if (runId !== null) {
    return { base: `${apiBase()}/training/runs/${runId}/px4`, training: true }
  }
  return { base: defaultBridgeBase(), training: false }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const endpoint = endpointBase()
  const response = await fetch(`${endpoint.base}${path}`, {
    ...init,
    credentials: endpoint.training ? 'include' : 'omit',
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
  connect: (connectionUrl?: string) => {
    const training = trainingRunId() !== null
    return request<Px4Status>('/connect', {
      method: 'POST',
      ...(training ? {} : { body: JSON.stringify({ connection_url: connectionUrl || null }) }),
    })
  },
  disconnect: () => request<Px4Status>('/disconnect', { method: 'POST' }),
  requestStreams: () => request<{ ok: boolean }>('/request-streams', { method: 'POST' }),
  arm: () => request<Px4CommandResult>('/arm', { method: 'POST' }),
  disarm: () => request<Px4CommandResult>('/disarm', { method: 'POST' }),
  takeoff: (altitudeM = 2) => request<Px4CommandResult>('/takeoff', {
    method: 'POST',
    body: JSON.stringify({ altitude_m: altitudeM }),
  }),
  land: () => request<Px4CommandResult>('/land', { method: 'POST' }),
  prearmCheck: () => request<Px4CommandResult>('/prearm-check', { method: 'POST' }),
  calibrateSensor: (sensor: Px4SensorKey) => request<{ accepted: boolean; timeout: boolean; command: number; result?: number; sensor: Px4SensorKey }>(`/sensors/${sensor}/calibrate`, {
    method: 'POST',
  }),
  testMotor: (motor: string, value = .2, timeoutS = 1.5) => request<Px4CommandResult>(`/motors/${motor}/test`, {
    method: 'POST',
    body: JSON.stringify({ value, timeout_s: timeoutS }),
  }),
  getParameter: (name: string) => request<{ name: string; value: number; type: number }>(`/parameters/${encodeURIComponent(name)}`),
  setParameter: (name: string, value: number) => request<{ name: string; value: number; type: number }>(`/parameters/${encodeURIComponent(name)}`, {
    method: 'PUT',
    body: JSON.stringify({ value }),
  }),
}
