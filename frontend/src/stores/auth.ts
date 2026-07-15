import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as apiLogin, logout as apiLogout, getSessionId, clearSession, verifySession } from '@/api'

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

  async function restore() {
    const sid = getSessionId()
    if (!sid) {
      loggedIn.value = false
      return
    }
    // 서버에 세션 유효성 확인
    const res = await verifySession(sid)
    if (res.data && res.data.valid) {
      sessionId.value = sid
      userName.value = res.data.name || ''
      loggedIn.value = true
    } else {
      clearSession()
      loggedIn.value = false
      userName.value = ''
      sessionId.value = ''
    }
  }

  return { loggedIn, userName, sessionId, loading, error, login, logout, restore }
})
