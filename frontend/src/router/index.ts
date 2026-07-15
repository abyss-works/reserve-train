import { createRouter, createWebHistory } from 'vue-router'
import LoginView from '@/views/LoginView.vue'
import SearchView from '@/views/SearchView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
    },
    {
      path: '/',
      name: 'search',
      component: SearchView,
    },
    {
      path: '/reservations',
      name: 'reservations',
      component: () => import('@/views/ReservationsView.vue'),
    },
  ],
})

export default router
