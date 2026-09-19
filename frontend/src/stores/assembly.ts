import axios from 'axios'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api/client'
import type {
  AircraftDefinition,
  AssemblyState,
  Component,
} from '../types/aircraft'
import {
  installedComponentId,
  SLOT_FIELDS,
  type AssemblySlot,
} from '../utils/assembly'

const DEFAULT_AIRCRAFT_ID = 1

function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return '无法连接本地服务，请确认后端已启动。'
}

export const useAssemblyStore = defineStore('assembly', () => {
  const components = ref<Component[]>([])
  const assemblyState = ref<AssemblyState | null>(null)
  const selectedSlot = ref<AssemblySlot | null>(null)
  const loading = ref(false)
  const saving = ref(false)
  const error = ref('')

  const aircraft = computed(() => assemblyState.value?.aircraft ?? null)
  const engineering = computed(() => assemblyState.value?.engineering ?? null)
  const validation = computed(
    () =>
      assemblyState.value?.validation ?? {
        passed: false,
        blocking_errors: [],
        warnings: [],
      },
  )
  const aircraftName = computed(() => aircraft.value?.name ?? '正在载入')

  async function initialize(): Promise<void> {
    if (assemblyState.value || loading.value) return
    loading.value = true
    error.value = ''
    try {
      const [componentsResponse, aircraftResponse] = await Promise.all([
        api.get<Component[]>('/components'),
        api.get<AssemblyState>(`/aircraft/${DEFAULT_AIRCRAFT_ID}`),
      ])
      components.value = componentsResponse.data
      assemblyState.value = aircraftResponse.data
    } catch (caught) {
      error.value = errorMessage(caught)
    } finally {
      loading.value = false
    }
  }

  async function installComponent(
    slot: AssemblySlot,
    componentId: number,
  ): Promise<void> {
    if (!assemblyState.value) return
    const component = components.value.find(item => item.id === componentId)
    if (!component || component.type !== slot) return

    const nextAircraft: AircraftDefinition = {
      ...assemblyState.value.aircraft,
      [SLOT_FIELDS[slot]]: component.id,
    }
    if (slot === 'payload') {
      const mount = component.parameters_json.mount
      nextAircraft.payload_position_m =
        mount === 'front'
          ? { x: 0.18, y: 0, z: -0.02 }
          : { x: 0.08, y: 0, z: -0.12 }
    }
    await saveAircraft(nextAircraft)
    selectedSlot.value = slot
  }

  async function removeComponent(slot: AssemblySlot): Promise<void> {
    if (!assemblyState.value) return
    const nextAircraft: AircraftDefinition = {
      ...assemblyState.value.aircraft,
      [SLOT_FIELDS[slot]]: null,
    }
    if (slot === 'payload') nextAircraft.payload_position_m = null
    if (slot === 'gnss') nextAircraft.gnss_position_m = null
    await saveAircraft(nextAircraft)
    selectedSlot.value = slot
  }

  async function saveAircraft(nextAircraft: AircraftDefinition): Promise<void> {
    saving.value = true
    error.value = ''
    try {
      const response = await api.put<AssemblyState>(
        `/aircraft/${DEFAULT_AIRCRAFT_ID}`,
        nextAircraft,
      )
      assemblyState.value = response.data
    } catch (caught) {
      error.value = errorMessage(caught)
      throw caught
    } finally {
      saving.value = false
    }
  }

  async function refreshCalculation(): Promise<void> {
    if (!assemblyState.value) return
    saving.value = true
    error.value = ''
    try {
      const response = await api.post<AssemblyState>(
        `/aircraft/${DEFAULT_AIRCRAFT_ID}/calculate`,
      )
      assemblyState.value = response.data
    } catch (caught) {
      error.value = errorMessage(caught)
    } finally {
      saving.value = false
    }
  }

  function componentForSlot(slot: AssemblySlot): Component | null {
    const componentId = aircraft.value
      ? installedComponentId(aircraft.value, slot)
      : null
    return components.value.find(component => component.id === componentId) ?? null
  }

  function selectSlot(slot: AssemblySlot | null): void {
    selectedSlot.value = slot
  }

  return {
    components,
    assemblyState,
    aircraft,
    engineering,
    validation,
    aircraftName,
    selectedSlot,
    loading,
    saving,
    error,
    initialize,
    installComponent,
    removeComponent,
    refreshCalculation,
    componentForSlot,
    selectSlot,
  }
})
