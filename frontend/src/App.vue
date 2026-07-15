<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useTrainStore } from '@/stores/train'
import SearchTab from '@/views/SearchTab.vue'
import ReservationsTab from '@/views/ReservationsTab.vue'
import MonitorTab from '@/views/MonitorTab.vue'

const auth = useAuthStore()
const store = useTrainStore()
const drawer = ref(false)
const activeTab = ref<'search' | 'reservations' | 'monitor'>('search')

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
  drawer.value = false
}

function setTab(tab: 'search' | 'reservations' | 'monitor') {
  activeTab.value = tab
  drawer.value = false
  if (tab === 'reservations') store.loadReservations()
}
</script>

<template>
  <v-app>
    <!-- App Bar -->
    <v-app-bar elevation="1">
      <v-app-bar-nav-icon @click="drawer = !drawer" />
      <v-app-bar-title>🚄 KTX 예매 도우미</v-app-bar-title>

      <template v-if="auth.loggedIn" #append>
        <v-btn variant="text" prepend-icon="mdi-logout" size="small" @click="onLogout">
          {{ auth.userName || '회원' }}
        </v-btn>
      </template>
    </v-app-bar>

    <!-- Navigation Drawer -->
    <v-navigation-drawer v-model="drawer" temporary>
      <!-- Login (not logged in) -->
      <template v-if="!auth.loggedIn">
        <v-list-item class="pa-4">
          <v-text-field v-model="korailId" label="Korail ID" placeholder="회원번호/이메일/전화번호" variant="outlined" density="compact" hide-details />
        </v-list-item>
        <v-list-item class="pa-4 pt-0">
          <v-text-field v-model="korailPw" label="비밀번호" type="password" variant="outlined" density="compact" hide-details />
        </v-list-item>
        <v-list-item v-if="loginError" class="text-caption text-error px-4 pb-2">{{ loginError }}</v-list-item>
        <v-list-item class="px-4 pb-2">
          <v-btn color="primary" block :loading="loginLoading" @click="onLogin">로그인</v-btn>
        </v-list-item>
      </template>

      <!-- Logged in -->
      <template v-else>
        <v-list-item class="text-body-2 font-weight-medium px-4 py-3">
          👤 {{ auth.userName || '회원' }}
        </v-list-item>
      </template>

      <v-divider />

      <!-- Navigation -->
      <v-list nav>
        <v-list-item prepend-icon="mdi-magnify" title="열차 조회" :active="activeTab === 'search'" @click="setTab('search')" />
        <v-list-item prepend-icon="mdi-ticket-outline" title="예약 내역" :active="activeTab === 'reservations'" @click="setTab('reservations')" />
        <v-list-item prepend-icon="mdi-clock-outline" title="자동 예매" :active="activeTab === 'monitor'" @click="setTab('monitor')" />
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
