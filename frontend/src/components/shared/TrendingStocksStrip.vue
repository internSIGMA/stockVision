<script setup>
import { nextTick, ref, watch } from 'vue'
import { ChevronLeft, ChevronRight } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/market'
import { useCarousel } from '@/composables/useCarousel'
import { getOhlcHistory, getStockSummary } from '@/api/StockVision'
import Sparkline from '@/components/charts/Sparkline.vue'
import { formatNumber, formatPercent, trendClass } from '@/utils/format'

const auth = useAuthStore()
const market = useMarketStore()

const LEBAR_KARTU = 240
const JARAK = 12

const { track, bisaMundur, bisaMaju, ukur, maju, mundur } = useCarousel({
  lebarKartu: LEBAR_KARTU,
  jarak: JARAK,
  langkah: 2,
})

/** { [ticker]: { harga, perubahanPersen, closes } } */
const kartu = ref({})
const loading = ref(true)

/**
 * Satu emiten yang gagal tidak boleh mengosongkan seluruh strip — emiten yang
 * belum pernah di-crawl memang menjawab 404 di /api/data/stock-info.
 */
async function muatSatu(ticker) {
  const [summary, ohlc] = await Promise.allSettled([
    getStockSummary(ticker),
    getOhlcHistory(ticker),
  ])

  const s = summary.status === 'fulfilled' ? summary.value : null
  const rows = ohlc.status === 'fulfilled' && Array.isArray(ohlc.value) ? ohlc.value : []

  return {
    harga: s?.harga ?? null,
    perubahanPersen: s?.perubahan_persen ?? null,
    closes: rows.slice(-7).map((r) => Number(r.close)),
  }
}

async function muat() {
  const tickers = auth.watchlist
  if (!tickers.length) {
    loading.value = false
    return
  }

  loading.value = true
  const hasil = await Promise.all(tickers.map(muatSatu))
  kartu.value = Object.fromEntries(tickers.map((t, i) => [t, hasil[i]]))
  loading.value = false

  // Jumlah kartu berubah -> scrollWidth berubah, tapi ukuran kontainer tidak,
  // jadi ResizeObserver di useCarousel tidak ikut terpanggil.
  await nextTick()
  ukur()
}

watch(() => auth.watchlist, muat, { immediate: true, deep: true })

defineExpose({ reload: muat })
</script>

<template>
  <section class="group relative" aria-label="Watchlist emiten">
    <!-- data-lenis-prevent: strip ini bergulir horizontal, Lenis hanya urus vertikal. -->
    <div
      ref="track"
      class="flex snap-x gap-3 overflow-x-auto scroll-smooth pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      data-lenis-prevent
    >
      <template v-if="loading">
        <div
          v-for="i in 5"
          :key="i"
          class="h-[68px] w-[240px] shrink-0 animate-pulse rounded-lg border-[0.5px] border-border bg-muted"
        />
      </template>

      <button
        v-for="ticker in auth.watchlist"
        v-else
        :key="ticker"
        type="button"
        class="flex w-[240px] shrink-0 snap-start flex-col gap-1.5 rounded-lg border bg-card p-2.5 text-left transition-colors"
        :class="
          market.selectedTicker === ticker
            ? 'border-[var(--color-info)] bg-[var(--color-info-bg)]'
            : 'border-border border-[0.5px] hover:bg-accent'
        "
        :aria-pressed="market.selectedTicker === ticker"
        @click="market.setTicker(ticker)"
      >
        <div class="flex items-center justify-between">
          <span class="text-[12px] font-semibold">{{ ticker }}</span>
          <Sparkline :values="kartu[ticker]?.closes || []" />
        </div>

        <div class="flex items-baseline justify-between gap-2">
          <span class="tabular text-[14px] font-medium">
            {{ formatNumber(kartu[ticker]?.harga) }}
          </span>
          <span
            class="tabular text-[11px] font-medium"
            :class="trendClass(kartu[ticker]?.perubahanPersen)"
          >
            {{ formatPercent(kartu[ticker]?.perubahanPersen) }}
          </span>
        </div>
      </button>
    </div>

    <!-- Gradien tepi memberi tanda masih ada kartu di balik batas kontainer. -->
    <Transition name="fade">
      <div
        v-if="bisaMundur"
        class="pointer-events-none absolute inset-y-0 left-0 w-20 bg-gradient-to-r from-background to-transparent"
        aria-hidden="true"
      />
    </Transition>
    <Transition name="fade">
      <div
        v-if="bisaMaju"
        class="pointer-events-none absolute inset-y-0 right-0 w-20 bg-gradient-to-l from-background to-transparent"
        aria-hidden="true"
      />
    </Transition>

    <Transition name="fade">
      <button
        v-if="bisaMundur"
        type="button"
        class="absolute left-1 top-1/2 flex size-8 -translate-y-1/2 items-center justify-center rounded-full border-[0.5px] border-border bg-card text-muted-foreground shadow-md transition duration-150 hover:scale-105 hover:bg-accent hover:text-foreground active:scale-95"
        aria-label="Geser ke kartu sebelumnya"
        @click="mundur"
      >
        <ChevronLeft class="size-4" />
      </button>
    </Transition>

    <Transition name="fade">
      <button
        v-if="bisaMaju"
        type="button"
        class="absolute right-1 top-1/2 flex size-8 -translate-y-1/2 items-center justify-center rounded-full border-[0.5px] border-border bg-card text-muted-foreground shadow-md transition duration-150 hover:scale-105 hover:bg-accent hover:text-foreground active:scale-95"
        aria-label="Geser ke kartu berikutnya"
        @click="maju"
      >
        <ChevronRight class="size-4" />
      </button>
    </Transition>
  </section>
</template>
