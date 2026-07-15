<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useTrainStore } from '@/stores/train'
import { getStations, startMonitor } from '@/api'
import type { Station, Train } from '@/types'
import TrainCard from '@/components/TrainCard.vue'

const store = useTrainStore()
const stations = ref<Station[]>([])

const dep = ref('서울')
const arr = ref('부산')
const depDate = ref(new Date().toISOString().slice(0, 10))
const depTime = ref('09:00')
const trainType = ref('all')
const includeNoSeats = ref(true)
const includeWaiting = ref(false)
const selectedIdx = ref<number | null>(null)
const seatOption = ref('general-first')
const tryWaiting = ref(false)
const searched = ref(false)
const monMsg = ref('')
const dateMenu = ref(false)

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

const hours = Array.from({ length: 18 }, (_, i) => i + 6)
const timeMenu = ref(false)
const selectedHour = ref(9)

onMounted(async () => {
  const res = await getStations()
  if (res.data) stations.value = res.data.stations
})

async function onSearch() {
  selectedIdx.value = null
  store.clearReserveResult()
  searched.value = true
  store.error = ''
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
  selectedIdx.value = (selectedIdx.value === idx) ? null : idx
}

async function onReserve() {
  if (selectedIdx.value === null) return
  await store.reserve(selectedIdx.value, seatOption.value, tryWaiting.value)
}

function swapStation() {
  [dep.value, arr.value] = [arr.value, dep.value]
}

async function onAutoMonitor(train: Train) {
  monMsg.value = ''
  const res = await startMonitor({
    dep: dep.value, arr: arr.value,
    date: depDate.value.replace(/-/g, ''),
    time: depTime.value.replace(/:/g, '') + '00',
    train_type: trainType.value,
    train_idx: train.idx, train_no: train.train_no,
    train_label: `${train.train_type} ${train.train_no}`,
    seat_option: seatOption.value,
    try_waiting: tryWaiting.value,
  })
  monMsg.value = res.data ? '🔁 자동 예매가 시작되었습니다' : (res.error || '실패')
  setTimeout(() => { monMsg.value = '' }, 4000)
}

const dateStr = computed(() => {
  if (!depDate.value) return '날짜 선택'
  const d = new Date(depDate.value + 'T00:00:00')
  return `${d.getMonth() + 1}월 ${d.getDate()}일 (${['일','월','화','수','목','금','토'][d.getDay()]})`
})
</script>

<template>
  <div class="pa-4" style="max-width: 900px; margin: 0 auto;">
    <!-- Search Card -->
    <v-card class="mb-4">
      <v-card-title class="d-flex align-center ga-2">
        <v-icon>mdi-magnify</v-icon> 열차 조회
        <v-spacer />
        <span class="text-caption text-medium-emphasis">{{ stations.length }}개역</span>
      </v-card-title>
      <v-divider />

      <v-card-text class="pt-4">
        <v-row dense>
          <!-- 출발역 -->
          <v-col cols="5">
            <v-combobox v-model="dep" :items="stations.map(s => s.name)" label="출발역" variant="outlined" density="compact" hide-details />
          </v-col>
          <v-col cols="2" class="d-flex align-center justify-center">
            <v-btn icon variant="text" size="small" color="grey" @click="swapStation">
              <v-icon>mdi-swap-horizontal</v-icon>
            </v-btn>
          </v-col>
          <!-- 도착역 -->
          <v-col cols="5">
            <v-combobox v-model="arr" :items="stations.map(s => s.name)" label="도착역" variant="outlined" density="compact" hide-details />
          </v-col>
        </v-row>

        <v-row dense class="mt-2">
          <v-col cols="4">
            <v-menu v-model="dateMenu" :close-on-content-click="false">
              <template #activator="{ props }">
                <v-text-field v-bind="props" :model-value="dateStr" label="출발일" variant="outlined" density="compact" hide-details readonly />
              </template>
              <v-date-picker v-model="depDate" @update:model-value="dateMenu = false" />
            </v-menu>
          </v-col>
          <v-col cols="3">
            <v-select v-model="selectedHour" :items="hours" label="출발 시각" variant="outlined" density="compact" hide-details @update:model-value="depTime = String($event).padStart(2,'0') + ':00'" />
          </v-col>
          <v-col cols="3">
            <v-select v-model="trainType" :items="trainTypes" item-title="label" item-value="value" label="열차 종류" variant="outlined" density="compact" hide-details />
          </v-col>
          <v-col cols="2" class="d-flex align-center ga-2">
            <v-checkbox v-model="includeNoSeats" label="매진" hide-details density="compact" />
            <v-checkbox v-model="includeWaiting" label="대기" hide-details density="compact" />
          </v-col>
        </v-row>
      </v-card-text>

      <v-card-actions class="px-4 pb-4">
        <v-btn color="primary" variant="flat" size="large" :loading="store.loading" @click="onSearch">
          <v-icon start>mdi-magnify</v-icon> 조회
        </v-btn>
        <v-spacer />
        <v-btn v-if="searched && store.trains.length > 0" variant="text" color="grey" size="small" @click="selectedIdx = null">선택 해제</v-btn>
      </v-card-actions>
    </v-card>

    <!-- Error -->
    <v-alert v-if="store.error" type="error" variant="tonal" closable class="mb-3" density="compact">{{ store.error }}</v-alert>
    <v-alert v-if="monMsg" type="success" variant="tonal" class="mb-3" density="compact">{{ monMsg }}</v-alert>

    <!-- Loading -->
    <v-row v-if="store.loading" dense>
      <v-col v-for="i in 4" :key="i" cols="6">
        <v-skeleton-loader type="card" />
      </v-col>
    </v-row>

    <!-- Results -->
    <template v-else-if="store.trains.length > 0">
      <div class="text-caption text-medium-emphasis mb-2">{{ store.trains.length }}건 조회됨</div>
      <v-row dense>
        <v-col v-for="t in store.trains" :key="t.idx" cols="6">
          <TrainCard
            :train="t"
            :selected="selectedIdx === t.idx"
            @select="onSelectTrain(t.idx)"
            @auto-monitor="onAutoMonitor(t)"
          />
        </v-col>
      </v-row>
    </template>

    <!-- No results -->
    <v-card v-else-if="searched" class="pa-8 text-center">
      <v-icon size="48" color="grey-lighten-1">mdi-train</v-icon>
      <div class="text-body-1 text-medium-emphasis mt-2">{{ store.message || '조건에 맞는 열차가 없습니다' }}</div>
      <div class="text-caption text-disabled mt-1">검색 조건을 변경해보세요</div>
    </v-card>

    <!-- Reserve Panel -->
    <v-card v-if="selectedIdx !== null && store.trains[selectedIdx]" class="mt-4" color="primary-lighten-5" variant="tonal">
      <v-card-title class="d-flex align-center ga-2 text-body-1 font-weight-bold">
        <v-icon>mdi-ticket-confirmation</v-icon> 예약: {{ store.trains[selectedIdx].train_type }} {{ store.trains[selectedIdx].train_no }}
        <v-spacer />
        <span class="text-caption text-medium-emphasis font-weight-regular">{{ store.trains[selectedIdx].dep_name }} → {{ store.trains[selectedIdx].arr_name }}</span>
      </v-card-title>
      <v-divider />
      <v-card-text>
        <v-radio-group v-model="seatOption" inline hide-details density="compact">
          <v-radio v-for="opt in seatOptions" :key="opt.value" :label="opt.label" :value="opt.value" color="primary" />
        </v-radio-group>
        <v-checkbox v-model="tryWaiting" label="매진 시 예약대기 신청" hide-details density="compact" class="mt-2" />
      </v-card-text>
      <v-card-actions class="px-4 pb-4">
        <v-btn color="primary" variant="flat" :loading="store.loading" @click="onReserve">
          <v-icon start>mdi-check</v-icon> 예약하기
        </v-btn>
      </v-card-actions>
    </v-card>

    <!-- Reserve Result -->
    <v-card v-if="store.reserveResult" class="mt-4" color="success" variant="tonal">
      <v-card-title class="d-flex align-center ga-2">
        <v-icon>mdi-check-circle</v-icon> 예약 완료
      </v-card-title>
      <v-card-text class="pt-0">
        <div class="d-flex ga-4 flex-wrap">
          <div><span class="text-caption text-medium-emphasis">예약번호</span><br><code class="text-body-2">{{ store.reserveResult.rsv_id }}</code></div>
          <div><span class="text-caption text-medium-emphasis">운임</span><br><span class="text-body-2">{{ store.reserveResult.price?.toLocaleString() }}원</span></div>
          <div><span class="text-caption text-medium-emphasis">좌석</span><br><span class="text-body-2">{{ store.reserveResult.seat_count }}석</span></div>
        </div>
        <v-alert type="warning" variant="tonal" density="compact" class="mt-2">
          ⏰ 구입기한: {{ store.reserveResult.limit_display }}까지 · 결제는 코레일 앱/웹에서 직접 해주세요
        </v-alert>
      </v-card-text>
      <v-card-actions>
        <v-btn variant="text" color="grey" @click="store.clearReserveResult(); selectedIdx = null">새 예약하기</v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>
