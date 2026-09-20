<template>
  <div class="auth-page">
    <section class="auth-brand-panel">
      <div class="brand-lockup">
        <img src="/branding/zjitc-campus-mark.svg" alt="浙江工贸" />
        <div>
          <span>UAV STUDIO</span>
          <h1>无人机数字设计与飞行验证平台</h1>
        </div>
      </div>
      <div class="auth-value-copy">
        <span class="eyebrow">ENGINEERING WORKSPACE</span>
        <h2>从数字装配到飞行验证，<br />每个用户拥有自己的设计空间。</h2>
        <p>登录后，你的飞机设计、装配状态、工程参数、实验记录和个人设置都会与账号绑定。</p>
      </div>
      <div class="workflow-strip">
        <span>需求</span><i>→</i><span>设计</span><i>→</i><span>装配</span><i>→</i><span>验证</span><i>→</i><span>飞行</span>
      </div>
    </section>

    <main class="auth-card-wrap">
      <form class="auth-card" data-testid="login-form" @submit.prevent="submit">
        <header>
          <span class="eyebrow">WELCOME BACK</span>
          <h2>登录 UAV Studio</h2>
          <p>进入你的无人机工程工作空间。</p>
        </header>

        <label class="auth-field">
          <span>用户名</span>
          <input
            v-model.trim="form.username"
            data-testid="login-username"
            autocomplete="username"
            maxlength="64"
            autofocus
            placeholder="请输入用户名"
          />
        </label>
        <label class="auth-field">
          <span>密码</span>
          <input
            v-model="form.password"
            data-testid="login-password"
            type="password"
            autocomplete="current-password"
            maxlength="128"
            placeholder="请输入密码"
          />
        </label>

        <p v-if="message" class="auth-error">{{ message }}</p>

        <button
          class="auth-primary"
          data-testid="login-submit"
          :disabled="auth.loading || !form.username || !form.password"
          type="submit"
        >
          {{ auth.loading ? '正在登录…' : '登录' }}
        </button>

        <div class="auth-divider"><span>首次使用</span></div>
        <RouterLink class="auth-secondary" to="/register">创建个人账号</RouterLink>
      </form>
    </main>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const message = ref('')
const form = reactive({ username: '', password: '' })

async function submit(): Promise<void> {
  if (!form.username || !form.password || auth.loading) return
  message.value = ''
  try {
    await auth.login({ username: form.username, password: form.password })
    const redirect = typeof route.query.redirect === 'string'
      ? route.query.redirect
      : '/aircraft'
    await router.replace(redirect)
  } catch {
    message.value = auth.error || '登录失败。'
  }
}
</script>

<style scoped>
.auth-page{min-height:100vh;display:grid;grid-template-columns:minmax(440px,1.15fr) minmax(420px,.85fr);background:#eef4fa;color:#1d3148}.auth-brand-panel{position:relative;overflow:hidden;display:flex;flex-direction:column;justify-content:space-between;padding:42px clamp(36px,6vw,86px);background:radial-gradient(circle at 15% 15%,rgba(78,190,238,.18),transparent 28%),radial-gradient(circle at 85% 75%,rgba(63,116,217,.24),transparent 34%),linear-gradient(145deg,#0c2038 0%,#153858 52%,#0c2d49 100%);color:#eff8ff}.auth-brand-panel::after{content:'';position:absolute;inset:0;background-image:linear-gradient(rgba(255,255,255,.025) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.025) 1px,transparent 1px);background-size:28px 28px;mask-image:linear-gradient(to bottom,black,transparent 90%);pointer-events:none}.brand-lockup,.auth-value-copy,.workflow-strip{position:relative;z-index:1}.brand-lockup{display:flex;align-items:center;gap:14px}.brand-lockup img{width:48px;height:48px;border-radius:12px}.brand-lockup span{font-size:10px;letter-spacing:.18em;color:#8fe6ff;font-weight:800}.brand-lockup h1{margin:5px 0 0;font-size:15px;font-weight:650;color:#f7fbff}.auth-value-copy{max-width:680px}.eyebrow{font-size:9px;letter-spacing:.18em;color:#3c7ec3;font-weight:900}.auth-brand-panel .eyebrow{color:#83dbf7}.auth-value-copy h2{margin:12px 0 14px;font-size:clamp(30px,3.6vw,52px);line-height:1.15;letter-spacing:-.04em}.auth-value-copy p{max-width:590px;margin:0;color:rgba(226,240,252,.74);font-size:13px;line-height:1.8}.workflow-strip{display:flex;align-items:center;gap:10px;color:rgba(229,243,255,.7);font-size:10px;font-weight:700}.workflow-strip i{font-style:normal;color:#55c8ef}.auth-card-wrap{display:grid;place-items:center;padding:30px;background:radial-gradient(circle at 70% 15%,rgba(76,146,230,.1),transparent 28%),#f4f7fb}.auth-card{width:min(430px,100%);padding:30px;border:1px solid #d9e4f0;border-radius:18px;background:rgba(255,255,255,.96);box-shadow:0 24px 70px rgba(19,48,82,.12)}.auth-card header{margin-bottom:22px}.auth-card h2{margin:6px 0 5px;color:#1b334f;font-size:24px;letter-spacing:-.03em}.auth-card header p{margin:0;color:#7a899c;font-size:10px}.auth-field{display:grid;gap:6px;margin-top:13px}.auth-field span{color:#536a84;font-size:10px;font-weight:750}.auth-field input{width:100%;box-sizing:border-box;border:1px solid #d5e0ec;border-radius:9px;background:#fbfdff;padding:11px 12px;color:#243b56;font:inherit;font-size:11px;outline:none;transition:border-color .15s,box-shadow .15s}.auth-field input:focus{border-color:#66a0e6;box-shadow:0 0 0 3px rgba(56,126,216,.09)}.auth-error{margin:12px 0 0;padding:9px 10px;border:1px solid #f0cbc6;border-radius:8px;background:#fff5f4;color:#aa3e34;font-size:9px}.auth-primary,.auth-secondary{width:100%;box-sizing:border-box;display:grid;place-items:center;margin-top:16px;border-radius:9px;padding:11px 12px;font-size:10px;font-weight:850;text-decoration:none}.auth-primary{border:1px solid #246dd0;background:linear-gradient(180deg,#347fdf,#2565be);color:white;box-shadow:0 9px 20px rgba(37,101,190,.18);cursor:pointer}.auth-primary:disabled{opacity:.55;cursor:not-allowed}.auth-divider{display:flex;align-items:center;gap:10px;margin:18px 0 0;color:#97a3b1;font-size:8px}.auth-divider::before,.auth-divider::after{content:'';height:1px;flex:1;background:#e5ebf2}.auth-secondary{margin-top:10px;border:1px solid #d2dfec;background:#f9fbfe;color:#3b5f84}@media(max-width:900px){.auth-page{grid-template-columns:1fr}.auth-brand-panel{min-height:280px;padding:28px}.auth-value-copy h2{font-size:30px}.workflow-strip{display:none}.auth-card-wrap{padding:24px}.auth-card{padding:24px}}
</style>
