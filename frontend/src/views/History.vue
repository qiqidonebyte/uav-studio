<template>
  <div class="history-page">
    <div class="history-head">
      <div>
        <h2>实验记录</h2>
        <p>保存的无人机仿真实验与 Replay 数据。</p>
      </div>
      <button :disabled="store.loading" @click="store.loadExperiments">
        {{ store.loading ? '正在刷新…' : '刷新' }}
      </button>
    </div>

    <p v-if="store.error" class="record-error">{{ store.error }}</p>

    <div class="history-table">
      <div class="history-row history-header">
        <span>时间</span>
        <span>飞机</span>
        <span>时长</span>
        <span>最大高度</span>
        <span>帧数</span>
        <span>状态</span>
        <span>操作</span>
      </div>
      <div
        v-for="record in store.experiments"
        :key="record.id"
        class="history-row"
      >
        <span>{{ formatDate(record.started_at) }}</span>
        <span>{{ record.aircraft_name }}</span>
        <span>{{ formatDuration(record.duration_s) }}</span>
        <span>{{ record.max_altitude_m.toFixed(2) }} m</span>
        <span>{{ record.frame_count }}</span>
        <span><b class="status-pill ok">已完成</b></span>
        <span><RouterLink :to="`/history/${record.id}`">查看 / 回放</RouterLink></span>
      </div>
      <div v-if="!store.loading && store.experiments.length === 0" class="history-empty">
        暂无实验记录。完成一次飞行实验并停止后，记录会显示在这里。
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useExperimentsStore } from '../stores/experiments'

const store = useExperimentsStore()

onMounted(() => {
  void store.loadExperiments()
})

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const remainder = seconds - minutes * 60
  return `${String(minutes).padStart(2, '0')}:${remainder.toFixed(1).padStart(4, '0')}`
}
</script>
