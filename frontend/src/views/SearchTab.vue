<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTrainStore } from '@/stores/train'
import { getStations } from '@/api'
import type { Station } from '@/types'
import TrainCard from '@/components/TrainCard.vue'

const store = useTrainStore()

const stations = ref<Station[]>([])
const stationsLoading = ref(false)

const dep = ref('서울')
const arr = ref('부산')
const depDate = ref(new Date().toISOString().slice(0, 10))
const depTime = ref('09:00')
const trainType = ref('all')
const includeNoSeats = ref(false)
const includeWaiting = ref(false)
const selectedIdx = ref<number | null>(null)
const seatOption = ref('general-first')
const tryWaiting = ref(false)
const searched = ref(false)

onMounted(async () => {
  stationsLoading.value = true
  const res = await getStations()
  if (res.data) {
    stations.value = res.data.stations
  }
  stationsLoading.value = false
})

async function onSearch() {
  selectedIdx.value = null
  store.clearReserveResult()
  searched.value = true
  store.error = ''  // Clear previous errors
  await store.search({
    dep: dep.value, arr: arr.value,
    date: depDate.value.replace(/-/g, ''),
    time: depTime.value.replace(/:/g, '') + '00',
    train_type: trainType.value,
    include_no_seats: includeNoSeats.value,
    include_waiting_list: includeWaiting.value,
  })
}

function onSelectTrain(idx: number) {
  selectedIdx.value = idx
}

async function onReserve() {
  if (selectedIdx.value === null) return
  await store.reserve(selectedIdx.value, seatOption.value, tryWaiting.value)
}

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

function swapStation() {
  const tmp = dep.value
  dep.value = arr.value
  arr.value = tmp
}
</script>

<template>
  <div class="p-6 max-w-4xl">
    <!-- Search Form -->
    <div class="bg-surface-elevated rounded-xl border border-border p-5 mb-5">
      <h2 class="text-text font-semibold mb-4">🔍 열차 조회</h2>

      <div class="grid grid-cols-5 gap-3 mb-3 items-end">
        <div>
          <label class="block text-text-muted text-xs mb-1">출발역</label>
          <div class="flex gap-1">
            <input v-model="dep" list="stations-dep" placeholder="서울"
              class="flex-1 bg-surface border border-border rounded-lg px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-brand" />
            <datalist id="stations-dep">
              <option v-for="s in stations" :key="s.code" :value="s.name" />
            </datalist>
          </div>
        </div>
        <div class="text-center pt-5">
          <button class="text-text-dim hover:text-text cursor-pointer text-lg" @click="swapStation" title="출발/도착 변경">⇄</button>
        </div>
        <div>
          <label class="block text-text-muted text-xs mb-1">도착역</label>
          <input v-model="arr" list="stations-arr" placeholder="부산"
            class="w-full bg-surface border border-border rounded-lg px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-brand" />
          <datalist id="stations-arr">
            <option v-for="s in stations" :key="s.code" :value="s.name" />
          </datalist>
        </div>
        <div>
          <label class="block text-text-muted text-xs mb-1">출발일</label>
          <input v-model="depDate" type="date"
            class="w-full bg-surface border border-border rounded-lg px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-brand" />
        </div>
        <div>
          <label class="block text-text-muted text-xs mb-1">출발 시각</label>
          <input v-model="depTime" type="time"
            class="w-full bg-surface border border-border rounded-lg px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-brand" />
        </div>
      </div>

      <div class="flex items-center gap-4 mb-4">
        <select v-model="trainType"
          class="bg-surface border border-border rounded-lg px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-brand">
          <option v-for="t in trainTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>
        <label class="flex items-center gap-1.5 text-text-muted text-xs cursor-pointer">
          <input v-model="includeNoSeats" type="checkbox" class="accent-brand" /> 매진 포함
        </label>
        <label class="flex items-center gap-1.5 text-text-muted text-xs cursor-pointer">
          <input v-model="includeWaiting" type="checkbox" class="accent-brand" /> 예약대기
        </label>
        <span v-if="stationsLoading" class="text-text-dim text-xs">역 정보 로딩 중...</span>
        <span v-else class="text-text-dim text-xs">{{ stations.length }}개 역</span>
      </div>

      <button
        class="bg-brand text-black font-semibold rounded-lg px-6 py-2 text-sm hover:bg-brand-hover transition-colors disabled:opacity-50 cursor-pointer"
        :disabled="store.loading"
        @click="onSearch"
      >
        {{ store.loading ? '조회 중...' : '🔍 조회' }}
      </button>
    </div>

    <!-- Error -->
    <div v-if="store.error" class="bg-danger/10 border border-danger/20 rounded-xl p-4 mb-4">
      <p class="text-danger text-sm">{{ store.error }}</p>
    </div>

    <!-- Loading -->
    <div v-if="store.loading" class="grid grid-cols-2 gap-3 mb-4">
      <div v-for="i in 4" :key="i" class="bg-surface-elevated rounded-xl border border-border p-4">
        <div class="h-4 skeleton rounded w-1/3 mb-3"/>
        <div class="h-6 skeleton rounded w-full mb-2"/>
        <div class="h-3 skeleton rounded w-1/2"/>
      </div>
    </div>

    <!-- Results -->
    <div v-else-if="store.trains.length > 0" class="mb-5">
      <p class="text-text-muted text-xs mb-3">{{ store.trains.length }}건 조회됨</p>
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

    <!-- No results -->
    <div v-else-if="searched && !store.loading" class="bg-surface-elevated rounded-xl border border-border p-8 text-center mb-5">
      <p class="text-text-muted text-sm">{{ store.message || '검색 결과가 없습니다' }}</p>
    </div>

    <!-- Reserve Panel -->
    <div v-if="selectedIdx !== null && store.trains[selectedIdx]" class="bg-surface-elevated rounded-xl border border-border p-5 mb-5">
      <h3 class="text-text font-semibold mb-3">✅ 예약: {{ store.trains[selectedIdx].train_type }} {{ store.trains[selectedIdx].train_no }}</h3>
      <div class="flex items-center gap-4 mb-3">
        <span class="text-text-muted text-sm">좌석:</span>
        <label v-for="opt in seatOptions" :key="opt.value" class="flex items-center gap-1.5 text-text-muted text-sm cursor-pointer">
          <input v-model="seatOption" type="radio" :value="opt.value" class="accent-brand" /> {{ opt.label }}
        </label>
      </div>
      <label class="flex items-center gap-1.5 text-text-muted text-sm cursor-pointer mb-4">
        <input v-model="tryWaiting" type="checkbox" class="accent-brand" /> 매진 시 예약대기
      </label>
      <button
        class="bg-brand text-black font-semibold rounded-lg px-6 py-2 text-sm hover:bg-brand-hover transition-colors disabled:opacity-50 cursor-pointer"
        :disabled="store.loading"
        @click="onReserve"
      >
        {{ store.loading ? '예약 중...' : '✅ 예약하기' }}
      </button>
    </div>

    <!-- Reserve Result -->
    <div v-if="store.reserveResult" class="bg-surface-elevated rounded-xl border border-brand/30 p-5 mb-5">
      <p class="text-success font-semibold text-lg mb-3">✅ 예약 완료!</p>
      <div class="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p class="text-text-muted">예약번호</p>
          <p class="text-text font-mono">{{ store.reserveResult.rsv_id }}</p>
        </div>
        <div>
          <p class="text-text-muted">열차</p>
          <p class="text-text">{{ store.reserveResult.train_type }} {{ store.reserveResult.train_no }}</p>
        </div>
        <div>
          <p class="text-text-muted">구간</p>
          <p class="text-text">{{ store.reserveResult.dep_name }}({{ store.reserveResult.dep_display }}) → {{ store.reserveResult.arr_name }}({{ store.reserveResult.arr_display }})</p>
        </div>
        <div>
          <p class="text-text-muted">운임</p>
          <p class="text-text">{{ store.reserveResult.price?.toLocaleString() }}원 ({{ store.reserveResult.seat_count }}석)</p>
        </div>
        <div class="col-span-2">
          <p class="text-warning">⏰ 구입기한: {{ store.reserveResult.limit_display }}까지</p>
          <p class="text-text-dim text-xs mt-1">결제는 코레일 앱/웹에서 직접 해주세요</p>
        </div>
      </div>
      <button
        class="mt-4 border border-border text-text-muted rounded-lg px-4 py-2 text-sm hover:bg-surface transition-colors cursor-pointer"
        @click="store.clearReserveResult(); selectedIdx = null"
      >
        새 예약하기
      </button>
    </div>
  </div>
</template>
