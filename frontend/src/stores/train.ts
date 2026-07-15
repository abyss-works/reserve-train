import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Train, Reservation } from '@/types'
import {
  searchTrains as apiSearch,
  getReservations as apiReservations,
  reserveTrain as apiReserve,
  cancelReservation as apiCancel,
} from '@/api'

export const useTrainStore = defineStore('train', () => {
  const trains = ref<Train[]>([])
  const reservations = ref<Reservation[]>([])
  const loading = ref(false)
  const error = ref('')
  const reserveResult = ref<Reservation | null>(null)
  const message = ref('')

  async function search(params: {
    dep: string; arr: string; date: string; time: string
    train_type: string; include_no_seats: boolean; include_waiting_list: boolean
  }) {
    loading.value = true
    error.value = ''
    message.value = ''
    try {
      const res = await apiSearch(params)
      if (res.data) {
        trains.value = res.data.trains || []
        message.value = res.data.message || ''
      } else {
        error.value = res.error || '조회 실패'
      }
    } catch {
      error.value = '네트워크 오류'
    } finally {
      loading.value = false
    }
  }

  async function loadReservations() {
    loading.value = true
    error.value = ''
    try {
      const res = await apiReservations()
      if (res.data) {
        reservations.value = res.data.reservations || []
      } else {
        error.value = res.error || '조회 실패'
      }
    } catch {
      error.value = '네트워크 오류'
    } finally {
      loading.value = false
    }
  }

  async function reserve(trainIdx: number, seatOption: string, tryWaiting: boolean): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const res = await apiReserve(trainIdx, seatOption, tryWaiting)
      if (res.data) {
        reserveResult.value = res.data.reservation
        return true
      }
      error.value = res.error || '예약 실패'
      return false
    } catch {
      error.value = '네트워크 오류'
      return false
    } finally {
      loading.value = false
    }
  }

  async function cancel(reservationIdx: number): Promise<boolean> {
    loading.value = true
    error.value = ''
    try {
      const res = await apiCancel(reservationIdx)
      if (res.data) {
        reservations.value = reservations.value.filter((_, i) => i !== reservationIdx)
        return true
      }
      error.value = res.error || '취소 실패'
      return false
    } catch {
      error.value = '네트워크 오류'
      return false
    } finally {
      loading.value = false
    }
  }

  function clearReserveResult() {
    reserveResult.value = null
  }

  function clearAll() {
    trains.value = []
    reservations.value = []
    reserveResult.value = null
    error.value = ''
    message.value = ''
  }

  return {
    trains, reservations, loading, error, reserveResult, message,
    search, loadReservations, reserve, cancel, clearReserveResult, clearAll,
  }
})
