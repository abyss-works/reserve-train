<script setup lang="ts">
import NavBar from '@/components/NavBar.vue'
import { useAuthStore } from '@/stores/auth'
import { onMounted } from 'vue'

const auth = useAuthStore()
onMounted(() => auth.restore())
</script>

<template>
  <div class="bg-bg min-h-screen">
    <router-view />
    <NavBar v-if="auth.loggedIn" />
  </div>
</template>
