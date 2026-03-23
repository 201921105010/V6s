<template>
  <div class="login-container">
    <div class="login-card">
      <h2>成品机管理系统登录</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>用户名</label>
          <input type="text" v-model="username" required placeholder="请输入用户名" />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input type="password" v-model="password" required placeholder="请输入密码" />
        </div>
        <button type="submit">登录</button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'

const username = ref('')
const password = ref('')
const router = useRouter()
const userStore = useUserStore()

const handleLogin = () => {
  // In a real app, this would be an API call
  if (username.value && password.value) {
    // Mock login
    userStore.login({
      username: username.value,
      role: 'Admin',
      name: username.value === 'boss' ? '老板' : '管理员'
    })
    router.push('/')
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f7fa;
}
.login-card {
  background: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  width: 100%;
  max-width: 400px;
}
h2 {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
}
.form-group {
  margin-bottom: 20px;
}
label {
  display: block;
  margin-bottom: 8px;
  color: #666;
}
input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
button {
  width: 100%;
  padding: 12px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}
button:hover {
  background-color: #34495e;
}
</style>
