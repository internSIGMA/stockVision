<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { SUPPORTED_TICKERS } from '@/api/StockVision'

const auth = useAuthStore()
const router = useRouter()

const form = ref({
  name: '',
  email: '',
  username: '',
  password: '',
  default_ticker: 'BBCA',
})
const error = ref('')

const MIN_PASSWORD = 8

/**
 * Backend melempar ValueError tanpa penangan untuk field wajib yang kosong,
 * jadi errornya keluar sebagai HTTP 500. Validasi di sini yang menahannya.
 */
const masalah = computed(() => {
  const { name, email, username, password } = form.value
  if (!name.trim()) return 'Nama belum diisi.'
  if (!email.trim()) return 'Email belum diisi.'
  if (!username.trim()) return 'Username belum diisi.'
  if (password.length < MIN_PASSWORD) return `Kata sandi minimal ${MIN_PASSWORD} karakter.`
  return ''
})

async function onSubmit() {
  error.value = masalah.value
  if (error.value) return

  try {
    await auth.register({
      ...form.value,
      email: form.value.email.trim().toLowerCase(),
      username: form.value.username.trim(),
      name: form.value.name.trim(),
    })
    router.push('/stream')
  } catch (err) {
    // Email/username kembar melanggar UNIQUE constraint dan muncul sebagai 500.
    error.value = /duplicate|unique/i.test(err.message)
      ? 'Email atau username sudah terpakai.'
      : err.message
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-[#1c1c1c] px-6 py-12">
    <div class="w-full max-w-[340px]">
      <h1 class="text-[24px] font-semibold text-white">Buat akun StockVision</h1>
      <p class="mt-1 text-[11px] text-white/40">Gratis, langsung bisa dipakai memantau IDX</p>

      <form class="mt-8 flex flex-col gap-4" @submit.prevent="onSubmit">
        <div class="space-y-2">
          <label for="nama" class="block text-[12px] font-medium text-white/85">Nama</label>
          <input
            id="nama"
            v-model="form.name"
            type="text"
            autocomplete="name"
            placeholder="Nama lengkap"
            class="h-10 w-full rounded-md border border-white/10 bg-[#2b2b2b] px-3 text-[13px] text-white outline-none transition-colors placeholder:text-white/30 focus:border-white/30"
          />
        </div>

        <div class="space-y-2">
          <label for="email" class="block text-[12px] font-medium text-white/85">Email</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            autocomplete="email"
            placeholder="email@contoh.com"
            class="h-10 w-full rounded-md border border-white/10 bg-[#2b2b2b] px-3 text-[13px] text-white outline-none transition-colors placeholder:text-white/30 focus:border-white/30"
          />
        </div>

        <div class="space-y-2">
          <label for="username" class="block text-[12px] font-medium text-white/85">Username</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            autocomplete="username"
            placeholder="username"
            class="h-10 w-full rounded-md border border-white/10 bg-[#2b2b2b] px-3 text-[13px] text-white outline-none transition-colors placeholder:text-white/30 focus:border-white/30"
          />
        </div>

        <div class="space-y-2">
          <label for="password" class="block text-[12px] font-medium text-white/85">
            Kata sandi
          </label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            autocomplete="new-password"
            :placeholder="`Minimal ${MIN_PASSWORD} karakter`"
            class="h-10 w-full rounded-md border border-white/10 bg-[#2b2b2b] px-3 text-[13px] text-white outline-none transition-colors placeholder:text-white/30 focus:border-white/30"
          />
        </div>

        <div class="space-y-2">
          <label for="emiten" class="block text-[12px] font-medium text-white/85">
            Emiten utama
          </label>
          <select
            id="emiten"
            v-model="form.default_ticker"
            class="tabular h-10 w-full rounded-md border border-white/10 bg-[#2b2b2b] px-3 text-[13px] text-white outline-none transition-colors focus:border-white/30"
          >
            <option v-for="t in SUPPORTED_TICKERS" :key="t" :value="t">{{ t }}</option>
          </select>
        </div>

        <p v-if="error" role="alert" class="text-[12px] text-[#f87171]">{{ error }}</p>

        <button
          type="submit"
          :disabled="auth.loading"
          class="h-10 w-full rounded-md bg-white text-[13px] font-semibold text-[#171717] transition-colors hover:bg-white/90 disabled:opacity-60"
        >
          {{ auth.loading ? 'Mendaftarkan…' : 'Daftar' }}
        </button>
      </form>

      <p class="mt-6 text-center text-[12px] text-white/40">
        Sudah punya akun?
        <RouterLink to="/login" class="text-white/80 transition-colors hover:text-white">
          Masuk
        </RouterLink>
      </p>
    </div>
  </div>
</template>
