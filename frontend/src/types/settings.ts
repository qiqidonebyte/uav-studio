export type DefaultPage = 'assembly' | 'flight' | 'history' | 'components'
export type RenderQuality = 'performance' | 'balanced' | 'high'
export type ShadowQuality = 'off' | 'low' | 'medium' | 'high'
export type CameraMode = 'free' | 'follow' | 'top' | 'side'
export type FlightViewMode = '3d' | 'map' | 'split'

export interface GeneralSettings {
  unit_system: 'metric'
  decimal_places: number
  default_page: DefaultPage
  default_aircraft_id: number
  confirm_dangerous_actions: boolean
}

export interface Display3DSettings {
  quality: RenderQuality
  antialias: boolean
  shadows: ShadowQuality
  environment_reflection: boolean
  show_grid: boolean
  show_axes: boolean
  show_cg: boolean
  show_thrust_vectors: boolean
  show_gravity_vector: boolean
  show_wind_vector: boolean
  show_trajectory: boolean
  trajectory_points: number
  default_camera: CameraMode
}

export interface FlightSettings {
  default_altitude_m: number
  default_wind_speed_mps: number
  default_wind_direction_deg: number
  default_view: FlightViewMode
  chart_window_seconds: number
  max_trajectory_points: number
  auto_create_simulation: boolean
  auto_connect_telemetry: boolean
  auto_save_experiment: boolean
}

export interface UserSettings {
  general: GeneralSettings
  display_3d: Display3DSettings
  flight: FlightSettings
}

export interface UserInfo {
  username: string
}

export const DEFAULT_USER_SETTINGS: UserSettings = {
  general: {
    unit_system: 'metric',
    decimal_places: 2,
    default_page: 'assembly',
    default_aircraft_id: 1,
    confirm_dangerous_actions: true,
  },
  display_3d: {
    quality: 'balanced',
    antialias: true,
    shadows: 'medium',
    environment_reflection: true,
    show_grid: true,
    show_axes: true,
    show_cg: true,
    show_thrust_vectors: true,
    show_gravity_vector: true,
    show_wind_vector: true,
    show_trajectory: true,
    trajectory_points: 600,
    default_camera: 'free',
  },
  flight: {
    default_altitude_m: 5,
    default_wind_speed_mps: 0,
    default_wind_direction_deg: 90,
    default_view: 'split',
    chart_window_seconds: 60,
    max_trajectory_points: 600,
    auto_create_simulation: false,
    auto_connect_telemetry: true,
    auto_save_experiment: true,
  },
}
