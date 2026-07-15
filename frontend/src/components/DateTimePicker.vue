<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{ modelDate: string; modelTime: string }>()
const emit = defineEmits<{ 'update:modelDate': [v: string]; 'update:modelTime': [v: string] }>()

const DAY_NAMES = ['일', '월', '화', '수', '목', '금', '토']

const open = ref(false)

// 날짜
const today = new Date()
const viewYear = ref(today.getFullYear())
const viewMonth = ref(today.getMonth() + 1)

const weeks = computed(() => {
  const first = new Date(viewYear.value, viewMonth.value - 1, 1)
  const last = new Date(viewYear.value, viewMonth.value, 0)
  const startDow = first.getDay()
  const daysInMonth = last.getDate()
  const rows: { day: number; disabled: boolean }[][] = []
  let row: { day: number; disabled: boolean }[] = []
  for (let i = 0; i < startDow; i++) {
    row.push({ day: 0, disabled: true })
  }
  for (let d = 1; d <= daysInMonth; d++) {
    const date = new Date(viewYear.value, viewMonth.value - 1, d)
    const disabled = date < new Date(today.getFullYear(), today.getMonth(), today.getDate())
    row.push({ day: d, disabled })
    if (row.length === 7) {
      rows.push(row)
      row = []
    }
  }
  if (row.length > 0) {
    while (row.length < 7) row.push({ day: 0, disabled: true })
    rows.push(row)
  }
  return rows
})

function prevMonth() {
  if (viewMonth.value === 1) { viewYear.value--; viewMonth.value = 12 }
  else viewMonth.value--
}

function nextMonth() {
  if (viewMonth.value === 12) { viewYear.value++; viewMonth.value = 1 }
  else viewMonth.value++
}

const selectedDateStr = computed(() => {
  const parts = props.modelDate.split('-')
  if (parts.length !== 3) return ''
  const d = new Date(+parts[0], +parts[1] - 1, +parts[2])
  return `${parts[1]}월 ${parts[2]}일 (${DAY_NAMES[d.getDay()]})`
})

function selectDay(day: number) {
  const m = String(viewMonth.value).padStart(2, '0')
  const d = String(day).padStart(2, '0')
  emit('update:modelDate', `${viewYear.value}-${m}-${d}`)
}

const selHour = computed(() => {
  const h = props.modelTime.split(':')[0]
  return h ? `${h}시` : ''
})

function selectHour(h: number) {
  emit('update:modelTime', `${String(h).padStart(2, '0')}:00`)
}

const hours = Array.from({ length: 18 }, (_, i) => i + 6) // 06~23

function formatLabel(d: string, t: string): string {
  if (!d) return '출발일 · 시간 선택'
  const parts = d.split('-')
  if (parts.length !== 3) return '출발일 · 시간 선택'
  const dt = new Date(+parts[0], +parts[1] - 1, +parts[2])
  const dow = DAY_NAMES[dt.getDay()]
  const h = t.split(':')[0]
  return `${parts[1]}월 ${parts[2]}일(${dow}) ${h ? `${h}:00` : ''}`
}

function onConfirm() {
  open.value = false
}
</script>

<template>
  <div class="relative">
    <!-- Trigger Button -->
    <button
      class="w-full bg-surface border border-border rounded-lg px-3.5 py-2.5 text-sm text-left focus:outline-none focus:ring-2 focus:ring-brand cursor-pointer"
      :class="modelDate ? 'text-text' : 'text-text-dim'"
      @click="open = !open"
    >
      {{ formatLabel(modelDate, modelTime) }}
    </button>

    <!-- Modal -->
    <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="open = false">
      <div class="bg-surface-elevated border border-border rounded-2xl shadow-2xl w-[340px] overflow-hidden">
        <!-- Header: month nav -->
        <div class="flex items-center justify-between px-5 py-3 border-b border-border">
          <button class="text-text-dim hover:text-text cursor-pointer p-1" @click="prevMonth">‹</button>
          <span class="text-text font-medium text-sm">{{ viewYear }}년 {{ viewMonth }}월</span>
          <button class="text-text-dim hover:text-text cursor-pointer p-1" @click="nextMonth">›</button>
        </div>

        <!-- Calendar grid -->
        <div class="px-4 py-3">
          <div class="grid grid-cols-7 mb-1">
            <div v-for="d in DAY_NAMES" :key="d" class="text-center text-text-dim text-[11px] py-1 font-medium">{{ d }}</div>
          </div>
          <div v-for="(row, ri) in weeks" :key="ri" class="grid grid-cols-7">
            <button
              v-for="(cell, ci) in row" :key="ci"
              :disabled="cell.disabled || cell.day === 0"
              :class="[
                'text-center py-2 text-sm rounded-lg transition-colors cursor-pointer',
                cell.disabled || cell.day === 0 ? 'text-text-dim/30 cursor-default' :
                modelDate === `${viewYear}-${String(viewMonth).padStart(2,'0')}-${String(cell.day).padStart(2,'0')}`
                  ? 'bg-brand text-black font-semibold'
                  : 'text-text hover:bg-brand/10 hover:text-brand'
              ]"
              @click="selectDay(cell.day)"
            >{{ cell.day || '' }}</button>
          </div>
        </div>

        <!-- Time slots -->
        <div class="px-4 pb-2">
          <p class="text-text-muted text-[11px] font-medium mb-2">출발 시각</p>
          <div class="grid grid-cols-6 gap-1.5 max-h-[120px] overflow-y-auto">
            <button
              v-for="h in hours" :key="h"
              :class="[
                'py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer',
                selHour === `${h}시`
                  ? 'bg-brand text-black'
                  : 'bg-surface text-text-muted hover:bg-brand/10 hover:text-brand'
              ]"
              @click="selectHour(h)"
            >{{ h }}:00</button>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-4 py-3 border-t border-border flex justify-end gap-2">
          <button class="px-4 py-1.5 text-xs text-text-muted hover:text-text cursor-pointer" @click="open = false">취소</button>
          <button
            class="px-4 py-1.5 text-xs bg-brand text-black font-semibold rounded-lg hover:bg-brand-hover transition-colors cursor-pointer"
            :disabled="!modelDate"
            @click="onConfirm"
          >확인</button>
        </div>
      </div>
    </div>
  </div>
</template>
