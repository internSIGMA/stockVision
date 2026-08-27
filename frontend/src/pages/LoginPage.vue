<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { Eye, EyeOff } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'
import { useGoogleSignIn } from '@/composables/useGoogleSignIn'
import { useLandingSpotlight } from '@/composables/useLandingSpotlight'
import { formatDate, formatNumber, formatPercent, trendClass } from '@/utils/format'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref(typeof route.query.email === 'string' ? route.query.email : '')
const password = ref('')
const remember = ref(true)
const error = ref('')
const lihatSandi = ref(false)

function lanjut() {
  const redirect =
    typeof route.query.redirect === 'string' ? route.query.redirect : '/stream'

  // Setiap pengguna biasa melewati pemilihan emiten dulu — bukan hanya
  // pendaftar baru. Admin tidak punya watchlist sendiri, jadi langsung masuk.
  if (!auth.isAdmin && auth.user) {
    router.push('/preferences')
    return
  }

  router.push(redirect)
}

function pesanError(err) {
  const rawMsg =
    err?.response?.data?.error ||
    err?.response?.data?.message ||
    err?.message ||
    ''

  if (
    rawMsg.toLowerCase().includes('timeout') ||
    rawMsg.toLowerCase().includes('menyiapkan') ||
    err?.code === 'ECONNABORTED'
  ) {
    return 'Server sedang menyiapkan sinkronisasi data awal di latar belakang. Silakan coba masuk kembali beberapa saat lagi.'
  }
  if (
    rawMsg.toLowerCase().includes('tidak dapat terhubung') ||
    rawMsg.toLowerCase().includes('network error')
  ) {
    return 'Sedang menghubungkan ke server... Pastikan koneksi internet stabil lalu coba kembali.'
  }
  if (
    rawMsg.toLowerCase().includes('password') ||
    rawMsg.toLowerCase().includes('sandi') ||
    rawMsg.toLowerCase().includes('email') ||
    rawMsg.toLowerCase().includes('kredensial') ||
    rawMsg.toLowerCase().includes('invalid') ||
    rawMsg.toLowerCase().includes('unauthorized')
  ) {
    return 'Email atau kata sandi yang Anda masukkan belum sesuai. Silakan periksa kembali.'
  }
  return rawMsg || 'Login belum berhasil. Silakan periksa koneksi dan coba beberapa saat lagi.'
}

async function onSubmit() {
  error.value = ''
  try {
    await auth.login(email.value.trim(), password.value)
    lanjut()
  } catch (err) {
    error.value = pesanError(err)
  }
}

// Tombol Google resmi dirender transparan di atas tombol bergaya sendiri.
const { siap, error: googleError, pasang } = useGoogleSignIn(async (credential) => {
  error.value = ''
  try {
    await auth.googleLogin(credential)
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

// ---- Panel kiri: emiten berperforma terbaik, sama untuk semua pengunjung ----

const {
  ticker: sorotanTicker,
  rows: sorotanRows,
  hargaTerakhir,
  perubahanPersen,
  loading: sorotanLoading,
  error: sorotanError,
} = useLandingSpotlight()

/** Sesi yang digambar di grafik panel kiri. */
const SESI = 90
const PERIODE_MA = 20

const LEBAR = 340
const ATAS = 8
const BAWAH = 104
const SISI = 6

const jendela = computed(() => sorotanRows.value.slice(-SESI))

/** Rata-rata bergerak, disejajarkan ke ekor jendela yang sama. */
const seriRata = computed(() => {
  const closes = jendela.value.map((r) => r.close)
  if (closes.length < PERIODE_MA) return []
  return closes.map((_, i) =>
    i < PERIODE_MA - 1
      ? null
      : closes.slice(i - PERIODE_MA + 1, i + 1).reduce((a, b) => a + b, 0) / PERIODE_MA,
  )
})

/**
 * Kedua garis dinormalkan pada skala yang sama supaya posisi harga terhadap
 * rata-ratanya terbaca jujur — bukan dua garis yang masing-masing dipaskan.
 */
const skala = computed(() => {
  const nilai = [
    ...jendela.value.map((r) => r.close),
    ...seriRata.value.filter((v) => v != null),
  ]
  if (!nilai.length) return null
  const min = Math.min(...nilai)
  const max = Math.max(...nilai)
  return { min, span: max - min || 1 }
})

function garis(seri) {
  const s = skala.value
  if (!s || seri.length < 2) return ''
  const jarak = (LEBAR - SISI * 2) / (seri.length - 1)
  return seri
    .map((v, i) => {
      if (v == null) return null
      const x = SISI + i * jarak
      const y = BAWAH - ((v - s.min) / s.span) * (BAWAH - ATAS)
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .filter(Boolean)
    .join(' ')
}

const garisHarga = computed(() => garis(jendela.value.map((r) => r.close)))
const garisRata = computed(() => garis(seriRata.value))

/** Empat tanggal merata sebagai sumbu X. */
const labelTanggal = computed(() => {
  const w = jendela.value
  if (w.length < 2) return []
  return [0, 1, 2, 3].map((i) => {
    const r = w[Math.round((i / 3) * (w.length - 1))]
    return formatDate(r.tanggal)
  })
})
</script>

<template>
  <div class="flex min-h-screen bg-background">
    <!-- Panel kiri: ilustrasi. Baru muncul di lg supaya form tidak terhimpit. -->
    <section
      class="hidden w-1/2 flex-col justify-center gap-12 bg-[var(--background-secondary)] px-10 py-12 text-foreground lg:flex xl:px-16"
    >
      <header>
        <p class="text-[20px] font-semibold tracking-tight xl:text-[22px]">◆StockVision</p>
        <p class="tabular mt-1.5 text-[13px] text-muted-foreground">
          Dashboard Pasar Saham Indonesia
        </p>
      </header>

      <div class="w-full max-w-[440px]">
        <div class="flex items-baseline gap-2">
          <span class="text-[26px] font-bold tracking-tight">
            {{ sorotanTicker ?? '—' }}
          </span>
          <span class="tabular text-[11px] uppercase text-muted-foreground">IDX</span>
          <span
            v-if="sorotanTicker"
            class="rounded bg-[var(--color-info-bg)] px-2 py-0.5 text-[11px] font-medium text-[var(--color-info-ink)]"
          >
            Performa terbaik
          </span>
        </div>

        <p class="tabular mt-2.5 text-[44px] font-bold leading-none tracking-[0.04em] xl:text-[52px]">
          {{ hargaTerakhir != null ? formatNumber(hargaTerakhir) : '—' }}
        </p>

        <p
          v-if="perubahanPersen != null"
          class="tabular mt-2.5 text-[15px] font-medium"
          :class="trendClass(perubahanPersen)"
        >
          {{ formatPercent(perubahanPersen) }} · {{ jendela.length }} sesi terakhir
        </p>

        <figure
          class="mt-8"
          :aria-label="`Pergerakan harga ${sorotanTicker ?? ''} beserta rata-rata bergerak ${PERIODE_MA} sesi`"
        >
          <div v-if="sorotanLoading" class="h-[140px] w-full animate-pulse rounded bg-muted" />

          <p
            v-else-if="sorotanError || !garisHarga"
            class="flex h-[140px] items-center text-[13px] text-muted-foreground"
          >
            {{ sorotanError || 'Data pasar belum tersedia.' }}
          </p>

          <svg
            v-else
            :viewBox="`0 0 ${LEBAR} 112`"
            class="h-[140px] w-full"
            fill="none"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            <polyline
              v-if="garisRata"
              :points="garisRata"
              stroke="var(--chart-2)"
              stroke-width="1.6"
              stroke-linejoin="round"
              stroke-linecap="round"
              vector-effect="non-scaling-stroke"
            />

            <polyline
              :points="garisHarga"
              stroke="var(--chart-1)"
              stroke-width="1.6"
              stroke-linejoin="round"
              stroke-linecap="round"
              vector-effect="non-scaling-stroke"
            />
          </svg>

          <div class="h-px w-full bg-border"></div>

          <figcaption
            v-if="labelTanggal.length"
            class="tabular mt-2 flex justify-between text-[11px] text-muted-foreground"
          >
            <span v-for="(tgl, i) in labelTanggal" :key="i">{{ tgl }}</span>
          </figcaption>
        </figure>
      </div>

      <p class="max-w-[440px] text-[14px] leading-relaxed text-muted-foreground">
        Pantau Data OHLC, Insider transaction, dan jalankan
        crawling data saham Indonesia secara real-time.
      </p>
    </section>

    <!-- Panel kanan: form login -->
    <section class="flex w-full items-center justify-center px-5 py-10 sm:px-6 sm:py-14 lg:w-1/2">
      <div class="w-full max-w-[400px]">
        <!-- Identitas produk untuk layar yang tidak menampilkan panel kiri. -->
        <p class="mb-6 text-[20px] font-semibold tracking-tight text-foreground lg:hidden">
          ◆StockVision
        </p>

        <h1 class="text-[26px] font-semibold leading-tight tracking-tight text-foreground sm:text-[30px]">
          Masuk ke StockVision
        </h1>

        <form
          class="mt-7 flex flex-col gap-5"
          @submit.prevent="onSubmit"
        >
          <div class="space-y-2">
            <label
              for="email"
              class="block text-[13px] font-medium text-foreground sm:text-sm"
            >
              Email
            </label>

            <input
              id="email"
              v-model="email"
              type="email"
              autocomplete="email"
              placeholder="email@contoh.com"
              required
              class="field"
            />
          </div>

          <div class="space-y-2">
            <label
              for="password"
              class="block text-[13px] font-medium text-foreground sm:text-sm"
            >
              Password
            </label>

            <div class="relative">
              <input
                id="password"
                v-model="password"
                :type="lihatSandi ? 'text' : 'password'"
                autocomplete="current-password"
                placeholder="••••••••"
                required
                class="field field-aksi"
              />

              <button
                type="button"
                class="absolute inset-y-0 right-0 flex items-center rounded-r-lg px-3.5 text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-[var(--ring)]"
                :aria-label="lihatSandi ? 'Sembunyikan kata sandi' : 'Tampilkan kata sandi'"
                @click="lihatSandi = !lihatSandi"
              >
                <component :is="lihatSandi ? EyeOff : Eye" class="size-[18px]" aria-hidden="true" />
              </button>
            </div>
          </div>

          <div class="flex flex-wrap items-center justify-between gap-2">
            <label
              class="flex cursor-pointer items-center gap-2 text-[14px] text-muted-foreground transition-colors hover:text-foreground"
            >
              <input
                v-model="remember"
                type="checkbox"
                class="size-4 cursor-pointer accent-[var(--primary)]"
              />

              ingat saya
            </label>

            <RouterLink
              to="/forgot-password"
              class="text-[14px] text-muted-foreground underline-offset-4 transition-colors hover:text-foreground hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--ring)]"
            >
              Lupa Password?
            </RouterLink>
          </div>

          <p
            v-if="error"
            role="alert"
            class="rounded-lg bg-[var(--color-down-bg)] px-3.5 py-2.5 text-[13px] text-[var(--color-down-ink)]"
          >
            {{ error }}
          </p>

          <button
            type="submit"
            :disabled="auth.loading"
            class="h-11 w-full rounded-lg bg-[var(--primary)] text-[15px] font-semibold text-[var(--primary-foreground)] transition-[background-color,transform] hover:bg-[var(--primary-hover)] active:scale-[0.99] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--ring)] disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100 sm:h-12"
          >
            {{ auth.loading ? 'Memverifikasi...' : 'Masuk' }}
          </button>
        </form>

        <div class="my-7 flex items-center gap-3">
          <span class="h-px flex-1 bg-border"></span>

          <span class="text-[11px] font-medium tracking-[0.12em] text-muted-foreground">
            OR SIGN IN WITH
          </span>

          <span class="h-px flex-1 bg-border"></span>
        </div>

        <div class="relative">
          <button
            type="button"
            :disabled="auth.loading"
            class="flex h-11 w-full items-center justify-center gap-2.5 rounded-lg border border-border bg-card text-[15px] font-medium text-foreground transition-[background-color,transform] hover:bg-[var(--card-hover)] active:scale-[0.99] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--ring)] disabled:opacity-60 sm:h-12"
            @click="googleTidakSiap"
          >
            <svg
              class="size-5 shrink-0"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
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

          <!-- Tombol asli Google, transparan di atas tombol bergaya di atas -->
          <div
            ref="wadahGoogle"
            :class="[
              'absolute inset-0 overflow-hidden opacity-0 [&>div]:!w-full',
              siap ? '' : 'pointer-events-none',
            ]"
          ></div>
        </div>

        <p class="register-text">
          Belum punya akun?
          <RouterLink
            to="/register"
            class="register-link"
          >
            Daftar Sekarang
          </RouterLink>
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
/* Satu gaya input dipakai semua field supaya tinggi dan fokusnya seragam. */
.field {
  height: 44px;
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 8px;
  background-color: var(--card);
  padding: 0 14px;
  color: var(--foreground);
  font-size: 15px;
  outline: none;

  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease;
}

@media (min-width: 640px) {
  .field {
    height: 48px;
  }
}

/* Ruang untuk tombol lihat/sembunyikan sandi di dalam input. */
.field-aksi {
  padding-right: 46px;
}

.field::placeholder {
  color: var(--muted-foreground);
}

/* Sembunyikan ikon mata bawaan dari browser (khususnya MS Edge) */
input[type="password"]::-ms-reveal,
input[type="password"]::-ms-clear {
  display: none;
}

.field:hover {
  border-color: var(--primary-light);
}

.field:focus {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px var(--primary-soft);
}

.register-text {
  margin-top: 28px;
  color: var(--muted-foreground);
  font-size: 14px;
  line-height: 1.5;
  text-align: center;
}

.register-link {
  margin-left: 4px;
  color: var(--primary);
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;

  transition:
    color 0.15s ease,
    text-decoration-color 0.15s ease;
}

.register-link:hover {
  color: var(--primary-hover);
  text-decoration: underline;
  text-underline-offset: 3px;
}

.register-link:focus-visible {
  outline: 2px solid var(--ring);
  outline-offset: 3px;
  border-radius: 3px;
}
</style>
