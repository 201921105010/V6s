<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo">成品机管理系统</div>
      <nav>
        <router-link to="/">🏠 首页</router-link>
        <router-link to="/planning">👑 生产统筹</router-link>
        <router-link to="/inventory">🔍 库存查询</router-link>
        <router-link to="/inbound">📥 成品入库</router-link>
      </nav>
      <div class="user-info" v-if="userStore.userInfo">
        <p>当前用户: {{ userStore.userInfo.name }}</p>
        <button @click="handleLogout">退出登录</button>
      </div>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useUserStore } from '../store/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}
.sidebar {
  width: 250px;
  background-color: #2c3e50;
  color: white;
  display: flex;
  flex-direction: column;
}
.logo {
  padding: 20px;
  font-size: 1.2rem;
  font-weight: bold;
  text-align: center;
  border-bottom: 1px solid #34495e;
}
nav {
  display: flex;
  flex-direction: column;
  padding: 20px 0;
  flex-grow: 1;
}
nav a {
  color: white;
  text-decoration: none;
  padding: 15px 20px;
  transition: background-color 0.3s;
}
nav a:hover, nav a.router-link-active {
  background-color: #34495e;
}
.user-info {
  padding: 20px;
  border-top: 1px solid #34495e;
  text-align: center;
}
.user-info button {
  margin-top: 10px;
  padding: 5px 15px;
  cursor: pointer;
}
.main-content {
  flex-grow: 1;
  padding: 20px;
  background-color: #f5f7fa;
  overflow-y: auto;
}
</style>
