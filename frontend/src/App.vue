<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand brand-campus">
        <img class="campus-mark" src="/branding/zjitc-campus-mark.svg" alt="浙江工贸" />
        <div class="brand-copy">
          <div class="brand-mainline"><strong>UAV Studio</strong><span>浙江工贸</span></div>
          <small>无人机数字设计与飞行验证平台</small>
        </div>
      </div>

      <nav>
        <RouterLink to="/assembly">无人机装配</RouterLink>
        <RouterLink to="/flight">飞行实验</RouterLink>
        <RouterLink to="/history">实验记录</RouterLink>
        <RouterLink to="/components">组件库</RouterLink>
        <RouterLink to="/settings">系统设置</RouterLink>
      </nav>

      <div class="top-status">
        <span class="aircraft-chip">{{ assemblyStore.aircraftName }}</span>
        <span class="status-pill info">{{ simulationStore.simulationStatusZh }}</span>
        <RouterLink class="user-chip" to="/settings" title="账户与系统设置">{{ settingsStore.username }}</RouterLink>
      </div>
    </header>
    <RouterView />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAssemblyStore } from './stores/assembly'
import { useSimulationStore } from './stores/simulation'
import { useSettingsStore } from './stores/settings'

const simulationStore = useSimulationStore()
const assemblyStore = useAssemblyStore()
const settingsStore = useSettingsStore()

onMounted(() => {
  void Promise.all([
    assemblyStore.initialize(),
    settingsStore.initialize(),
  ])
})
</script>

<style scoped>
.brand-campus { min-width:0; display:flex; align-items:center; gap:8px; }
.campus-mark { display:block; width:28px; height:28px; flex:0 0 28px; border-radius:7px; }
.brand-copy { min-width:0; display:grid; gap:1px; }
.brand-mainline { min-width:0; display:flex; align-items:center; gap:6px; }
.brand-mainline strong { color:#f8fbff; font-size:16px; line-height:18px; font-weight:800; letter-spacing:-.02em; white-space:nowrap; }
.brand-mainline span { flex:0 0 auto; padding:1px 6px; border-radius:999px; border:1px solid rgba(98,205,238,.24); background:rgba(51,179,222,.12); color:#8ae8ff; font-size:9px; line-height:15px; font-weight:700; }
.brand-copy small { display:block; min-width:0; margin:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:rgba(222,233,249,.72); font-size:9px; line-height:12px; font-weight:500; }
.user-chip { display:grid; place-items:center; min-width:38px; height:30px; padding:0 9px; border:1px solid rgba(151,177,211,.20); border-radius:999px; background:rgba(255,255,255,.07); color:#dcecff; text-decoration:none; font-size:10px; font-weight:700; }
.user-chip.router-link-active { border-color:rgba(103,232,249,.28); color:#cffafe; background:rgba(8,145,178,.12); }
@media(max-width:1280px){.brand-mainline span{display:none}.user-chip{display:none}}
</style>
