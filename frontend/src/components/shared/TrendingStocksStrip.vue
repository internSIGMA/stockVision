<script setup>
import { ref, watch } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useMarketStore } from '@/stores/market'
import { getOhlcHistory, getStockSummary } from '@/api/StockVision'
import Sparkline from '@/components/charts/Sparkline.vue'
import { formatNumber, formatPercent, trendClass } from '@/utils/format'

const auth = useAuthStore()
const market = useMarketStore()

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
}

watch(() => auth.watchlist, muat, { immediate: true, deep: true })

defineExpose({ reload: muat })
</script>

<template>
  <section aria-label="Trending stocks">
    <!-- data-lenis-prevent: strip ini bergulir horizontal, Lenis hanya urus vertikal. -->
    <div
      class="flex gap-2 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
      data-lenis-prevent
    >
      <template v-if="loading">
        <div
          v-for="i in 5"
          :key="i"
          class="h-[68px] w-[168px] shrink-0 animate-pulse rounded-lg border-[0.5px] border-border bg-muted"
        />
      </template>

      <button
        v-for="ticker in auth.watchlist"
        v-else
        :key="ticker"
        type="button"
        class="flex w-[168px] shrink-0 flex-col gap-1.5 rounded-lg border bg-card p-2.5 text-left transition-colors"
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
  </section>
</template>
