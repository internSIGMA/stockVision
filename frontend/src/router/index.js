import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

/**
 * Halaman dimuat lazy supaya bundle awal (login) tetap ringan.
 * meta.layout === 'none' membuat App.vue melewati AppShell — dipakai halaman
 * yang tidak punya header/sidebar.
 */
const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: { layout: 'none', guestOnly: true },
  },
  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: () => import('@/pages/ForgotPasswordPage.vue'),
    meta: { layout: 'none', guestOnly: true },
  },
  { path: '/', redirect: '/stream' },
  {
    path: '/stream',
    name: 'stream',
    component: () => import('@/pages/StreamPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/crawl-logs',
    name: 'crawl-logs',
    component: () => import('@/pages/CrawlLogsPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/auto-scheduler',
    name: 'auto-scheduler',
    component: () => import('@/pages/AutoSchedulerPage.vue'),
    meta: { requiresAuth: true },
  },
  { path: '/:pathMatch(.*)*', redirect: '/stream' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && auth.isLoggedIn) {
    return { name: 'stream' }
  }
})

export default router
