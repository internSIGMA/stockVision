<script setup>
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'
import { Eye, EyeOff } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'
import { useGoogleSignIn } from '@/composables/useGoogleSignIn'

const auth = useAuthStore()
const router = useRouter()

/*
  default_ticker tidak lagi ditanyakan saat mendaftar — kolomnya tetap dikirim
  supaya backend punya nilai dan seed watchlist jalan. Emiten utama bisa
  diganti kapan saja lewat pengaturan akun.
*/
const form = ref({
  name: '',
  email: '',
  username: '',
  password: '',
  default_ticker: 'BBCA',
})
const error = ref('')
const lihatSandi = ref(false)

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

/*
  Daftar lewat Google memakai endpoint yang sama dengan login: backend
  membuatkan akun baru kalau emailnya belum terdaftar, dan langsung memakai
  yang lama kalau sudah ada. Jadi tidak ada jalur registrasi terpisah.
*/
const { siap, error: googleError, pasang } = useGoogleSignIn(async (credential) => {
  error.value = ''
  try {
    await auth.googleLogin(credential)
    router.push('/stream')
  } catch (err) {
    error.value = err.message
  }
})

const wadahGoogle = ref(null)

onMounted(() => pasang(wadahGoogle.value, wadahGoogle.value?.offsetWidth))

/** Klik hanya sampai ke sini kalau tombol asli Google gagal dipasang. */
function googleTidakSiap() {
  error.value = googleError.value || 'Google Sign-In belum siap, coba beberapa saat lagi.'
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-background px-5 py-10 sm:px-6 sm:py-14">
    <div class="w-full max-w-[400px] sm:rounded-2xl sm:border sm:border-border sm:bg-card sm:p-9 sm:shadow-[0_1px_2px_rgba(17,24,39,0.04),0_12px_32px_-12px_rgba(17,24,39,0.12)]">
      <h1 class="text-[26px] font-semibold leading-tight tracking-tight text-foreground sm:text-[30px]">
        Buat akun StockVision
      </h1>

      <form class="mt-7 flex flex-col gap-5" @submit.prevent="onSubmit">
        <div class="space-y-2">
          <label for="nama" class="block text-[13px] font-medium text-foreground sm:text-sm">Nama</label>
          <input
            id="nama"
            v-model="form.name"
            type="text"
            autocomplete="name"
            placeholder="Nama lengkap"
            class="field"
          />
        </div>

        <div class="space-y-2">
          <label for="email" class="block text-[13px] font-medium text-foreground sm:text-sm">Email</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            autocomplete="email"
            placeholder="email@contoh.com"
            class="field"
          />
        </div>

        <div class="space-y-2">
          <label for="username" class="block text-[13px] font-medium text-foreground sm:text-sm">Username</label>
          <input
            id="username"
            v-model="form.username"
            type="text"
            autocomplete="username"
            placeholder="username"
            class="field"
          />
        </div>

        <div class="space-y-2">
          <label for="password" class="block text-[13px] font-medium text-foreground sm:text-sm">
            Kata sandi
          </label>

          <div class="relative">
            <input
              id="password"
              v-model="form.password"
              :type="lihatSandi ? 'text' : 'password'"
              autocomplete="new-password"
              :placeholder="`Minimal ${MIN_PASSWORD} karakter`"
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
          {{ auth.loading ? 'Mendaftarkan…' : 'Daftar' }}
        </button>
      </form>

      <div class="my-7 flex items-center gap-3">
        <span class="h-px flex-1 bg-border"></span>

        <span class="text-[11px] font-medium tracking-[0.12em] text-muted-foreground">
          ATAU DAFTAR DENGAN
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

          Daftar dengan Google
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

      <p class="mt-7 text-center text-[14px] text-muted-foreground">
        Sudah punya akun?
        <RouterLink
          to="/login"
          class="ml-1 font-semibold text-[var(--primary)] underline-offset-4 transition-colors hover:text-[var(--primary-hover)] hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--ring)]"
        >
          Masuk
        </RouterLink>
      </p>
    </div>
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

.field:hover {
  border-color: var(--primary-light);
}

.field:focus {
  border-color: var(--ring);
  box-shadow: 0 0 0 3px var(--primary-soft);
}
</style>
