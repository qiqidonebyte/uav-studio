import axios from 'axios'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api/client'
import type {
  AuthSessionResponse,
  AuthUser,
  LoginPayload,
  RegisterPayload,
} from '../types/auth'

function authErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return '认证服务不可用，请确认后端已启动。'
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const initialized = ref(false)
  const loading = ref(false)
  const error = ref('')

  const authenticated = computed(() => user.value !== null)
  const aircraftLimit = computed(() => user.value?.aircraft_limit ?? 10)

  async function initialize(force = false): Promise<boolean> {
    if (initialized.value && !force) return authenticated.value
    if (loading.value) return authenticated.value
    loading.value = true
    error.value = ''
    try {
      const response = await api.get<AuthUser>('/auth/me')
      user.value = response.data
    } catch (caught) {
      if (axios.isAxiosError(caught) && caught.response?.status === 401) {
        user.value = null
      } else {
        error.value = authErrorMessage(caught)
        user.value = null
      }
    } finally {
      initialized.value = true
      loading.value = false
    }
    return authenticated.value
  }

  async function login(payload: LoginPayload): Promise<AuthUser> {
    loading.value = true
    error.value = ''
    try {
      const response = await api.post<AuthSessionResponse>('/auth/login', payload)
      user.value = response.data.user
      initialized.value = true
      return response.data.user
    } catch (caught) {
      error.value = authErrorMessage(caught)
      throw caught
    } finally {
      loading.value = false
    }
  }

  async function register(payload: RegisterPayload): Promise<AuthUser> {
    loading.value = true
    error.value = ''
    try {
      const response = await api.post<AuthSessionResponse>('/auth/register', payload)
      user.value = response.data.user
      initialized.value = true
      return response.data.user
    } catch (caught) {
      error.value = authErrorMessage(caught)
      throw caught
    } finally {
      loading.value = false
    }
  }

  async function logout(): Promise<void> {
    error.value = ''
    try {
      await api.post('/auth/logout')
    } finally {
      user.value = null
      initialized.value = true
    }
  }

  function clearSession(): void {
    user.value = null
    initialized.value = true
  }

  return {
    user,
    initialized,
    loading,
    error,
    authenticated,
    aircraftLimit,
    initialize,
    login,
    register,
    logout,
    clearSession,
  }
})
