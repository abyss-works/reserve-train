import type {
  ApiResult, LoginResult, SearchResult,
  ReservationsResult, ReserveResult,
} from '@/types'

let _sessionId = localStorage.getItem('session_id') || ''

export function getSessionId(): string {
  return _sessionId
}

export function setSessionId(id: string) {
  _sessionId = id
  localStorage.setItem('session_id', id)
}

export function clearSession() {
  _sessionId = ''
  localStorage.removeItem('session_id')
}

async function apiCall<T>(url: string, options?: RequestInit): Promise<ApiResult<T>> {
  try {
    const res = await fetch(url, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      return { error: body.detail || `HTTP ${res.status}` }
    }
    const data = await res.json()
    return { data }
  } catch (e) {
    return { error: e instanceof Error ? e.message : 'Network error' }
  }
}

export async function login(id: string, password: string): Promise<ApiResult<LoginResult>> {
  const res = await apiCall<LoginResult>('/api/v1/login', {
    method: 'POST',
    body: JSON.stringify({ id, password }),
  })
  if (res.data) {
    setSessionId(res.data.session_id)
  }
  return res
}

export async function logout(): Promise<void> {
  const sid = getSessionId()
  if (sid) {
    await fetch(`/api/v1/logout?session_id=${sid}`, { method: 'POST' })
  }
  clearSession()
}

export async function searchTrains(params: {
  dep: string; arr: string; date: string; time: string
  train_type: string; include_no_seats: boolean; include_waiting_list: boolean
}): Promise<ApiResult<SearchResult>> {
  const sid = getSessionId()
  const qp: Record<string, string> = {
    dep: params.dep, arr: params.arr, date: params.date || '', time: params.time || '',
    train_type: params.train_type, include_no_seats: String(params.include_no_seats),
    include_waiting_list: String(params.include_waiting_list), session_id: sid,
  }
  const q = new URLSearchParams(qp)
  return apiCall<SearchResult>(`/api/v1/search?${q}`)
}

export async function getReservations(): Promise<ApiResult<ReservationsResult>> {
  return apiCall<ReservationsResult>(`/api/v1/reservations?session_id=${getSessionId()}`)
}

export async function reserveTrain(trainIdx: number, seatOption: string, tryWaiting: boolean): Promise<ApiResult<ReserveResult>> {
  return apiCall<ReserveResult>(`/api/v1/reserve?session_id=${getSessionId()}`, {
    method: 'POST',
    body: JSON.stringify({ train_idx: trainIdx, seat_option: seatOption, try_waiting: tryWaiting }),
  })
}

export async function cancelReservation(reservationIdx: number): Promise<ApiResult<{ success: boolean }>> {
  return apiCall<{ success: boolean }>(`/api/v1/cancel?session_id=${getSessionId()}`, {
    method: 'POST',
    body: JSON.stringify({ reservation_idx: reservationIdx }),
  })
}
