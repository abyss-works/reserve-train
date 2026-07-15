<script setup lang="ts">
import { onMounted } from 'vue'
import { useTrainStore } from '@/stores/train'

const store = useTrainStore()

onMounted(() => {
  store.loadReservations()
})

async function onCancel(idx: number) {
  if (confirm('예약을 취소하시겠습니까?')) {
    await store.cancel(idx)
  }
}

async function onRefresh() {
  await store.loadReservations()
}
</script>

<template>
  <div class="p-6 max-w-4xl">
    <div class="flex items-center justify-between mb-5">
      <h2 class="text-text font-semibold">📋 예약 내역</h2>
      <button
        class="border border-border text-text-muted rounded-lg px-4 py-1.5 text-xs hover:bg-surface-elevated transition-colors cursor-pointer"
        @click="onRefresh"
      >
        새로고침
      </button>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="space-y-3">
      <div v-for="i in 3" :key="i" class="bg-surface-elevated rounded-xl border border-border p-4">
        <div class="h-4 skeleton rounded w-1/2 mb-3"/>
        <div class="h-3 skeleton rounded w-3/4"/>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="store.error" class="bg-danger/10 border border-danger/20 rounded-xl p-4 mb-4">
      <p class="text-danger text-sm">{{ store.error }}</p>
    </div>

    <!-- Empty -->
    <div v-else-if="store.reservations.length === 0" class="bg-surface-elevated rounded-xl border border-border p-8 text-center">
      <p class="text-text-muted">📭 현재 예약 내역이 없습니다</p>
    </div>

    <!-- List -->
    <div v-else class="space-y-3">
      <p class="text-text-muted text-xs">{{ store.reservations.length }}건</p>
      <div
        v-for="(r, i) in store.reservations"
        :key="r.rsv_id"
        class="bg-surface-elevated rounded-xl border border-border p-5"
      >
        <div class="flex items-center justify-between mb-2">
          <span class="text-text font-semibold">{{ r.train_type }} {{ r.train_no }}</span>
          <span class="text-text-dim text-xs font-mono bg-surface rounded px-2 py-0.5">{{ r.rsv_id }}</span>
        </div>
        <p class="text-text-muted text-sm mb-2">
          {{ r.dep_name }}({{ r.dep_display }}) → {{ r.arr_name }}({{ r.arr_display }})
        </p>
        <div class="flex items-center justify-between">
          <span class="text-text text-sm font-medium">{{ r.price?.toLocaleString() }}원 ({{ r.seat_count }}석)</span>
          <span class="text-text-dim text-xs">구입기한: {{ r.limit_display }}</span>
        </div>
        <button
          class="mt-3 bg-danger/10 text-danger border border-danger/20 rounded-lg px-4 py-1.5 text-xs hover:bg-danger/20 transition-colors cursor-pointer"
          @click="onCancel(i)"
        >
          ❌ 예약 취소
        </button>
      </div>
    </div>
  </div>
</template>
