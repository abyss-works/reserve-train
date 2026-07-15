export interface Train {
  idx: number
  train_type: string
  train_no: string
  dep_name: string
  arr_name: string
  dep_date: string
  dep_time: string
  arr_time: string
  dep_display: string
  arr_display: string
  duration: string
  general_available: boolean
  special_available: boolean
  waiting_possible: boolean
}

export interface Reservation {
  idx: number
  rsv_id: string
  train_type: string
  train_no: string
  dep_name: string
  arr_name: string
  dep_time: string
  arr_time: string
  dep_display: string
  arr_display: string
  price: number
  seat_count: number
  limit_display: string
}

export interface ApiResult<T> {
  data?: T
  error?: string
}

export interface LoginResult {
  session_id: string
  name: string
}

export interface SearchResult {
  trains: Train[]
  message?: string
}

export interface Station {
  name: string
  code: string
}

export interface StationsResult {
  stations: Station[]
}

export interface ReservationsResult {
  reservations: Reservation[]
}

export interface ReserveResult {
  reservation: Reservation
}
