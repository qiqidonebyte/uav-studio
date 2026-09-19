import axios from 'axios'
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api'
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const wsBaseUrl =
  import.meta.env.VITE_WS_BASE_URL ?? `${wsProtocol}//${window.location.host}`

export const api = axios.create({ baseURL: apiBaseUrl, timeout: 10000 })
export const telemetryWsUrl = (simulationId: number | string) =>
  `${wsBaseUrl}/ws/simulations/${simulationId}`
