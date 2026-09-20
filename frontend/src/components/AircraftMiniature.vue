<template>
  <div class="aircraft-miniature" data-testid="aircraft-miniature">
    <img
      v-if="previewUrl"
      :src="previewUrl"
      :alt="`${aircraft.name} 3D 缩略图`"
      draggable="false"
    />
    <div v-if="loading" class="mini-loading">生成 3D 缩略图…</div>
    <div v-if="error" class="mini-error">3D 预览不可用</div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { AircraftDefinition, Component } from '../types/aircraft'
import { aircraftPreviewDataUrl } from '../three/aircraftPreview'

const props = defineProps<{
  aircraft: AircraftDefinition
  components: Component[]
}>()

const loading = ref(false)
const error = ref(false)
const previewUrl = ref('')
let generation = 0

async function rebuild(): Promise<void> {
  const current = ++generation
  loading.value = true
  error.value = false
  try {
    const url = await aircraftPreviewDataUrl(props.aircraft, props.components)
    if (current !== generation) return
    previewUrl.value = url
  } catch (caught) {
    if (current !== generation) return
    console.warn('[UAV Studio] aircraft miniature failed:', caught)
    previewUrl.value = ''
    error.value = true
  } finally {
    if (current === generation) loading.value = false
  }
}

watch(
  () => [
    props.aircraft,
    props.components.map(item => `${item.id}:${item.visual?.asset_key ?? ''}`).join('|'),
  ] as const,
  () => { void rebuild() },
  { deep: true, immediate: true },
)
</script>

<style scoped>
.aircraft-miniature {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 170px;
  overflow: hidden;
  background:
    radial-gradient(circle at 50% 44%, rgba(255,255,255,.98), rgba(240,246,253,.84) 48%, rgba(226,236,248,.76) 100%),
    linear-gradient(180deg, #f8fbff, #eaf1f9);
}
.aircraft-miniature::after {
  content: '';
  position: absolute;
  left: 16%;
  right: 16%;
  bottom: 13%;
  height: 12px;
  border-radius: 50%;
  background: rgba(35, 58, 83, .10);
  filter: blur(9px);
  pointer-events: none;
}
.aircraft-miniature img {
  position: relative;
  z-index: 1;
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  user-select: none;
}
.mini-loading,
.mini-error {
  position: absolute;
  z-index: 2;
  left: 10px;
  bottom: 9px;
  padding: 4px 7px;
  border-radius: 999px;
  background: rgba(255,255,255,.82);
  color: #6a7a8f;
  font-size: 8px;
  backdrop-filter: blur(8px);
}
.mini-error { color: #a9443c; }
</style>
