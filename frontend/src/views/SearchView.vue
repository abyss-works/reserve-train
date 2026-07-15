<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTrainStore } from '@/stores/train'
import TrainCard from '@/components/TrainCard.vue'

const router = useRouter()
const auth = useAuthStore()
const store = useTrainStore()

const dep = ref('서울')
const arr = ref('부산')
const depDate = ref(new Date().toISOString().slice(0, 10))
const depTime = ref('09:00')
const trainType = ref('ktx')
const includeNoSeats = ref(false)
const includeWaiting = ref(false)
const selectedIdx = ref<number | null>(null)
const seatOption = ref('general-first')
const tryWaiting = ref(false)
const searched = ref(false)

onMounted(() => {
  if (!auth.loggedIn) router.replace('/login')
})

async function onSearch() {
  selectedIdx.value = null
  store.reserveResult = null
  searched.value = true
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
  selectedIdx.value = idx
}

async function onReserve() {
  if (selectedIdx.value === null) return
  const ok = await store.reserve(selectedIdx.value, seatOption.value, tryWaiting.value)
  if (!ok) {
    // If 401 error, redirect to login
    if (store.error?.includes('로그인')) {
      await auth.logout()
      router.replace('/login')
    }
  }
}

function onLogout() {
  auth.logout()
  router.replace('/login')
}
</script>

<template>
  <div class="min-h-screen pb-20">
    <!-- Header -->
    <header class="sticky top-0 z-40 bg-bg/80 backdrop-blur-lg border-b border-border-subtle safe-top">
      <div class="max-w-lg mx-auto px-4 py-3 flex items-center justify-between">
        <h1 class="text-text text-lg font-semibold">🚄 KTX 예매</h1>
        <button class="text-text-dim text-xs cursor-pointer" @click="onLogout">로그아웃</button>
      </div>
    </header>

    <main class="max-w-lg mx-auto px-4 pt-4">
      <!-- Search Form -->
      <div class="bg-surface-elevated rounded-xl border border-border p-4 mb-4">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-text-muted text-xs mb-1">출발역</label>
            <input v-model="dep" class="w-full bg-surface border border-border rounded-lg px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-brand" />
          </div>
          <div>
            <label class="block text-text-muted text-xs mb-1">도착역</label>
            <input v-model="arr" class="w-full bg-surface border border-border rounded-lg px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-brand" />
          </div>
          <div>
            <label class="block text-text-muted text-xs mb-1">날짜</label>
            <input v-model="depDate" type="date" class="w-full bg-surface border border-border rounded-lg px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-brand" />
          </div>
          <div>
            <label class="block text-text-muted text-xs mb-1">시각 이후</label>
            <input v-model="depTime" type="time" class="w-full bg-surface border border-border rounded-lg px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-brand" />
          </div>
        </div>
        <div class="flex items-center gap-4 mt-3">
          <select v-model="trainType" class="bg-surface border border-border rounded-lg px-3 py-2 text-text text-sm focus:outline-none focus:ring-2 focus:ring-brand">
            <option value="ktx">KTX</option>
            <option value="ktx-sancheon">KTX-산천</option>
            <option value="itx-cheongchun">ITX-청춘</option>
            <option value="itx-saemaeul">ITX-새마을</option>
            <option value="mugunghwa">무궁화호</option>
            <option value="all">전체</option>
          </select>
          <label class="flex items-center gap-1 text-text-muted text-xs cursor-pointer">
            <input v-model="includeNoSeats" type="checkbox" class="accent-brand" /> 매진포함
          </label>
          <label class="flex items-center gap-1 text-text-muted text-xs cursor-pointer">
            <input v-model="includeWaiting" type="checkbox" class="accent-brand" /> 예약대기
          </label>
        </div>
        <button
          class="w-full mt-3 bg-brand text-black font-semibold rounded-xl py-2.5 hover:bg-brand-hover transition-colors disabled:opacity-50 cursor-pointer"
          :disabled="store.loading"
          @click="onSearch"
        >
          {{ store.loading ? '조회 중...' : '🔍 조회' }}
        </button>
      </div>

      <!-- Error -->
      <p v-if="store.error && !searched" class="text-danger text-sm text-center mb-4">{{ store.error }}</p>

      <!-- Train List -->
      <div v-if="store.trains.length > 0" class="space-y-3 pb-4">
        <p class="text-text-muted text-xs">{{ store.trains.length }}건 조회됨</p>
        <TrainCard
          v-for="t in store.trains"
          :key="t.idx"
          :train="t"
          @select="onSelectTrain(t.idx)"
        />
      </div>

      <!-- No results -->
      <div v-else-if="searched && !store.loading" class="text-center pt-8">
        <p class="text-text-muted text-sm">{{ store.message || '검색 결과가 없습니다' }}</p>
      </div>

      <!-- Loading skeleton -->
      <div v-if="store.loading" class="space-y-3 pt-2">
        <div v-for="i in 3" :key="i" class="bg-surface-elevated rounded-xl border border-border p-4">
          <div class="h-4 skeleton rounded w-1/3 mb-3"/>
          <div class="h-6 skeleton rounded w-full mb-2"/>
          <div class="h-3 skeleton rounded w-1/2"/>
        </div>
      </div>

      <!-- Reserve Panel (when train selected) -->
      <div v-if="selectedIdx !== null && store.trains[selectedIdx]" class="bg-surface-elevated rounded-xl border border-border p-4 mb-4">
        <p class="text-text text-sm font-semibold mb-2">예약: {{ store.trains[selectedIdx].train_type }} {{ store.trains[selectedIdx].train_no }}</p>
        <div class="flex gap-2 mb-3">
          <label class="flex items-center gap-1 text-text-muted text-xs cursor-pointer">
            <input v-model="seatOption" type="radio" value="general-first" class="accent-brand" /> 일반실 우선
          </label>
          <label class="flex items-center gap-1 text-text-muted text-xs cursor-pointer">
            <input v-model="seatOption" type="radio" value="general-only" class="accent-brand" /> 일반실만
          </label>
          <label class="flex items-center gap-1 text-text-muted text-xs cursor-pointer">
            <input v-model="seatOption" type="radio" value="special-first" class="accent-brand" /> 특실 우선
          </label>
        </div>
        <label class="flex items-center gap-1 text-text-muted text-xs cursor-pointer mb-3">
          <input v-model="tryWaiting" type="checkbox" class="accent-brand" /> 매진 시 예약대기
        </label>
        <button
          class="w-full bg-brand text-black font-semibold rounded-xl py-2.5 hover:bg-brand-hover transition-colors disabled:opacity-50 cursor-pointer"
          :disabled="store.loading"
          @click="onReserve"
        >
          {{ store.loading ? '예약 중...' : '✅ 예약하기' }}
        </button>
        <p v-if="store.error" class="text-danger text-xs mt-2">{{ store.error }}</p>
      </div>

      <!-- Reserve Result -->
      <div v-if="store.reserveResult" class="bg-surface-elevated rounded-xl border border-border p-4 mb-4">
        <p class="text-success font-semibold mb-2">✅ 예약 완료!</p>
        <div class="space-y-1 text-sm">
          <p class="text-text-muted">예약번호: <span class="text-text font-mono">{{ store.reserveResult.rsv_id }}</span></p>
          <p class="text-text-muted">열차: {{ store.reserveResult.train_type }} {{ store.reserveResult.train_no }}</p>
          <p class="text-text-muted">{{ store.reserveResult.dep_name }}({{ store.reserveResult.dep_display }}) → {{ store.reserveResult.arr_name }}({{ store.reserveResult.arr_display }})</p>
          <p class="text-text-muted">{{ store.reserveResult.price?.toLocaleString() }}원 ({{ store.reserveResult.seat_count }}석)</p>
          <p class="text-warning text-xs mt-2">⏰ 구입기한: {{ store.reserveResult.limit_display }}까지</p>
          <p class="text-text-dim text-xs">결제는 코레일 앱/웹에서 직접 해주세요</p>
        </div>
        <button
          class="w-full mt-3 bg-surface border border-border text-text rounded-xl py-2 hover:bg-surface-elevated transition-colors cursor-pointer"
          @click="store.clearReserveResult()"
        >
          새 예약하기
        </button>
      </div>
    </main>
  </div>
</template>
