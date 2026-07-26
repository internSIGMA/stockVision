import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    name: 'landing',
    component: () => import('@/pages/LandingPage.vue'),
    meta: { layout: 'none' },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: { layout: 'none', guestOnly: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/RegisterView.vue'),
    meta: { layout: 'none', guestOnly: true },
  },
  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: () => import('@/pages/ForgotPasswordPage.vue'),
    meta: { layout: 'none', guestOnly: true },
  },
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
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/auto-scheduler',
    name: 'auto-scheduler',
    component: () => import('@/pages/AutoSchedulerPage.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/stream',
  },
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
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return { name: 'stream', query: { accessDenied: 'true' } }
  }
  if (to.meta.guestOnly && auth.isLoggedIn) {
    return { name: 'stream' }
  }
  return true
})

export default router