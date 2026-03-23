<template>
  <div class="home">
    <h1>欢迎来到成品机管理系统</h1>
    <div class="dashboard-cards">
      <div class="card" @click="go('/planning')">
        <h3>👑 生产统筹</h3>
        <p>查看和管理生产计划</p>
      </div>
      <div class="card" @click="go('/inventory')">
        <h3>🔍 库存查询</h3>
        <p>查询当前成品库存状态</p>
      </div>
      <div class="card" @click="go('/inbound')">
        <h3>📥 成品入库</h3>
        <p>登记新的成品机入库</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
const go = (path: string) => {
  router.push(path)
}
</script>

<style scoped>
.home {
  padding: 20px;
}
.dashboard-cards {
  display: flex;
  gap: 20px;
  margin-top: 30px;
  flex-wrap: wrap;
}
.card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  width: 250px;
  cursor: pointer;
  transition: transform 0.2s;
}
.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.card h3 {
  margin-top: 0;
  color: #2c3e50;
}
.card p {
  color: #666;
  margin-bottom: 0;
}
</style>
