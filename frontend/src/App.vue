<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand">UAV Studio <small>无人机数字设计与飞行验证平台</small></div>
      <nav>
        <RouterLink to="/assembly">无人机装配</RouterLink>
        <RouterLink to="/flight">飞行实验</RouterLink>
        <RouterLink to="/history">实验记录</RouterLink>
      </nav>
      <div class="top-status">
        <span class="aircraft-chip">{{ assemblyStore.aircraftName }}</span>
        <span class="status-pill info">{{ store.simulationStatusZh }}</span>
      </div>
    </header>
    <RouterView />
  </div>
</template>
<script setup lang="ts">
import { onMounted } from 'vue'
import { useAssemblyStore } from './stores/assembly'
import { useSimulationStore } from './stores/simulation'
const store = useSimulationStore()
const assemblyStore = useAssemblyStore()

onMounted(() => {
  void assemblyStore.initialize()
})
</script>
