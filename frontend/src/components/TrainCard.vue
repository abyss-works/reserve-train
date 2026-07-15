<script setup lang="ts">
import type { Train } from '@/types'

const props = defineProps<{ train: Train; selected?: boolean }>()
const emit = defineEmits<{ select: [] }>()
</script>

<template>
  <div
    :class="[
      'rounded-xl border p-4 cursor-pointer active:scale-[0.99] transition-all',
      selected ? 'bg-brand/10 border-brand ring-1 ring-brand/30' : 'bg-surface-elevated border-border hover:border-brand/40'
    ]"
    @click="emit('select')"
  >
    <!-- Header: Train type + Duration -->
    <div class="flex items-center justify-between mb-2.5">
      <span class="text-text font-semibold text-sm">{{ train.train_type }} <span class="text-text-muted font-normal">{{ train.train_no }}</span></span>
      <span class="text-text-dim text-[11px] font-medium px-2 py-0.5 rounded-full bg-surface">{{ train.duration }}</span>
    </div>

    <!-- Time + Route -->
    <div class="flex items-center gap-2">
      <!-- Departure -->
      <div class="text-center min-w-[60px]">
        <div class="text-text text-base font-bold leading-tight">{{ train.dep_display }}</div>
        <div class="text-text-muted text-[11px] mt-0.5 truncate">{{ train.dep_name }}</div>
      </div>

      <!-- Arrow line -->
      <div class="flex-1 flex items-center gap-1">
        <div class="h-px flex-1 bg-border"></div>
        <svg class="w-3.5 h-3.5 text-text-dim shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        <div class="h-px flex-1 bg-border"></div>
      </div>

      <!-- Arrival -->
      <div class="text-center min-w-[60px]">
        <div class="text-text text-base font-bold leading-tight">{{ train.arr_display }}</div>
        <div class="text-text-muted text-[11px] mt-0.5 truncate">{{ train.arr_name }}</div>
      </div>
    </div>

    <!-- Seat status -->
    <div class="flex gap-3 mt-3 pt-2.5 border-t border-border">
      <div class="flex items-center gap-1.5 text-[11px]">
        <span :class="train.general_available ? 'w-2 h-2 rounded-full bg-success' : train.waiting_possible ? 'w-2 h-2 rounded-full bg-warning' : 'w-2 h-2 rounded-full bg-danger'"></span>
        <span class="text-text-muted">일반실 <span :class="train.general_available ? 'text-success' : train.waiting_possible ? 'text-warning' : 'text-danger'">{{ train.general_available ? '가능' : train.waiting_possible ? '대기' : '매진' }}</span></span>
      </div>
      <div v-if="train.train_type === 'KTX' || train.train_type === 'KTX-산천'" class="flex items-center gap-1.5 text-[11px]">
        <span :class="train.special_available ? 'w-2 h-2 rounded-full bg-success' : 'w-2 h-2 rounded-full bg-danger'"></span>
        <span class="text-text-muted">특실 <span :class="train.special_available ? 'text-success' : 'text-danger'">{{ train.special_available ? '가능' : '매진' }}</span></span>
      </div>
    </div>
  </div>
</template>
