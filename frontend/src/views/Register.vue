<template>
  <div class="register-page">
    <main class="register-card" data-testid="register-form">
      <div class="register-brand">
        <img src="/branding/zjitc-campus-mark.svg" alt="浙江工贸" />
        <div><b>UAV Studio</b><span>个人工程工作空间</span></div>
      </div>
      <header>
        <span class="eyebrow">CREATE ACCOUNT</span>
        <h1>创建账号</h1>
        <p>注册后系统会为你建立独立的飞机设计空间。每个账号最多保存 10 架飞机。</p>
      </header>

      <div class="field-grid">
        <label class="field">
          <span>用户名</span>
          <input v-model.trim="form.username" data-testid="register-username" autocomplete="username" maxlength="32" placeholder="3-32 位字母、数字、_ 或 -" />
        </label>
        <label class="field">
          <span>显示名称</span>
          <input v-model.trim="form.displayName" data-testid="register-display-name" maxlength="120" placeholder="例如：张三" />
        </label>
      </div>
      <label class="field">
        <span>密码</span>
        <input v-model="form.password" data-testid="register-password" type="password" autocomplete="new-password" maxlength="128" placeholder="至少 6 位" />
      </label>
      <label class="field">
        <span>确认密码</span>
        <input v-model="form.confirm" data-testid="register-confirm" type="password" autocomplete="new-password" maxlength="128" placeholder="再次输入密码" />
      </label>

      <div class="account-contract">
        <div><b>独立设计空间</b><span>你的飞机与其他账号隔离</span></div>
        <div><b>10 架上限</b><span>包含新建和复制的飞机设计</span></div>
        <div><b>独立设置</b><span>3D 与飞行偏好按账号保存</span></div>
      </div>

      <p v-if="message" class="error">{{ message }}</p>
      <button class="primary" data-testid="register-submit" :disabled="auth.loading || !canSubmit" @click="submit">
        {{ auth.loading ? '正在创建…' : '创建账号并进入 UAV Studio' }}
      </button>
      <p class="login-link">已有账号？ <RouterLink to="/login">返回登录</RouterLink></p>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const message = ref('')
const form = reactive({ username: '', displayName: '', password: '', confirm: '' })
const usernamePattern = /^[A-Za-z0-9_-]{3,32}$/

const canSubmit = computed(() =>
  usernamePattern.test(form.username) &&
  form.password.length >= 6 &&
  form.password === form.confirm,
)

async function submit(): Promise<void> {
  message.value = ''
  if (!usernamePattern.test(form.username)) {
    message.value = '用户名只能包含字母、数字、下划线或连字符，长度 3-32 位。'
    return
  }
  if (form.password.length < 6) {
    message.value = '密码至少 6 位。'
    return
  }
  if (form.password !== form.confirm) {
    message.value = '两次输入的密码不一致。'
    return
  }
  try {
    await auth.register({
      username: form.username,
      display_name: form.displayName,
      password: form.password,
    })
    await router.replace('/aircraft')
  } catch {
    message.value = auth.error || '注册失败。'
  }
}
</script>

<style scoped>
.register-page{min-height:100vh;display:grid;place-items:center;padding:34px;background:radial-gradient(circle at 12% 10%,rgba(67,160,225,.16),transparent 27%),radial-gradient(circle at 88% 86%,rgba(55,97,180,.12),transparent 30%),linear-gradient(145deg,#eef4fa,#f7f9fc)}.register-card{width:min(620px,96vw);box-sizing:border-box;padding:30px;border:1px solid #d8e3ef;border-radius:18px;background:rgba(255,255,255,.97);box-shadow:0 24px 70px rgba(19,48,82,.12)}.register-brand{display:flex;align-items:center;gap:10px;padding-bottom:18px;border-bottom:1px solid #e8edf4}.register-brand img{width:38px;height:38px;border-radius:9px}.register-brand b{display:block;color:#1c3756;font-size:14px}.register-brand span{display:block;margin-top:2px;color:#7b8a9d;font-size:9px}.eyebrow{font-size:9px;letter-spacing:.17em;color:#3a7bc2;font-weight:900}header{padding:22px 0 8px}h1{margin:6px 0 5px;color:#19314d;font-size:26px;letter-spacing:-.035em}header p{max-width:520px;margin:0;color:#718197;font-size:10px;line-height:1.65}.field-grid{display:grid;grid-template-columns:1fr 1fr;gap:11px}.field{display:grid;gap:6px;margin-top:12px}.field span{color:#526b85;font-size:9px;font-weight:750}.field input{width:100%;box-sizing:border-box;border:1px solid #d5e0ec;border-radius:9px;background:#fbfdff;padding:10px 11px;color:#263d58;font:inherit;font-size:10px;outline:none}.field input:focus{border-color:#6da4e7;box-shadow:0 0 0 3px rgba(56,126,216,.08)}.account-contract{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:17px}.account-contract div{padding:10px;border:1px solid #e0e8f1;border-radius:9px;background:#f8fbfe}.account-contract b{display:block;color:#375775;font-size:9px}.account-contract span{display:block;margin-top:3px;color:#8593a5;font-size:8px;line-height:1.45}.error{margin:13px 0 0;padding:9px;border:1px solid #efcac5;border-radius:8px;background:#fff5f4;color:#aa4138;font-size:9px}.primary{width:100%;margin-top:16px;border:1px solid #2568c2;border-radius:9px;background:linear-gradient(180deg,#347fdf,#2565be);color:#fff;padding:11px;font-size:10px;font-weight:850;cursor:pointer}.primary:disabled{opacity:.52;cursor:not-allowed}.login-link{margin:14px 0 0;text-align:center;color:#7c899a;font-size:9px}.login-link a{color:#2869ba;font-weight:800;text-decoration:none}@media(max-width:650px){.register-page{padding:18px}.register-card{padding:22px}.field-grid,.account-contract{grid-template-columns:1fr}}
</style>
