<script setup>
import { ref } from 'vue'
import { 
  Mail,
  Activity,
  LogOut,
  MapPin,
  Phone
} from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import LogoutConfirmDialog from '@/components/LogoutConfirmDialog.vue'

const auth = useAuthStore()
const router = useRouter()
const showLogoutDialog = ref(false)

function openLogoutDialog() {
  showLogoutDialog.value = true
}

function performLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <footer class="relative mt-auto w-full border-t border-border bg-card/40 overflow-hidden">
    <!-- Garis aksen neon tipis di atas -->
    <div class="absolute inset-x-0 top-0 h-[1px] bg-gradient-to-r from-transparent via-[var(--primary)] to-transparent opacity-20"></div>

    <!-- Pattern Latar Belakang (dots) -->
    <div class="pointer-events-none absolute inset-0 opacity-[0.03] dark:opacity-5" style="background-image: radial-gradient(circle at 2px 2px, currentColor 1px, transparent 0); background-size: 32px 32px;"></div>

    <!-- Decorative Glows (Diagonal) -->
    <div class="pointer-events-none absolute -left-[200px] -top-[200px] h-[500px] w-[500px] rounded-full bg-[var(--primary)]/15 blur-[120px]"></div>
    <div class="pointer-events-none absolute -bottom-[200px] -right-[200px] h-[500px] w-[500px] rounded-full bg-[var(--primary)]/15 blur-[120px]"></div>

    <div class="relative mx-auto w-full max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 gap-10 md:grid-cols-12 md:gap-8">
        
        <!-- Kolom 1: Brand & Deskripsi -->
        <div class="flex flex-col gap-4 md:col-span-5 lg:col-span-4 lg:pr-8">
          <div class="flex items-center gap-2 text-foreground">
            <div class="flex size-7 items-center justify-center rounded bg-[var(--primary)] text-white shadow-sm">
              <Activity class="size-4" />
            </div>
            <span class="text-lg font-bold tracking-tight">StockVision</span>
          </div>
          <p class="text-[12.5px] leading-relaxed text-muted-foreground">
            Platform analisis saham preskriptif berbasis AI. Seluruh data disajikan sebagai referensi tambahan, bukan ajakan untuk membeli atau menjual.
          </p>
          <div class="mt-2 flex items-center gap-4 text-muted-foreground">
            <a href="#" aria-label="Twitter" class="transition-colors hover:text-[var(--primary)]">
              <svg class="size-4" fill="currentColor" viewBox="0 0 24 24"><path d="M22.46 6c-.77.35-1.6.58-2.46.69.88-.53 1.56-1.37 1.88-2.38-.83.5-1.75.85-2.72 1.05C18.37 4.5 17.26 4 16 4c-2.35 0-4.27 1.92-4.27 4.29 0 .34.04.67.11.98C8.28 9.09 5.11 7.38 3 4.79c-.37.63-.58 1.37-.58 2.15 0 1.49.75 2.81 1.91 3.56-.71 0-1.37-.2-1.95-.5v.05c0 2.08 1.48 3.82 3.44 4.21a4.22 4.22 0 0 1-1.93.07 4.28 4.28 0 0 0 4 2.98 8.521 8.521 0 0 1-5.33 1.84c-.34 0-.68-.02-1.02-.06C3.44 20.29 5.7 21 8.12 21 16 21 20.33 14.46 20.33 8.79c0-.19 0-.37-.01-.56.84-.6 1.56-1.36 2.14-2.23z"/></svg>
            </a>
            <a href="#" aria-label="Instagram" class="transition-colors hover:text-[var(--primary)]">
              <svg class="size-4" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 1 0 0 12.324 6.162 6.162 0 0 0 0-12.324zM12 16a4 4 0 1 1 0-8 4 4 0 0 1 0 8zm6.406-11.845a1.44 1.44 0 1 0 0 2.881 1.44 1.44 0 0 0 0-2.881z"/></svg>
            </a>
            <a href="#" aria-label="LinkedIn" class="transition-colors hover:text-[var(--primary)]">
              <svg class="size-4" fill="currentColor" viewBox="0 0 24 24"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
            </a>
          </div>
        </div>

        <!-- Kolom 2: Tautan Cepat -->
        <div class="flex flex-col gap-4 md:col-span-3 lg:col-span-4 lg:pl-12">
          <h3 class="text-[11px] font-semibold uppercase tracking-wider text-foreground/70">Menu Utama</h3>
          <ul class="flex flex-col gap-3 text-[13px] font-medium text-muted-foreground">
            <li>
              <router-link to="/stream" class="transition-colors hover:text-[var(--primary)]">Halaman Stream</router-link>
            </li>
            <li>
              <a href="#" class="transition-colors hover:text-[var(--primary)]">Syarat & Ketentuan</a>
            </li>
            <li>
              <a href="#" class="transition-colors hover:text-[var(--primary)]">Kebijakan Privasi</a>
            </li>
            <li v-if="auth.isLoggedIn">
              <button @click="openLogoutDialog" class="flex items-center gap-1.5 text-down transition-colors hover:text-red-600">
                <LogOut class="size-3.5" /> Keluar
              </button>
            </li>
          </ul>
        </div>

        <!-- Kolom 3: Kontak Info -->
        <div class="flex flex-col gap-4 md:col-span-4 lg:col-span-4">
          <h3 class="text-[11px] font-semibold uppercase tracking-wider text-foreground/70">Hubungi Kami</h3>
          <ul class="flex flex-col gap-3 text-[13px] text-muted-foreground">
            <li class="flex items-start gap-2.5">
              <MapPin class="mt-0.5 size-4 shrink-0 text-[var(--primary)]" />
              <span class="leading-relaxed">Bandung, Jawa Barat 12190</span>
            </li>
            <li class="flex items-center gap-2.5">
              <Phone class="size-4 shrink-0 text-[var(--primary)]" />
              <a href="tel:+6281122334455" class="transition-colors hover:text-[var(--primary)]">+62 811 2233 4455</a>
            </li>
            <li class="flex items-center gap-2.5">
              <Mail class="size-4 shrink-0 text-[var(--primary)]" />
              <a href="mailto:support@stockvision.id" class="transition-colors hover:text-[var(--primary)]">support@stockvision.id</a>
            </li>
          </ul>
        </div>
        
      </div>
      
      <!-- Bottom Bar (Hak Cipta) -->
      <div class="mt-12 flex flex-col items-center justify-between gap-3 border-t-[0.5px] border-border/80 pt-6 text-[11px] text-muted-foreground sm:flex-row">
        <p>&copy; {{ new Date().getFullYear() }} StockVision. Hak Cipta Dilindungi.</p>
        <p>Dibangun menggunakan AI untuk investasi yang cerdas.</p>
      </div>
    </div>

    <LogoutConfirmDialog
      v-model:open="showLogoutDialog"
      @confirm="performLogout"
    />
  </footer>
</template>
