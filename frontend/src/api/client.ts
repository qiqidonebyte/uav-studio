import axios from 'axios'

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api'
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const wsBaseUrl =
  import.meta.env.VITE_WS_BASE_URL ?? `${wsProtocol}//${window.location.host}`

export const api = axios.create({
  baseURL: apiBaseUrl,
  timeout: 10000,
  withCredentials: true,
})

api.interceptors.response.use(
  response => response,
  error => {
    const url = String(error?.config?.url ?? '')
    const isAuthAttempt = url.includes('/auth/login') || url.includes('/auth/register')
    if (error?.response?.status === 401 && !isAuthAttempt) {
      globalThis.dispatchEvent?.(new CustomEvent('uav-auth-expired'))
    }
    return Promise.reject(error)
  },
)

export const telemetryWsUrl = (simulationId: number | string) =>
  `${wsBaseUrl}/ws/simulations/${simulationId}`
