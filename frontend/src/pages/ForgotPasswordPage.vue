<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Eye, EyeOff, Loader2 } from '@lucide/vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useAuthReset, MIN_PASSWORD, PANJANG_KODE } from '@/composables/useAuthReset'
import { useNotify } from '@/composables/useNotify'

const router = useRouter()
const notify = useNotify()

const {
  step,
  email,
  code,
  password,
  konfirmasi,
  loading,
  error,
  kodeSimulasi,
  sisaJeda,
  emailValid,
  kodeValid,
  passwordValid,
  bisaKirimUlang,
  setKode,
  kirimKode,
  verifikasiKode,
  simpanPassword,
  kembaliKeStep1,
} = useAuthReset()

const lihatPassword = ref(false)
const lihatKonfirmasi = ref(false)

const JUDUL = {
  1: { judul: 'Reset Password', sub: 'Reset akun database stockVision secara aman' },
  2: { judul: 'Reset Password', sub: 'Reset akun database stockVision secara aman' },
  3: { judul: 'Buat Password Baru', sub: 'Password baru harus berbeda dari password sebelumnya.' },
}
const header = computed(() => JUDUL[step.value])

async function onSimpan() {
  if (!(await simpanPassword())) return

  notify.success('Password berhasil diperbarui', 'Silakan masuk dengan password baru kamu.')
  // Email dibawa ke Login supaya user tidak perlu mengetiknya lagi.
  router.push({ name: 'login', query: { email: email.value.trim() } })
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-muted/40 p-6">
    <div class="w-full max-w-sm">
      <p class="text-center text-[14px] font-medium">◆ StockVision</p>

      <!-- Progress 3 step -->
      <div class="mt-5 flex items-center gap-1.5" aria-hidden="true">
        <span
          v-for="n in 3"
          :key="n"
          class="h-1 flex-1 rounded-full transition-colors duration-200"
          :class="n <= step ? 'bg-foreground' : 'bg-border'"
        ></span>
      </div>

      <div class="mt-4 rounded-xl border-[0.5px] border-border bg-card p-6">
        <h1 class="text-[18px] font-medium">{{ header.judul }}</h1>
        <p class="mt-1 text-[13px] text-muted-foreground">{{ header.sub }}</p>

        <Transition name="fade" mode="out-in">
          <!-- STEP 1 — email -->
          <form v-if="step === 1" key="1" class="mt-6 flex flex-col gap-4" @submit.prevent="kirimKode()">
            <div class="space-y-2">
              <Label for="reset-email">Email</Label>
              <Input
                id="reset-email"
                v-model="email"
                type="email"
                autocomplete="email"
                placeholder="email@contoh.com"
                autofocus
                required
              />
            </div>

            <p v-if="error" role="alert" class="text-down text-[12px]">{{ error }}</p>

            <Button type="submit" class="w-full" :disabled="loading || !emailValid">
              <Loader2 v-if="loading" class="size-3.5 animate-spin" />
              {{ loading ? 'Mengirim kode...' : 'Kirim Kode Verifikasi' }}
            </Button>
          </form>

          <!-- STEP 2 — kode verifikasi -->
          <form v-else-if="step === 2" key="2" class="mt-6 flex flex-col gap-4" @submit.prevent="verifikasiKode()">
            <p
              class="rounded-lg border-[0.5px] border-blue-200 bg-blue-50 px-3.5 py-2.5 text-[12px] leading-relaxed text-blue-900 dark:border-blue-900/60 dark:bg-blue-950/40 dark:text-blue-100"
            >
              Kode verifikasi {{ PANJANG_KODE }} digit telah dikirim ke
              <span class="font-medium">{{ email }}</span>
            </p>

            <!-- SMTP belum dikonfigurasi: backend menitipkan kodenya lewat response. -->
            <p
              v-if="kodeSimulasi"
              class="rounded-lg border-[0.5px] border-[var(--color-skip)]/30 bg-[var(--color-skip-bg)] px-3.5 py-2.5 text-[11px] leading-relaxed text-[var(--color-skip)]"
              role="status"
            >
              <span class="font-medium">Mode simulasi.</span>
              Email belum benar-benar terkirim — pakai kode
              <span class="tabular font-medium tracking-[0.15em]">{{ kodeSimulasi }}</span>
            </p>

            <div class="space-y-2">
              <Label for="reset-code" class="text-[10px] uppercase tracking-[0.06em] text-muted-foreground">
                {{ PANJANG_KODE }}-digit verification code
              </Label>
              <Input
                id="reset-code"
                :model-value="code"
                inputmode="text"
                autocomplete="one-time-code"
                :maxlength="PANJANG_KODE"
                placeholder="——————"
                autofocus
                class="tabular h-12 text-center text-[20px] font-medium uppercase tracking-[0.4em]"
                @update:model-value="setKode"
              />
            </div>

            <p v-if="error" role="alert" class="text-down text-[12px]">{{ error }}</p>

            <Button type="submit" class="w-full" :disabled="loading || !kodeValid">
              <Loader2 v-if="loading" class="size-3.5 animate-spin" />
              {{ loading ? 'Memverifikasi...' : 'Verifikasi Kode' }}
            </Button>

            <button
              type="button"
              class="text-[12px] text-muted-foreground transition-colors hover:text-foreground disabled:cursor-not-allowed disabled:hover:text-muted-foreground"
              :disabled="!bisaKirimUlang"
              @click="kirimKode({ lanjutStep: false })"
            >
              <span v-if="sisaJeda > 0" class="tabular">Kirim ulang kode dalam {{ sisaJeda }}s</span>
              <span v-else>Kirim ulang kode</span>
            </button>
          </form>

          <!-- STEP 3 — password baru -->
          <form v-else key="3" class="mt-6 flex flex-col gap-4" @submit.prevent="onSimpan">
            <div class="space-y-2">
              <Label for="reset-password">Password Baru</Label>
              <div class="relative">
                <Input
                  id="reset-password"
                  v-model="password"
                  :type="lihatPassword ? 'text' : 'password'"
                  autocomplete="new-password"
                  placeholder="••••••••"
                  class="pr-9"
                  autofocus
                  required
                />
                <button
                  type="button"
                  class="absolute inset-y-0 right-0 flex items-center px-2.5 text-muted-foreground transition-colors hover:text-foreground"
                  :aria-label="lihatPassword ? 'Sembunyikan password' : 'Tampilkan password'"
                  @click="lihatPassword = !lihatPassword"
                >
                  <component :is="lihatPassword ? EyeOff : Eye" class="size-3.5" />
                </button>
              </div>
              <p class="text-[11px] text-muted-foreground">Minimal {{ MIN_PASSWORD }} karakter.</p>
            </div>

            <div class="space-y-2">
              <Label for="reset-konfirmasi">Konfirmasi Password Baru</Label>
              <div class="relative">
                <Input
                  id="reset-konfirmasi"
                  v-model="konfirmasi"
                  :type="lihatKonfirmasi ? 'text' : 'password'"
                  autocomplete="new-password"
                  placeholder="••••••••"
                  class="pr-9"
                  required
                />
                <button
                  type="button"
                  class="absolute inset-y-0 right-0 flex items-center px-2.5 text-muted-foreground transition-colors hover:text-foreground"
                  :aria-label="lihatKonfirmasi ? 'Sembunyikan password' : 'Tampilkan password'"
                  @click="lihatKonfirmasi = !lihatKonfirmasi"
                >
                  <component :is="lihatKonfirmasi ? EyeOff : Eye" class="size-3.5" />
                </button>
              </div>
              <!-- Peringatan hanya muncul setelah user benar-benar mulai mengetik konfirmasi. -->
              <p v-if="konfirmasi && password !== konfirmasi" class="text-down text-[11px]">
                Konfirmasi password tidak sama.
              </p>
            </div>

            <p v-if="error" role="alert" class="text-down text-[12px]">{{ error }}</p>

            <Button type="submit" class="w-full" :disabled="loading || !passwordValid">
              <Loader2 v-if="loading" class="size-3.5 animate-spin" />
              {{ loading ? 'Menyimpan...' : 'Simpan Password Baru' }}
            </Button>
          </form>
        </Transition>
      </div>

      <div class="mt-4 flex justify-center gap-4 text-[12px]">
        <button
          v-if="step === 2"
          type="button"
          class="text-muted-foreground transition-colors hover:text-foreground"
          @click="kembaliKeStep1"
        >
          Kembali ke Step 1
        </button>
        <RouterLink to="/login" class="text-muted-foreground transition-colors hover:text-foreground">
          Kembali ke halaman Login
        </RouterLink>
      </div>
    </div>
  </div>
</template>
