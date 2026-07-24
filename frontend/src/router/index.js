import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

/**
 * Halaman dimuat secara lazy agar bundle awal tetap ringan.
 * meta.layout === 'none' digunakan untuk halaman tanpa header/sidebar.
 */
const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: {
      layout: 'none',
      guestOnly: true,
    },
  },

  {
    path: '/register',
    name: 'register',
    component: () => import('@/views/RegisterView.vue'),
    meta: {
      layout: 'none',
      guestOnly: true,
    },
  },

  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: () => import('@/pages/ForgotPasswordPage.vue'),
    meta: {
      layout: 'none',
      guestOnly: true,
    },
  },

  {
    path: '/',
    redirect: '/stream',
  },

  /**
   * Stream dapat diakses admin maupun user biasa.
   */
  {
    path: '/stream',
    name: 'stream',
    component: () => import('@/pages/StreamPage.vue'),
    meta: {
      requiresAuth: true,
    },
  },

  /**
   * Hanya admin yang dapat membuka Crawl Logs.
   */
  {
    path: '/crawl-logs',
    name: 'crawl-logs',
    component: () => import('@/pages/CrawlLogsPage.vue'),
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
    },
  },

  /**
   * Hanya admin yang dapat membuka Auto Scheduler.
   */
  {
    path: '/auto-scheduler',
    name: 'auto-scheduler',
    component: () => import('@/pages/AutoSchedulerPage.vue'),
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
    },
  },

  // Route ini wajib berada paling bawah.
  {
    path: '/:pathMatch(.*)*',
    redirect: '/stream',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,

  scrollBehavior: () => ({
    top: 0,
  }),
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  /**
   * User yang belum login diarahkan ke halaman login.
   */
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return {
      name: 'login',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  /**
   * User biasa tidak boleh membuka halaman khusus admin.
   * Contohnya Dewi akan dikembalikan ke Stream.
   */
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return {
      name: 'stream',
      query: {
        accessDenied: 'true',
      },
    }
  }

  /**
   * User yang sudah login tidak dapat kembali ke login/register.
   */
  if (to.meta.guestOnly && auth.isLoggedIn) {
    return {
      name: 'stream',
    }
  }

  return true
})

export default router