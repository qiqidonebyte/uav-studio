<template>
  <div class="settings-page">
    <aside class="settings-nav panel">
      <div class="settings-user">
        <span class="settings-avatar">A</span>
        <div><b>{{ store.username }}</b><small>本地管理员</small></div>
      </div>
      <button v-for="item in sections" :key="item.id" :class="{ active: active === item.id }" @click="active = item.id">
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
        <div class="settings-card narrow">
          <h3>管理员账户</h3>
          <p class="settings-note">当前版本只保留一个本地管理员账户。密码以哈希形式保存在 SQLite 中。</p>
          <label class="setting-field"><span>用户名</span><input :value="store.username" disabled /></label>
          <label class="setting-field"><span>当前密码</span><input v-model="password.current" type="password" autocomplete="current-password" /></label>
          <label class="setting-field"><span>新密码</span><input v-model="password.next" type="password" autocomplete="new-password" /></label>
          <label class="setting-field"><span>确认新密码</span><input v-model="password.confirm" type="password" autocomplete="new-password" /></label>
          <p v-if="passwordMessage" :class="['password-message', { error: passwordError }]">{{ passwordMessage }}</p>
          <button class="primary-action compact" :disabled="changingPassword" @click="changePassword">
            {{ changingPassword ? '修改中…' : '修改密码' }}
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
            <label class="setting-field"><span>默认飞机 ID</span><input v-model.number="store.settings.general.default_aircraft_id" type="number" min="1" /></label>
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
            <div><dt>产品版本</dt><dd>Reference V1</dd></div>
            <div><dt>3D Asset</dt><dd>V1.1</dd></div>
            <div><dt>组件数据库</dt><dd>V1</dd></div>
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
import { useSettingsStore } from '../stores/settings'

const store = useSettingsStore()
const active = ref<'account' | 'general' | 'display' | 'flight' | 'about'>('general')
const changingPassword = ref(false)
const passwordMessage = ref('')
const passwordError = ref(false)
const savedMessage = ref('')
const password = reactive({ current: '', next: '', confirm: '' })

const sections = [
  { id: 'account', label: '账户与密码', hint: 'admin', description: '修改本地管理员密码。' },
  { id: 'general', label: '通用设置', hint: '单位与默认页', description: '控制 UAV Studio 的通用显示和默认工作流。' },
  { id: 'display', label: '3D 显示', hint: '质量与辅助信息', description: '控制 Three.js 渲染质量与工程辅助元素。' },
  { id: 'flight', label: '飞行实验', hint: '默认实验参数', description: '设置进入飞行实验时使用的默认参数。' },
  { id: 'about', label: '关于', hint: '版本信息', description: 'UAV Studio 版本与项目范围。' },
] as const

const activeSection = computed(() => sections.find(item => item.id === active.value) ?? sections[1])

onMounted(async () => { await store.initialize() })

async function saveSettings(): Promise<void> {
  savedMessage.value = ''
  await store.save()
  savedMessage.value = '已保存'
  window.setTimeout(() => { savedMessage.value = '' }, 1800)
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
</script>

<style scoped>
.settings-page{height:calc(100vh - 56px);display:grid;grid-template-columns:220px minmax(0,1fr);gap:12px;padding:12px;overflow:hidden}.settings-nav{padding:10px;overflow:auto}.settings-user{display:flex;align-items:center;gap:9px;padding:10px;margin-bottom:10px;border-bottom:1px solid #e9eef5}.settings-avatar{display:grid;place-items:center;width:32px;height:32px;border-radius:50%;background:#1f5da8;color:#fff;font-weight:800}.settings-user b{display:block;color:#24364e;font-size:12px}.settings-user small{display:block;margin-top:2px;color:#8390a1;font-size:9px}.settings-nav>button{width:100%;display:grid;gap:2px;padding:10px;border:1px solid transparent;border-radius:7px;background:transparent;text-align:left;color:#53647a}.settings-nav>button:hover{background:#f7f9fc}.settings-nav>button.active{background:#eef5ff;border-color:#dce9fb;color:#1f5da8}.settings-nav>button span{font-size:11px;font-weight:700}.settings-nav>button small{font-size:8px;color:#8a96a6}.settings-content{position:relative;overflow:auto;padding:18px}.settings-head{display:flex;align-items:center;justify-content:space-between;gap:16px;padding-bottom:14px;border-bottom:1px solid #e8edf4}.settings-head h2{margin:0;color:#192b42;font-size:18px}.settings-head p{margin:4px 0 0;color:#718096;font-size:10px}.settings-actions{display:flex;align-items:center;gap:8px}.settings-actions button{width:auto;margin:0}.save-ok{color:#137445;font-size:10px}.settings-section{display:grid;gap:12px;padding-top:14px}.settings-card,.about-card{border:1px solid #e0e7f0;border-radius:8px;background:#fff;padding:14px}.settings-card.narrow{max-width:560px}.settings-card h3{margin:0 0 12px;color:#2a3d55;font-size:13px}.setting-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.setting-field{display:grid;gap:5px;color:#5e6f84;font-size:10px}.setting-field input,.setting-field select{width:100%;min-width:0;border:1px solid #d7e1ed;border-radius:6px;background:#fff;padding:8px 9px;color:#26384f;font:inherit;outline:none}.setting-field input:focus,.setting-field select:focus{border-color:#7ba9e9;box-shadow:0 0 0 2px rgba(37,99,235,.06)}.setting-field input:disabled{background:#f4f6f8;color:#7b8798}.toggle-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}.toggle-row{display:flex;align-items:flex-start;gap:8px;padding:9px;border:1px solid #e7ecf3;border-radius:7px;background:#fbfcfe}.toggle-row input{margin-top:2px;accent-color:#2563eb}.toggle-row b{display:block;color:#32465f;font-size:10px}.toggle-row small{display:block;margin-top:2px;color:#8592a3;font-size:8px;line-height:1.4}.settings-note{margin:0 0 12px;padding:9px;border-radius:6px;background:#f6f9fd;color:#6d7d91;font-size:9px;line-height:1.5}.safety-note{margin-top:9px;margin-bottom:0;color:#745b2c;background:#fff9ed}.password-message{margin:2px 0;padding:7px;border-radius:5px;background:#eefaf4;color:#137445;font-size:9px}.password-message.error,.settings-global-error{background:#fff1f0;color:#b42318}.settings-global-error{position:sticky;bottom:0;margin:12px 0 0;padding:9px;border-radius:6px;font-size:10px}.about-card{max-width:780px}.about-brand{display:flex;align-items:center;gap:12px;margin-bottom:16px}.about-brand img{width:44px;height:44px}.about-brand b{display:block;color:#1d3049;font-size:18px}.about-brand span{display:block;margin-top:3px;color:#708096;font-size:10px}.about-card dl{margin:0}.about-card dl>div{display:grid;grid-template-columns:120px 1fr;gap:12px;padding:9px 0;border-bottom:1px solid #edf1f5;font-size:10px}.about-card dt{color:#7b899a}.about-card dd{margin:0;color:#2b3d55;font-weight:600}.primary-action.compact{width:auto;margin:0}.settings-card>.primary-action.compact{margin-top:10px}.editor-actions .primary-action.compact{width:100%}@media(max-width:1000px){.settings-page{grid-template-columns:180px minmax(0,1fr)}.setting-grid,.toggle-grid{grid-template-columns:1fr}}
</style>
