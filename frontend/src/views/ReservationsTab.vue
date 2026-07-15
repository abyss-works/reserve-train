<script setup lang="ts">
import { onMounted } from 'vue'
import { useTrainStore } from '@/stores/train'
import { Ticket, X, RefreshCw, Clock } from 'lucide-vue-next'

const store = useTrainStore()
onMounted(() => { store.loadReservations() })

async function onCancel(idx: number) {
  if (confirm('예약을 취소하시겠습니까?')) {
    await store.cancel(idx)
  }
}
</script>

<template>
  <div class="pa-4" style="max-width: 900px; margin: 0 auto;">
    <div class="d-flex align-center mb-4">
      <Ticket :size="20" class="mr-2" />
      <span class="text-h6 font-weight-bold">예약 내역</span>
      <v-spacer />
      <v-btn variant="text" density="compact" @click="store.loadReservations()">
        <template #prepend><RefreshCw :size="14" /></template>
        새로고침
      </v-btn>
    </div>

    <div v-if="store.loading">
      <v-skeleton-loader v-for="i in 3" :key="i" type="card" class="mb-2" />
    </div>

    <v-alert v-else-if="store.error" type="error" variant="tonal" closable class="mb-3" density="compact">{{ store.error }}</v-alert>

    <v-card v-else-if="store.reservations.length === 0" class="pa-8 text-center">
      <Ticket :size="48" class="text-grey-lighten-1" />
      <div class="text-body-1 text-medium-emphasis mt-2">예약 내역이 없습니다</div>
    </v-card>

    <template v-else>
      <div class="text-caption text-medium-emphasis mb-2">{{ store.reservations.length }}건</div>
      <v-card v-for="(r, i) in store.reservations" :key="r.rsv_id" class="mb-2" variant="outlined">
        <v-card-text>
          <div class="d-flex align-center ga-2 mb-1">
            <span class="text-body-2 font-weight-bold">{{ r.train_type }} {{ r.train_no }}</span>
            <v-chip size="x-small" label variant="tonal">
              <code class="text-caption">{{ r.rsv_id }}</code>
            </v-chip>
            <v-spacer />
            <span class="text-caption text-medium-emphasis">{{ r.dep_display }} → {{ r.arr_display }}</span>
          </div>
          <div class="d-flex align-center ga-4 text-caption text-medium-emphasis">
            <span>{{ r.price?.toLocaleString() }}원 ({{ r.seat_count }}석)</span>
            <span class="d-flex align-center ga-1">
              <Clock :size="12" />
              {{ r.limit_display }}까지
            </span>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-btn color="error" variant="text" size="small" @click="onCancel(i)">
            <template #prepend><X :size="14" /></template>
            예약 취소
          </v-btn>
        </v-card-actions>
      </v-card>
    </template>
  </div>
</template>
