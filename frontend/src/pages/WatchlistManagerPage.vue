<script setup>
import { computed, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/market'
import { useNotify } from '@/composables/useNotify'
import { SUPPORTED_TICKERS } from '@/api/StockVision'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'

/**
 * Dipakai di dalam Sheet dari Stream — tidak punya route sendiri lagi.
 *
 * Pilihan dibatasi ke SUPPORTED_TICKERS: endpoint data menolak emiten lain
 * dengan HTTP 400, jadi membiarkan user menambah emiten sembarang hanya akan
 * menghasilkan panel error di Stream.
 */
const auth = useAuthStore()
const market = useMarketStore()
const notify = useNotify()

const menyimpan = ref(false)

/** Salinan lokal supaya centang terasa instan; commit ke backend saat Simpan. */
const dipilih = ref([...auth.watchlist])

const berubah = computed(() => {
  const awal = [...auth.watchlist].sort().join(',')
  const kini = [...dipilih.value].sort().join(',')
  return awal !== kini
})

function toggle(ticker, aktif) {
  dipilih.value = aktif ? [...dipilih.value, ticker] : dipilih.value.filter((t) => t !== ticker)
}

async function simpan() {
  if (!berubah.value || menyimpan.value) return

  menyimpan.value = true
  try {
    await auth.saveWatchlist(dipilih.value)

    // Ticker yang sedang aktif bisa saja baru dicabut dari watchlist.
    if (!dipilih.value.includes(market.selectedTicker)) {
      market.setTicker(dipilih.value[0] ?? auth.emitenUtama)
    }
    notify.success('Watchlist tersimpan', `${dipilih.value.length} emiten dipantau.`)
  } catch (err) {
    notify.error('Gagal menyimpan watchlist', err.message)
  } finally {
    menyimpan.value = false
  }
}

function batal() {
  dipilih.value = [...auth.watchlist]
}
</script>

<template>
  <div class="flex flex-col gap-4 p-4">
    <fieldset class="flex flex-col gap-1">
      <legend class="sr-only">Pilih emiten untuk dipantau</legend>

      <label
        v-for="ticker in SUPPORTED_TICKERS"
        :key="ticker"
        class="flex cursor-pointer items-center gap-2.5 rounded-md px-2 py-2 transition-colors hover:bg-accent"
      >
        <Checkbox
          :model-value="dipilih.includes(ticker)"
          @update:model-value="toggle(ticker, $event)"
        />
        <span class="tabular text-[13px] font-medium">{{ ticker }}</span>
        <span
          v-if="auth.emitenUtama === ticker"
          class="ml-auto text-[10px] text-[var(--color-skip)]"
        >
          Emiten utama
        </span>
      </label>
    </fieldset>

    <p class="text-[11px] leading-relaxed text-muted-foreground">
      Hanya {{ SUPPORTED_TICKERS.length }} emiten ini yang dilayani backend saat ini.
    </p>

    <div class="flex items-center gap-2">
      <Button size="sm" :disabled="!berubah || menyimpan" @click="simpan">
        {{ menyimpan ? 'Menyimpan…' : 'Simpan' }}
      </Button>
      <Button v-if="berubah" variant="ghost" size="sm" :disabled="menyimpan" @click="batal">
        Batal
      </Button>
    </div>
  </div>
</template>
