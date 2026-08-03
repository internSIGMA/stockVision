<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/market'
import { useNotify } from '@/composables/useNotify'
import { getWatchlistQuota, isSupported } from '@/api/StockVision'
import { Button } from '@/components/ui/button'

/**
 * WatchlistManagerPage
 * - Input bebas untuk semua emiten IDX
 * - Kuota maks 10 emiten unik per akun (cek di backend & front-end)
 * - Menyimpan perubahan secara batch (Save)
 */
const auth   = useAuthStore()
const market = useMarketStore()
const notify = useNotify()

// ──────────────────────────────────────────────
// State
// ──────────────────────────────────────────────
const menyimpan    = ref(false)
const inputTicker  = ref('')
const inputError   = ref('')
const quota        = ref({ used_quota: 0, max_quota: 10, remaining_quota: 10, unique_symbols: [] })
const loadingQuota = ref(false)

/** Salinan lokal supaya bisa di-cancel */
const dipilih = ref([...auth.watchlist])

// ──────────────────────────────────────────────
// Computed
// ──────────────────────────────────────────────
const berubah = computed(() => {
  const awal = [...auth.watchlist].sort().join(',')
  const kini = [...dipilih.value].sort().join(',')
  return awal !== kini
})

const uniqueCount   = computed(() => new Set(dipilih.value.map(s => s.toUpperCase())).size)
const remainingSlot = computed(() => Math.max(0, 10 - uniqueCount.value))

// Warna progress bar kuota
const quotaBarColor = computed(() => {
  if (uniqueCount.value >= 10)  return 'bg-destructive'
  if (uniqueCount.value >= 8)   return 'bg-yellow-500'
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
function tambah() {
  const t = inputTicker.value.trim().toUpperCase()
  inputError.value = ''

  if (!t) return

  if (!isSupported(t)) {
    inputError.value = `"${t}" bukan format kode emiten IDX yang valid (contoh: BBCA, TLKM, GOTO).`
    return
  }

  if (dipilih.value.map(s => s.toUpperCase()).includes(t)) {
    inputError.value = `${t} sudah ada di watchlist.`
    return
  }

  const currentUnique = new Set(dipilih.value.map(s => s.toUpperCase()))
  if (currentUnique.size >= 10) {
    inputError.value = `Batas kuota emiten tercapai! Akun ini hanya dapat memiliki maksimal 10 emiten unik. Hapus salah satu emiten untuk menambah yang baru.`
    return
  }

  dipilih.value = [...dipilih.value, t]
  inputTicker.value = ''
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
  menyimpan.value = true
  try {
    await auth.saveWatchlist(dipilih.value)
    if (!dipilih.value.includes(market.selectedTicker)) {
      market.setTicker(dipilih.value[0] ?? auth.emitenUtama)
    }
    notify.success('Watchlist tersimpan', `${dipilih.value.length} emiten dipantau.`)
    await muatKuota()
  } catch (err) {
    const msg = err?.response?.data?.error || err.message || 'Gagal menyimpan watchlist'
    notify.error('Gagal menyimpan watchlist', msg)
  } finally {
    menyimpan.value = false
  }
}

function batal() {
  dipilih.value   = [...auth.watchlist]
  inputTicker.value = ''
  inputError.value  = ''
}

function onKeydown(e) {
  if (e.key === 'Enter') tambah()
}
</script>

<template>
  <div class="flex flex-col gap-4 p-4">

    <!-- Quota bar -->
    <div class="rounded-lg border border-border bg-card p-3">
      <div class="mb-1.5 flex items-center justify-between">
        <span class="text-[11px] font-medium text-muted-foreground">Kuota Emiten</span>
        <span
          class="tabular text-[11px] font-semibold"
          :class="uniqueCount >= 10 ? 'text-destructive' : 'text-foreground'"
        >
          {{ uniqueCount }} / 10
        </span>
      </div>
      <div class="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          class="h-full rounded-full transition-all duration-300"
          :class="quotaBarColor"
          :style="{ width: `${(uniqueCount / 10) * 100}%` }"
        />
      </div>
      <p class="mt-1 text-[10px] text-muted-foreground">
        {{ remainingSlot > 0 ? `Sisa ${remainingSlot} slot` : 'Kuota penuh — hapus emiten lama untuk menambah yang baru.' }}
      </p>
    </div>

    <!-- Input tambah emiten -->
    <div class="flex flex-col gap-1.5">
      <label class="text-[11px] font-medium text-muted-foreground">
        Tambah Emiten IDX (contoh: TLKM, ASII, GOTO)
      </label>
      <div class="flex gap-2">
        <input
          v-model="inputTicker"
          type="text"
          maxlength="6"
          placeholder="Kode emiten..."
          class="flex-1 rounded-md border border-input bg-background px-3 py-1.5 font-mono text-[13px] uppercase shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
          :disabled="uniqueCount >= 10"
          @keydown="onKeydown"
          @input="inputError = ''"
        />
        <Button
          size="sm"
          :disabled="!inputTicker.trim() || uniqueCount >= 10"
          @click="tambah"
        >
          + Tambah
        </Button>
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
    </div>

  </div>
</template>
