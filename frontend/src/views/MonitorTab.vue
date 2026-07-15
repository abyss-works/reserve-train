<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { listMonitors, stopMonitor } from '@/api'
import type { MonitorEntry } from '@/api'

const monitors = ref<MonitorEntry[]>([])
const loading = ref(false)
let timer: ReturnType<typeof setInterval> | null = null

async function load() {
  loading.value = true
  const res = await listMonitors()
  if (res.data) monitors.value = res.data.monitors
  loading.value = false
}

async function onStop(taskId: string) {
  await stopMonitor(taskId)
  monitors.value = monitors.value.filter(m => m.task_id !== taskId)
}

onMounted(() => {
  load()
  timer = setInterval(load, 10000) // 10초마다 갱신
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

function statusBadge(status: string): string {
  switch (status) {
    case 'monitoring': return 'bg-brand/10 text-brand'
    case 'reserved': return 'bg-success/10 text-success'
    case 'failed': return 'bg-danger/10 text-danger'
    case 'stopped': return 'bg-surface text-text-dim'
    default: return 'bg-surface text-text-dim'
  }
}

function statusLabel(status: string): string {
  switch (status) {
    case 'monitoring': return '모니터링 중'
    case 'reserved': return '✅ 예약 완료'
    case 'failed': return '실패'
    case 'stopped': return '중지됨'
    default: return status
  }
}
</script>

<template>
  <div class="p-6 max-w-4xl">
    <div class="flex items-center justify-between mb-5">
      <h2 class="text-text font-semibold">📡 자동 예매</h2>
      <button
        class="border border-border text-text-muted rounded-lg px-4 py-1.5 text-xs hover:bg-surface-elevated transition-colors cursor-pointer"
        @click="load"
      >새로고침</button>
    </div>

    <div v-if="loading && monitors.length === 0" class="bg-surface-elevated rounded-xl border border-border p-8 text-center">
      <p class="text-text-muted text-sm">불러오는 중...</p>
    </div>

    <div v-else-if="monitors.length === 0" class="bg-surface-elevated rounded-xl border border-border p-8 text-center">
      <p class="text-text-muted text-sm">📭 등록된 자동 예매가 없습니다</p>
      <p class="text-text-dim text-xs mt-2">매진 열차의 🔁 자동 예매 버튼으로 등록할 수 있습니다</p>
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="m in monitors"
        :key="m.task_id"
        class="bg-surface-elevated rounded-xl border border-border p-5"
      >
        <div class="flex items-center justify-between mb-2">
          <span class="text-text font-semibold">{{ m.train_label }}</span>
          <span :class="['px-2.5 py-0.5 rounded-full text-[11px] font-medium', statusBadge(m.status)]">
            {{ statusLabel(m.status) }}
          </span>
        </div>
        <p class="text-text-muted text-sm mb-1">{{ m.dep }} → {{ m.arr }}</p>

        <!-- monitoring status -->
        <template v-if="m.status === 'monitoring'">
          <div class="flex items-center gap-2 text-text-dim text-xs">
            <span class="w-2 h-2 rounded-full bg-brand animate-pulse"></span>
            <span>{{ m.check_count }}회 확인</span>
          </div>
          <button
            class="mt-3 border border-border text-text-muted rounded-lg px-3 py-1 text-xs hover:bg-surface transition-colors cursor-pointer"
            @click="onStop(m.task_id)"
          >중지</button>
        </template>

        <!-- reserved result -->
        <template v-if="m.status === 'reserved' && m.result">
          <div class="mt-2 bg-success/10 border border-success/20 rounded-lg p-3 space-y-1 text-sm">
            <p class="text-text-muted text-xs">예약번호: <span class="text-text font-mono">{{ m.result.rsv_id }}</span></p>
            <p class="text-text-muted text-xs">운임: {{ m.result.price?.toLocaleString() }}원 ({{ m.result.seat_count }}석)</p>
            <p class="text-warning text-xs">⏰ 구입기한: {{ m.result.limit_display }}까지</p>
          </div>
        </template>

        <!-- failed -->
        <p v-if="m.status === 'failed' && m.error_msg" class="text-danger text-xs mt-2">{{ m.error_msg }}</p>
      </div>
    </div>
  </div>
</template>
