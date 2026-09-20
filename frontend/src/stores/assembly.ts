import axios from 'axios'
import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api/client'
import { useAuthStore } from './auth'
import type {
  AircraftDefinition,
  AircraftLibraryItem,
  AircraftMetadataUpdate,
  AircraftTemplate,
  AssemblyState,
  Component,
  FrameMountPoints,
  MotorName,
  RotorDirection,
  Vector3Value,
} from '../types/aircraft'
import {
  installedComponentId,
  SLOT_FIELDS,
  type AssemblySlot,
} from '../utils/assembly'
import {
  buildMountPoints,
  clearSlotInstances,
  componentIdAtMount,
  installInstance,
  instanceAtMount,
  removeInstance,
  replaceSlotInstances,
  slotCompletion,
  type MountPoint,
} from '../three/assemblySemantics'

const ACTIVE_AIRCRAFT_KEY_PREFIX = 'uavstudio.activeAircraftId'

function activeAircraftKey(userId: number): string {
  return `${ACTIVE_AIRCRAFT_KEY_PREFIX}:${userId}`
}

function storedAircraftId(userId: number): number | null {
  try {
    const value = globalThis.localStorage?.getItem(activeAircraftKey(userId))
    if (!value) return null
    const parsed = Number(value)
    return Number.isInteger(parsed) && parsed > 0 ? parsed : null
  } catch {
    return null
  }
}

function rememberAircraftId(userId: number, aircraftId: number): void {
  try {
    globalThis.localStorage?.setItem(
      activeAircraftKey(userId),
      String(aircraftId),
    )
  } catch {
    // Local storage is a convenience only; SQLite remains the source of truth.
  }
}

export interface PendingInstall {
  slot: AssemblySlot
  componentId: number
}

export interface InstallationPulse {
  mountId: string
  serial: number
}

function errorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
  }
  return '无法连接本地服务，请确认后端已启动。'
}

function vectorFromUnknown(value: unknown): Vector3Value | null {
  if (!value || typeof value !== 'object') return null
  const item = value as Record<string, unknown>
  if (typeof item.x !== 'number' || typeof item.y !== 'number' || typeof item.z !== 'number') {
    return null
  }
  return { x: item.x, y: item.y, z: item.z }
}

function frameMounts(component: Component | null): FrameMountPoints | null {
  const raw = component?.parameters_json.mount_points
  if (!raw || typeof raw !== 'object') return null
  return raw as unknown as FrameMountPoints
}

export const useAssemblyStore = defineStore('assembly', () => {
  const components = ref<Component[]>([])
  const aircraftLibrary = ref<AircraftLibraryItem[]>([])
  const aircraftTemplates = ref<AircraftTemplate[]>([])
  const activeAircraftId = ref<number | null>(null)
  const initializedUserId = ref<number | null>(null)
  const libraryLoading = ref(false)
  const saveStatus = ref<'saved' | 'saving' | 'error'>('saved')
  const lastSavedAt = ref<Date | null>(null)
  const assemblyState = ref<AssemblyState | null>(null)
  const selectedSlot = ref<AssemblySlot | null>(null)
  const selectedMountId = ref<string | null>(null)
  const pendingInstall = ref<PendingInstall | null>(null)
  const lastInstallation = ref<InstallationPulse | null>(null)
  const lastRemoval = ref<InstallationPulse | null>(null)
  const removingMountId = ref<string | null>(null)
  const loading = ref(false)
  const saving = ref(false)
  const error = ref('')
  let installationSerial = 0

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
  const authStore = useAuthStore()
  const aircraftLimit = computed(() => authStore.aircraftLimit)
  const aircraftCount = computed(() => aircraftLibrary.value.length)
  const canCreateAircraft = computed(
    () => aircraftCount.value < aircraftLimit.value,
  )
  const activeLibraryItem = computed(
    () => aircraftLibrary.value.find(
      item => item.aircraft.id === activeAircraftId.value,
    ) ?? null,
  )
  const saveStatusZh = computed(() => {
    if (saveStatus.value === 'saving') return '正在保存…'
    if (saveStatus.value === 'error') return '保存失败'
    return '已保存'
  })
  const mountPoints = computed(() => buildMountPoints(aircraft.value, components.value))

  async function refreshComponents(): Promise<void> {
    const response = await api.get<Component[]>('/components')
    components.value = response.data
  }

  async function refreshLibrary(): Promise<void> {
    libraryLoading.value = true
    try {
      const response = await api.get<AircraftLibraryItem[]>('/aircraft')
      aircraftLibrary.value = response.data
    } finally {
      libraryLoading.value = false
    }
  }

  async function refreshTemplates(): Promise<void> {
    const response = await api.get<AircraftTemplate[]>('/aircraft/templates')
    aircraftTemplates.value = response.data
  }

  function applyLibraryItem(item: AircraftLibraryItem): void {
    assemblyState.value = {
      aircraft: item.aircraft,
      engineering: item.engineering,
      validation: item.validation,
    }
    if (item.aircraft.id && authStore.user) {
      activeAircraftId.value = item.aircraft.id
      rememberAircraftId(authStore.user.id, item.aircraft.id)
    }
    selectedSlot.value = null
    selectedMountId.value = null
    pendingInstall.value = null
    saveStatus.value = 'saved'
  }

  function upsertLibraryItem(item: AircraftLibraryItem): void {
    const id = item.aircraft.id
    if (!id) return
    const index = aircraftLibrary.value.findIndex(
      current => current.aircraft.id === id,
    )
    if (index >= 0) {
      aircraftLibrary.value.splice(index, 1, item)
    } else {
      aircraftLibrary.value.unshift(item)
    }
    aircraftLibrary.value.sort(
      (a, b) =>
        new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
    )
  }

  function resetWorkspace(): void {
    aircraftLibrary.value = []
    aircraftTemplates.value = []
    activeAircraftId.value = null
    initializedUserId.value = null
    assemblyState.value = null
    selectedSlot.value = null
    selectedMountId.value = null
    pendingInstall.value = null
    lastInstallation.value = null
    lastRemoval.value = null
    removingMountId.value = null
    saveStatus.value = 'saved'
    lastSavedAt.value = null
    error.value = ''
  }

  async function initialize(): Promise<void> {
    const userId = authStore.user?.id
    if (!userId) {
      resetWorkspace()
      return
    }
    if (initializedUserId.value === userId && assemblyState.value) return
    if (loading.value) return
    if (initializedUserId.value !== null && initializedUserId.value !== userId) {
      resetWorkspace()
    }
    initializedUserId.value = userId
    activeAircraftId.value = storedAircraftId(userId)
    loading.value = true
    error.value = ''
    try {
      const [componentsResponse, libraryResponse, templatesResponse] = await Promise.all([
        api.get<Component[]>('/components'),
        api.get<AircraftLibraryItem[]>('/aircraft'),
        api.get<AircraftTemplate[]>('/aircraft/templates'),
      ])
      components.value = componentsResponse.data
      aircraftLibrary.value = libraryResponse.data
      aircraftTemplates.value = templatesResponse.data

      let item = aircraftLibrary.value.find(
        value => value.aircraft.id === activeAircraftId.value,
      ) ?? aircraftLibrary.value[0]

      if (!item) {
        const created = await api.post<AircraftLibraryItem>(
          '/aircraft/from-template/reference-650',
          { name: '我的 EduQuad-650', description: '由系统参考模板创建。' },
        )
        item = created.data
        aircraftLibrary.value = [item]
      }
      applyLibraryItem(item)
    } catch (caught) {
      error.value = errorMessage(caught)
    } finally {
      loading.value = false
    }
  }

  async function loadAircraft(aircraftId: number): Promise<void> {
    loading.value = true
    error.value = ''
    try {
      const response = await api.get<AssemblyState>(`/aircraft/${aircraftId}`)
      assemblyState.value = response.data
      activeAircraftId.value = aircraftId
      if (authStore.user) rememberAircraftId(authStore.user.id, aircraftId)
      selectedSlot.value = null
      selectedMountId.value = null
      pendingInstall.value = null
      saveStatus.value = 'saved'
      await refreshLibrary()
    } catch (caught) {
      error.value = errorMessage(caught)
      throw caught
    } finally {
      loading.value = false
    }
  }

  async function createFromTemplate(
    templateKey: string,
    name?: string,
    description = '',
  ): Promise<AircraftLibraryItem> {
    if (!canCreateAircraft.value) {
      throw new Error(`每个用户最多保存 ${aircraftLimit.value} 架飞机。`)
    }
    try {
      const response = await api.post<AircraftLibraryItem>(
        `/aircraft/from-template/${templateKey}`,
        { name: name?.trim() || null, description },
      )
      upsertLibraryItem(response.data)
      applyLibraryItem(response.data)
      lastSavedAt.value = new Date(response.data.updated_at)
      return response.data
    } catch (caught) {
      error.value = errorMessage(caught)
      throw new Error(error.value)
    }
  }

  async function duplicateAircraft(
    aircraftId: number,
    name?: string,
  ): Promise<AircraftLibraryItem> {
    if (!canCreateAircraft.value) {
      throw new Error(`每个用户最多保存 ${aircraftLimit.value} 架飞机。`)
    }
    try {
      const response = await api.post<AircraftLibraryItem>(
        `/aircraft/${aircraftId}/duplicate`,
        { name: name?.trim() || null },
      )
      upsertLibraryItem(response.data)
      return response.data
    } catch (caught) {
      error.value = errorMessage(caught)
      throw new Error(error.value)
    }
  }

  async function duplicateActive(name?: string): Promise<AircraftLibraryItem | null> {
    if (!activeAircraftId.value) return null
    const item = await duplicateAircraft(activeAircraftId.value, name)
    applyLibraryItem(item)
    return item
  }

  async function updateAircraftMetadata(
    aircraftId: number,
    update: AircraftMetadataUpdate,
  ): Promise<AircraftLibraryItem> {
    const response = await api.patch<AircraftLibraryItem>(
      `/aircraft/${aircraftId}/metadata`,
      update,
    )
    upsertLibraryItem(response.data)
    if (aircraftId === activeAircraftId.value) {
      applyLibraryItem(response.data)
    }
    lastSavedAt.value = new Date(response.data.updated_at)
    return response.data
  }

  async function deleteAircraft(aircraftId: number): Promise<void> {
    await api.delete(`/aircraft/${aircraftId}`)
    aircraftLibrary.value = aircraftLibrary.value.filter(
      item => item.aircraft.id !== aircraftId,
    )
    if (activeAircraftId.value === aircraftId) {
      const fallback = aircraftLibrary.value[0]
      if (fallback?.aircraft.id) {
        applyLibraryItem(fallback)
      } else {
        activeAircraftId.value = null
        assemblyState.value = null
      }
    }
  }

  function applySingleMountPosition(
    nextAircraft: AircraftDefinition,
    slot: AssemblySlot,
    component: Component,
  ): void {
    const frame = components.value.find(item => item.id === nextAircraft.frame_id) ?? null
    const mounts = frameMounts(frame)

    if (slot === 'payload') {
      const mount = component.parameters_json.mount
      const key = mount === 'front' ? 'payload_front' : 'payload_bottom'
      nextAircraft.payload_position_m = vectorFromUnknown(mounts?.[key]) ?? (
        mount === 'front'
          ? { x: 0.18, y: 0, z: -0.02 }
          : { x: 0.08, y: 0, z: -0.12 }
      )
    }
    if (slot === 'gnss') {
      nextAircraft.gnss_position_m = vectorFromUnknown(mounts?.gnss)
        ?? { x: -0.16, y: 0, z: 0.08 }
    }
  }

  /**
   * Compatibility / teacher shortcut: configure the selected catalog component
   * and physically populate every legal mount in one operation.
   */
  async function installComponent(
    slot: AssemblySlot,
    componentId: number,
  ): Promise<void> {
    if (!assemblyState.value) return
    const component = components.value.find(item => item.id === componentId)
    if (!component || component.type !== slot) return

    const current = assemblyState.value.aircraft
    const nextAircraft: AircraftDefinition = {
      ...current,
      [SLOT_FIELDS[slot]]: component.id,
    }
    const nextMounts = buildMountPoints(nextAircraft, components.value)
    nextAircraft.assembly_instances = replaceSlotInstances(
      current,
      nextMounts,
      slot,
      component.id,
    )
    applySingleMountPosition(nextAircraft, slot, component)

    await saveAircraft(nextAircraft)
    selectedSlot.value = slot
    selectedMountId.value = null
    pendingInstall.value = null
  }

  /**
   * Enter constrained 3D assembly mode.
   *
   * Selecting a new component intentionally removes the previous physical
   * instances for that slot while keeping the catalog choice. The student then
   * installs the component into each legal mount using the 3D scene.
   */
  async function beginMountAssembly(
    slot: AssemblySlot,
    componentId: number,
  ): Promise<void> {
    if (!assemblyState.value) return
    const component = components.value.find(item => item.id === componentId)
    if (!component || component.type !== slot) return

    if (slot === 'frame') {
      await installComponent(slot, componentId)
      return
    }

    const current = assemblyState.value.aircraft
    const existingCompletion = slotCompletion(current, slot)
    const sameCatalogComponent = current[SLOT_FIELDS[slot]] === component.id
    const canResumePartial =
      sameCatalogComponent &&
      existingCompletion.installed > 0 &&
      existingCompletion.installed < existingCompletion.total

    const nextAircraft: AircraftDefinition = {
      ...current,
      [SLOT_FIELDS[slot]]: component.id,
      assembly_instances: canResumePartial
        ? current.assembly_instances
        : clearSlotInstances(current, slot),
    }
    applySingleMountPosition(nextAircraft, slot, component)

    await saveAircraft(nextAircraft)
    pendingInstall.value = { slot, componentId }
    selectedSlot.value = slot
    selectedMountId.value = null
  }

  async function installAtMount(mountId: string): Promise<void> {
    if (!assemblyState.value || !pendingInstall.value) return
    const pending = pendingInstall.value
    const mount = mountPoints.value.find(item => item.id === mountId)
    if (!mount || mount.slot !== pending.slot) return

    const current = assemblyState.value.aircraft
    const nextAircraft: AircraftDefinition = {
      ...current,
      assembly_instances: installInstance(
        current,
        mount,
        pending.componentId,
      ),
    }

    await saveAircraft(nextAircraft)
    selectedSlot.value = mount.slot
    selectedMountId.value = mount.id
    installationSerial += 1
    lastInstallation.value = {
      mountId: mount.id,
      serial: installationSerial,
    }

    const completion = slotCompletion(assemblyState.value?.aircraft, mount.slot)
    if (completion.installed >= completion.total) {
      pendingInstall.value = null
    }
  }

  async function removeMount(mountId: string): Promise<void> {
    if (!assemblyState.value || removingMountId.value) return
    const mount = mountPoints.value.find(item => item.id === mountId)
    if (!mount || mount.slot === 'frame') return

    // Animate the real installed part away from its datum before persisting the
    // physical removal. This keeps visual state and database state ordered.
    installationSerial += 1
    removingMountId.value = mountId
    lastRemoval.value = {
      mountId,
      serial: installationSerial,
    }
    await new Promise(resolve => globalThis.setTimeout(resolve, 380))

    try {
      const current = assemblyState.value.aircraft
      const nextAircraft: AircraftDefinition = {
        ...current,
        assembly_instances: removeInstance(current, mountId),
      }
      await saveAircraft(nextAircraft)
      selectedSlot.value = mount.slot
      selectedMountId.value = mount.id
    } catch (caught) {
      // If persistence fails, visually return the still-installed real part to
      // its datum instead of leaving the scene in a detached-only state.
      installationSerial += 1
      lastInstallation.value = {
        mountId,
        serial: installationSerial,
      }
      throw caught
    } finally {
      removingMountId.value = null
    }
  }

  async function removeComponent(slot: AssemblySlot): Promise<void> {
    if (!assemblyState.value) return
    const current = assemblyState.value.aircraft
    const nextAircraft: AircraftDefinition = {
      ...current,
      [SLOT_FIELDS[slot]]: null,
      assembly_instances: clearSlotInstances(current, slot),
    }
    if (slot === 'payload') nextAircraft.payload_position_m = null
    if (slot === 'gnss') nextAircraft.gnss_position_m = null
    await saveAircraft(nextAircraft)
    selectedSlot.value = slot
    selectedMountId.value = null
    if (pendingInstall.value?.slot === slot) pendingInstall.value = null
  }

  function cancelMountAssembly(): void {
    pendingInstall.value = null
  }

  async function setPropellerDirection(
    motor: MotorName,
    direction: RotorDirection,
  ): Promise<void> {
    if (!assemblyState.value) return
    const nextAircraft: AircraftDefinition = {
      ...assemblyState.value.aircraft,
      propeller_directions: {
        M1: assemblyState.value.aircraft.propeller_directions?.M1 ?? 'CCW',
        M2: assemblyState.value.aircraft.propeller_directions?.M2 ?? 'CW',
        M3: assemblyState.value.aircraft.propeller_directions?.M3 ?? 'CCW',
        M4: assemblyState.value.aircraft.propeller_directions?.M4 ?? 'CW',
        [motor]: direction,
      },
    }
    await saveAircraft(nextAircraft)
    selectedSlot.value = 'propeller'
  }

  async function saveAircraft(nextAircraft: AircraftDefinition): Promise<void> {
    if (!activeAircraftId.value) return
    saving.value = true
    saveStatus.value = 'saving'
    error.value = ''
    try {
      const response = await api.put<AssemblyState>(
        `/aircraft/${activeAircraftId.value}`,
        nextAircraft,
      )
      assemblyState.value = response.data
      saveStatus.value = 'saved'
      lastSavedAt.value = new Date()
      void refreshLibrary()
    } catch (caught) {
      saveStatus.value = 'error'
      error.value = errorMessage(caught)
      throw caught
    } finally {
      saving.value = false
    }
  }

  async function refreshCalculation(): Promise<void> {
    if (!assemblyState.value || !activeAircraftId.value) return
    saving.value = true
    error.value = ''
    try {
      const response = await api.post<AssemblyState>(
        `/aircraft/${activeAircraftId.value}/calculate`,
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

  function componentForMount(mountId: string): Component | null {
    const componentId = instanceAtMount(aircraft.value ?? undefined, mountId)?.component_id
      ?? null
    return components.value.find(component => component.id === componentId) ?? null
  }

  function selectSlot(slot: AssemblySlot | null): void {
    selectedSlot.value = slot
    if (slot === null) selectedMountId.value = null
  }

  function selectMount(mountId: string | null): void {
    selectedMountId.value = mountId
    if (!mountId) return
    const mount = mountPoints.value.find(item => item.id === mountId)
    if (mount) selectedSlot.value = mount.slot
  }

  function completionForSlot(slot: AssemblySlot) {
    return slotCompletion(aircraft.value, slot)
  }

  return {
    components,
    aircraftLibrary,
    aircraftTemplates,
    activeAircraftId,
    activeLibraryItem,
    aircraftLimit,
    aircraftCount,
    canCreateAircraft,
    assemblyState,
    aircraft,
    engineering,
    validation,
    aircraftName,
    selectedSlot,
    selectedMountId,
    pendingInstall,
    lastInstallation,
    lastRemoval,
    removingMountId,
    mountPoints,
    loading,
    libraryLoading,
    saving,
    saveStatus,
    saveStatusZh,
    lastSavedAt,
    error,
    initialize,
    resetWorkspace,
    refreshComponents,
    refreshLibrary,
    refreshTemplates,
    loadAircraft,
    createFromTemplate,
    duplicateAircraft,
    duplicateActive,
    updateAircraftMetadata,
    deleteAircraft,
    installComponent,
    beginMountAssembly,
    installAtMount,
    removeMount,
    removeComponent,
    cancelMountAssembly,
    setPropellerDirection,
    refreshCalculation,
    componentForSlot,
    componentForMount,
    completionForSlot,
    selectSlot,
    selectMount,
  }
})
