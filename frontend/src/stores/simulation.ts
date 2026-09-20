import axios from 'axios'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api, telemetryWsUrl } from '../api/client'
import { useAssemblyStore } from './assembly'
import type { Vector3Value } from '../types/aircraft'
import type {
  SimulationSnapshot,
  SimulationStatus,
  TelemetryFrame,
} from '../types/telemetry'
import {
  FLIGHT_MODE_LABELS,
  SIMULATION_STATUS_LABELS,
} from '../utils/telemetry'

const emptyTelemetry: TelemetryFrame = {
  t: 0,
  position: { x: 0, y: 0, z: 0 },
  velocity: { x: 0, y: 0, z: 0 },
  attitude: { roll: 0, pitch: 0, yaw: 0 },
  angular_velocity: { p: 0, q: 0, r: 0 },
  center_of_gravity: { x: 0, y: 0, z: 0 },
  motors: { outputs: [0, 0, 0, 0], thrusts_n: [0, 0, 0, 0] },
  forces: { gravity_n: 0, total_thrust_n: 0 },
  wind: { speed_mps: 0, direction_deg: 0 },
  power: {
    estimated_power_w: 0,
    battery_remaining: 1,
    voltage_v: 0,
    current_a: 0,
  },
  armed: false,
  flight_mode: 'IDLE',
}

function requestErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return '无法连接仿真服务，请确认后端已启动。'
}

export const useSimulationStore = defineStore('simulation', () => {
  const telemetry = ref<TelemetryFrame>(emptyTelemetry)
  const history = ref<TelemetryFrame[]>([])
  const simulationId = ref<number | null>(null)
  const simulationStatus = ref<SimulationStatus>('STOPPED')
  const connectionStatus = ref<'DISCONNECTED' | 'CONNECTING' | 'CONNECTED'>(
    'DISCONNECTED',
  )
  const error = ref('')
  const hasTelemetry = ref(false)
  const targetAltitude = ref(10)
  const windSpeed = ref(5)
  const windDirection = ref(90)
  const targetPosition = ref<Vector3Value>({ x: 0, y: 0, z: 0 })
  const waypoints = ref<Vector3Value[]>([])
  const boundaryM = ref(25)
  const ws = ref<WebSocket | null>(null)
  let socketGeneration = 0

  const batteryPercent = computed(() =>
    Math.round(telemetry.value.power.battery_remaining * 100),
  )
  const simulationStatusZh = computed(
    () => SIMULATION_STATUS_LABELS[simulationStatus.value],
  )
  const flightModeZh = computed(
    () => FLIGHT_MODE_LABELS[telemetry.value.flight_mode],
  )
  const airborne = computed(() => telemetry.value.position.z > 0.2)

  function applySnapshot(snapshot: SimulationSnapshot): void {
    simulationId.value = snapshot.id
    simulationStatus.value = snapshot.status
    targetPosition.value = snapshot.target_position
    waypoints.value = snapshot.waypoints
    boundaryM.value = snapshot.boundary_m
    setTelemetry(snapshot.telemetry)
  }

  function setTelemetry(frame: TelemetryFrame): void {
    if (
      history.value.length > 0 &&
      frame.t < history.value[history.value.length - 1].t
    ) {
      history.value = []
    }
    telemetry.value = frame
    hasTelemetry.value = true
    history.value.push(frame)
    if (history.value.length > 2400) {
      history.value.splice(0, history.value.length - 2400)
    }
  }

  async function postCommand(
    path: string,
    body?: Record<string, unknown>,
  ): Promise<void> {
    error.value = ''
    try {
      const response = await api.post<SimulationSnapshot>(path, body)
      applySnapshot(response.data)
    } catch (caught) {
      error.value = requestErrorMessage(caught)
      throw caught
    }
  }

  async function createSimulation(): Promise<void> {
    error.value = ''
    try {
      const assemblyStore = useAssemblyStore()
      await assemblyStore.initialize()
      const aircraftId = assemblyStore.activeAircraftId
      if (!aircraftId) {
        throw new Error('当前没有可用于飞行实验的飞机设计')
      }

      const response = await api.post<SimulationSnapshot>('/simulations', {
        aircraft_id: aircraftId,
      })
      history.value = []
      applySnapshot(response.data)
      connectTelemetry()
    } catch (caught) {
      error.value = requestErrorMessage(caught)
      if (caught instanceof Error && !axios.isAxiosError(caught)) {
        error.value = caught.message
      }
      throw caught
    }
  }

  async function start(): Promise<void> {
    if (simulationStatus.value === 'RUNNING') return
    if (
      simulationStatus.value !== 'PAUSED' ||
      simulationId.value === null
    ) {
      await createSimulation()
    }
    if (simulationId.value === null) return
    await postCommand(`/simulations/${simulationId.value}/start`)
  }

  async function pause(): Promise<void> {
    if (simulationId.value === null) return
    await postCommand(`/simulations/${simulationId.value}/pause`)
  }

  async function reset(): Promise<void> {
    if (simulationId.value === null) return
    history.value = []
    await postCommand(`/simulations/${simulationId.value}/reset`)
  }

  async function stop(): Promise<void> {
    if (simulationId.value === null) return
    await postCommand(`/simulations/${simulationId.value}/stop`)
  }

  async function arm(): Promise<void> {
    if (simulationId.value === null) return
    await postCommand(`/simulations/${simulationId.value}/arm`)
  }

  async function takeoff(): Promise<void> {
    if (simulationId.value === null) return
    await postCommand(`/simulations/${simulationId.value}/takeoff`, {
      altitude_m: targetAltitude.value,
    })
  }

  async function land(): Promise<void> {
    if (simulationId.value === null) return
    await postCommand(`/simulations/${simulationId.value}/land`)
  }

  async function applyWind(): Promise<void> {
    if (simulationId.value === null) return
    await postCommand(`/simulations/${simulationId.value}/wind`, {
      speed_mps: windSpeed.value,
      direction_deg: windDirection.value,
    })
  }

  async function setTarget(x: number, y: number): Promise<void> {
    if (simulationId.value === null) return
    await postCommand(`/simulations/${simulationId.value}/target`, { x, y })
  }

  async function setWaypoints(nextWaypoints: Vector3Value[]): Promise<void> {
    if (simulationId.value === null) return
    await postCommand(`/simulations/${simulationId.value}/waypoints`, {
      waypoints: nextWaypoints,
    })
  }

  function connectTelemetry(): void {
    if (simulationId.value === null) return
    const generation = ++socketGeneration
    ws.value?.close()
    connectionStatus.value = 'CONNECTING'
    const socket = new WebSocket(telemetryWsUrl(simulationId.value))
    ws.value = socket

    socket.onopen = () => {
      if (generation === socketGeneration) connectionStatus.value = 'CONNECTED'
    }
    socket.onmessage = event => {
      if (generation !== socketGeneration) return
      const frame = JSON.parse(event.data) as TelemetryFrame
      setTelemetry(frame)
    }
    socket.onerror = () => {
      if (generation === socketGeneration) error.value = '实时遥测连接异常。'
    }
    socket.onclose = () => {
      if (generation !== socketGeneration) return
      ws.value = null
      connectionStatus.value = 'DISCONNECTED'
    }
  }

  function disconnectTelemetry(): void {
    socketGeneration += 1
    ws.value?.close()
    ws.value = null
    connectionStatus.value = 'DISCONNECTED'
  }

  return {
    telemetry,
    history,
    simulationId,
    simulationStatus,
    connectionStatus,
    error,
    hasTelemetry,
    targetAltitude,
    windSpeed,
    windDirection,
    targetPosition,
    waypoints,
    boundaryM,
    batteryPercent,
    simulationStatusZh,
    flightModeZh,
    airborne,
    createSimulation,
    start,
    pause,
    reset,
    stop,
    arm,
    takeoff,
    land,
    applyWind,
    setTarget,
    setWaypoints,
    connectTelemetry,
    disconnectTelemetry,
  }
})
