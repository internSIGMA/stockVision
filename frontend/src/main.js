import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Lenis from 'lenis'
import App from '@/App.vue'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'
import '@/assets/globals.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Tema dipasang sebelum mount supaya tidak ada kedipan putih di dark mode.
if (localStorage.getItem('stockvision.theme') === 'dark') {
  document.documentElement.classList.add('dark')
}

// Smooth scroll dilewati untuk yang meminta gerakan minimal.
if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  new Lenis({ autoRaf: true })
}

// Sesi ada di localStorage, tapi watchlist-nya tidak — ambil ulang di latar.
const auth = useAuthStore(pinia)
auth.restore().catch((err) => console.error('Gagal memuat watchlist:', err.message))

app.mount('#app')
