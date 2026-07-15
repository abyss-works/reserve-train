<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useTrainStore } from '@/stores/train'
import SearchTab from '@/views/SearchTab.vue'
import ReservationsTab from '@/views/ReservationsTab.vue'

const auth = useAuthStore()
const store = useTrainStore()
const activeTab = ref<'search' | 'reservations'>('search')

const korailId = ref('')
const korailPw = ref('')
const loginError = ref('')
const loginLoading = ref(false)

onMounted(() => {
  auth.restore()
})

async function onLogin() {
  if (!korailId.value || !korailPw.value) return
  loginLoading.value = true
  loginError.value = ''
  const ok = await auth.login(korailId.value, korailPw.value)
  loginLoading.value = false
  if (!ok) {
    loginError.value = auth.error || '로그인 실패'
  }
}

function onLogout() {
  auth.logout()
  store.clearAll()
}

function setTab(tab: 'search' | 'reservations') {
  activeTab.value = tab
  if (tab === 'reservations') {
    store.loadReservations()
  }
}
</script>

<template>
  <div class="bg-bg min-h-screen flex">
    <!-- Sidebar -->
    <aside class="w-72 bg-surface border-r border-border flex flex-col shrink-0">
      <div class="p-5 border-b border-border">
        <div class="text-2xl mb-1">🚄</div>
        <h1 class="text-text text-lg font-semibold">KTX 예매 도우미</h1>
      </div>

      <!-- Login Form (not logged in) -->
      <div v-if="!auth.loggedIn" class="p-5 space-y-3">
        <div>
          <label class="block text-text-muted text-xs mb-1">Korail ID</label>
          <input
            v-model="korailId"
            type="text"
            placeholder="회원번호 / 이메일 / 전화번호"
            class="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-text text-sm placeholder:text-text-dim focus:outline-none focus:ring-2 focus:ring-brand"
          />
        </div>
        <div>
          <label class="block text-text-muted text-xs mb-1">비밀번호</label>
          <input
            v-model="korailPw"
            type="password"
            placeholder="********"
            class="w-full bg-surface-elevated border border-border rounded-lg px-3 py-2 text-text text-sm placeholder:text-text-dim focus:outline-none focus:ring-2 focus:ring-brand"
          />
        </div>
        <p v-if="loginError" class="text-danger text-xs">{{ loginError }}</p>
        <button
          class="w-full bg-brand text-black font-semibold rounded-lg py-2 text-sm hover:bg-brand-hover transition-colors disabled:opacity-50 cursor-pointer"
          :disabled="loginLoading"
          @click="onLogin"
        >
          {{ loginLoading ? '로그인 중...' : '🔑 로그인' }}
        </button>
        <p class="text-text-dim text-[10px] text-center">
          로그인 정보는 서버에 저장되지 않습니다
        </p>
      </div>

      <!-- User Info (logged in) -->
      <div v-else class="p-5 space-y-3">
        <div class="flex items-center gap-2">
          <span class="text-brand text-lg">👤</span>
          <span class="text-text text-sm font-medium">{{ auth.userName || '회원' }}</span>
        </div>
        <button
          class="w-full border border-border text-text-muted rounded-lg py-2 text-sm hover:bg-surface-elevated transition-colors cursor-pointer"
          @click="onLogout"
        >
          로그아웃
        </button>
      </div>

      <!-- Navigation Tabs -->
      <nav class="flex-1 p-3 space-y-1">
        <button
          :class="[
            'w-full text-left px-4 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer',
            activeTab === 'search'
              ? 'bg-brand/10 text-brand'
              : 'text-text-muted hover:bg-surface-elevated hover:text-text'
          ]"
          @click="setTab('search')"
        >
          🔍 열차 조회
        </button>
        <button
          :class="[
            'w-full text-left px-4 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer',
            activeTab === 'reservations'
              ? 'bg-brand/10 text-brand'
              : 'text-text-muted hover:bg-surface-elevated hover:text-text'
          ]"
          @click="setTab('reservations')"
        >
          📋 예약 내역
        </button>
      </nav>

      <div class="p-5 border-t border-border">
        <p class="text-text-dim text-[10px]">v0.1.0 · korail2 기반</p>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 overflow-auto">
      <!-- Search Tab -->
      <SearchTab v-if="activeTab === 'search'" />

      <!-- Reservations Tab -->
      <ReservationsTab v-else-if="activeTab === 'reservations'" />
    </main>
  </div>
</template>
