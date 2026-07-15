<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useTrainStore } from '@/stores/train'
import { getStations } from '@/api'
import type { Station, Train } from '@/types'
import TrainCard from '@/components/TrainCard.vue'

const store = useTrainStore()

const stations = ref<Station[]>([])
const stationNames = computed(() => stations.value.map(s => s.name))
const stationsLoading = ref(false)

// ─── 검색 폼 ──────────────────────────────────

const dep = ref('서울')
const arr = ref('부산')
const depDate = ref(new Date().toISOString().slice(0, 10))
const depTime = ref('09:00')
const trainType = ref('all')
const includeNoSeats = ref(true)
const includeWaiting = ref(false)

// ─── 상태 ─────────────────────────────────────

const selectedIdx = ref<number | null>(null)
const seatOption = ref('general-first')
const tryWaiting = ref(false)
const searched = ref(false)
const depInput = ref('')
const arrInput = ref('')
const depFocused = ref(false)
const arrFocused = ref(false)

const filteredDepStations = computed(() => {
  if (!depInput.value) return stationNames.value.slice(0, 10)
  return stationNames.value.filter(s => s.includes(depInput.value)).slice(0, 10)
})
const filteredArrStations = computed(() => {
  if (!arrInput.value) return stationNames.value.slice(0, 10)
  return stationNames.value.filter(s => s.includes(arrInput.value)).slice(0, 10)
})

// ─── 초기화 ───────────────────────────────────

onMounted(async () => {
  stationsLoading.value = true
  const res = await getStations()
  if (res.data) stations.value = res.data.stations
  stationsLoading.value = false
})

// ─── 검색 ─────────────────────────────────────

async function onSearch() {
  selectedIdx.value = null
  store.clearReserveResult()
  searched.value = true
  store.error = ''
  await store.search({
    dep: dep.value,
    arr: arr.value,
    date: depDate.value.replace(/-/g, ''),
    time: depTime.value.replace(/:/g, '') + '00',
    train_type: trainType.value,
    include_no_seats: includeNoSeats.value,
    include_waiting_list: includeWaiting.value,
  })
}

function onSelectTrain(idx: number) {
  selectedIdx.value = (selectedIdx.value === idx) ? null : idx
}

async function onReserve() {
  if (selectedIdx.value === null) return
  await store.reserve(selectedIdx.value, seatOption.value, tryWaiting.value)
}

function swapStation() {
  [dep.value, arr.value] = [arr.value, dep.value]
  ;[depInput.value, arrInput.value] = [arrInput.value, depInput.value]
}

function selectDepStation(name: string) {
  dep.value = name
  depInput.value = name
  depFocused.value = false
}

function selectArrStation(name: string) {
  arr.value = name
  arrInput.value = name
  arrFocused.value = false
}

function onDepInput(e: Event) {
  const v = (e.target as HTMLInputElement).value
  dep.value = v
  depInput.value = v
}

function onArrInput(e: Event) {
  const v = (e.target as HTMLInputElement).value
  arr.value = v
  arrInput.value = v
}

function onBlurDep() {
  setTimeout(() => { depFocused.value = false }, 200)
}

function onBlurArr() {
  setTimeout(() => { arrFocused.value = false }, 200)
}

// ─── 옵션 ─────────────────────────────────────

const trainTypes = [
  { value: 'all', label: '전체' },
  { value: 'ktx', label: 'KTX' },
  { value: 'ktx-sancheon', label: 'KTX-산천' },
  { value: 'itx-cheongchun', label: 'ITX-청춘' },
  { value: 'itx-saemaeul', label: 'ITX-새마을' },
  { value: 'mugunghwa', label: '무궁화호' },
]

const seatOptions = [
  { value: 'general-first', label: '일반실 우선' },
  { value: 'general-only', label: '일반실만' },
  { value: 'special-first', label: '특실 우선' },
  { value: 'special-only', label: '특실만' },
]

// ─── 선택된 열차 ──────────────────────────────

const selectedTrain = computed<Train | null>(() =>
  selectedIdx.value !== null && store.trains[selectedIdx.value] ? store.trains[selectedIdx.value] : null
)
</script>

<template>
  <div class="p-6 max-w-4xl mx-auto">
    <!-- ───── 검색 폼 ───── -->
    <div class="bg-surface-elevated rounded-xl border border-border">
      <!-- 헤더 -->
      <div class="px-5 py-4 border-b border-border flex items-center justify-between">
        <h2 class="text-text font-semibold">열차 조회</h2>
        <span v-if="!stationsLoading" class="text-text-dim text-[11px]">{{ stations.length }}개역</span>
      </div>

      <!-- 본문 -->
      <div class="p-5 space-y-5">
        <!-- 역 입력 -->
        <div class="grid grid-cols-[1fr_auto_1fr] gap-3 items-end">
          <div class="relative">
            <label class="block text-text-muted text-[11px] mb-1.5 font-medium">출발역</label>
            <input
              v-model="depInput"
              @input="onDepInput"
              @focus="depFocused = true"
              @blur="onBlurDep"
              placeholder="역명 입력"
              class="w-full bg-surface border border-border rounded-lg px-3.5 py-2.5 text-text text-sm placeholder:text-text-dim focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent"
            />
            <div
              v-if="depFocused && filteredDepStations.length > 0"
              class="absolute top-full left-0 right-0 mt-1 z-10 bg-surface-elevated border border-border rounded-lg shadow-xl max-h-48 overflow-y-auto"
            >
              <button
                v-for="s in filteredDepStations"
                :key="s"
                class="w-full text-left px-3.5 py-2 text-text text-sm hover:bg-brand/10 hover:text-brand transition-colors cursor-pointer"
                @mousedown.prevent="selectDepStation(s)"
              >{{ s }}</button>
            </div>
          </div>

          <div class="pb-1">
            <button
              class="w-9 h-9 flex items-center justify-center rounded-lg border border-border text-text-dim hover:text-text hover:border-brand/50 transition-colors cursor-pointer"
              @click="swapStation"
              title="출발/도착 맞바꾸기"
            >
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4"/>
              </svg>
            </button>
          </div>

          <div class="relative">
            <label class="block text-text-muted text-[11px] mb-1.5 font-medium">도착역</label>
            <input
              v-model="arrInput"
              @input="onArrInput"
              @focus="arrFocused = true"
              @blur="onBlurArr"
              placeholder="역명 입력"
              class="w-full bg-surface border border-border rounded-lg px-3.5 py-2.5 text-text text-sm placeholder:text-text-dim focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent"
            />
            <div
              v-if="arrFocused && filteredArrStations.length > 0"
              class="absolute top-full left-0 right-0 mt-1 z-10 bg-surface-elevated border border-border rounded-lg shadow-xl max-h-48 overflow-y-auto"
            >
              <button
                v-for="s in filteredArrStations"
                :key="s"
                class="w-full text-left px-3.5 py-2 text-text text-sm hover:bg-brand/10 hover:text-brand transition-colors cursor-pointer"
                @mousedown.prevent="selectArrStation(s)"
              >{{ s }}</button>
            </div>
          </div>
        </div>

        <!-- 날짜/시간/열차종류 -->
        <div class="grid grid-cols-4 gap-3">
          <div>
            <label class="block text-text-muted text-[11px] mb-1.5 font-medium">출발일</label>
            <input
              v-model="depDate" type="date"
              class="w-full bg-surface border border-border rounded-lg px-3.5 py-2.5 text-text text-sm focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent"
            />
          </div>
          <div>
            <label class="block text-text-muted text-[11px] mb-1.5 font-medium">출발 시각</label>
            <input
              v-model="depTime" type="time"
              class="w-full bg-surface border border-border rounded-lg px-3.5 py-2.5 text-text text-sm focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent"
            />
          </div>
          <div>
            <label class="block text-text-muted text-[11px] mb-1.5 font-medium">열차 종류</label>
            <select
              v-model="trainType"
              class="w-full bg-surface border border-border rounded-lg px-3.5 py-2.5 text-text text-sm focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent"
            >
              <option v-for="t in trainTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
          </div>
          <div class="flex items-end gap-2 pb-1">
            <label class="flex items-center gap-1.5 text-text-muted text-xs cursor-pointer whitespace-nowrap">
              <input v-model="includeNoSeats" type="checkbox" class="accent-brand w-3.5 h-3.5" /> 매진포함
            </label>
            <label class="flex items-center gap-1.5 text-text-muted text-xs cursor-pointer whitespace-nowrap">
              <input v-model="includeWaiting" type="checkbox" class="accent-brand w-3.5 h-3.5" /> 예약대기
            </label>
          </div>
        </div>

        <!-- 검색 버튼 -->
        <div class="flex items-center gap-3">
          <button
            class="flex-1 bg-brand text-black font-semibold rounded-lg py-2.5 text-sm hover:bg-brand-hover transition-colors disabled:opacity-50 cursor-pointer"
            :disabled="store.loading"
            @click="onSearch"
          >
            {{ store.loading ? '조회 중...' : '🔍 조회' }}
          </button>
          <button
            v-if="searched && store.trains.length > 0"
            class="px-4 py-2.5 border border-border text-text-muted rounded-lg text-sm hover:bg-surface transition-colors cursor-pointer"
            @click="selectedIdx = null"
          >
            선택 해제
          </button>
        </div>
      </div>
    </div>

    <!-- ───── 에러 ───── -->
    <div v-if="store.error" class="mt-4 bg-danger/10 border border-danger/20 rounded-xl p-4">
      <p class="text-danger text-sm">{{ store.error }}</p>
    </div>

    <!-- ───── 로딩 스켈레톤 ───── -->
    <div v-if="store.loading" class="mt-4 grid grid-cols-2 gap-3">
      <div v-for="i in 4" :key="i" class="bg-surface-elevated rounded-xl border border-border p-4">
        <div class="h-4 skeleton rounded w-1/3 mb-3"/>
        <div class="h-8 skeleton rounded w-full mb-2"/>
        <div class="h-3 skeleton rounded w-1/2"/>
      </div>
    </div>

    <!-- ───── 검색 결과 ───── -->
    <div v-else-if="store.trains.length > 0" class="mt-4 mb-5">
      <div class="flex items-center justify-between mb-3">
        <span class="text-text-muted text-xs">{{ store.trains.length }}건 조회됨</span>
        <span class="text-text-dim text-[11px]">열차를 선택하면 예약 패널이 열립니다</span>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <TrainCard
          v-for="t in store.trains"
          :key="t.idx"
          :train="t"
          :selected="selectedIdx === t.idx"
          @select="onSelectTrain(t.idx)"
        />
      </div>
    </div>

    <!-- ───── 결과 없음 ───── -->
    <div v-else-if="searched && !store.loading" class="mt-4 bg-surface-elevated rounded-xl border border-border p-10 text-center">
      <p class="text-text-muted text-sm">{{ store.message || '조건에 맞는 열차가 없습니다' }}</p>
      <p class="text-text-dim text-xs mt-2">검색 조건을 변경해보세요</p>
    </div>

    <!-- ───── 예약 패널 ───── -->
    <div
      v-if="selectedTrain"
      class="mt-4 bg-surface-elevated rounded-xl border border-brand/30"
    >
      <div class="px-5 py-3 border-b border-border flex items-center justify-between">
        <h3 class="text-text font-semibold text-sm">예약: {{ selectedTrain.train_type }} {{ selectedTrain.train_no }}</h3>
        <span class="text-text-muted text-xs">{{ selectedTrain.dep_name }}({{ selectedTrain.dep_display }}) → {{ selectedTrain.arr_name }}({{ selectedTrain.arr_display }})</span>
      </div>
      <div class="p-5 space-y-4">
        <!-- 좌석 옵션 -->
        <div>
          <label class="block text-text-muted text-[11px] mb-2 font-medium">좌석 옵션</label>
          <div class="flex flex-wrap gap-2">
            <label
              v-for="opt in seatOptions"
              :key="opt.value"
              :class="[
                'px-3.5 py-2 rounded-lg border text-sm cursor-pointer transition-colors',
                seatOption === opt.value
                  ? 'bg-brand/10 border-brand text-brand'
                  : 'bg-surface border-border text-text-muted hover:border-brand/50'
              ]"
            >
              <input v-model="seatOption" type="radio" :value="opt.value" class="hidden" />
              {{ opt.label }}
            </label>
          </div>
        </div>

        <!-- 예약대기 -->
        <label class="flex items-center gap-2 text-text-muted text-sm cursor-pointer">
          <input v-model="tryWaiting" type="checkbox" class="accent-brand w-4 h-4" />
          <span>매진 시 예약대기 신청</span>
        </label>

        <!-- 예약 버튼 -->
        <button
          class="w-full bg-brand text-black font-semibold rounded-lg py-2.5 text-sm hover:bg-brand-hover transition-colors disabled:opacity-50 cursor-pointer"
          :disabled="store.loading"
          @click="onReserve"
        >
          {{ store.loading ? '예약 중...' : '✅ 예약하기' }}
        </button>
      </div>
    </div>

    <!-- ───── 예약 완료 ───── -->
    <div v-if="store.reserveResult" class="mt-4 bg-surface-elevated rounded-xl border border-success/30">
      <div class="px-5 py-4 border-b border-border">
        <p class="text-success font-semibold">✅ 예약 완료</p>
      </div>
      <div class="p-5 space-y-2 text-sm">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <span class="text-text-muted text-[11px]">예약번호</span>
            <p class="text-text font-mono text-xs mt-0.5">{{ store.reserveResult.rsv_id }}</p>
          </div>
          <div>
            <span class="text-text-muted text-[11px]">열차</span>
            <p class="text-text mt-0.5">{{ store.reserveResult.train_type }} {{ store.reserveResult.train_no }}</p>
          </div>
          <div>
            <span class="text-text-muted text-[11px]">구간</span>
            <p class="text-text mt-0.5">{{ store.reserveResult.dep_name }}→{{ store.reserveResult.arr_name }}</p>
          </div>
          <div>
            <span class="text-text-muted text-[11px]">운임</span>
            <p class="text-text mt-0.5">{{ store.reserveResult.price?.toLocaleString() }}원 ({{ store.reserveResult.seat_count }}석)</p>
          </div>
        </div>
        <div class="bg-warning/10 border border-warning/20 rounded-lg p-3 mt-2">
          <p class="text-warning text-xs font-medium">⏰ 구입기한: {{ store.reserveResult.limit_display }}까지</p>
          <p class="text-text-dim text-[11px] mt-0.5">결제는 코레일 앱 또는 웹사이트에서 직접 해주세요</p>
        </div>
        <button
          class="w-full border border-border text-text-muted rounded-lg py-2 text-sm hover:bg-surface transition-colors cursor-pointer mt-2"
          @click="store.clearReserveResult(); selectedIdx = null"
        >
          새 예약하기
        </button>
      </div>
    </div>
  </div>
</template>
