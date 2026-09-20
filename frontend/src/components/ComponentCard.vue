<template>
  <article
    class="component-card"
    :class="{ installed, selected, unavailable: !thumbnail }"
    data-testid="component-card"
    :data-component-id="component.id"
    :data-component-type="component.type"
    @click="emit('choose')"
  >
    <div class="component-card-media" data-testid="component-media">
      <img
        v-if="thumbnail"
        data-testid="component-thumbnail"
        :src="thumbnail"
        :alt="`${component.name} 缩略图`"
        loading="lazy"
      />
      <div v-else class="component-card-missing">
        缺少视觉资产
      </div>
      <span v-if="installed" class="component-card-installed">已安装</span>
    </div>

    <div class="component-card-body">
      <div class="component-card-title-row">
        <b data-testid="component-name">{{ component.name }}</b>
        <span data-testid="component-mass">{{ component.mass_kg.toFixed(3) }} kg</span>
      </div>

      <div class="component-card-specs">
        <span
          v-for="(spec, index) in specs"
          :key="`${component.id}-${spec}`"
          :data-testid="index === 0 ? 'component-primary-spec' : undefined"
        >
          {{ spec }}
        </span>
      </div>

      <div :class="['component-card-actions', { dual: secondaryActionLabel }]">
        <button
          class="component-card-action"
          data-testid="component-install"
          :disabled="disabled || installed || !thumbnail"
          @click.stop="emit('install')"
        >
          {{ installed ? '已安装' : actionLabel }}
        </button>
        <button
          v-if="secondaryActionLabel"
          class="component-card-action assembly-action"
          data-testid="component-3d-assemble"
          :disabled="disabled || secondaryDisabled || !thumbnail"
          @click.stop="emit('secondary')"
        >
          {{ secondaryActionLabel }}
        </button>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Component } from '../types/aircraft'
import { thumbnailForComponent } from '../three/assetRegistry'

const props = withDefaults(
  defineProps<{
    component: Component
    installed?: boolean
    selected?: boolean
    disabled?: boolean
    specs?: string[]
    actionLabel?: string
    secondaryActionLabel?: string
    secondaryDisabled?: boolean
  }>(),
  {
    installed: false,
    selected: false,
    disabled: false,
    specs: () => [],
    actionLabel: '快速配置',
    secondaryActionLabel: '',
    secondaryDisabled: false,
  },
)

const emit = defineEmits<{
  (event: 'choose'): void
  (event: 'install'): void
  (event: 'secondary'): void
}>()

const thumbnail = computed(() => {
  try {
    return thumbnailForComponent(props.component)
  } catch {
    return ''
  }
})
</script>

<style scoped>
.component-card {
  overflow: hidden;
  border: 1px solid #dfe6ef;
  border-radius: 8px;
  background: #fff;
  transition: border-color .15s ease, box-shadow .15s ease, transform .15s ease;
}
.component-card:hover {
  border-color: #9ec2f7;
  box-shadow: 0 4px 14px rgba(28, 67, 112, .08);
  transform: translateY(-1px);
}
.component-card.selected {
  border-color: #4b8fe8;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, .08);
}
.component-card.installed {
  border-color: #bfe7d1;
}
.component-card-media {
  position: relative;
  height: 136px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 8px;
  background: linear-gradient(180deg, #f7faff 0%, #edf3f9 100%);
  border-bottom: 1px solid #edf1f5;
}
.component-card-media img {
  display: block;
  width: auto;
  height: auto;
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  object-position: center center;
  transform: none;
}
.component-card-missing {
  color: #b42318;
  font-size: 11px;
  font-weight: 700;
}
.component-card-installed {
  position: absolute;
  top: 7px;
  right: 7px;
  padding: 3px 7px;
  border-radius: 10px;
  background: rgba(234, 249, 241, .94);
  color: #137445;
  font-size: 10px;
  font-weight: 800;
}
.component-card-body {
  padding: 9px;
}
.component-card-title-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: start;
}
.component-card-title-row b {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #22344c;
  font-size: 11px;
}
.component-card-title-row span {
  color: #6e7c90;
  font-size: 9px;
  white-space: nowrap;
}
.component-card-specs {
  min-height: 34px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-content: flex-start;
  margin: 7px 0;
}
.component-card-specs span {
  padding: 3px 5px;
  border-radius: 4px;
  background: #f3f6fa;
  color: #56667d;
  font-size: 9px;
}
.component-card-actions {
  display: grid;
  gap: 6px;
}
.component-card-actions.dual {
  grid-template-columns: minmax(0, .84fr) minmax(0, 1.16fr);
}
.component-card-action {
  width: 100%;
  border: 1px solid #cbd9e8;
  border-radius: 6px;
  background: #f8fbff;
  color: #245da5;
  padding: 7px 7px;
  font-size: 9px;
  font-weight: 800;
  white-space: nowrap;
}
.component-card-action.assembly-action {
  border-color: #8bb8f8;
  background: linear-gradient(180deg, #eef6ff, #e6f1ff);
  color: #1459ac;
}
.component-card.selected .component-card-action.assembly-action:not(:disabled) {
  border-color: #2563eb;
  background: #2563eb;
  color: #fff;
}
.component-card-action:disabled {
  cursor: not-allowed;
  opacity: .55;
}
.component-card.unavailable {
  border-color: #efc5c0;
}
</style>
