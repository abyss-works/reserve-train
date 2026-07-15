<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTrainStore } from '@/stores/train'

const router = useRouter()
const auth = useAuthStore()
const store = useTrainStore()

onMounted(async () => {
  if (!auth.loggedIn) {
    router.replace('/login')
    return
  }
  await store.loadReservations()
})

async function onCancel(idx: number) {
  await store.cancel(idx)
}

async function onRefresh() {
  await store.loadReservations()
}
</script>

<template>
  <div class="min-h-screen pb-20">
    <header class="sticky top-0 z-40 bg-bg/80 backdrop-blur-lg border-b border-border-subtle safe-top">
      <div class="max-w-lg mx-auto px-4 py-3 flex items-center justify-between">
        <h1 class="text-text text-lg font-semibold">📋 예약 내역</h1>
        <button class="text-text-dim text-xs cursor-pointer" @click="onRefresh">새로고침</button>
      </div>
    </header>

    <main class="max-w-lg mx-auto px-4 pt-4">
      <!-- Loading -->
      <div v-if="store.loading" class="space-y-3 pt-2">
        <div v-for="i in 2" :key="i" class="bg-surface-elevated rounded-xl border border-border p-4">
          <div class="h-4 skeleton rounded w-1/2 mb-3"/>
          <div class="h-3 skeleton rounded w-3/4"/>
        </div>
      </div>

      <!-- Error -->
      <p v-else-if="store.error" class="text-danger text-sm text-center">{{ store.error }}</p>

      <!-- Empty -->
      <div v-else-if="store.reservations.length === 0" class="text-center pt-16">
        <p class="text-text-muted text-sm">📭 현재 예약 내역이 없습니다</p>
      </div>

      <!-- Reservation list -->
      <div v-else class="space-y-3 pb-4">
        <p class="text-text-muted text-xs">{{ store.reservations.length }}건</p>
        <div
          v-for="(r, i) in store.reservations"
          :key="r.rsv_id"
          class="bg-surface-elevated rounded-xl border border-border p-4"
        >
          <div class="flex items-center justify-between mb-2">
            <span class="text-text font-semibold">{{ r.train_type }} {{ r.train_no }}</span>
            <span class="text-text-dim text-xs font-mono">{{ r.rsv_id }}</span>
          </div>
          <p class="text-text-muted text-sm">
            {{ r.dep_name }}({{ r.dep_display }}) → {{ r.arr_name }}({{ r.arr_display }})
          </p>
          <div class="flex items-center justify-between mt-2">
            <span class="text-text text-sm">{{ r.price?.toLocaleString() }}원 ({{ r.seat_count }}석)</span>
            <span class="text-text-dim text-xs">구입기한: {{ r.limit_display }}</span>
          </div>
          <button
            class="w-full mt-3 bg-danger/10 text-danger border border-danger/20 rounded-xl py-2 text-sm hover:bg-danger/20 transition-colors cursor-pointer"
            @click="onCancel(i)"
          >
            ❌ 예약 취소
          </button>
        </div>
      </div>
    </main>
  </div>
</template>
