<template>
  <div class="settings-page">
    <aside class="settings-nav panel">
      <div class="settings-user">
        <span class="settings-avatar">{{ avatarText }}</span>
        <div>
          <b>{{ store.displayName || store.username }}</b>
          <small>{{ roleLabel }} · @{{ store.username }}</small>
        </div>
      </div>
      <button
        v-for="item in sections"
        :key="item.id"
        :class="{ active: active === item.id }"
        @click="active = item.id"
      >
        <span>{{ item.label }}</span><small>{{ item.hint }}</small>
      </button>
    </aside>

    <main class="settings-content panel">
      <div class="settings-head">
        <div><h2>{{ activeSection.label }}</h2><p>{{ activeSection.description }}</p></div>
        <div v-if="active !== 'account' && active !== 'about'" class="settings-actions">
          <span v-if="savedMessage" class="save-ok">{{ savedMessage }}</span>
          <button class="primary-action compact" :disabled="store.saving" @click="saveSettings">
            {{ store.saving ? '保存中…' : '保存设置' }}
          </button>
        </div>
      </div>

      <section v-if="active === 'account'" class="settings-section">
        <div class="settings-card account-card">
          <div class="account-head">
            <span class="account-avatar">{{ avatarText }}</span>
            <div>
              <h3>{{ store.displayName || store.username }}</h3>
              <p>@{{ store.username }} · {{ roleLabel }}</p>
            </div>
          </div>
          <div class="account-facts">
            <div><span>账号 ID</span><b>#{{ auth.user?.id ?? '—' }}</b></div>
            <div><span>飞机额度</span><b>{{ aircraftStore.aircraftCount }} / {{ auth.aircraftLimit }}</b></div>
            <div><span>账号类型</span><b>{{ roleLabel }}</b></div>
          </div>
          <p class="settings-note">飞机、实验记录和个人设置现在按账号隔离。普通设计修改会自动保存到当前账号的工作空间。</p>
        </div>

        <div class="settings-card narrow">
          <h3>修改密码</h3>
          <label class="setting-field"><span>当前密码</span><input v-model="password.current" type="password" autocomplete="current-password" /></label>
          <label class="setting-field"><span>新密码</span><input v-model="password.next" type="password" autocomplete="new-password" /></label>
          <label class="setting-field"><span>确认新密码</span><input v-model="password.confirm" type="password" autocomplete="new-password" /></label>
          <p v-if="passwordMessage" :class="['password-message', { error: passwordError }]">{{ passwordMessage }}</p>
          <button class="primary-action compact" :disabled="changingPassword" @click="changePassword">
            {{ changingPassword ? '修改中…' : '修改密码' }}
          </button>
        </div>

        <div class="settings-card account-session-card">
          <div>
            <h3>登录状态</h3>
            <p>当前账号为 <b>{{ store.displayName || store.username }}</b>。退出后需要重新登录才能继续使用工作空间。</p>
          </div>
          <button
            class="logout-account-button"
            data-testid="settings-logout"
            :disabled="loggingOut"
            @click="logout"
          >
            {{ loggingOut ? '正在退出…' : '退出登录' }}
          </button>
        </div>
      </section>

      <section v-else-if="active === 'general'" class="settings-section">
        <div class="settings-card">
          <h3>显示与工作流</h3>
          <div class="setting-grid">
            <label class="setting-field"><span>单位制</span><select v-model="store.settings.general.unit_system"><option value="metric">公制 Metric</option></select></label>
            <label class="setting-field"><span>数值小数位</span><input v-model.number="store.settings.general.decimal_places" type="number" min="0" max="4" /></label>
            <label class="setting-field"><span>默认进入页面</span><select v-model="store.settings.general.default_page"><option value="assembly">无人机装配</option><option value="flight">飞行实验</option><option value="history">实验记录</option><option value="components">组件库</option></select></label>
          </div>
          <label class="toggle-row"><input v-model="store.settings.general.confirm_dangerous_actions" type="checkbox" /><span><b>危险操作确认</b><small>删除/覆盖等操作执行前再次确认</small></span></label>
        </div>
      </section>

      <section v-else-if="active === 'display'" class="settings-section">
        <div class="settings-card">
          <h3>3D 渲染</h3>
          <div class="setting-grid">
            <label class="setting-field"><span>渲染质量</span><select v-model="store.settings.display_3d.quality"><option value="performance">性能优先</option><option value="balanced">平衡</option><option value="high">高质量</option></select></label>
            <label class="setting-field"><span>阴影质量</span><select v-model="store.settings.display_3d.shadows"><option value="off">关闭</option><option value="low">低</option><option value="medium">中</option><option value="high">高</option></select></label>
            <label class="setting-field"><span>默认相机</span><select v-model="store.settings.display_3d.default_camera"><option value="free">自由</option><option value="follow">跟随</option><option value="top">俯视</option><option value="side">侧视</option></select></label>
            <label class="setting-field"><span>轨迹最大点数</span><input v-model.number="store.settings.display_3d.trajectory_points" type="number" min="100" max="2000" step="100" /></label>
          </div>
        </div>
        <div class="settings-card">
          <h3>工程辅助显示</h3>
          <div class="toggle-grid">
            <label class="toggle-row"><input v-model="store.settings.display_3d.antialias" type="checkbox" /><span><b>抗锯齿</b><small>新建 3D 场景时生效</small></span></label>
            <label class="toggle-row"><input v-model="store.settings.display_3d.environment_reflection" type="checkbox" /><span><b>环境反射</b><small>提高组件材质层次</small></span></label>
            <label class="toggle-row"><input v-model="store.settings.display_3d.show_grid" type="checkbox" /><span><b>工程网格</b><small>显示地面参考网格</small></span></label>
            <label class="toggle-row"><input v-model="store.settings.display_3d.show_axes" type="checkbox" /><span><b>坐标轴</b><small>显示 X/Y/Z 参考轴</small></span></label>
            <label class="toggle-row"><input v-model="store.settings.display_3d.show_cg" type="checkbox" /><span><b>重心 CG</b><small>显示整机重心</small></span></label>
            <label class="toggle-row"><input v-model="store.settings.display_3d.show_thrust_vectors" type="checkbox" /><span><b>推力向量</b><small>显示 M1-M4 推力箭头</small></span></label>
            <label class="toggle-row"><input v-model="store.settings.display_3d.show_gravity_vector" type="checkbox" /><span><b>重力向量</b><small>显示重力箭头</small></span></label>
            <label class="toggle-row"><input v-model="store.settings.display_3d.show_wind_vector" type="checkbox" /><span><b>风向量</b><small>显示风向和强度</small></span></label>
            <label class="toggle-row"><input v-model="store.settings.display_3d.show_trajectory" type="checkbox" /><span><b>飞行轨迹</b><small>显示 3D 历史轨迹</small></span></label>
          </div>
        </div>
      </section>

      <section v-else-if="active === 'flight'" class="settings-section">
        <div class="settings-card">
          <h3>默认实验参数</h3>
          <div class="setting-grid">
            <label class="setting-field"><span>默认目标高度 (m)</span><input v-model.number="store.settings.flight.default_altitude_m" type="number" min="0.5" max="120" step="0.5" /></label>
            <label class="setting-field"><span>默认风速 (m/s)</span><input v-model.number="store.settings.flight.default_wind_speed_mps" type="number" min="0" max="30" step="0.5" /></label>
            <label class="setting-field"><span>默认风向 (°)</span><input v-model.number="store.settings.flight.default_wind_direction_deg" type="number" min="0" max="360" step="1" /></label>
            <label class="setting-field"><span>默认视图</span><select v-model="store.settings.flight.default_view"><option value="3d">三维视图</option><option value="map">基础地图</option><option value="split">分屏</option></select></label>
            <label class="setting-field"><span>实时图表窗口 (s)</span><input v-model.number="store.settings.flight.chart_window_seconds" type="number" min="10" max="300" step="10" /></label>
          </div>
        </div>
        <div class="settings-card">
          <h3>实验行为</h3>
          <label class="toggle-row"><input v-model="store.settings.flight.auto_create_simulation" type="checkbox" /><span><b>进入页面自动创建仿真</b><small>默认关闭；不会自动解锁或起飞</small></span></label>
          <label class="toggle-row"><input v-model="store.settings.flight.auto_connect_telemetry" type="checkbox" /><span><b>自动连接遥测</b><small>创建仿真后连接 WebSocket</small></span></label>
          <p class="settings-note safety-note">安全顺序固定为：开始 → 解锁 → 起飞 → 降落。设置页不会提供“自动解锁/自动起飞”。</p>
        </div>
      </section>

      <section v-else class="settings-section">
        <div class="about-card">
          <div class="about-brand"><img src="/branding/zjitc-campus-mark.svg" alt="浙江工贸" /><div><b>UAV Studio</b><span>无人机数字设计与飞行验证平台</span></div></div>
          <dl>
            <div><dt>建设单位</dt><dd>浙江工贸职业技术学院</dd></div>
            <div><dt>作者</dt><dd>小龙老师</dd></div>
            <div><dt>产品版本</dt><dd>Accounts & Workspace V1</dd></div>
            <div><dt>账户模型</dt><dd>Cookie Session · 用户飞机隔离 · 每用户最多 10 架</dd></div>
            <div><dt>技术栈</dt><dd>Vue 3 · Three.js · FastAPI · NumPy · SQLite</dd></div>
            <div><dt>产品边界</dt><dd>数字装配 · 工程校核 · 基础飞行验证 · Local Flight Map · Replay</dd></div>
          </dl>
        </div>
      </section>

      <p v-if="store.error" class="settings-global-error">{{ store.error }}</p>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useAssemblyStore } from '../stores/assembly'
import { useSimulationStore } from '../stores/simulation'
import { useSettingsStore } from '../stores/settings'

const router = useRouter()
const auth = useAuthStore()
const aircraftStore = useAssemblyStore()
const simulationStore = useSimulationStore()
const store = useSettingsStore()
const active = ref<'account' | 'general' | 'display' | 'flight' | 'about'>('general')
const changingPassword = ref(false)
const loggingOut = ref(false)
const passwordMessage = ref('')
const passwordError = ref(false)
const savedMessage = ref('')
const password = reactive({ current: '', next: '', confirm: '' })

const roleLabel = computed(() => auth.user?.role === 'admin' ? '管理员' : auth.user?.role === 'teacher' ? '教师' : '用户')
const avatarText = computed(() => (store.displayName || store.username || 'U').slice(0, 1).toUpperCase())

const sections = [
  { id: 'account', label: '账户与密码', hint: '个人账号', description: '查看当前账号、飞机额度并修改密码。' },
  { id: 'general', label: '通用设置', hint: '单位与默认页', description: '控制当前账号的通用显示和默认工作流。' },
  { id: 'display', label: '3D 显示', hint: '质量与辅助信息', description: '控制当前账号的 Three.js 渲染质量与工程辅助元素。' },
  { id: 'flight', label: '飞行实验', hint: '默认实验参数', description: '设置当前账号进入飞行实验时使用的默认参数。' },
  { id: 'about', label: '关于', hint: '版本信息', description: 'UAV Studio 版本与项目范围。' },
] as const

const activeSection = computed(() => sections.find(item => item.id === active.value) ?? sections[1])

onMounted(async () => { await Promise.all([store.initialize(), aircraftStore.initialize()]) })

async function saveSettings(): Promise<void> {
  savedMessage.value = ''
  await store.save()
  savedMessage.value = '已保存'
  globalThis.setTimeout(() => { savedMessage.value = '' }, 1800)
}

async function changePassword(): Promise<void> {
  passwordMessage.value = ''
  passwordError.value = false
  if (password.next.length < 6) {
    passwordMessage.value = '新密码至少 6 位。'
    passwordError.value = true
    return
  }
  if (password.next !== password.confirm) {
    passwordMessage.value = '两次输入的新密码不一致。'
    passwordError.value = true
    return
  }
  changingPassword.value = true
  try {
    await store.changePassword(password.current, password.next)
    password.current = ''
    password.next = ''
    password.confirm = ''
    passwordMessage.value = '密码修改成功。'
  } catch {
    passwordMessage.value = store.error || '密码修改失败。'
    passwordError.value = true
  } finally {
    changingPassword.value = false
  }
}

async function logout(): Promise<void> {
  if (loggingOut.value) return
  loggingOut.value = true
  simulationStore.resetForLogout()
  try {
    await auth.logout()
  } finally {
    aircraftStore.resetWorkspace()
    store.resetForLogout()
    await router.replace('/login')
    loggingOut.value = false
  }
}
</script>

<style scoped>
.settings-page{height:calc(100vh - 56px);display:grid;grid-template-columns:220px minmax(0,1fr);gap:12px;padding:12px;overflow:hidden}.settings-nav{padding:10px;overflow:auto}.settings-user{display:flex;align-items:center;gap:9px;padding:10px;margin-bottom:10px;border-bottom:1px solid #e9eef5}.settings-avatar,.account-avatar{display:grid;place-items:center;border-radius:50%;background:#1f5da8;color:#fff;font-weight:800}.settings-avatar{width:32px;height:32px}.account-avatar{width:46px;height:46px;font-size:16px}.settings-user b{display:block;color:#24364e;font-size:12px}.settings-user small{display:block;margin-top:2px;color:#8390a1;font-size:8px}.settings-nav>button{width:100%;display:grid;gap:2px;padding:10px;border:1px solid transparent;border-radius:7px;background:transparent;text-align:left;color:#53647a}.settings-nav>button:hover{background:#f7f9fc}.settings-nav>button.active{background:#eef5ff;border-color:#dce9fb;color:#1f5da8}.settings-nav>button span{font-size:11px;font-weight:700}.settings-nav>button small{font-size:8px;color:#8a96a6}.settings-content{position:relative;overflow:auto;padding:18px}.settings-head{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-bottom:14px;border-bottom:1px solid #e8edf4}.settings-head h2{margin:0;color:#192b42;font-size:18px}.settings-head p{margin:4px 0 0;color:#718096;font-size:10px}.settings-actions{display:flex;align-items:center;gap:8px}.settings-actions button{width:auto;margin:0}.save-ok{color:#137445;font-size:10px}.settings-section{display:grid;gap:12px;padding-top:14px}.settings-card,.about-card{border:1px solid #e0e7f0;border-radius:8px;background:#fff;padding:14px}.settings-card.narrow{max-width:560px}.settings-card h3{margin:0 0 12px;color:#2a3d55;font-size:13px}.account-card{max-width:720px}.account-head{display:flex;align-items:center;gap:11px}.account-head h3{margin:0;color:#233b57;font-size:15px}.account-head p{margin:3px 0 0;color:#8190a2;font-size:9px}.account-facts{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:14px 0}.account-facts div{display:grid;gap:3px;padding:9px;border:1px solid #e5ebf2;border-radius:7px;background:#f9fbfd}.account-facts span{color:#8794a4;font-size:8px}.account-facts b{color:#38516e;font-size:10px}.setting-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.setting-field{display:grid;gap:5px;color:#5e6f84;font-size:10px}.setting-field input,.setting-field select{width:100%;min-width:0;box-sizing:border-box;border:1px solid #d7e1ed;border-radius:6px;background:#fff;padding:8px 9px;color:#26384f;font:inherit;outline:none}.setting-field input:focus,.setting-field select:focus{border-color:#7ba9e9;box-shadow:0 0 0 2px rgba(37,99,235,.06)}.toggle-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}.toggle-row{display:flex;align-items:flex-start;gap:8px;padding:9px;border:1px solid #e7ecf3;border-radius:7px;background:#fbfcfe}.toggle-row input{margin-top:2px;accent-color:#2563eb}.toggle-row b{display:block;color:#32465f;font-size:10px}.toggle-row small{display:block;margin-top:2px;color:#8592a3;font-size:8px;line-height:1.4}.settings-note{margin:0 0 12px;padding:9px;border-radius:6px;background:#f6f9fd;color:#6d7d91;font-size:9px;line-height:1.5}.account-card .settings-note{margin:0}.safety-note{margin-top:9px;margin-bottom:0;color:#745b2c;background:#fff9ed}.password-message{margin:8px 0 0;padding:7px;border-radius:5px;background:#eefaf4;color:#137445;font-size:9px}.password-message.error,.settings-global-error{background:#fff1f0;color:#b42318}.settings-global-error{position:sticky;bottom:0;margin:12px 0 0;padding:9px;border-radius:6px;font-size:10px}.about-card{max-width:780px}.about-brand{display:flex;align-items:center;gap:12px;margin-bottom:16px}.about-brand img{width:44px;height:44px}.about-brand b{display:block;color:#1d3049;font-size:18px}.about-brand span{display:block;margin-top:3px;color:#708096;font-size:10px}.about-card dl{margin:0}.about-card dl>div{display:grid;grid-template-columns:120px 1fr;gap:12px;padding:9px 0;border-bottom:1px solid #edf1f5;font-size:10px}.about-card dt{color:#7b899a}.about-card dd{margin:0;color:#2b3d55;font-weight:600}.primary-action.compact{width:auto;margin:0}.settings-card>.primary-action.compact{margin-top:10px}@media(max-width:1000px){.settings-page{grid-template-columns:180px minmax(0,1fr)}.setting-grid,.toggle-grid,.account-facts{grid-template-columns:1fr}}
</style>

<style scoped>
.account-session-card {
  max-width: 720px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  border-color: #f0d8d4;
  background: #fffafa;
}
.account-session-card h3 { margin: 0; }
.account-session-card p {
  max-width: 520px;
  margin: 5px 0 0;
  color: #7c6c6a;
  font-size: 9px;
  line-height: 1.55;
}
.account-session-card p b { color: #51413f; }
.logout-account-button {
  flex: 0 0 auto;
  border: 1px solid #dca8a1;
  border-radius: 8px;
  background: #fff;
  color: #b13f35;
  padding: 9px 13px;
  font-size: 9px;
  font-weight: 850;
  cursor: pointer;
}
.logout-account-button:hover {
  border-color: #cf8178;
  background: #fff3f1;
}
.logout-account-button:disabled {
  opacity: .55;
  cursor: not-allowed;
}
@media(max-width: 620px) {
  .account-session-card { align-items: flex-start; flex-direction: column; }
  .logout-account-button { width: 100%; }
}
</style>
