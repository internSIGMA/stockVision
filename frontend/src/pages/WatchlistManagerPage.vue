<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/market'
import { useNotify } from '@/composables/useNotify'
import { getWatchlistQuota, isSupported, SUPPORTED_TICKERS } from '@/api/StockVision'
import { Button } from '@/components/ui/button'
import { Check, Plus } from '@lucide/vue'

/**
 * WatchlistManagerPage
 * - Edit nama daftar pantau
 * - Input bebas untuk semua emiten IDX
 * - Kuota maks 9 emiten unik per akun
 */
const emit = defineEmits(['close'])

const auth   = useAuthStore()
const market = useMarketStore()
const notify = useNotify()

// ──────────────────────────────────────────────
// State
// ──────────────────────────────────────────────
const menyimpan    = ref(false)
const inputError   = ref('')
const quota        = ref({ used_quota: 0, max_quota: 9, remaining_quota: 9, unique_symbols: [] })
const loadingQuota = ref(false)
const menghapus    = ref(false)

/** Salinan lokal supaya bisa di-cancel */
const dipilih = ref([...auth.watchlistTersimpan])
const inputName = ref(auth.activeWatchlist?.name || '')

// ──────────────────────────────────────────────
// Computed
// ──────────────────────────────────────────────
const berubah = computed(() => {
  const awal = [...auth.watchlistTersimpan].sort().join(',')
  const kini = [...dipilih.value].sort().join(',')
  const namaAwal = auth.activeWatchlist?.name || ''
  return awal !== kini || inputName.value.trim() !== namaAwal
})

const uniqueCount   = computed(() => new Set(dipilih.value.map(s => s.toUpperCase())).size)
const remainingSlot = computed(() => Math.max(0, 9 - uniqueCount.value))

// Warna progress bar kuota
const quotaBarColor = computed(() => {
  if (uniqueCount.value >= 9)  return 'bg-destructive'
  if (uniqueCount.value >= 7)   return 'bg-yellow-500'
  return 'bg-primary'
})

// ──────────────────────────────────────────────
// Load quota dari server
// ──────────────────────────────────────────────
async function muatKuota() {
  if (!auth.user?.id) return
  loadingQuota.value = true
  try {
    const q = await getWatchlistQuota(auth.user.id)
    quota.value = q
  } catch {
    // silent — local computed is good enough
  } finally {
    loadingQuota.value = false
  }
}

onMounted(muatKuota)

// ──────────────────────────────────────────────
// Add ticker
// ──────────────────────────────────────────────
function tambahTicker(ticker) {
  inputError.value = ''

  if (dipilih.value.map(s => s.toUpperCase()).includes(ticker.toUpperCase())) {
    return
  }

  const currentUnique = new Set(dipilih.value.map(s => s.toUpperCase()))
  if (currentUnique.size >= 9) {
    inputError.value = `Batas kuota emiten tercapai!`
    return
  }

  dipilih.value = [...dipilih.value, ticker]
}

function hapus(ticker) {
  dipilih.value = dipilih.value.filter(t => t.toUpperCase() !== ticker.toUpperCase())
  if (auth.emitenUtama === ticker) {
    market.setTicker(dipilih.value[0] ?? '')
  }
}

// ──────────────────────────────────────────────
// Save & Cancel
// ──────────────────────────────────────────────
async function simpan() {
  if (!berubah.value || menyimpan.value) return
  if (!inputName.value.trim()) {
    notify.error('Gagal menyimpan', 'Nama daftar pantau tidak boleh kosong.')
    return
  }
  menyimpan.value = true
  try {
    await auth.saveWatchlist(dipilih.value, inputName.value.trim())
    if (!dipilih.value.includes(market.selectedTicker)) {
      market.setTicker(dipilih.value[0] ?? auth.emitenUtama)
    }
    notify.success('Daftar pantau tersimpan', `${inputName.value.trim()} diperbarui.`)
    await muatKuota()
  } catch (err) {
    const msg = err?.response?.data?.error || err.message || 'Gagal menyimpan watchlist'
    notify.error('Gagal menyimpan watchlist', msg)
  } finally {
    menyimpan.value = false
  }
}

function batal() {
  dipilih.value   = [...auth.watchlistTersimpan]
  inputName.value = auth.activeWatchlist?.name || ''
  inputError.value  = ''
}

async function hapusDaftarPantau() {
  if (auth.watchlists.length <= 1 || menghapus.value) return
  if (!confirm(`Hapus daftar pantau "${auth.activeWatchlist?.name}"?`)) return
  
  menghapus.value = true
  try {
    await auth.hapusWatchlist(auth.activeWatchlistId)
    notify.success('Daftar pantau dihapus')
    emit('close')
  } catch (err) {
    notify.error('Gagal menghapus daftar pantau', err.message)
  } finally {
    menghapus.value = false
  }
}


</script>

<template>
  <div class="flex flex-col gap-4 p-4">

    <!-- Input Nama Watchlist -->
    <div class="flex flex-col gap-1.5">
      <label class="text-[11px] font-medium text-muted-foreground">
        Nama Daftar Pantau
      </label>
      <input
        v-model="inputName"
        type="text"
        placeholder="Contoh: Saham Teknologi"
        class="rounded-md border border-input bg-background px-3 py-1.5 text-[13px] shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
      />
    </div>

    <!-- Quota bar -->
    <div class="rounded-lg border border-border bg-card p-3">
      <div class="mb-1.5 flex items-center justify-between">
        <span class="text-[11px] font-medium text-muted-foreground">Kuota Emiten</span>
        <span
          class="tabular text-[11px] font-semibold"
          :class="uniqueCount >= 9 ? 'text-destructive' : 'text-foreground'"
        >
          {{ uniqueCount }} / 9
        </span>
      </div>
      <div class="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          class="h-full rounded-full transition-all duration-300"
          :class="quotaBarColor"
          :style="{ width: `${(uniqueCount / 9) * 100}%` }"
        />
      </div>
      <p class="mt-1 text-[10px] text-muted-foreground">
        {{ remainingSlot > 0 ? `Sisa ${remainingSlot} slot` : 'Kuota penuh — hapus emiten lama untuk menambah yang baru.' }}
      </p>
    </div>

    <!-- Pilihan Emiten -->
    <div class="flex flex-col gap-2">
      <label class="text-[11px] font-medium text-muted-foreground">
        Emiten Tersedia (Pilih untuk menambah/menghapus)
      </label>
      <div class="grid grid-cols-3 gap-2 sm:grid-cols-4">
        <button
          v-for="ticker in SUPPORTED_TICKERS"
          :key="ticker"
          type="button"
          class="flex items-center justify-center gap-1.5 rounded-md border px-2 py-1.5 text-[12px] font-medium transition-all"
          :class="{
            'border-primary bg-primary text-primary-foreground shadow-sm': dipilih.map(s => s.toUpperCase()).includes(ticker.toUpperCase()),
            'border-border bg-card hover:bg-accent hover:text-accent-foreground': !dipilih.map(s => s.toUpperCase()).includes(ticker.toUpperCase()) && uniqueCount < 9,
            'border-border bg-muted text-muted-foreground opacity-50 cursor-not-allowed': !dipilih.map(s => s.toUpperCase()).includes(ticker.toUpperCase()) && uniqueCount >= 9
          }"
          :disabled="!dipilih.map(s => s.toUpperCase()).includes(ticker.toUpperCase()) && uniqueCount >= 9"
          @click="dipilih.map(s => s.toUpperCase()).includes(ticker.toUpperCase()) ? hapus(ticker) : tambahTicker(ticker)"
        >
          <Check v-if="dipilih.map(s => s.toUpperCase()).includes(ticker.toUpperCase())" class="size-3.5" />
          <Plus v-else class="size-3.5 opacity-70" />
          {{ ticker }}
        </button>
      </div>
      <p v-if="inputError" class="text-[11px] text-destructive">{{ inputError }}</p>
    </div>

    <!-- Daftar emiten terpilih -->
    <div class="flex flex-col gap-1">
      <p class="text-[11px] font-medium text-muted-foreground">Emiten di Watchlist ({{ dipilih.length }})</p>

      <p v-if="!dipilih.length" class="text-[12px] text-muted-foreground italic">
        Belum ada emiten. Tambahkan di atas.
      </p>

      <ul class="grid grid-cols-2 gap-1.5 sm:grid-cols-3">
        <li
          v-for="ticker in dipilih"
          :key="ticker"
          class="flex items-center justify-between gap-1 rounded-md border border-border bg-card px-2.5 py-1.5"
        >
          <span class="flex items-center gap-1.5">
            <span
              class="flex size-6 shrink-0 items-center justify-center rounded-full bg-[var(--color-info-bg)] font-mono text-[10px] font-semibold text-[var(--color-info-ink)]"
            >
              {{ ticker.charAt(0) }}
            </span>
            <span class="tabular text-[12px] font-semibold">{{ ticker }}</span>
            <span
              v-if="auth.emitenUtama === ticker"
              class="rounded-full bg-primary/15 px-1.5 py-0.5 text-[9px] font-medium text-primary"
            >
              Utama
            </span>
          </span>
          <button
            class="size-5 shrink-0 rounded text-[10px] text-muted-foreground hover:bg-destructive/15 hover:text-destructive"
            title="Hapus dari watchlist"
            @click="hapus(ticker)"
          >
            ✕
          </button>
        </li>
      </ul>
    </div>

    <!-- Catatan -->
    <p class="text-[10px] leading-relaxed text-muted-foreground">
      Data OHLC historis untuk emiten baru akan diunduh otomatis dari
      <strong>yfinance</strong> saat emiten pertama kali dipilih di Stream.
      Proses ini mungkin memakan waktu beberapa detik.
    </p>

    <!-- Aksi -->
    <div class="flex items-center gap-2 border-t border-border pt-3">
      <Button size="sm" :disabled="!berubah || menyimpan" @click="simpan">
        {{ menyimpan ? 'Menyimpan…' : 'Simpan' }}
      </Button>
      <Button v-if="berubah" variant="ghost" size="sm" :disabled="menyimpan" @click="batal">
        Batal
      </Button>
      <Button
        v-if="auth.watchlists.length > 1"
        variant="destructive"
        size="sm"
        class="ml-auto"
        :disabled="menyimpan || menghapus"
        @click="hapusDaftarPantau"
      >
        {{ menghapus ? 'Menghapus...' : 'Hapus Daftar' }}
      </Button>
    </div>

  </div>
</template>
