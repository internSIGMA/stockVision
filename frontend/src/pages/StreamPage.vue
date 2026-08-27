<script setup>
import { computed, ref } from 'vue'

import { useAuthStore } from '@/stores/auth'
import { useEmitenData } from '@/composables/useEmitenData'
import EmitenHeader from '@/components/layout/EmitenHeader.vue'
import TrendingStocksStrip from '@/components/shared/TrendingStocksStrip.vue'
import WatchlistPanel from '@/components/stream/WatchlistPanel.vue'
import PrescriptivePanel from '@/components/stream/PrescriptivePanel.vue'
import DiagnosticPanel from '@/components/stream/DiagnosticPanel.vue'
import AnalysisBrokerCard from '@/components/stream/AnalysisBrokerCard.vue'
import InsiderTable from '@/components/stream/InsiderTable.vue'
import ForecastCandlestickChart from '@/components/charts/ForecastCandlestickChart.vue'
import RsiChart from '@/components/charts/RsiChart.vue'
import MacdChart from '@/components/charts/MacdChart.vue'
import StatCard from '@/components/ui/StatCard.vue'
import StatusPill from '@/components/ui/StatusPill.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { Button } from '@/components/ui/button'
import { useForecastData } from '@/composables/useForecastData'
import { usePrescriptive } from '@/composables/usePrescriptive'
import { useDiagnostic } from '@/composables/useDiagnostic'
import { useTechnicalData } from '@/composables/useTechnicalData'
import { formatCompact, formatDate, formatNumber } from '@/utils/format'
import { rsiReading, macdReading } from '@/utils/technicalIndicators'

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

// Pembacaan status nilai terakhir indikator untuk pill ringkasan di header panel
const nilaiRsiTerakhir = computed(() => {
  const arr = indikatorDeret.value?.rsi
  if (!arr || !arr.length) return null
  for (let i = arr.length - 1; i >= 0; i--) {
    if (arr[i] != null) return arr[i]
  }
  return null
})

const bacaanRsi = computed(() => rsiReading(nilaiRsiTerakhir.value))

const nilaiMacdTerakhir = computed(() => {
  const m = indikatorDeret.value?.macd
  if (!m || !m.macdLine || !m.macdLine.length) return null
  for (let i = m.macdLine.length - 1; i >= 0; i--) {
    if (m.macdLine[i] != null) {
      return {
        macd: m.macdLine[i],
        signal: m.signalLine?.[i] ?? 0,
        histogram: m.histogram?.[i] ?? 0,
      }
    }
  }
  return null
})

const bacaanMacd = computed(() => macdReading(nilaiMacdTerakhir.value))

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
  { value: 'ALL', label: 'All' },
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
        <!-- 2 — Stat Cards Ringkasan Pasar -->
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

        <!-- 3 — Kotak 1: Technical & Forecasting Chart (Candlestick + Forecast + Volume) -->
        <section class="rounded-lg border-[0.5px] border-border bg-card">
          <header class="flex flex-wrap items-center gap-3 border-b-[0.5px] border-border px-3.5 py-2.5">
            <div class="min-w-0">
              <h2 class="text-[13px] font-medium">
                Technical &amp; Forecasting — <span class="tabular">{{ ticker ?? '—' }}</span>
              </h2>
              <p class="mt-0.5 text-[10px] text-muted-foreground">
                Grafik historis OHLC, volume transaksi, dan proyeksi model time-series.
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

            <!-- Horizon selector untuk proyeksi -->
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

          <div v-if="forecastLoading || loading" class="h-[440px] animate-pulse bg-muted/50" />

          <EmptyState
            v-else-if="!ohlc.length"
            title="Belum ada data grafik"
            description="Emiten ini belum memiliki histori harga."
          />

          <div v-else class="flex flex-col gap-3.5 p-3.5">
            <ForecastCandlestickChart 
              :rows="ohlc" 
              :points="titikProyeksi"
              :timeframe="selectedTimeframe"
              :height="400"
            />

            <!-- Ringkasan Statistik Proyeksi -->
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

        <!-- 4 — Kotak 2: Relative Strength Index (RSI 14) -->
        <section class="rounded-lg border-[0.5px] border-border bg-card">
          <header class="flex flex-wrap items-center justify-between gap-3 border-b-[0.5px] border-border px-3.5 py-2.5">
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <h2 class="text-[13px] font-medium">
                  Relative Strength Index (RSI 14) — <span class="tabular">{{ ticker ?? '—' }}</span>
                </h2>
                <span
                  v-if="bacaanRsi?.value != null"
                  class="rounded-full px-2 py-0.5 text-[10px] font-medium"
                  :class="
                    bacaanRsi.tone === 'down'
                      ? 'bg-[var(--color-down-bg)] text-[var(--color-down-ink)]'
                      : bacaanRsi.tone === 'up'
                        ? 'bg-[var(--color-up-bg)] text-[var(--color-up-ink)]'
                        : 'bg-muted text-muted-foreground'
                  "
                >
                  {{ bacaanRsi.label }} ({{ bacaanRsi.display }})
                </span>
              </div>
              <p class="mt-0.5 text-[10px] text-muted-foreground">
                Indikator momentum harga pada skala 0–100 dengan batas overbought (70) dan oversold (30).
              </p>
            </div>

            <div class="flex shrink-0 items-center gap-2">
              <span
                v-if="asalIndikator"
                class="rounded-full border-[0.5px] border-border px-2 py-0.5 text-[10px] text-muted-foreground"
                :title="asalIndikator.title"
              >
                {{ asalIndikator.label }}
              </span>
            </div>
          </header>

          <div class="p-3.5">
            <RsiChart
              :dates="indikatorDeret?.tanggal || []"
              :data="indikatorDeret?.rsi || []"
              :loading="indikatorLoading && !indikatorDeret"
              :timeframe="selectedTimeframe"
              :height="220"
            />
          </div>
        </section>

        <!-- 5 — Kotak 3: MACD (12, 26, 9) -->
        <section class="rounded-lg border-[0.5px] border-border bg-card">
          <header class="flex flex-wrap items-center justify-between gap-3 border-b-[0.5px] border-border px-3.5 py-2.5">
            <div class="min-w-0">
              <div class="flex items-center gap-2">
                <h2 class="text-[13px] font-medium">
                  MACD (12, 26, 9) — <span class="tabular">{{ ticker ?? '—' }}</span>
                </h2>
                <span
                  v-if="bacaanMacd?.value != null"
                  class="rounded-full px-2 py-0.5 text-[10px] font-medium"
                  :class="
                    bacaanMacd.tone === 'up'
                      ? 'bg-[var(--color-up-bg)] text-[var(--color-up-ink)]'
                      : 'bg-[var(--color-down-bg)] text-[var(--color-down-ink)]'
                  "
                >
                  {{ bacaanMacd.label }} ({{ bacaanMacd.display }})
                </span>
              </div>
              <p class="mt-0.5 text-[10px] text-muted-foreground">
                Moving Average Convergence Divergence, sinyal tren garis MACD &amp; sinyal beserta histogram momentum.
              </p>
            </div>

            <div class="flex shrink-0 items-center gap-2">
              <span
                v-if="asalIndikator"
                class="rounded-full border-[0.5px] border-border px-2 py-0.5 text-[10px] text-muted-foreground"
                :title="asalIndikator.title"
              >
                {{ asalIndikator.label }}
              </span>
            </div>
          </header>

          <div class="p-3.5">
            <MacdChart
              :dates="indikatorDeret?.tanggal || []"
              :macd-line="indikatorDeret?.macd?.macdLine || []"
              :signal-line="indikatorDeret?.macd?.signalLine || []"
              :histogram="indikatorDeret?.macd?.histogram || []"
              :loading="indikatorLoading && !indikatorDeret"
              :timeframe="selectedTimeframe"
              :height="220"
            />
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

      <!-- 7 — Analysis/Broker Summary -->
      <div class="flex flex-col gap-4">
        <AnalysisBrokerCard :ohlc="ohlc" :broker="broker" :loading="loading" />
      </div>

      <!-- 8 — Insider Activity -->
      <InsiderTable :rows="insider" :loading="loading" />
    </div>
  </div>
</template>
