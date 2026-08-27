<script setup>
import { computed, nextTick, ref, watch } from 'vue'

import { useAuthStore } from '@/stores/auth'
import { useEmitenData } from '@/composables/useEmitenData'
import EmitenHeader from '@/components/layout/EmitenHeader.vue'
import TrendingStocksStrip from '@/components/shared/TrendingStocksStrip.vue'
import WatchlistPanel from '@/components/stream/WatchlistPanel.vue'
import PrescriptivePanel from '@/components/stream/PrescriptivePanel.vue'
import DiagnosticPanel from '@/components/stream/DiagnosticPanel.vue'
import AnalysisBrokerCard from '@/components/stream/AnalysisBrokerCard.vue'
import InsiderTable from '@/components/stream/InsiderTable.vue'
import CombinedChart from '@/components/charts/CombinedChart.vue'
import StatCard from '@/components/ui/StatCard.vue'
import StatusPill from '@/components/ui/StatusPill.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { Button } from '@/components/ui/button'
import { useForecastData } from '@/composables/useForecastData'
import { usePrescriptive } from '@/composables/usePrescriptive'
import { useDiagnostic } from '@/composables/useDiagnostic'
import { useTechnicalData } from '@/composables/useTechnicalData'
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

const authStore = useAuthStore()

const strip = ref(null)

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
  terakhir: proyeksiAkhir,
  rentang: rentangProyeksi,
  volumeRata: volumeProyeksi,
  perubahanPersen: proyeksiPersen,
  trend: trenProyeksi,
  isLoading: forecastLoading,
  error: forecastError,
  setHorizon,
} = useForecastData({ ohlc })

// RSI & MACD dari /api/data/technical (tabel yang diisi crawler yfinance),
// dengan `ohlc` sebagai jalur cadangan kalau emitennya belum pernah di-crawl.
const {
  deret: indikatorDeret,
  sumber: indikatorSumber,
  loading: indikatorLoading,
} = useTechnicalData(ohlc)

/** Keterangan asal angka — supaya user tahu kapan yang tampil hasil hitung lokal. */
const ASAL = {
  yfinance: { label: 'Sumber: yfinance', title: 'Angka diambil dari tabel indikator hasil crawler yfinance.' },
  lokal: {
    label: 'Dihitung lokal',
    title: 'Tabel indikator belum terisi untuk emiten ini, jadi RSI & MACD dihitung di browser dari histori harga yfinance.',
  },
}
const asalIndikator = computed(() => ASAL[indikatorSumber.value] ?? null)

// Prescriptive juga berdiri sendiri: emiten yang belum pernah dianalisis
// pipeline wajar kosong, dan itu tidak boleh menjatuhkan bagian lain.
const {
  data: prescriptive,
  tradingLevels,
  isLoading: prescriptiveLoading,
  reload: muatUlangPrescriptive,
} = usePrescriptive()

// Diagnostik menjawab "kenapa harganya begini" dan dimuat terpisah dari
// prescriptive: tabelnya diisi pipeline lain, jadi salah satunya bisa kosong
// tanpa mengosongkan yang lain.
const {
  data: diagnostic,
  temuan: temuanDiagnostik,
  isLoading: diagnosticLoading,
} = useDiagnostic()

const TREN_CLASS = {
  NAIK: 'text-up',
  TURUN: 'text-down',
}

const trenClass = computed(() => TREN_CLASS[trenProyeksi.value] ?? 'text-muted-foreground')

const TIMEFRAMES = [
  { value: '1D', label: '1D' },
  { value: '5D', label: '5D' },
  { value: '1M', label: '1M' },
  { value: '3M', label: '3M' },
  { value: '6M', label: '6M' },
  { value: 'YTD', label: 'YTD' },
  { value: '1Y', label: '1Y' },
  { value: 'ALL', label: 'All' }
]
const selectedTimeframe = ref('6M')
</script>

<template>
  <div class="flex flex-col">
    <EmitenHeader @crawled="segarkan" />

    <div class="flex flex-col gap-4 p-4">
      <!-- Snapshot harga bisa 404 kalau emiten belum pernah di-crawl; chart & tabel tetap jalan. -->
      <p
        v-if="error && !loading"
        class="rounded-lg border-[0.5px] border-[var(--color-down)]/30 bg-[var(--color-down-bg)] px-3.5 py-2 text-[11px] text-[var(--color-down-ink)]"
        role="status"
      >
        {{ error }}
      </p>

      <!-- 1 — Trending / Watchlist -->
      <TrendingStocksStrip v-if="authStore.isAdmin" ref="strip" class="mb-4" />
      
      <div v-else class="mb-4">
        <WatchlistPanel ref="strip" />
      </div>

      <div class="flex flex-col gap-4">
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

          <!-- 3 — Advanced Combined Chart -->
          <section class="rounded-lg border-[0.5px] border-border bg-card">
            <header class="flex flex-wrap items-center gap-3 border-b-[0.5px] border-border px-3.5 py-2.5">
              <div class="min-w-0">
                <h2 class="text-[13px] font-medium">
                  Technical & Forecasting — <span class="tabular">{{ ticker ?? '—' }}</span>
                </h2>
                <p class="mt-0.5 text-[10px] text-muted-foreground">
                  Grafik historis, proyeksi, RSI, dan MACD terintegrasi.
                </p>
              </div>

              <div class="ml-auto flex shrink-0 items-center gap-1.5" :class="{ 'border-r-[0.5px] border-border pr-3 mr-3': horizonTersedia.length > 1 }">
                <Button
                  v-for="tf in TIMEFRAMES"
                  :key="tf.value"
                  variant="ghost"
                  size="sm"
                  class="tabular h-8 px-3 text-[13px] transition-colors"
                  :class="tf.value === selectedTimeframe ? 'bg-primary/15 font-bold text-primary' : 'font-semibold text-muted-foreground hover:bg-primary/10 hover:text-primary'"
                  :aria-pressed="tf.value === selectedTimeframe"
                  @click="selectedTimeframe = tf.value"
                >
                  {{ tf.label }}
                </Button>
              </div>

              <!-- Hanya horizon yang datanya benar-benar dikirim backend yang muncul. -->
              <div v-if="horizonTersedia.length > 1" class="flex shrink-0 items-center gap-1">
                <Button
                  v-for="h in horizonTersedia"
                  :key="h"
                  variant="ghost"
                  size="sm"
                  class="tabular h-7 px-2.5 text-xs"
                  :class="h === horizon ? 'bg-muted font-medium text-foreground' : 'text-muted-foreground hover:text-foreground'"
                  :aria-pressed="h === horizon"
                  @click="setHorizon(h)"
                >
                  {{ h }} Hari
                </Button>
              </div>
            </header>

            <div v-if="forecastLoading || loading" class="h-[600px] animate-pulse bg-muted/50" />

            <EmptyState
              v-else-if="!ohlc.length"
              title="Belum ada data grafik"
              description="Emiten ini belum memiliki histori harga."
            />

            <div v-else class="flex flex-col gap-3.5 p-3.5">
              <CombinedChart 
                :rows="ohlc" 
                :points="titikProyeksi"
                :rsi="{ dates: indikatorDeret?.tanggal || [], rsi: indikatorDeret?.rsi || [] }"
                :macd="{ dates: indikatorDeret?.tanggal || [], macdLine: indikatorDeret?.macd?.macdLine || [], signalLine: indikatorDeret?.macd?.signalLine || [], histogram: indikatorDeret?.macd?.histogram || [] }"
                :timeframe="selectedTimeframe"
              />

              <!-- Keempat angka ini seluruhnya kolom dari /api/data/forecast -->
              <div v-if="adaProyeksi" class="grid grid-cols-2 gap-3 xl:grid-cols-4 mt-2 border-t-[0.5px] border-border pt-4">
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

              <p v-if="adaProyeksi" class="text-[11px] italic leading-relaxed text-muted-foreground">
                Proyeksi ini bersifat estimatif berdasarkan data historis dan bukan merupakan
                rekomendasi investasi.
              </p>
            </div>
          </section>
        </div>

      <!-- 6 — Prescriptive, berdampingan dengan Diagnostic -->
      <PrescriptivePanel
        :rows="ohlc"
        :forecast="titikProyeksi"
        :loading="loading"
        :forecast-loading="forecastLoading"
        :backend="prescriptive"
        :backend-loading="prescriptiveLoading"
        :levels="tradingLevels"
        @recompute="muatUlangPrescriptive"
      >
        <template #samping>
          <DiagnosticPanel
            :backend="diagnostic"
            :backend-loading="diagnosticLoading"
            :temuan="temuanDiagnostik"
          />
        </template>
      </PrescriptivePanel>

      <!-- 7 — Analysis/Broker -->
      <div class="flex flex-col gap-4">
        <AnalysisBrokerCard :ohlc="ohlc" :broker="broker" :loading="loading" />
      </div>

      <!-- 7 — Insider -->
      <InsiderTable :rows="insider" :loading="loading" />
    </div>
  </div>
</template>
