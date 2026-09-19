import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api/client'
import type {
  ExperimentReplay,
  SimulationStatus,
  TelemetryFrame,
} from '../types/telemetry'
import { replayFrameIndex } from '../utils/replay'

export const useReplayStore = defineStore('replay', () => {
  const document = ref<ExperimentReplay | null>(null)
  const currentTime = ref(0)
  const playing = ref(false)
  const playbackRate = ref(1)
  const loading = ref(false)
  const error = ref('')
  let animationFrame = 0
  let wallStartTime = 0
  let timeAtPlay = 0

  const frames = computed(() => document.value?.frames ?? [])
  const duration = computed(() =>
    frames.value.length > 0 ? frames.value[frames.value.length - 1].t : 0,
  )
  const currentIndex = computed(() =>
    replayFrameIndex(frames.value, currentTime.value),
  )
  const currentFrame = computed<TelemetryFrame | null>(
    () => frames.value[currentIndex.value] ?? null,
  )
  const history = computed(() =>
    currentIndex.value >= 0
      ? frames.value.slice(0, currentIndex.value + 1)
      : [],
  )
  const status = computed<SimulationStatus>(() =>
    playing.value ? 'RUNNING' : 'PAUSED',
  )

  async function load(simulationId: number | string): Promise<void> {
    pause()
    loading.value = true
    error.value = ''
    try {
      const response = await api.get<ExperimentReplay>(
        `/experiments/${simulationId}`,
      )
      document.value = response.data
      currentTime.value = frames.value[0]?.t ?? 0
    } catch {
      error.value = '无法读取实验回放数据。'
      document.value = null
    } finally {
      loading.value = false
    }
  }

  function play(): void {
    if (!document.value || frames.value.length === 0 || playing.value) return
    if (currentTime.value >= duration.value) currentTime.value = 0
    playing.value = true
    timeAtPlay = currentTime.value
    wallStartTime = performance.now()
    animationFrame = requestAnimationFrame(tick)
  }

  function pause(): void {
    playing.value = false
    if (animationFrame) cancelAnimationFrame(animationFrame)
    animationFrame = 0
  }

  function reset(): void {
    pause()
    currentTime.value = frames.value[0]?.t ?? 0
  }

  function seek(seconds: number): void {
    currentTime.value = Math.max(0, Math.min(duration.value, seconds))
    if (playing.value) {
      timeAtPlay = currentTime.value
      wallStartTime = performance.now()
    }
  }

  function tick(now: number): void {
    if (!playing.value) return
    const elapsed = ((now - wallStartTime) / 1000) * playbackRate.value
    currentTime.value = Math.min(duration.value, timeAtPlay + elapsed)
    if (currentTime.value >= duration.value) {
      pause()
      return
    }
    animationFrame = requestAnimationFrame(tick)
  }

  function dispose(): void {
    pause()
    document.value = null
    currentTime.value = 0
  }

  return {
    document,
    frames,
    currentTime,
    duration,
    playing,
    playbackRate,
    loading,
    error,
    status,
    currentIndex,
    currentFrame,
    history,
    load,
    play,
    pause,
    reset,
    seek,
    dispose,
  }
})
