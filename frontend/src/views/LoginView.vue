<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const id = ref('')
const password = ref('')

async function onSubmit() {
  if (!id.value || !password.value) return
  const ok = await auth.login(id.value, password.value)
  if (ok) {
    router.replace('/')
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4">
    <div class="w-full max-w-sm">
      <div class="text-center mb-8">
        <div class="text-4xl mb-2">🚄</div>
        <h1 class="text-text text-xl font-semibold">KTX 예매 도우미</h1>
        <p class="text-text-muted text-sm mt-1">Korail 계정으로 로그인</p>
      </div>

      <form @submit.prevent="onSubmit" class="space-y-4">
        <div>
          <label class="block text-text-muted text-xs mb-1">Korail ID</label>
          <input
            v-model="id"
            type="text"
            placeholder="회원번호 / 이메일 / 전화번호"
            class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-3 text-text placeholder:text-text-dim focus:outline-none focus:ring-2 focus:ring-brand"
          />
        </div>
        <div>
          <label class="block text-text-muted text-xs mb-1">비밀번호</label>
          <input
            v-model="password"
            type="password"
            placeholder="********"
            class="w-full bg-surface-elevated border border-border rounded-xl px-4 py-3 text-text placeholder:text-text-dim focus:outline-none focus:ring-2 focus:ring-brand"
          />
        </div>

        <p v-if="auth.error" class="text-danger text-sm text-center">{{ auth.error }}</p>

        <button
          type="submit"
          :disabled="auth.loading"
          class="w-full bg-brand text-black font-semibold rounded-xl py-3 hover:bg-brand-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ auth.loading ? '로그인 중...' : '🔑 로그인' }}
        </button>
      </form>

      <p class="text-text-dim text-xs text-center mt-6">
        로그인 정보는 서버에 저장되지 않습니다
      </p>
    </div>
  </div>
</template>
