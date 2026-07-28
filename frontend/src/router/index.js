import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/',
    name: 'landing',
    component: () => import('@/pages/LandingPage.vue'),
    meta: {
      public: true,
      hideHeader: true,
    },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: {
      public: true,
      guestOnly: true,
      hideHeader: true,
    },
  },
  {
    path: '/stream',
    name: 'stream',
    component: () => import('@/pages/StreamPage.vue'),
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/crawl-logs',
    name: 'crawl-logs',
    component: () => import('@/pages/CrawlLogsPage.vue'),
    meta: {
      requiresAuth: true,
      adminOnly: true,
    },
  },
  {
    path: '/auto-scheduler',
    name: 'auto-scheduler',
    component: () => import('@/pages/AutoSchedulerPage.vue'),
    meta: {
      requiresAuth: true,
      adminOnly: true,
    },
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  const isDeveloperMode =
    import.meta.env.DEV &&
    import.meta.env.VITE_DEVELOPER_BYPASS === 'true'

  const isLoggedIn = Boolean(auth.isAuthenticated)

  const role = String(auth.user?.role || '')
    .trim()
    .toLowerCase()

  const isAdmin = role === 'admin'

  // Landing page dan login tetap dapat dibuka.
  if (to.meta.public) {
    if (to.meta.guestOnly && isLoggedIn) {
      return '/stream'
    }

    return true
  }

  if (
    to.meta.requiresAuth &&
    !isLoggedIn &&
    !isDeveloperMode
  ) {
    return {
      path: '/login',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  if (
    to.meta.adminOnly &&
    !isAdmin &&
    !isDeveloperMode
  ) {
    return '/stream'
  }

  return true
})

export default router