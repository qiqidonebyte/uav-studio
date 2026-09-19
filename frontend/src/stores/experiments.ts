import { ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api/client'
import type { ExperimentSummary } from '../types/telemetry'

export const useExperimentsStore = defineStore('experiments', () => {
  const experiments = ref<ExperimentSummary[]>([])
  const loading = ref(false)
  const error = ref('')

  async function loadExperiments(): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      const response = await api.get<ExperimentSummary[]>('/experiments')
      experiments.value = response.data
    } catch {
      error.value = '无法读取实验记录。'
    } finally {
      loading.value = false
    }
  }

  return { experiments, loading, error, loadExperiments }
})
