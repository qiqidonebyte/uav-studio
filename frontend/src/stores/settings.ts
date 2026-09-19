import axios from 'axios'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api/client'
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
  const user = ref<UserInfo>({ username: 'admin' })
  const settings = ref<UserSettings>(cloneDefaults())
  const loaded = ref(false)
  const loading = ref(false)
  const saving = ref(false)
  const error = ref('')
  const savedAt = ref<number | null>(null)

  const username = computed(() => user.value.username)

  async function initialize(force = false): Promise<void> {
    if ((loaded.value && !force) || loading.value) return
    loading.value = true
    error.value = ''
    try {
      const [userResponse, settingsResponse] = await Promise.all([
        api.get<UserInfo>('/user/me'),
        api.get<UserSettings>('/settings'),
      ])
      user.value = userResponse.data
      settings.value = settingsResponse.data
      loaded.value = true
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
      loaded.value = true
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

  return {
    user,
    username,
    settings,
    loaded,
    loading,
    saving,
    error,
    savedAt,
    initialize,
    save,
    changePassword,
    resetDraft,
  }
})
