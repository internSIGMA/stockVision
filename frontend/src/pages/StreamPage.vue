<script setup>
import { computed, ref } from 'vue'
import { useEmitenData } from '@/composables/useEmitenData'
import EmitenHeader from '@/components/layout/EmitenHeader.vue'
import TrendingStocksStrip from '@/components/shared/TrendingStocksStrip.vue'
import WatchlistPanel from '@/components/stream/WatchlistPanel.vue'
import TechnicalSummary from '@/components/stream/TechnicalSummary.vue'
import AnalysisBrokerCard from '@/components/stream/AnalysisBrokerCard.vue'
import InsiderTable from '@/components/stream/InsiderTable.vue'
import CandlestickChart from '@/components/charts/CandlestickChart.vue'
import ForeignFlowChart from '@/components/charts/ForeignFlowChart.vue'
import ForecastChart from '@/components/charts/ForecastChart.vue'
import StatCard from '@/components/ui/StatCard.vue'
import StatusPill from '@/components/ui/StatusPill.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { Button } from '@/components/ui/button'
import { useForecastData } from '@/composables/useForecastData'
import { formatCompact, formatDate, formatNumber } from '@/utils/format'

/**
 * Satu halaman scroll panjang: semua section berbagi ticker aktif yang sama
 * (market.selectedTicker), jadi cukup satu kali fetch untuk seluruh Stream.
 */
const { ticker, summary, ohlc, insider, broker, loading, error, reload } = useEmitenData({
  summary: true,
  ohlc: true,
  insider: true,
  broker: true,
})

const strip = ref(null)
const candle = ref(null)

function segarkan() {
  reload()
  strip.value?.reload()
}

const statusPasar = computed(() => summary.value?.status_pasar || null)

/** Volume dari snapshot; jatuh ke baris OHLC terakhir bila snapshot belum ada. */
const volume = computed(
  () => summary.value?.volume ?? (ohlc.value.length ? ohlc.value[ohlc.value.length - 1].volume : null),
)

// Forecasting berdiri di composable sendiri: gagalnya endpoint proyeksi tidak
// boleh menjatuhkan chart & tabel yang lain.
const {
  horizon,
  horizonTersedia,
  points: titikProyeksi,
  hasData: adaProyeksi,
  hasBand,
  terakhir: proyeksiAkhir,
  rentang: rentangProyeksi,
  volumeRata: volumeProyeksi,
  perubahanPersen: proyeksiPersen,
  trend: trenProyeksi,
  isLoading: forecastLoading,
  error: forecastError,
  setHorizon,
} = useForecastData({ ohlc })

const TREN_CLASS = {
  NAIK: 'text-up',
  TURUN: 'text-down',
}

const trenClass = computed(() => TREN_CLASS[trenProyeksi.value] ?? 'text-muted-foreground')
</script>

<template>
  <div class="flex flex-col">
    <EmitenHeader @crawled="segarkan" />

    <div class="flex flex-col gap-4 p-4">
      <!-- 1 — Trending -->
      <TrendingStocksStrip ref="strip" />

      <!-- Snapshot harga bisa 404 kalau emiten belum pernah di-crawl; chart & tabel tetap jalan. -->
      <p
        v-if="error && !loading"
        class="rounded-lg border-[0.5px] border-[var(--color-down)]/30 bg-[var(--color-down-bg)] px-3.5 py-2 text-[11px] text-[var(--color-down-ink)]"
        role="status"
      >
        {{ error }}
      </p>

      <!-- 2 — Watchlist di kiri; statistik dan candlestick berbagi kolom kanan -->
      <div class="grid grid-cols-1 gap-4 lg:grid-cols-[260px_1fr]">
        <WatchlistPanel />

        <div class="flex min-w-0 flex-col gap-4">
          <div class="grid grid-cols-2 gap-3 xl:grid-cols-4">
            <StatCard
              label="Last Price"
              :value="formatNumber(summary?.harga)"
              :change="summary?.perubahan_persen ?? null"
              :sub="summary?.perubahan != null ? `${summary.perubahan > 0 ? '+' : ''}${formatNumber(summary.perubahan)}` : null"
              :loading="loading"
            />
            <StatCard
              label="Best Bid"
              :value="formatNumber(summary?.bid_price)"
              :sub="summary?.bid_volume != null ? `${formatCompact(summary.bid_volume)} lot` : null"
              :loading="loading"
            />
            <StatCard
              label="Best Offer"
              :value="formatNumber(summary?.offer_price)"
              :sub="summary?.offer_volume != null ? `${formatCompact(summary.offer_volume)} lot` : null"
              :loading="loading"
            />
            <StatCard
              label="Volume"
              :value="formatCompact(volume)"
              :sub="summary?.rata_rata != null ? `Avg ${formatNumber(summary.rata_rata)}` : null"
              :loading="loading"
            >
              <template #badge>
                <StatusPill v-if="statusPasar" :label="statusPasar" />
              </template>
            </StatCard>
          </div>

          <!-- 3 — Candlestick -->
          <section class="rounded-lg border-[0.5px] border-border bg-card">
            <header class="flex items-center gap-3 border-b-[0.5px] border-border px-3.5 py-2.5">
              <div class="min-w-0">
                <h2 class="text-[13px] font-medium">
                  Historical Candlestick — <span class="tabular">{{ ticker ?? '—' }}</span>
                </h2>
                <p class="mt-0.5 text-[10px] text-muted-foreground">
                  Data OHLC tersimpan di database lokal, diperbarui lewat crawler.
                </p>
              </div>

              <div class="ml-auto flex shrink-0 items-center gap-2">
                <span
                  v-if="ohlc.length"
                  class="tabular rounded-full border-[0.5px] border-border px-2 py-0.5 text-[10px] text-muted-foreground"
                >
                  {{ ohlc.length }} trading days
                </span>
                <Button
                  v-if="ohlc.length"
                  variant="ghost"
                  size="sm"
                  class="h-6 px-2 text-[10px]"
                  @click="candle?.resetZoom()"
                >
                  Reset zoom
                </Button>
              </div>
            </header>

            <div v-if="loading" class="h-[340px] animate-pulse bg-muted/50" />

            <EmptyState
              v-else-if="!ohlc.length"
              title="Belum ada data candlestick"
              description="Emiten ini belum pernah di-crawl. Jalankan Trigger Crawler di atas untuk mengambil histori harganya."
            />

            <div v-else class="p-2">
              <CandlestickChart ref="candle" :rows="ohlc" />
            </div>
          </section>
        </div>
      </div>

      <!-- 4 — Forecasting -->
      <section class="rounded-lg border-[0.5px] border-border bg-card">
        <header class="flex flex-wrap items-center gap-3 border-b-[0.5px] border-border px-3.5 py-2.5">
          <div class="min-w-0">
            <h2 class="text-[13px] font-medium">
              Forecasting — <span class="tabular">{{ ticker ?? '—' }}</span>
            </h2>
            <p class="mt-0.5 text-[10px] text-muted-foreground">
              Proyeksi harga berdasarkan model time-series.
            </p>
          </div>

          <!-- Hanya horizon yang datanya benar-benar dikirim backend yang muncul. -->
          <div v-if="horizonTersedia.length > 1" class="ml-auto flex shrink-0 items-center gap-1">
            <Button
              v-for="h in horizonTersedia"
              :key="h"
              variant="ghost"
              size="sm"
              class="tabular h-6 px-2 text-[10px]"
              :class="h === horizon ? 'bg-muted font-medium text-foreground' : 'text-muted-foreground'"
              :aria-pressed="h === horizon"
              @click="setHorizon(h)"
            >
              {{ h }} Hari
            </Button>
          </div>

          <span
            v-else-if="adaProyeksi"
            class="tabular ml-auto shrink-0 rounded-full border-[0.5px] border-border px-2 py-0.5 text-[10px] text-muted-foreground"
          >
            {{ horizon }} hari ke depan
          </span>
        </header>

        <div v-if="forecastLoading || loading" class="h-[320px] animate-pulse bg-muted/50" />

        <EmptyState
          v-else-if="forecastError || !adaProyeksi"
          title="Data forecasting belum tersedia untuk emiten ini"
          :description="forecastError || 'Proyeksi muncul setelah emiten ini punya histori harga yang cukup.'"
        />

        <div v-else class="flex flex-col gap-3.5 p-3.5">
          <ForecastChart :rows="ohlc" :points="titikProyeksi" :show-band="hasBand" />

          <!-- Keempat angka ini seluruhnya kolom dari /api/data/forecast:
               close, low, high, dan volume. Backend tidak mengirim skor
               confidence atau nama model, jadi tidak ada kartu untuk itu. -->
          <div class="grid grid-cols-2 gap-3 xl:grid-cols-4">
            <StatCard
              label="Proyeksi Harga Penutupan"
              :value="formatNumber(proyeksiAkhir?.prediksi)"
              :sub="proyeksiAkhir ? formatDate(proyeksiAkhir.tanggal) : null"
            />
            <StatCard
              label="Arah Tren"
              :value="trenProyeksi ?? '—'"
              :change="proyeksiPersen"
              :value-class="trenClass"
            />
            <StatCard
              label="Rentang Proyeksi"
              :value="
                rentangProyeksi
                  ? `${formatNumber(rentangProyeksi.bawah)}–${formatNumber(rentangProyeksi.atas)}`
                  : '—'
              "
              :sub="rentangProyeksi ? `Terendah–tertinggi ${horizon} hari` : null"
            />
            <StatCard
              label="Volume Proyeksi"
              :value="formatCompact(volumeProyeksi)"
              :sub="volumeProyeksi != null ? `Rata-rata ${horizon} hari` : null"
            />
          </div>

          <p class="text-[11px] italic leading-relaxed text-muted-foreground">
            Proyeksi ini bersifat estimatif berdasarkan data historis dan bukan merupakan
            rekomendasi investasi.
          </p>
        </div>
      </section>

      <!-- 5 — Foreign flow -->
      <section class="rounded-lg border-[0.5px] border-border bg-card">
        <header class="border-b-[0.5px] border-border px-3.5 py-2.5">
          <h2 class="text-[13px] font-medium">Foreign Flow Activity (IDR)</h2>
          <p class="mt-0.5 text-[10px] text-muted-foreground">
            Selisih beli dan jual asing per hari, dalam miliar rupiah.
          </p>
        </header>

        <div v-if="loading" class="h-[300px] animate-pulse bg-muted/50" />

        <EmptyState
          v-else-if="!ohlc.length"
          title="Belum ada data foreign flow"
          description="Foreign flow ikut terambil bersama histori OHLC."
        />

        <div v-else class="p-3.5">
          <ForeignFlowChart :rows="ohlc" />
        </div>
      </section>

      <!-- 6 — Technical + Analysis/Broker -->
      <div class="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <TechnicalSummary :rows="ohlc" :loading="loading" />
        <AnalysisBrokerCard :ohlc="ohlc" :broker="broker" :loading="loading" />
      </div>

      <!-- 7 — Insider -->
      <InsiderTable :rows="insider" :loading="loading" />
    </div>
  </div>
</template>
