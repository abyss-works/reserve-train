import { createRouter, createWebHistory } from 'vue-router'
import SearchTab from '@/views/SearchTab.vue'
import ReservationsTab from '@/views/ReservationsTab.vue'
import MonitorTab from '@/views/MonitorTab.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'search', component: SearchTab },
    { path: '/reservations', name: 'reservations', component: ReservationsTab },
    { path: '/monitor', name: 'monitor', component: MonitorTab },
  ],
})

export default router
