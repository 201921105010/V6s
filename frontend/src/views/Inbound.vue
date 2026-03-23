<template>
  <div class="inbound">
    <h2>成品入库与库位图</h2>
    <div class="toolbar">
      <button @click="fetchInventory">刷新库存</button>
      <button @click="addNewSlot">新增库位</button>
      <button @click="saveLayout">保存布局</button>
      <button class="danger" @click="resetLayout">重置布局</button>
    </div>

    <div v-if="error" class="error">{{ error }}</div>

    <div class="layout-wrap">
      <div class="layout-canvas" @mousemove="onDragMove" @mouseup="onDragEnd" @mouseleave="onDragEnd">
        <div
          v-for="slot in slots"
          :key="slot.id"
          class="slot-rect"
          :class="{
            full: slotStats[slot.code]?.isFull,
            overflow: slotStats[slot.code]?.isOverflow,
            selected: selectedSlotCode === slot.code
          }"
          :style="rectStyle(slot)"
          @mousedown="onDragStart($event, slot)"
          @click="selectedSlotCode = slot.code"
        >
          <div class="slot-head">
            <input
              class="slot-code-input"
              :value="slot.code"
              @click.stop
              @input="onSlotCodeInput(slot.id, ($event.target as HTMLInputElement).value)"
            />
            <button class="slot-del" @click.stop="removeOneSlot(slot.id)">×</button>
          </div>
          <div class="slot-body">
            <div>数量: {{ slotStats[slot.code]?.count || 0 }}/5</div>
            <div>最新入库: {{ slotStats[slot.code]?.latestInboundTime || '-' }}</div>
            <div v-if="slotStats[slot.code]?.isOverflow" class="warn">超量，禁止入库</div>
          </div>
        </div>
      </div>
    </div>

    <div class="pending-panel">
      <h3>待入库机台</h3>
      <div v-if="loading">加载中...</div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>流水号</th>
            <th>机型</th>
            <th>批次号</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in pendingRows" :key="row['流水号']">
            <td>{{ row['流水号'] }}</td>
            <td>{{ row['机型'] }}</td>
            <td>{{ row['批次号'] }}</td>
            <td><button @click="openInboundPicker(row)">选择库位入库</button></td>
          </tr>
          <tr v-if="pendingRows.length === 0">
            <td colspan="4" class="empty">暂无待入库机台</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="pickerVisible" class="modal-mask" @click="closeInboundPicker">
      <div class="modal-card" @click.stop>
        <h4>选择库位</h4>
        <p>流水号：{{ activeRow?.['流水号'] }}</p>
        <div class="slot-list">
          <button
            v-for="slot in slots"
            :key="`pick-${slot.id}`"
            :disabled="slotStats[slot.code]?.isFull"
            @click="confirmInbound(slot.code)"
          >
            {{ slot.code }}（{{ slotStats[slot.code]?.count || 0 }}/5）
          </button>
        </div>
        <div class="modal-actions">
          <button @click="closeInboundPicker">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import axios from 'axios'
import {
  addSlot,
  buildSlotStats,
  defaultSlots,
  persistLayoutToLocal,
  removeSlot,
  restoreLayoutFromLocal,
  updateSlot,
  type WarehouseSlot
} from './inboundLayout'

const layoutId = 'default'
const loading = ref(false)
const error = ref('')
const inventory = ref<any[]>([])
const slots = ref<WarehouseSlot[]>([])
const selectedSlotCode = ref('')
const pickerVisible = ref(false)
const activeRow = ref<any | null>(null)

const dragState = reactive({
  draggingId: '',
  startX: 0,
  startY: 0,
  originX: 0,
  originY: 0
})

const pendingRows = computed(() => {
  return inventory.value.filter((item) => String(item['状态'] || '').includes('待入库'))
})

const slotStats = computed(() => {
  return buildSlotStats(inventory.value, slots.value)
})

const rectStyle = (slot: WarehouseSlot) => ({
  left: `${slot.x}px`,
  top: `${slot.y}px`,
  width: `${slot.w}px`,
  height: `${slot.h}px`
})

const fetchInventory = async () => {
  loading.value = true
  error.value = ''
  try {
    const response = await axios.get('/api/v1/inventory/')
    inventory.value = response.data.data || []
  } catch (err: any) {
    error.value = `读取库存失败: ${err.message || err}`
  } finally {
    loading.value = false
  }
}

const loadLayout = async () => {
  const local = restoreLayoutFromLocal(layoutId)
  if (local.length > 0) {
    slots.value = local
    return
  }
  try {
    const response = await axios.get(`/api/v1/inventory/layout/${layoutId}`)
    const remoteSlots = response.data?.layout_json?.slots
    if (Array.isArray(remoteSlots) && remoteSlots.length > 0) {
      slots.value = remoteSlots
      persistLayoutToLocal(layoutId, slots.value)
      return
    }
  } catch (err: any) {
    error.value = `读取布局失败: ${err.message || err}`
  }
  slots.value = defaultSlots()
}

const saveLayout = async () => {
  persistLayoutToLocal(layoutId, slots.value)
  try {
    await axios.post('/api/v1/inventory/layout/save', {
      layout_id: layoutId,
      layout_json: { slots: slots.value }
    })
  } catch (err: any) {
    error.value = `布局保存失败: ${err.message || err}`
  }
}

const resetLayout = async () => {
  localStorage.removeItem(`warehouse-layout:${layoutId}`)
  slots.value = defaultSlots()
  selectedSlotCode.value = ''
  try {
    await axios.post('/api/v1/inventory/layout/reset', { layout_id: layoutId })
  } catch (err: any) {
    error.value = `布局重置失败: ${err.message || err}`
  }
}

const addNewSlot = () => {
  slots.value = addSlot(slots.value)
}

const removeOneSlot = (id: string) => {
  slots.value = removeSlot(slots.value, id)
}

const onSlotCodeInput = (id: string, code: string) => {
  slots.value = updateSlot(slots.value, id, { code: code.trim() || 'UNSET' })
}

const onDragStart = (evt: MouseEvent, slot: WarehouseSlot) => {
  dragState.draggingId = slot.id
  dragState.startX = evt.clientX
  dragState.startY = evt.clientY
  dragState.originX = slot.x
  dragState.originY = slot.y
}

const onDragMove = (evt: MouseEvent) => {
  if (!dragState.draggingId) {
    return
  }
  const dx = evt.clientX - dragState.startX
  const dy = evt.clientY - dragState.startY
  slots.value = updateSlot(slots.value, dragState.draggingId, {
    x: Math.max(0, dragState.originX + dx),
    y: Math.max(0, dragState.originY + dy)
  })
}

const onDragEnd = () => {
  dragState.draggingId = ''
}

const openInboundPicker = (row: any) => {
  activeRow.value = row
  pickerVisible.value = true
}

const closeInboundPicker = () => {
  pickerVisible.value = false
  activeRow.value = null
}

const confirmInbound = async (slotCode: string) => {
  if (!activeRow.value) {
    return
  }
  try {
    const result = await axios.post('/api/v1/inventory/inbound-to-slot', {
      serial_no: activeRow.value['流水号'],
      slot_code: slotCode
    })
    if (!result.data?.ok) {
      throw new Error(result.data?.message || '入库失败')
    }
    closeInboundPicker()
    await fetchInventory()
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    const detailText = typeof detail === 'string' ? detail : detail?.message
    error.value = `入库失败: ${detailText || err.message || err}`
  }
}

onMounted(async () => {
  await Promise.all([fetchInventory(), loadLayout()])
})
</script>

<style scoped>
.inbound {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
.toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}
button {
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  background: #409eff;
  color: white;
  cursor: pointer;
}
button:disabled {
  background: #b6d4fe;
  cursor: not-allowed;
}
.danger {
  background: #f56c6c;
}
.layout-wrap {
  border: 1px solid #e8edf2;
  border-radius: 8px;
  padding: 8px;
}
.layout-canvas {
  position: relative;
  height: 360px;
  width: 100%;
  background: #fafcff;
  overflow: auto;
}
.slot-rect {
  position: absolute;
  border: 2px solid #409eff;
  border-radius: 8px;
  background: #ecf5ff;
  padding: 6px;
  cursor: move;
}
.slot-rect.full {
  border-color: #e6a23c;
  background: #fdf6ec;
}
.slot-rect.overflow {
  border-color: #f56c6c;
  background: #fee;
}
.slot-rect.selected {
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.25);
}
.slot-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.slot-code-input {
  width: 70px;
}
.slot-del {
  background: #f56c6c;
  width: 22px;
  height: 22px;
  padding: 0;
}
.slot-body {
  margin-top: 8px;
  font-size: 12px;
  color: #606266;
}
.warn {
  color: #f56c6c;
  font-weight: bold;
}
.pending-panel {
  margin-top: 16px;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
}
.data-table th,
.data-table td {
  border: 1px solid #ebeef5;
  padding: 10px;
}
.empty {
  text-align: center;
  color: #999;
}
.error {
  margin: 10px 0;
  color: #f56c6c;
}
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
}
.modal-card {
  background: #fff;
  padding: 18px;
  width: 480px;
  border-radius: 8px;
}
.slot-list {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 10px;
}
.modal-actions {
  margin-top: 12px;
  text-align: right;
}
</style>
