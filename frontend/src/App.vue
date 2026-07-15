<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'
import { useAuthStore } from '@/stores/auth'
import { useTrainStore } from '@/stores/train'
import { Train, User, LogOut, Search, Ticket, Clock, Menu } from 'lucide-vue-next'

const { mobile } = useDisplay()
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const store = useTrainStore()
const drawer = ref(false)

const korailId = ref('')
const korailPw = ref('')
const loginError = ref('')
const loginLoading = ref(false)

const activeTab = computed(() => (route.name as string) || 'search')
const drawerProps = computed(() => mobile.value
  ? { temporary: true, width: 280 }
  : { permanent: true, width: 240 }
)

onMounted(() => { auth.restore() })

async function onLogin() {
  if (!korailId.value || !korailPw.value) return
  loginLoading.value = true; loginError.value = ''
  const ok = await auth.login(korailId.value, korailPw.value)
  loginLoading.value = false
  if (!ok) loginError.value = auth.error || '로그인 실패'
}

function onLogout() { auth.logout(); store.clearAll(); drawer.value = false }

function goTab(name: string) {
  router.push({ name }); drawer.value = false
  if (name === 'reservations') store.loadReservations()
}
</script>

<template>
  <v-app>
    <v-app-bar elevation="1">
      <v-app-bar-nav-icon v-if="mobile" @click="drawer = !drawer">
        <Menu :size="20" />
      </v-app-bar-nav-icon>
      <v-app-bar-title class="d-flex align-center ga-2 text-body-1 font-weight-bold">
        <Train :size="20" /> KTX 예매
      </v-app-bar-title>
      <template v-if="auth.loggedIn && !mobile" #append>
        <v-btn variant="text" size="small" @click="onLogout">
          <template #prepend><LogOut :size="16" /></template>
          {{ auth.userName || '회원' }}
        </v-btn>
      </template>
    </v-app-bar>

    <v-navigation-drawer v-model="drawer" v-bind="drawerProps">
      <div class="pa-4 d-flex align-center ga-2 border-b">
        <Train :size="20" class="text-primary" />
        <span class="font-weight-bold text-body-1">KTX 예매</span>
      </div>

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
          <v-spacer />
          <v-btn v-if="mobile" icon variant="text" size="x-small" @click="onLogout">
            <LogOut :size="16" />
          </v-btn>
        </div>
      </template>

      <v-divider />

      <v-list nav density="comfortable">
        <v-list-item title="열차 조회" :active="activeTab === 'search'" @click="goTab('search')">
          <template #prepend><Search :size="18" /></template>
        </v-list-item>
        <v-list-item title="예약 내역" :active="activeTab === 'reservations'" @click="goTab('reservations')">
          <template #prepend><Ticket :size="18" /></template>
        </v-list-item>
        <v-list-item title="자동 예매" :active="activeTab === 'monitor'" @click="goTab('monitor')">
          <template #prepend><Clock :size="18" /></template>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main class="bg-grey-lighten-3" style="min-height: 100dvh;">
      <router-view />
    </v-main>
  </v-app>
</template>
