import axios from 'axios'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api/client'
import { useAuthStore } from './auth'
import type { UserInfo, UserSettings } from '../types/settings'
import { DEFAULT_USER_SETTINGS } from '../types/settings'

function cloneDefaults(): UserSettings {
  return JSON.parse(JSON.stringify(DEFAULT_USER_SETTINGS)) as UserSettings
}

function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return '设置服务不可用，请确认后端已启动。'
}

export const useSettingsStore = defineStore('settings', () => {
  const auth = useAuthStore()
  const user = ref<UserInfo | null>(null)
  const settings = ref<UserSettings>(cloneDefaults())
  const loadedForUserId = ref<number | null>(null)
  const loading = ref(false)
  const saving = ref(false)
  const error = ref('')
  const savedAt = ref<number | null>(null)

  const username = computed(() => user.value?.username ?? auth.user?.username ?? '')
  const displayName = computed(
    () => user.value?.display_name ?? auth.user?.display_name ?? username.value,
  )
  const role = computed(() => user.value?.role ?? auth.user?.role ?? 'student')

  async function initialize(force = false): Promise<void> {
    const userId = auth.user?.id
    if (!userId) {
      resetForLogout()
      return
    }
    if ((!force && loadedForUserId.value === userId) || loading.value) return
    loading.value = true
    error.value = ''
    try {
      const [userResponse, settingsResponse] = await Promise.all([
        api.get<UserInfo>('/user/me'),
        api.get<UserSettings>('/settings'),
      ])
      user.value = userResponse.data
      settings.value = settingsResponse.data
      loadedForUserId.value = userId
    } catch (caught) {
      error.value = errorMessage(caught)
    } finally {
      loading.value = false
    }
  }

  async function save(): Promise<void> {
    saving.value = true
    error.value = ''
    try {
      const response = await api.put<UserSettings>('/settings', settings.value)
      settings.value = response.data
      loadedForUserId.value = auth.user?.id ?? null
      savedAt.value = Date.now()
    } catch (caught) {
      error.value = errorMessage(caught)
      throw caught
    } finally {
      saving.value = false
    }
  }

  async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
    error.value = ''
    try {
      await api.put('/user/password', {
        current_password: currentPassword,
        new_password: newPassword,
      })
    } catch (caught) {
      error.value = errorMessage(caught)
      throw caught
    }
  }

  function resetDraft(): void {
    settings.value = cloneDefaults()
  }

  function resetForLogout(): void {
    user.value = null
    settings.value = cloneDefaults()
    loadedForUserId.value = null
    savedAt.value = null
    error.value = ''
  }

  return {
    user,
    username,
    displayName,
    role,
    settings,
    loaded: computed(() => loadedForUserId.value !== null),
    loading,
    saving,
    error,
    savedAt,
    initialize,
    save,
    changePassword,
    resetDraft,
    resetForLogout,
  }
})
