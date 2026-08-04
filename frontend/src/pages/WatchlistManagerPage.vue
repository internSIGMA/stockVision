<script setup>
import { computed, onMounted, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/market'
import { useNotify } from '@/composables/useNotify'
import { isSupported } from '@/api/StockVision'
import { Button } from '@/components/ui/button'
import { Check, Plus } from '@lucide/vue'

/**
 * WatchlistManagerPage
 * - Edit nama daftar pantau
 * - Input bebas untuk semua emiten IDX

 */
const emit = defineEmits(['close'])

const auth   = useAuthStore()
const market = useMarketStore()
const notify = useNotify()

// ──────────────────────────────────────────────
// State
// ──────────────────────────────────────────────
const menyimpan    = ref(false)
const inputTicker  = ref('')
const inputError   = ref('')
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



// ──────────────────────────────────────────────
// Add ticker
// ──────────────────────────────────────────────
function toggleTicker(ticker) {
  const t = ticker.trim().toUpperCase()
  inputError.value = ''

  if (!t) return

  if (!isSupported(t)) {
    inputError.value = `"${t}" bukan format kode emiten IDX yang valid (contoh: BBCA, TLKM, GOTO).`
    return
  }

  const isSelected = dipilih.value.map(s => s.toUpperCase()).includes(t)
  if (isSelected) {
    return // Jangan hapus jika sudah ada di watchlist (sesuai permintaan user)
  } else {
    dipilih.value = [...dipilih.value, t]
  }
  // Biarkan inputTicker tetap ada agar user melihat status berubah jadi hijau/biru
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
    emit('close') // Tutup sidebar setelah berhasil simpan
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
  inputTicker.value = ''
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

function onKeydown(e) {
  if (e.key === 'Enter') {
    e.preventDefault()
    if (inputTicker.value.trim()) {
      toggleTicker(inputTicker.value)
    }
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

    <!-- Pencarian & Tambah Emiten -->
    <div class="flex flex-col gap-1.5">
      <label class="text-[11px] font-medium text-muted-foreground">
        Cari & Tambah Emiten IDX (contoh: TLKM, GOTO)
      </label>
      <div class="flex flex-col gap-2">
        <input
          v-model="inputTicker"
          type="text"
          maxlength="6"
          placeholder="Ketik kode emiten..."
          class="rounded-md border border-input bg-background px-3 py-1.5 font-mono text-[13px] uppercase shadow-sm focus:outline-none focus:ring-1 focus:ring-ring"
          @keydown="onKeydown"
          @input="inputError = ''"
        />

        <!-- Hasil Pencarian Live -->
        <div v-if="inputTicker.trim().length > 0" class="rounded-md border border-border bg-card p-1.5 shadow-sm">
          <div v-if="!isSupported(inputTicker.trim().toUpperCase())" class="text-[11px] font-medium text-destructive px-2 py-1">
            Kode emiten "{{ inputTicker.toUpperCase() }}" tidak ditemukan atau belum didukung.
          </div>
          <button
            v-else
            type="button"
            class="flex w-full items-center justify-between rounded-md px-3 py-2 text-[13px] font-bold font-mono transition-all"
            :class="[
              dipilih.map(s => s.toUpperCase()).includes(inputTicker.trim().toUpperCase())
                ? 'bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20'
                : 'bg-muted text-foreground border border-transparent hover:bg-accent hover:text-accent-foreground'
            ]"
            @click="toggleTicker(inputTicker.trim().toUpperCase())"
          >
            <span>{{ inputTicker.trim().toUpperCase() }}</span>
            
            <span v-if="dipilih.map(s => s.toUpperCase()).includes(inputTicker.trim().toUpperCase())" class="flex items-center gap-1.5 text-[11px] font-semibold tracking-wide">
              <Check class="size-3.5" /> DI WATCHLIST
            </span>
            <span v-else class="flex items-center gap-1 text-[11px] font-medium text-muted-foreground">
              <Plus class="size-3.5" /> Tambah
            </span>
          </button>
        </div>
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
