<script setup lang="ts">
import type { Train } from '@/types'

const props = defineProps<{ train: Train }>()
const emit = defineEmits<{ select: [] }>()

function seatLabel(available: boolean, waiting: boolean): string {
  if (available) return '가능'
  if (waiting) return '대기'
  return '매진'
}

function seatColor(available: boolean, waiting: boolean): string {
  if (available) return 'text-success'
  if (waiting) return 'text-warning'
  return 'text-danger'
}
</script>

<template>
  <div
    class="bg-surface-elevated rounded-xl border border-border p-4 cursor-pointer active:scale-[0.98] transition-transform"
    @click="emit('select')"
  >
    <div class="flex items-center justify-between mb-2">
      <span class="text-text font-semibold">{{ train.train_type }} {{ train.train_no }}</span>
      <span class="text-text-muted text-xs">{{ train.duration }}</span>
    </div>
    <div class="flex items-center justify-between">
      <div class="text-left">
        <div class="text-text text-lg font-bold">{{ train.dep_display }}</div>
        <div class="text-text-muted text-xs">{{ train.dep_name }}</div>
      </div>
      <div class="flex-1 mx-3 border-t border-border-dashed border-dashed relative">
        <span class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-text-dim text-xs">→</span>
      </div>
      <div class="text-right">
        <div class="text-text text-lg font-bold">{{ train.arr_display }}</div>
        <div class="text-text-muted text-xs">{{ train.arr_name }}</div>
      </div>
    </div>
    <div class="flex gap-3 mt-3 text-xs">
      <span>일반실: <span :class="seatColor(train.general_available, train.waiting_possible)">{{ seatLabel(train.general_available, train.waiting_possible) }}</span></span>
      <span v-if="train.train_type === 'KTX' || train.train_type === 'KTX-산천'">특실: <span :class="seatColor(train.special_available, false)">{{ train.special_available ? '가능' : '매진' }}</span></span>
    </div>
  </div>
</template>
