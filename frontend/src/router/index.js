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
    path: '/register',
    name: 'register',
    component: () => import('@/pages/RegisterPage.vue'),
    meta: {
      public: true,
      guestOnly: true,
      hideHeader: true,
    },
  },
  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: () => import('@/pages/ForgotPasswordPage.vue'),
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
    path: '/token-callback',
    name: 'token-callback',
    component: () => import('@/pages/TokenCallbackPage.vue'),
    meta: {
      public: true,
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

  const isLoggedIn = Boolean(auth.isLoggedIn)

  // Izin ada di kolom access_role, bukan role — role isinya jabatan
  // ("Trader — Perbankan"), jadi tidak pernah bernilai "admin".
  const isAdmin = Boolean(auth.isAdmin)

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