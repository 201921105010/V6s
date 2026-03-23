<template>
  <div class="inventory">
    <h2>库存查询</h2>
    <div class="actions">
      <button @click="fetchData">刷新数据</button>
    </div>
    
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    
    <table v-else class="data-table">
      <thead>
        <tr>
          <th>流水号</th>
          <th>机型</th>
          <th>批次号</th>
          <th>状态</th>
          <th>预计入库时间</th>
          <th>库位</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in inventoryList" :key="item['流水号']">
          <td>{{ item['流水号'] }}</td>
          <td>{{ item['机型'] }}</td>
          <td>{{ item['批次号'] }}</td>
          <td>
            <span :class="['status-badge', getStatusClass(item['状态'])]">
              {{ item['状态'] }}
            </span>
          </td>
          <td>{{ item['预计入库时间'] }}</td>
          <td>{{ item['Location_Code'] }}</td>
        </tr>
        <tr v-if="inventoryList.length === 0">
          <td colspan="6" class="empty-text">暂无数据</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const inventoryList = ref<any[]>([])
const loading = ref(false)
const error = ref('')

const fetchData = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await axios.get('/api/v1/inventory/')
    inventoryList.value = response.data.data
  } catch (err: any) {
    error.value = '获取数据失败: ' + err.message
    console.error(err)
  } finally {
    loading.value = false
  }
}

const getStatusClass = (status: string) => {
  if (status === '在库') return 'status-in'
  if (status === '已发货') return 'status-out'
  if (status === '待入库') return 'status-pending'
  return 'status-default'
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.inventory {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}
.actions {
  margin-bottom: 20px;
}
button {
  padding: 8px 16px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
}
.data-table th, .data-table td {
  border: 1px solid #ebeef5;
  padding: 12px;
  text-align: left;
}
.data-table th {
  background-color: #f8f9fa;
  font-weight: bold;
  color: #606266;
}
.status-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
}
.status-in { background-color: #e1f3d8; color: #67c23a; }
.status-out { background-color: #fde2e2; color: #f56c6c; }
.status-pending { background-color: #faecd8; color: #e6a23c; }
.status-default { background-color: #f4f4f5; color: #909399; }
.loading, .error, .empty-text {
  text-align: center;
  padding: 20px;
  color: #909399;
}
.error {
  color: #f56c6c;
}
</style>
