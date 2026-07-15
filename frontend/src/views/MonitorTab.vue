<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { listMonitors, stopMonitor } from '@/api'
import type { MonitorEntry } from '@/api'
import { Clock, RefreshCw, LoaderCircle, CheckCircle } from 'lucide-vue-next'

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

onMounted(() => { load(); timer = setInterval(load, 10000) })
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <div class="pa-4" style="max-width: 900px; margin: 0 auto;">
    <div class="d-flex align-center mb-4">
      <Clock :size="20" class="mr-2" />
      <span class="text-h6 font-weight-bold">자동 예매</span>
      <v-spacer />
      <v-btn variant="text" density="compact" @click="load">
        <template #prepend><RefreshCw :size="14" /></template>
        새로고침
      </v-btn>
    </div>

    <div v-if="loading && monitors.length === 0">
      <v-skeleton-loader type="card" class="mb-2" />
    </div>

    <v-card v-else-if="monitors.length === 0" class="pa-8 text-center">
      <Clock :size="48" class="text-grey-lighten-1" />
      <div class="text-body-1 text-medium-emphasis mt-2">등록된 자동 예매가 없습니다</div>
      <div class="text-caption text-disabled mt-1">매진 열차의 자동 예매 버튼으로 등록할 수 있습니다</div>
    </v-card>

    <template v-else>
      <v-card v-for="m in monitors" :key="m.task_id" class="mb-2">
        <v-card-text>
          <div class="d-flex align-center ga-2 mb-1">
            <span class="text-body-2 font-weight-bold">{{ m.train_label }}</span>
            <v-chip size="x-small" :color="m.status === 'reserved' ? 'success' : m.status === 'failed' ? 'error' : 'primary'" label variant="tonal">
              {{ m.status === 'monitoring' ? '모니터링 중' : m.status === 'reserved' ? '예약 완료' : m.status === 'failed' ? '실패' : '중지됨' }}
            </v-chip>
          </div>
          <div class="text-caption text-medium-emphasis mb-1">{{ m.dep }} → {{ m.arr }}</div>

          <template v-if="m.status === 'monitoring'">
            <div class="d-flex align-center ga-2 text-caption text-medium-emphasis">
              <LoaderCircle :size="14" class="text-primary" />
              <span>{{ m.check_count }}회 확인</span>
            </div>
            <v-btn variant="text" color="grey" size="x-small" class="mt-1" @click="onStop(m.task_id)">중지</v-btn>
          </template>

          <div v-if="m.status === 'reserved' && m.result" class="bg-success-lighten-5 rounded pa-3 mt-2 text-caption">
            <div class="d-flex align-center ga-1">
              <CheckCircle :size="14" class="text-success" />
              <span>예약번호: <code>{{ m.result.rsv_id }}</code></span>
            </div>
            <div>운임: {{ m.result.price?.toLocaleString() }}원 ({{ m.result.seat_count }}석)</div>
            <div class="d-flex align-center ga-1" style="color: rgb(180, 130, 0);">
              <Clock :size="12" />
              구입기한: {{ m.result.limit_display }}까지
            </div>
          </div>

          <div v-if="m.status === 'failed' && m.error_msg" class="text-caption text-error mt-1">{{ m.error_msg }}</div>
        </v-card-text>
      </v-card>
    </template>
  </div>
</template>
