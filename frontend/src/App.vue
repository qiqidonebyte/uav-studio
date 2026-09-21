<template>
  <RouterView v-if="!authStore.authenticated" />

  <div v-else class="app-shell">
    <header class="topbar">
      <div class="brand brand-campus">
        <img class="campus-mark" src="/branding/zjitc-campus-mark.svg" alt="浙江工贸" />
        <div class="brand-copy">
          <div class="brand-mainline"><strong>UAV Studio</strong><span>浙江工贸</span></div>
          <small>无人机数字设计与装调检修教学平台</small>
        </div>
      </div>

      <nav>
        <RouterLink v-if="authStore.user?.role === 'student'" to="/training">我的实训</RouterLink>
        <RouterLink to="/assembly">无人机装配</RouterLink>
        <RouterLink to="/debugging">系统调试</RouterLink>
        <RouterLink to="/flight">飞行实验</RouterLink>
        <RouterLink to="/review">训练复盘</RouterLink>
        <RouterLink to="/history">实验记录</RouterLink>
        <RouterLink to="/components">组件库</RouterLink>
        <RouterLink v-if="isTeacherRole" to="/teacher">教师工作台</RouterLink>
        <RouterLink to="/settings">系统设置</RouterLink>
      </nav>

      <div class="top-status">
        <div v-if="route.path === '/debugging'" class="debug-bridge-chips">
          <span><i></i>PX4 SITL · 教学模拟</span>
          <span class="muted"><i></i>Gazebo · 待接入</span>
        </div>
        <RouterLink
          class="aircraft-chip aircraft-link design-switcher"
          to="/aircraft"
          :title="`进入飞机设计库 · ${saveTitle}`"
        >
          <span class="design-switcher-copy">
            <b>我的飞机</b>
            <small>当前：{{ assemblyStore.aircraftName }}</small>
          </span>
          <span :class="['save-pill', assemblyStore.saveStatus]">
            <i></i>{{ assemblyStore.saveStatusZh }}
          </span>
          <span class="design-switcher-arrow" aria-hidden="true">›</span>
        </RouterLink>
        <span class="status-pill info">{{ simulationStore.simulationStatusZh }}</span>
        <RouterLink class="user-chip" to="/settings" title="账户与系统设置">
          <span>{{ authStore.user?.display_name || authStore.user?.username }}</span>
          <small>{{ roleLabel }}</small>
        </RouterLink>
        <button class="logout-chip" title="退出登录" @click="logout">退出</button>
      </div>
    </header>
    <LearningTaskNav :role="learningRole" @open-guide="guideOpen = true" />
    <RouterView />
    <LearningGuidePanel :open="guideOpen" :role="learningRole" @close="guideOpen = false" />
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { useAssemblyStore } from './stores/assembly'
import { useSimulationStore } from './stores/simulation'
import { useSettingsStore } from './stores/settings'
import LearningTaskNav from './components/LearningTaskNav.vue'
import LearningGuidePanel from './components/LearningGuidePanel.vue'
import type { LearningRole } from './utils/learningGuide'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const simulationStore = useSimulationStore()
const assemblyStore = useAssemblyStore()
const settingsStore = useSettingsStore()
const guideOpen = ref(false)
const learningRole = computed<LearningRole>(() => {
  const role = authStore.user?.role
  return role === 'teacher' || role === 'admin' ? role : 'student'
})

const roleLabel = computed(() => {
  if (authStore.user?.role === 'admin') return '管理员'
  if (authStore.user?.role === 'teacher') return '教师'
  return '学生'
})

const isTeacherRole = computed(() => ['teacher', 'admin'].includes(String(authStore.user?.role ?? 'student')))

const saveTitle = computed(() => {
  if (assemblyStore.saveStatus === 'saving') return '设计正在自动保存到本地 SQLite'
  if (assemblyStore.saveStatus === 'error') return '自动保存失败，请检查后端服务'
  const saved = assemblyStore.lastSavedAt
  return saved
    ? `已自动保存 · ${saved.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}`
    : '当前设计已保存'
})

async function initializeWorkspace(): Promise<void> {
  if (!authStore.authenticated) return
  await Promise.all([
    assemblyStore.initialize(),
    settingsStore.initialize(),
  ])
}

async function logout(): Promise<void> {
  simulationStore.resetForLogout()
  try {
    await authStore.logout()
  } finally {
    assemblyStore.resetWorkspace()
    settingsStore.resetForLogout()
    await router.replace('/login')
  }
}

function onAuthExpired(): void {
  if (!authStore.authenticated) return
  authStore.clearSession()
  simulationStore.resetForLogout()
  assemblyStore.resetWorkspace()
  settingsStore.resetForLogout()
  void router.replace({ path: '/login', query: { expired: '1' } })
}

watch(
  () => authStore.user?.id,
  () => { void initializeWorkspace() },
  { immediate: true },
)

watch(() => route.fullPath, () => { guideOpen.value = false })

onMounted(() => {
  globalThis.addEventListener?.('uav-auth-expired', onAuthExpired)
})

onBeforeUnmount(() => {
  globalThis.removeEventListener?.('uav-auth-expired', onAuthExpired)
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
.aircraft-link { text-decoration:none; }
.debug-bridge-chips{display:flex;align-items:center;gap:5px}.debug-bridge-chips span{display:inline-flex;align-items:center;gap:5px;height:25px;padding:0 8px;border:1px solid rgba(78,210,140,.22);border-radius:999px;background:rgba(34,132,83,.10);color:#83e9b0;font-size:8px;font-weight:800;white-space:nowrap}.debug-bridge-chips span.muted{border-color:rgba(125,149,182,.18);background:rgba(255,255,255,.04);color:#8ba6be}.debug-bridge-chips i{width:6px;height:6px;border-radius:50%;background:#53dd91}.debug-bridge-chips .muted i{background:#e6b64d}
.design-switcher {display:flex;align-items:center;gap:9px;min-width:0;min-height:38px;padding:4px 8px 4px 11px;border-radius:10px;transition:background .18s ease,border-color .18s ease,transform .18s ease}
.design-switcher:hover {transform:translateY(-1px);border-color:rgba(103,232,249,.28);background:rgba(255,255,255,.10)}
.design-switcher.router-link-active {border-color:rgba(103,232,249,.30);background:rgba(8,145,178,.13)}
.design-switcher-copy {min-width:0;display:grid;gap:1px;text-align:left}
.design-switcher-copy b {color:#f2f8ff;font-size:10px;line-height:13px;font-weight:800}
.design-switcher-copy small {max-width:150px;overflow:hidden;color:rgba(220,236,255,.68);font-size:8px;line-height:11px;text-overflow:ellipsis;white-space:nowrap}
.design-switcher-arrow {color:rgba(207,250,254,.75);font-size:16px;line-height:1}
.save-pill {display:inline-flex;align-items:center;gap:5px;height:24px;padding:0 7px;border:1px solid rgba(125,149,182,.20);border-radius:999px;background:rgba(255,255,255,.05);color:#dcecff;font-size:9px;font-weight:700;white-space:nowrap}
.save-pill i { width:6px; height:6px; border-radius:50%; background:#61d394; }
.save-pill.saving i { background:#64b5ff; animation:savePulse 1s ease-in-out infinite; }
.save-pill.error { color:#ffd8d2; border-color:rgba(248,113,113,.25); }
.save-pill.error i { background:#fb7185; }
.user-chip {display:flex;align-items:center;gap:5px;min-width:48px;height:30px;padding:0 9px;border:1px solid rgba(151,177,211,.20);border-radius:999px;background:rgba(255,255,255,.07);color:#dcecff;text-decoration:none;font-size:9px;font-weight:700}
.user-chip small {padding:1px 4px;border-radius:999px;background:rgba(255,255,255,.08);color:rgba(220,236,255,.64);font-size:7px}
.user-chip.router-link-active { border-color:rgba(103,232,249,.28); color:#cffafe; background:rgba(8,145,178,.12); }
.logout-chip{height:30px;border:1px solid rgba(151,177,211,.18);border-radius:999px;background:transparent;color:rgba(220,236,255,.72);padding:0 8px;font-size:8px;font-weight:700;cursor:pointer}.logout-chip:hover{border-color:rgba(248,113,113,.3);background:rgba(248,113,113,.08);color:#ffd6d1}
@keyframes savePulse { 50% { opacity:.45; transform:scale(.75); } }
@media(max-width:1600px){.debug-bridge-chips{display:none}}
@media(max-width:1500px){.design-switcher .save-pill{display:none}.topbar nav{gap:4px}.topbar nav a{padding:0 6px;font-size:9px}}
@media(max-width:1320px){.brand-mainline span{display:none}.user-chip small,.logout-chip{display:none}.brand-copy small{max-width:150px}}
</style>
