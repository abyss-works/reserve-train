<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useTrainStore } from '@/stores/train'
import SearchTab from '@/views/SearchTab.vue'
import ReservationsTab from '@/views/ReservationsTab.vue'
import MonitorTab from '@/views/MonitorTab.vue'
import { Train, User, LogOut, Search, Ticket, Clock } from 'lucide-vue-next'

const auth = useAuthStore()
const store = useTrainStore()
const activeTab = ref<'search' | 'reservations' | 'monitor'>('search')

const korailId = ref('')
const korailPw = ref('')
const loginError = ref('')
const loginLoading = ref(false)

onMounted(() => { auth.restore() })

async function onLogin() {
  if (!korailId.value || !korailPw.value) return
  loginLoading.value = true; loginError.value = ''
  const ok = await auth.login(korailId.value, korailPw.value)
  loginLoading.value = false
  if (!ok) loginError.value = auth.error || '로그인 실패'
}

function onLogout() { auth.logout(); store.clearAll() }

function setTab(tab: 'search' | 'reservations' | 'monitor') {
  activeTab.value = tab
  if (tab === 'reservations') store.loadReservations()
}
</script>

<template>
  <v-app>
    <!-- Top Bar -->
    <v-app-bar elevation="1">
      <v-app-bar-title class="d-flex align-center ga-2">
        <Train :size="22" /> KTX 예매 도우미
      </v-app-bar-title>
      <template v-if="auth.loggedIn" #append>
        <v-btn variant="text" size="small" @click="onLogout">
          <template #prepend><LogOut :size="16" /></template>
          {{ auth.userName || '회원' }}
        </v-btn>
      </template>
    </v-app-bar>

    <!-- Permanent Sidebar -->
    <v-navigation-drawer permanent width="260">
      <!-- Logo area -->
      <div class="pa-4 d-flex align-center ga-2 border-b">
        <Train :size="20" class="text-primary" />
        <span class="font-weight-bold text-body-1">KTX 예매</span>
      </div>

      <!-- Login form / User info -->
      <template v-if="!auth.loggedIn">
        <div class="pa-3">
          <v-text-field v-model="korailId" label="Korail ID" placeholder="회원번호/이메일/전화번호" variant="outlined" density="compact" hide-details class="mb-2" />
          <v-text-field v-model="korailPw" label="비밀번호" type="password" variant="outlined" density="compact" hide-details class="mb-2" />
          <p v-if="loginError" class="text-caption text-error mb-1">{{ loginError }}</p>
          <v-btn color="primary" block :loading="loginLoading" @click="onLogin">로그인</v-btn>
        </div>
      </template>
      <template v-else>
        <div class="pa-3 d-flex align-center ga-2">
          <User :size="18" />
          <span class="text-body-2">{{ auth.userName || '회원' }}</span>
        </div>
      </template>

      <v-divider />

      <!-- Navigation -->
      <v-list nav density="comfortable">
        <v-list-item title="열차 조회" :active="activeTab === 'search'" @click="setTab('search')">
          <template #prepend><Search :size="18" /></template>
        </v-list-item>
        <v-list-item title="예약 내역" :active="activeTab === 'reservations'" @click="setTab('reservations')">
          <template #prepend><Ticket :size="18" /></template>
        </v-list-item>
        <v-list-item title="자동 예매" :active="activeTab === 'monitor'" @click="setTab('monitor')">
          <template #prepend><Clock :size="18" /></template>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <!-- Main Content -->
    <v-main class="bg-grey-lighten-3" style="min-height: 100vh;">
      <SearchTab v-if="activeTab === 'search'" />
      <ReservationsTab v-else-if="activeTab === 'reservations'" />
      <MonitorTab v-else-if="activeTab === 'monitor'" />
    </v-main>
  </v-app>
</template>
