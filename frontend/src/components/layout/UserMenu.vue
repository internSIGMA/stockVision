<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronDown, LogOut, Settings, X } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'
import { useNotify } from '@/composables/useNotify'
import { useProfilePrefs } from '@/composables/useProfilePrefs'
import { SUPPORTED_TICKERS } from '@/api/StockVision'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'

const auth = useAuthStore()
const router = useRouter()
const notify = useNotify()

const terbuka = ref(false)
const akunTerbuka = ref(false)
const akar = ref(null)

const inisial = computed(() => (auth.user?.name?.[0] || '?').toUpperCase())

// Menu ini hanya berisi dua aksi, jadi cukup dropdown sendiri ketimbang
// menarik seluruh primitif DropdownMenu beserta portal dan focus trap-nya.
function tutupDiLuar(e) {
  if (terbuka.value && akar.value && !akar.value.contains(e.target)) terbuka.value = false
}

function tutupDiEscape(e) {
  if (e.key !== 'Escape') return
  if (akunTerbuka.value) akunTerbuka.value = false
  else terbuka.value = false
}

onMounted(() => {
  document.addEventListener('pointerdown', tutupDiLuar)
  document.addEventListener('keydown', tutupDiEscape)
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', tutupDiLuar)
  document.removeEventListener('keydown', tutupDiEscape)
})

// ---------------------------------------------------------------
// Form "Kelola Akun"
// ---------------------------------------------------------------

const prefs = useProfilePrefs(auth.user?.id)

const MAKS_FOTO = 2 * 1024 * 1024 // 2 MB

const form = ref({ name: '', username: '', email: '', defaultTicker: 'BBCA' })
const foto = ref('')
const phone = ref('')
const emailNotif = ref(true)
const menyimpan = ref(false)
const inputFoto = ref(null)

/** Isi ulang form dari sumber kebenaran tiap kali modal dibuka. */
function resetForm() {
  form.value = {
    name: auth.user?.name || '',
    username: auth.user?.username || '',
    email: auth.user?.email || '',
    defaultTicker: auth.emitenUtama,
  }
  foto.value = prefs.photo.value
  phone.value = prefs.phone.value
  emailNotif.value = prefs.emailNotif.value
}

watch(akunTerbuka, (buka) => {
  if (buka) resetForm()
})

function bukaAkun() {
  terbuka.value = false
  akunTerbuka.value = true
}

function pilihFoto(e) {
  const file = e.target.files?.[0]
  if (!file) return
  if (file.size > MAKS_FOTO) {
    notify.error('Foto terlalu besar', 'Maksimal 2 MB.')
    return
  }
  const reader = new FileReader()
  reader.onload = () => (foto.value = String(reader.result))
  reader.readAsDataURL(file)
}

async function simpan() {
  if (menyimpan.value) return
  menyimpan.value = true

  try {
    // Hanya field yang benar-benar disimpan backend yang dikirim.
    await auth.updateProfile({
      name: form.value.name.trim(),
      username: form.value.username.trim(),
      email: form.value.email.trim().toLowerCase(),
      default_ticker: form.value.defaultTicker,
    })

    // Nomor telepon, foto, dan notifikasi email tidak punya kolom di backend.
    prefs.phone.value = phone.value.trim()
    prefs.photo.value = foto.value
    prefs.emailNotif.value = emailNotif.value
    prefs.simpan()

    notify.success('Perubahan disimpan')
    akunTerbuka.value = false
  } catch (err) {
    notify.error('Gagal menyimpan', err.message)
  } finally {
    menyimpan.value = false
  }
}

function keluar() {
  terbuka.value = false
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div ref="akar" class="relative">
    <button
      type="button"
      class="flex h-[40px] items-center gap-2.5 rounded-lg border-[0.5px] border-border px-2.5 transition-colors hover:bg-accent"
      :aria-expanded="terbuka"
      aria-haspopup="menu"
      @click="terbuka = !terbuka"
    >
      <span
        class="flex size-[26px] items-center justify-center overflow-hidden rounded-full bg-muted text-[11px] font-medium"
        aria-hidden="true"
      >
        <img v-if="prefs.photo.value" :src="prefs.photo.value" alt="" class="size-full object-cover" />
        <template v-else>{{ inisial }}</template>
      </span>

      <!-- Nama emiten di samping nama user dihapus atas permintaan; nama saja. -->
      <span class="hidden whitespace-nowrap text-[13px] sm:inline">{{ auth.user?.name }}</span>

      <ChevronDown
        class="size-3 text-muted-foreground transition-transform"
        :class="terbuka && 'rotate-180'"
        aria-hidden="true"
      />
    </button>

    <div
      v-if="terbuka"
      role="menu"
      class="absolute right-0 top-[calc(100%+8px)] z-50 w-[260px] overflow-hidden rounded-xl border-[0.5px] border-border bg-popover shadow-lg"
    >
      <div class="flex items-center gap-3 p-4">
        <span
          class="flex size-9 shrink-0 items-center justify-center overflow-hidden rounded-full bg-muted text-[13px] font-medium"
          aria-hidden="true"
        >
          <img v-if="prefs.photo.value" :src="prefs.photo.value" alt="" class="size-full object-cover" />
          <template v-else>{{ inisial }}</template>
        </span>
        <div class="min-w-0">
          <p class="truncate text-[13px] font-semibold">{{ auth.user?.name }}</p>
          <p class="tabular truncate text-[11px] text-muted-foreground">{{ auth.user?.email }}</p>
        </div>
      </div>

      <div class="h-px bg-border"></div>

      <button
        type="button"
        role="menuitem"
        class="flex w-full items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-accent"
        @click="bukaAkun"
      >
        <Settings class="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
        <span>
          <span class="block text-[13px] font-medium">Kelola akun</span>
          <span class="block text-[11px] text-muted-foreground">Profil dan preferensi</span>
        </span>
      </button>

      <button
        type="button"
        role="menuitem"
        class="flex w-full items-start gap-3 px-4 py-3 text-left transition-colors hover:bg-accent"
        @click="keluar"
      >
        <LogOut class="text-down mt-0.5 size-4 shrink-0" aria-hidden="true" />
        <span>
          <span class="text-down block text-[13px] font-medium">Keluar</span>
          <span class="block text-[11px] text-muted-foreground">Keluar dari StockVision</span>
        </span>
      </button>
    </div>

    <!-- ============ Modal Kelola Akun ============ -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="akunTerbuka"
          class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4"
          @pointerdown.self="akunTerbuka = false"
        >
          <div
            class="flex max-h-[88vh] w-full max-w-[640px] flex-col overflow-hidden rounded-2xl bg-card shadow-xl"
            role="dialog"
            aria-modal="true"
            aria-labelledby="judul-akun"
          >
            <header class="flex items-start gap-3 px-6 pb-4 pt-6">
              <div class="min-w-0 flex-1">
                <h2 id="judul-akun" class="text-[20px] font-semibold">Kelola Akun</h2>
                <p class="mt-1 text-[13px] text-muted-foreground">
                  Perbarui informasi akun dan preferensi pengguna.
                </p>
              </div>
              <button
                type="button"
                class="flex size-8 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
                aria-label="Tutup"
                @click="akunTerbuka = false"
              >
                <X class="size-4" />
              </button>
            </header>

            <form class="flex-1 overflow-y-auto px-6 pb-2" @submit.prevent="simpan">
              <!-- Foto -->
              <div class="flex items-center gap-4 py-2">
                <span
                  class="flex size-14 shrink-0 items-center justify-center overflow-hidden rounded-full bg-muted text-[20px] font-medium"
                  aria-hidden="true"
                >
                  <img v-if="foto" :src="foto" alt="" class="size-full object-cover" />
                  <template v-else>{{ inisial }}</template>
                </span>
                <div>
                  <input
                    ref="inputFoto"
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    class="hidden"
                    @change="pilihFoto"
                  />
                  <Button type="button" variant="outline" size="sm" @click="inputFoto?.click()">
                    Ganti foto
                  </Button>
                  <p class="mt-2 text-[11px] text-muted-foreground">
                    JPG, PNG, atau WEBP, maksimal 2 MB.
                  </p>
                </div>
              </div>

              <div class="grid grid-cols-1 gap-x-5 gap-y-4 py-3 sm:grid-cols-2">
                <div class="space-y-1.5">
                  <label for="ak-nama" class="text-[13px] font-medium">Nama lengkap</label>
                  <input id="ak-nama" v-model="form.name" type="text" class="ak-input" />
                </div>
                <div class="space-y-1.5">
                  <label for="ak-username" class="text-[13px] font-medium">Username</label>
                  <input id="ak-username" v-model="form.username" type="text" class="ak-input tabular" />
                </div>
                <div class="space-y-1.5">
                  <label for="ak-email" class="text-[13px] font-medium">Email</label>
                  <input id="ak-email" v-model="form.email" type="email" class="ak-input tabular" />
                </div>
                <div class="space-y-1.5">
                  <label for="ak-phone" class="text-[13px] font-medium">Nomor telepon</label>
                  <input
                    id="ak-phone"
                    v-model="phone"
                    type="tel"
                    placeholder="08xxxxxxxxxx"
                    class="ak-input tabular"
                  />
                </div>
              </div>

              <div class="space-y-1.5 py-3">
                <label for="ak-saham" class="text-[13px] font-medium">Saham utama</label>
                <select id="ak-saham" v-model="form.defaultTicker" class="ak-input tabular">
                  <option v-for="t in SUPPORTED_TICKERS" :key="t" :value="t">{{ t }}</option>
                </select>
                <p class="text-[12px] text-muted-foreground">
                  Saham yang otomatis dibuka setelah pengguna masuk.
                </p>
              </div>

              <div class="flex items-center gap-3 rounded-xl border-[0.5px] border-border p-4">
                <div class="min-w-0 flex-1">
                  <p class="text-[13px] font-medium">Notifikasi email</p>
                  <p class="mt-0.5 text-[12px] text-muted-foreground">
                    Dapatkan informasi crawler dan perubahan saham.
                  </p>
                </div>
                <Switch v-model="emailNotif" aria-label="Notifikasi email" />
              </div>
            </form>

            <footer class="flex items-center justify-end gap-3 border-t-[0.5px] border-border px-6 py-4">
              <Button type="button" variant="outline" :disabled="menyimpan" @click="akunTerbuka = false">
                Batal
              </Button>
              <Button type="button" :disabled="menyimpan" @click="simpan">
                {{ menyimpan ? 'Menyimpan…' : 'Simpan perubahan' }}
              </Button>
            </footer>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.ak-input {
  height: 2.5rem;
  width: 100%;
  border-radius: 0.5rem;
  border: 0.5px solid var(--border);
  background: var(--background);
  padding: 0 0.75rem;
  font-size: 13px;
  outline: none;
  transition: border-color 0.15s;
}
.ak-input:focus {
  border-color: color-mix(in oklch, var(--foreground) 40%, transparent);
}
</style>
