import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login as apiLogin, logout as apiLogout, getSessionId, clearSession } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const loggedIn = ref(false)
  const userName = ref('')
  const sessionId = ref('')
  const loading = ref(false)
  const error = ref('')

  async function login(id: string, password: string): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const res = await apiLogin(id, password)
      if (res.data) {
        loggedIn.value = true
        userName.value = res.data.name
        sessionId.value = res.data.session_id
        return true
      }
      error.value = res.error || '로그인 실패'
      return false
    } catch {
      error.value = '네트워크 오류'
      return false
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    await apiLogout()
    loggedIn.value = false
    userName.value = ''
    sessionId.value = ''
  }

  function restore() {
    const sid = getSessionId()
    if (sid) {
      sessionId.value = sid
      loggedIn.value = true
    }
  }

  return { loggedIn, userName, sessionId, loading, error, login, logout, restore }
})
