import type {
  ApiResult, LoginResult, SearchResult, StationsResult,
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
  if (!sid) return { error: '로그인이 필요합니다' }
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

export async function getStations(): Promise<ApiResult<StationsResult>> {
  return apiCall<StationsResult>('/api/v1/stations')
}

export async function verifySession(sessionId: string): Promise<ApiResult<{ valid: boolean; name: string }>> {
  return apiCall<{ valid: boolean; name: string }>(`/api/v1/verify?session_id=${sessionId}`)
}

export async function startMonitor(params: {
  dep: string; arr: string; date: string; time: string
  train_type: string; train_idx: number; train_no: string; train_label: string
  seat_option: string; try_waiting: boolean; interval_sec: number
}): Promise<ApiResult<{ task_id: string }>> {
  return apiCall<{ task_id: string }>(`/api/v1/monitor/start?session_id=${getSessionId()}`, {
    method: 'POST', body: JSON.stringify(params),
  })
}

export async function stopMonitor(taskId: string): Promise<ApiResult<{ success: boolean }>> {
  return apiCall<{ success: boolean }>(`/api/v1/monitor/stop?task_id=${taskId}&session_id=${getSessionId()}`, {
    method: 'POST',
  })
}

export interface MonitorEntry {
  task_id: string
  dep: string; arr: string
  train_label: string; train_no: string
  status: string
  check_count: number
  error_msg: string
  interval_sec: number
  result: any
  created_at: string
}

export interface LogEntry {
  id: number
  level: string
  message: string
  created_at: string
}

export async function listMonitors(): Promise<ApiResult<{ monitors: MonitorEntry[] }>> {
  return apiCall<{ monitors: MonitorEntry[] }>(`/api/v1/monitor/list?session_id=${getSessionId()}`)
}

export async function getMonitorLogs(taskId: string): Promise<ApiResult<{ logs: LogEntry[] }>> {
  return apiCall<{ logs: LogEntry[] }>(`/api/v1/monitor/logs?task_id=${taskId}&session_id=${getSessionId()}`)
}
