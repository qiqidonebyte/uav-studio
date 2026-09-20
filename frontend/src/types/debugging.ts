import type { RotorDirection } from './aircraft'

export type DebugSeverity = 'pass' | 'warning' | 'error'
export type DebugGroup = 'engineering' | 'sensors' | 'propulsion' | 'link' | 'preflight'
export type DebugReadiness = 'READY' | 'CONDITIONAL' | 'BLOCKED'

export interface MotorBenchState {
  responding: boolean
  direction: RotorDirection
}

export interface DebuggingBenchState {
  scenarioKey: string
  imuCalibrated: boolean
  compassCalibrated: boolean
  gpsSatellites: number
  gpsHdop: number
  rcCalibrated: boolean
  rcSignalPercent: number
  batteryVoltageV: number
  lowBatteryPercent: number
  criticalBatteryPercent: number
  failsafeMode: 'RTH' | 'LAND' | 'HOLD'
  rthAltitudeM: number
  motors: Record<'M1' | 'M2' | 'M3' | 'M4', MotorBenchState>
  propellersSecured: boolean
  wiringSecured: boolean
  environmentClear: boolean
}

export interface DebuggingContext {
  validationPassed: boolean
  blockingErrorCount: number
  warningCount: number
  engineeringAvailable: boolean
  thrustWeightRatio: number | null
  cgHorizontalM: number | null
  escCurrentMarginA: number | null
  batteryContinuousMarginA: number | null
  powerModuleCurrentMarginA: number | null
  batteryMinVoltageV: number | null
  batteryNominalVoltageV: number | null
  batteryMaxVoltageV: number | null
}

export interface DebugCheck {
  key: string
  group: DebugGroup
  title: string
  severity: DebugSeverity
  value: string
  recommendation: string
}

export interface DebuggingEvaluation {
  readiness: DebugReadiness
  score: number
  checks: DebugCheck[]
  passCount: number
  warningCount: number
  errorCount: number
}

export interface DebuggingCheckpoint {
  id: string
  createdAt: string
  scenarioKey: string
  readiness: DebugReadiness
  score: number
  failedKeys: string[]
  warningKeys: string[]
}
