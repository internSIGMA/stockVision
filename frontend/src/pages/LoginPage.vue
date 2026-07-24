<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref(route.query.email || '')
const password = ref('')
const remember = ref(true)
const error = ref('')
const demoLoading = ref(null)

// Akun demo
const AKUN_DEMO = [
  {
    id: 'fariz',
    nama: 'Fariz',
    email: 'fariz@sahamscope.id',
    password: 'password123',
    watchlist: 'BBCA · BMRI',
  },
  {
    id: 'dewi',
    nama: 'Dewi',
    email: 'dewi@sahamscope.id',
    password: 'password123',
    watchlist: 'BBNI · BBCA · BBRI · BMRI',
  },
]

// Pilihan time range chart
const DAFTAR_TIME_RANGE = ['1D', '1W', '1Y']

const timeRangeAktif = ref('1D')

// Data ini hanya ilustrasi preview halaman login
const DATA_PREVIEW = {
  '1D': {
    harga: '9.875',
    perubahan: '+125 (+1,28%)',
    naik: true,
    batang: [38, 52, 45, 64, 58, 76, 68, 88],
  },

  '1W': {
    harga: '9.725',
    perubahan: '+275 (+2,91%)',
    naik: true,
    batang: [55, 42, 60, 48, 66, 72, 64, 81],
  },

  '1Y': {
    harga: '9.875',
    perubahan: '+1.425 (+16,86%)',
    naik: true,
    batang: [30, 38, 45, 52, 48, 66, 74, 88],
  },
}

const dataChartAktif = computed(() => {
  return DATA_PREVIEW[timeRangeAktif.value]
})

function pilihTimeRange(timeRange) {
  timeRangeAktif.value = timeRange
}

function lanjut() {
  const tujuan = route.query.redirect || '/stream'
  router.push(tujuan)
}

function pesanError(err) {
  if (err.message === 'invalid credentials') {
    return 'Email atau kata sandi salah.'
  }

  return err.message || 'Terjadi kesalahan saat masuk.'
}

async function onSubmit() {
  error.value = ''

  try {
    await auth.login(email.value, password.value, remember.value)
    lanjut()
  } catch (err) {
    error.value = pesanError(err)
  }
}

async function loginDemo(akun) {
  error.value = ''
  demoLoading.value = akun.id

  try {
    await auth.login(akun.email, akun.password, true)
    lanjut()
  } catch (err) {
    error.value = pesanError(err)
  } finally {
    demoLoading.value = null
  }
}
</script>

<template>
  <div class="flex min-h-screen">
    <!-- BAGIAN KIRI -->
    <section
      class="hidden w-1/2 flex-col justify-between bg-primary p-12 text-primary-foreground md:flex"
    >
      <header>
        <p class="text-[20px] font-medium">
          ◆ StockVision
        </p>

        <p class="mt-1 text-[13px] opacity-70">
          Dashboard Pasar Saham Indonesia
        </p>
      </header>

      <!-- Preview kartu saham -->
      <div class="rounded-xl bg-white/10 p-5">
        <div class="flex items-center gap-2">
          <span class="text-2xl font-bold">
            BBCA
          </span>

          <span
            class="rounded bg-white/15 px-1.5 py-0.5 text-[10px] font-medium tracking-wide"
          >
            IDX
          </span>
        </div>

        <!-- Harga berubah sesuai time range -->
        <p class="tabular mt-3 text-[32px] font-bold leading-none">
          {{ dataChartAktif.harga }}
        </p>

        <!-- Persentase berubah sesuai time range -->
        <p
          class="tabular mt-1.5 text-[13px] font-medium"
          :class="
            dataChartAktif.naik
              ? 'text-[#4ade80]'
              : 'text-[#f87171]'
          "
        >
          {{ dataChartAktif.perubahan }}
        </p>

        <!-- Grafik preview -->
        <div
          class="mt-5 flex h-16 items-end gap-1.5"
          aria-label="Grafik preview saham BBCA"
        >
          <div
            v-for="(tinggi, index) in dataChartAktif.batang"
            :key="`${timeRangeAktif}-${index}`"
            class="chart-bar flex-1 rounded-sm bg-current"
            :style="{
              height: `${tinggi}%`,
              opacity: 0.25 + index * 0.075,
            }"
          ></div>
        </div>

        <!-- Tombol time range -->
        <div class="mt-4 flex gap-1">
          <button
            v-for="timeRange in DAFTAR_TIME_RANGE"
            :key="timeRange"
            type="button"
            class="tabular rounded px-2 py-1 text-[11px] transition-all duration-200"
            :class="
              timeRangeAktif === timeRange
                ? 'bg-white/20 font-medium text-white'
                : 'opacity-50 hover:bg-white/10 hover:opacity-80'
            "
            @click="pilihTimeRange(timeRange)"
          >
            {{ timeRange }}
          </button>
        </div>
      </div>

      <p class="max-w-md text-[13px] leading-relaxed opacity-70">
        Pantau data OHLC, foreign flow, insider transaction, dan jalankan
        crawling data saham Indonesia secara real-time.
      </p>
    </section>

    <!-- BAGIAN KANAN -->
    <section
      class="flex w-full flex-col justify-center bg-background p-6 sm:p-12 md:w-1/2"
    >
      <div class="mx-auto w-full max-w-sm">
        <h1 class="text-[22px] font-medium">
          Masuk ke StockVision
        </h1>

        <p class="mt-1 text-[13px] text-muted-foreground">
          Masukkan email dan kata sandi untuk melanjutkan
        </p>

        <form
          class="mt-8 flex flex-col gap-4"
          @submit.prevent="onSubmit"
        >
          <!-- Email -->
          <div class="space-y-2">
            <Label for="email">
              Email
            </Label>

            <Input
              id="email"
              v-model="email"
              type="email"
              autocomplete="email"
              placeholder="email@contoh.com"
              required
            />
          </div>

          <!-- Password -->
          <div class="space-y-2">
            <Label for="password">
              Password
            </Label>

            <Input
              id="password"
              v-model="password"
              type="password"
              autocomplete="current-password"
              placeholder="••••••••"
              required
            />
          </div>

          <!-- Ingat saya dan lupa password -->
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <Checkbox
                id="remember"
                v-model="remember"
              />

              <Label
                for="remember"
                class="cursor-pointer text-[12px] font-normal"
              >
                Ingat saya
              </Label>
            </div>

            <RouterLink
              to="/forgot-password"
              class="text-[12px] text-muted-foreground transition-colors hover:text-foreground"
            >
              Lupa password?
            </RouterLink>
          </div>

          <!-- Error -->
          <p
            v-if="error"
            role="alert"
            class="text-down text-[12px]"
          >
            {{ error }}
          </p>

          <!-- Tombol login -->
          <Button
            type="submit"
            class="w-full"
            :disabled="auth.loading"
          >
            {{
              auth.loading && !demoLoading
                ? 'Memverifikasi...'
                : 'Masuk'
            }}
          </Button>

          <!-- Create account -->
          <p class="text-center text-[12px] text-muted-foreground">
            Belum punya akun?

            <RouterLink
              to="/register"
              class="ml-1 font-medium text-foreground transition-colors hover:underline"
            >
              Buat akun
            </RouterLink>
          </p>
        </form>

        <!-- Pemisah akun demo -->
        <div class="my-6 flex items-center gap-3">
          <span class="h-px flex-1 bg-border"></span>

          <span class="text-[11px] text-muted-foreground">
            atau coba akun demo
          </span>

          <span class="h-px flex-1 bg-border"></span>
        </div>

        <!-- Akun demo -->
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <Button
            v-for="akun in AKUN_DEMO"
            :key="akun.id"
            type="button"
            variant="outline"
            class="h-auto flex-col items-start gap-0.5 py-2.5"
            :disabled="auth.loading"
            @click="loginDemo(akun)"
          >
            <span class="text-[13px] font-medium">
              {{
                demoLoading === akun.id
                  ? 'Masuk...'
                  : `Login sebagai ${akun.nama}`
              }}
            </span>

            <span
              class="tabular text-[10px] font-normal text-muted-foreground"
            >
              {{ akun.watchlist }}
            </span>
          </Button>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.chart-bar {
  transition:
    height 0.35s ease,
    opacity 0.35s ease;
}
</style>