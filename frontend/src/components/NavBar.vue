<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const tabs = [
  { name: '조회', path: '/', icon: 'search' },
  { name: '예약내역', path: '/reservations', icon: 'ticket' },
]

function isActive(path: string) {
  return route.path === path
}

function go(path: string) {
  router.push(path)
}
</script>

<template>
  <nav class="fixed bottom-0 left-0 right-0 z-50 bg-surface border-t border-border safe-bottom">
    <div class="flex items-center justify-around h-16 max-w-lg mx-auto">
      <button
        v-for="tab in tabs"
        :key="tab.path"
        :class="[
          'flex flex-col items-center gap-0.5 text-[10px] font-medium transition-colors duration-150 cursor-pointer',
          isActive(tab.path) ? 'text-brand' : 'text-text-dim',
        ]"
        @click="go(tab.path)"
      >
        <!-- Search -->
        <svg v-if="tab.icon === 'search'" class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <path d="m21 21-4.35-4.35"/>
        </svg>
        <!-- Ticket -->
        <svg v-else class="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/>
          <path d="M9 9h.01"/>
          <path d="M15 9h.01"/>
        </svg>
        <span>{{ tab.name }}</span>
      </button>
    </div>
  </nav>
</template>
