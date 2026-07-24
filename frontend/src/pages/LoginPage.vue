<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useGoogleSignIn } from '@/composables/useGoogleSignIn'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

// Datang dari flow reset password: email sudah diketahui, jangan minta ketik ulang.
const email = ref(route.query.email || '')
const password = ref('')
const remember = ref(true)
const error = ref('')

function lanjut() {
  router.push(route.query.redirect || '/stream')
}

// Backend membalas 401 dengan pesan bahasa Inggris; tampilkan versi yang ramah.
function pesanError(err) {
  return err.message === 'invalid credentials' ? 'Email atau kata sandi salah.' : err.message
}

async function onSubmit() {
  error.value = ''
  try {
    await auth.login(email.value, password.value)
    lanjut()
  } catch (err) {
    error.value = pesanError(err)
  }
}

const { siap: googleSiap, error: googleError, pasang } = useGoogleSignIn(async (credential) => {
  error.value = ''
  try {
    await auth.loginWithGoogle(credential)
    lanjut()
  } catch (err) {
    error.value = pesanError(err)
  }
})

const wadahGoogle = ref(null)

onMounted(() => pasang(wadahGoogle.value, wadahGoogle.value?.offsetWidth))

/** Klik hanya sampai ke sini kalau tombol asli Google gagal dipasang. */
function googleTidakSiap() {
  error.value = googleError.value || 'Google Sign-In belum siap, coba beberapa saat lagi.'
}

// ---- Ilustrasi grafik di panel kiri (statis, bukan data pasar sungguhan) ----

const BULAN = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const SERI_HARGA = [6, 14, 22, 20, 30, 27, 40, 52, 48, 66, 80, 95]
const SERI_RATA = [5, 9, 13, 17, 21, 24, 27, 31, 34, 37, 40, 44]

const LEBAR = 340
const ATAS = 8
const BAWAH = 104
const SISI = 6

/** Nilai 0–100 dipetakan ke koordinat SVG, sumbu Y dibalik. */
function titik(seri) {
  const jarak = (LEBAR - SISI * 2) / (seri.length - 1)
  return seri
    .map((v, i) => {
      const x = SISI + i * jarak
      const y = BAWAH - (v / 100) * (BAWAH - ATAS)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}
</script>

<template>
  <div class="flex min-h-screen bg-[#1c1c1c]">
    <!-- KIRI — preview aplikasi (disembunyikan di mobile) -->
    <section
      class="hidden w-1/2 flex-col justify-center gap-12 bg-[#e9e9e9] px-14 py-12 text-[#171717] md:flex"
    >
      <header>
        <p class="text-[15px] font-semibold">◆StockVision</p>
        <p class="tabular mt-1 text-[11px] text-[#171717]/45">Dashboard Pasar Saham Indonesia</p>
      </header>

      <div>
        <div class="flex items-baseline gap-2">
          <span class="text-[22px] font-bold tracking-tight">BBCA</span>
          <span class="tabular text-[10px] uppercase text-[#171717]/40">IDX</span>
        </div>

        <p class="tabular mt-2 text-[40px] font-bold leading-none tracking-[0.06em]">9.875</p>
        <p class="tabular mt-2 text-[13px] font-medium text-[#16a34a]">+125 (+1,28)</p>

        <!-- Ilustrasi: garis harga (biru) di atas garis rata-rata (hijau). -->
        <figure class="mt-8" aria-label="Ilustrasi pergerakan harga sepanjang tahun">
          <svg
            :viewBox="`0 0 ${LEBAR} 112`"
            class="h-[120px] w-full"
            fill="none"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <polyline
              :points="titik(SERI_HARGA)"
              stroke="#3b6fd4"
              stroke-width="1.6"
              stroke-linejoin="round"
              stroke-linecap="round"
              vector-effect="non-scaling-stroke"
            />
            <polyline
              :points="titik(SERI_RATA)"
              stroke="#1f8a4c"
              stroke-width="1.6"
              stroke-linejoin="round"
              stroke-linecap="round"
              vector-effect="non-scaling-stroke"
            />
          </svg>

          <div class="h-px w-full bg-[#171717]/25"></div>

          <figcaption class="tabular mt-2 flex justify-between text-[9px] text-[#171717]/45">
            <span v-for="bulan in BULAN" :key="bulan">{{ bulan }}</span>
          </figcaption>
        </figure>
      </div>

      <p class="max-w-md text-[12px] leading-relaxed text-[#171717]/50">
        Pantau Data OHLC, Foreign Flow, Insider transaction, dan jalankan crawling data saham
        Indonesia secara real-time.
      </p>
    </section>

    <!-- KANAN — form login -->
    <section class="flex w-full items-center justify-center px-6 py-12 md:w-1/2">
      <div class="w-full max-w-[320px]">
        <h1 class="text-[24px] font-semibold text-white">Masuk ke StockVision</h1>
        <p class="mt-1 text-[11px] text-white/40">Gunakan akun demo untuk mencoba</p>

        <form class="mt-9 flex flex-col gap-4" @submit.prevent="onSubmit">
          <div class="space-y-2">
            <label for="email" class="block text-[12px] font-medium text-white/85">Email</label>
            <input
              id="email"
              v-model="email"
              type="email"
              autocomplete="email"
              placeholder="email@contoh.com"
              required
              class="h-10 w-full rounded-md border border-white/10 bg-[#2b2b2b] px-3 text-[13px] text-white outline-none transition-colors placeholder:text-white/30 focus:border-white/30"
            />
          </div>

          <div class="space-y-2">
            <label for="password" class="block text-[12px] font-medium text-white/85">
              Password
            </label>
            <input
              id="password"
              v-model="password"
              type="password"
              autocomplete="current-password"
              placeholder="••••••••"
              required
              class="h-10 w-full rounded-md border border-white/10 bg-[#2b2b2b] px-3 text-[13px] text-white outline-none transition-colors placeholder:text-white/30 focus:border-white/30"
            />
          </div>

          <div class="flex items-center justify-between">
            <label class="flex cursor-pointer items-center gap-2 text-[12px] text-white/70">
              <input
                v-model="remember"
                type="checkbox"
                class="size-3.5 cursor-pointer accent-white"
              />
              ingat saya
            </label>

            <RouterLink
              to="/forgot-password"
              class="text-[12px] text-white/40 transition-colors hover:text-white/80"
            >
              Lupa Password?
            </RouterLink>
          </div>

          <p v-if="error" role="alert" class="text-[12px] text-[#f87171]">{{ error }}</p>

          <button
            type="submit"
            :disabled="auth.loading"
            class="h-10 w-full rounded-md bg-white text-[13px] font-semibold text-[#171717] transition-colors hover:bg-white/90 disabled:opacity-60"
          >
            {{ auth.loading ? 'Memverifikasi...' : 'Masuk' }}
          </button>
        </form>

        <div class="my-7 flex items-center gap-3">
          <span class="h-px flex-1 bg-white/12"></span>
          <span class="text-[10px] font-medium tracking-[0.14em] text-white/35">
            OR SIGN IN WITH
          </span>
          <span class="h-px flex-1 bg-white/12"></span>
        </div>

        <div class="relative">
          <button
            type="button"
            :disabled="auth.loading"
            class="flex h-10 w-full items-center justify-center gap-2.5 rounded-md bg-white text-[13px] font-medium text-[#171717] transition-colors hover:bg-white/90 disabled:opacity-60"
            @click="googleTidakSiap"
          >
            <svg class="size-[18px]" viewBox="0 0 24 24" aria-hidden="true">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            Login With Google
          </button>

          <!-- Tombol asli Google ditumpuk transparan di atas tombol bergaya kita:
               popup-nya hanya boleh dibuka dari elemen milik Google sendiri. -->
          <div
            ref="wadahGoogle"
            class="absolute inset-0 overflow-hidden opacity-0 [&>div]:!w-full"
            :class="googleSiap ? '' : 'pointer-events-none'"
          ></div>
        </div>

        <p class="mt-7 text-center text-[12px] text-white/40">
          Belum punya akun?
          <RouterLink to="/register" class="text-white/80 transition-colors hover:text-white">
            Daftar
          </RouterLink>
        </p>
      </div>
    </section>
  </div>
</template>
