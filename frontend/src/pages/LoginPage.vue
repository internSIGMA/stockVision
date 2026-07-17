<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

// Datang dari flow reset password: email sudah diketahui, jangan minta ketik ulang.
const email = ref(route.query.email || '')
const password = ref('')
const remember = ref(true)
const error = ref('')
const demoLoading = ref(null)

// Akun yang disemai backend di tabel idxsaham.users.
// Subtitle = watchlist nyata dari DB SETELAH disaring ke emiten yang didukung
// backend (GOTO, ASII, TLKM, ANTM, PTBA ditolak dengan HTTP 400).
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

// Tinggi batang grafik preview — ilustrasi statis, bukan data pasar sungguhan.
const BATANG_PREVIEW = [38, 52, 45, 64, 58, 76, 68, 88]

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

async function loginDemo(akun) {
  error.value = ''
  demoLoading.value = akun.id
  try {
    await auth.login(akun.email, akun.password)
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
    <!-- KIRI — preview aplikasi (disembunyikan di mobile) -->
    <section
      class="hidden w-1/2 flex-col justify-between bg-primary p-12 text-primary-foreground md:flex"
    >
      <header>
        <p class="text-[20px] font-medium">◆ StockVision</p>
        <p class="mt-1 text-[13px] opacity-70">Dashboard Pasar Saham Indonesia</p>
      </header>

      <div class="rounded-xl bg-white/10 p-5">
        <div class="flex items-center gap-2">
          <span class="text-2xl font-bold">BBCA</span>
          <span class="rounded bg-white/15 px-1.5 py-0.5 text-[10px] font-medium tracking-wide">
            IDX
          </span>
        </div>

        <p class="tabular mt-3 text-[32px] font-bold leading-none">9.875</p>
        <p class="tabular mt-1.5 text-[13px] font-medium text-[#4ade80]">+125 (+1,28%)</p>

        <div class="mt-5 flex h-16 items-end gap-1.5" aria-hidden="true">
          <div
            v-for="(tinggi, i) in BATANG_PREVIEW"
            :key="i"
            class="flex-1 rounded-sm bg-current"
            :style="{ height: `${tinggi}%`, opacity: 0.25 + i * 0.075 }"
          ></div>
        </div>

        <div class="mt-4 flex gap-1">
          <span
            v-for="(tf, i) in ['1D', '1W', '1M', '3M']"
            :key="tf"
            class="tabular rounded px-2 py-1 text-[11px]"
            :class="i === 0 ? 'bg-white/20 font-medium' : 'opacity-50'"
          >
            {{ tf }}
          </span>
        </div>
      </div>

      <p class="max-w-md text-[13px] leading-relaxed opacity-70">
        Pantau data OHLC, foreign flow, insider transaction, dan jalankan crawling data saham
        Indonesia secara real-time.
      </p>
    </section>

    <!-- KANAN — form login -->
    <section class="flex w-full flex-col justify-center bg-background p-12 md:w-1/2">
      <div class="mx-auto w-full max-w-sm">
        <h1 class="text-[22px] font-medium">Masuk ke StockVision</h1>
        <p class="mt-1 text-[13px] text-muted-foreground">
          Gunakan akun demo di bawah untuk mencoba
        </p>

        <form class="mt-8 flex flex-col gap-4" @submit.prevent="onSubmit">
          <div class="space-y-2">
            <Label for="email">Email</Label>
            <Input
              id="email"
              v-model="email"
              type="email"
              autocomplete="email"
              placeholder="email@contoh.com"
              required
            />
          </div>

          <div class="space-y-2">
            <Label for="password">Password</Label>
            <Input
              id="password"
              v-model="password"
              type="password"
              autocomplete="current-password"
              placeholder="••••••••"
              required
            />
          </div>

          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <Checkbox id="remember" v-model="remember" />
              <Label for="remember" class="text-[12px] font-normal">Ingat saya</Label>
            </div>
            <RouterLink
              to="/forgot-password"
              class="text-[12px] text-muted-foreground transition-colors hover:text-foreground"
            >
              Lupa password?
            </RouterLink>
          </div>

          <p v-if="error" role="alert" class="text-down text-[12px]">{{ error }}</p>

          <Button type="submit" class="w-full" :disabled="auth.loading">
            {{ auth.loading && !demoLoading ? 'Memverifikasi...' : 'Masuk' }}
          </Button>
        </form>

        <div class="my-6 flex items-center gap-3">
          <span class="h-px flex-1 bg-border"></span>
          <span class="text-[11px] text-muted-foreground">atau coba akun demo</span>
          <span class="h-px flex-1 bg-border"></span>
        </div>

        <div class="grid grid-cols-2 gap-3">
          <Button
            v-for="akun in AKUN_DEMO"
            :key="akun.id"
            variant="outline"
            class="h-auto flex-col items-start gap-0.5 py-2.5"
            :disabled="auth.loading"
            @click="loginDemo(akun)"
          >
            <span class="text-[13px] font-medium">
              {{ demoLoading === akun.id ? 'Masuk...' : `Login sebagai ${akun.nama}` }}
            </span>
            <span class="tabular text-[10px] font-normal text-muted-foreground">
              {{ akun.watchlist }}
            </span>
          </Button>
        </div>
      </div>
    </section>
  </div>
</template>
