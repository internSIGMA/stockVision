<script setup>
import { computed, ref } from 'vue'
import {
  Info,
  Minus,
  RefreshCw,
  Share2,
  Sparkles,
  TrendingDown,
  TrendingUp,
  UserPlus,
  Wallet,
} from '@lucide/vue'
import { buildRecommendation, parseRingkasan, SARAN } from '@/utils/prescriptive'
import { summarizeIndicators } from '@/utils/technicalIndicators'
import { formatDate, formatNumber } from '@/utils/format'
import { useNotify } from '@/composables/useNotify'
import StatusPill from '@/components/ui/StatusPill.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const props = defineProps({
  /** Baris OHLC dari useEmitenData — sumber semua kalkulasi di panel ini. */
  rows: { type: Array, default: () => [] },
  /** Titik proyeksi ternormalisasi dari useForecastData. */
  forecast: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  forecastLoading: { type: Boolean, default: false },
  /** Hasil prescriptive backend — level trading, strategi, ringkasan LLM. */
  backend: { type: Object, default: null },
  backendLoading: { type: Boolean, default: false },
  /** Level entry/target/stop loss yang sudah dinormalkan usePrescriptive. */
  levels: { type: Object, default: null },
})

const emit = defineEmits(['recompute'])

const notify = useNotify()

const hasil = computed(() => buildRecommendation(props.rows))
const indikator = computed(() => summarizeIndicators(props.rows))
const ringkasan = computed(() => parseRingkasan(props.backend?.llm_summary))

const IKON = { BELI: TrendingUp, JUAL: TrendingDown, TAHAN: Minus }
const NADA = { BELI: 'up', JUAL: 'down', TAHAN: 'neutral' }

const ikonAksi = computed(() => IKON[hasil.value?.aksi] ?? Minus)
const nadaAksi = computed(() => NADA[hasil.value?.aksi] ?? 'neutral')

const KELAS_KARTU = {
  up: 'border-[var(--up)]/40 bg-[var(--up-bg)]',
  down: 'border-[var(--down)]/40 bg-[var(--down-bg)]',
  neutral: 'border-border bg-[var(--background-secondary)]',
}
const KELAS_TEKS = {
  up: 'text-[var(--color-up-ink)]',
  down: 'text-[var(--color-down-ink)]',
  neutral: 'text-foreground',
}

/** Chip ringkas: hanya sinyal yang datanya benar-benar ada. */
const chip = computed(() => {
  const h = hasil.value
  if (!h) return []
  const out = []

  if (h.rsi !== null) {
    out.push({
      teks: `RSI ${h.rsi.toFixed(1)}`,
      naik: h.rsi < 50,
    })
  }
  if (h.macd) {
    out.push({
      teks: `MACD ${h.macd.histogram > 0 ? '+' : ''}${h.macd.histogram.toFixed(2)}`,
      naik: h.macd.histogram > 0,
    })
  }
  // Kolom asing banyak yang kosong — chip-nya dilewati daripada menampilkan
  // "Net Sell" palsu untuk emiten yang datanya memang belum ada.
  if (h.foreignFlow !== null) {
    out.push({
      teks: `Asing ${h.foreignFlow > 0 ? 'net beli' : 'net jual'}`,
      naik: h.foreignFlow > 0,
    })
  }
  return out
})

/** Penilaian rasio risiko-imbalan; di bawah 1 artinya rugi > untung. */
const mutuRR = computed(() => {
  const rr = props.levels?.riskReward
  if (!Number.isFinite(rr)) return null
  if (rr >= 2) return { teks: 'rasio baik', tone: 'up' }
  if (rr >= 1) return { teks: 'rasio cukup', tone: 'skip' }
  return { teks: 'imbalan lebih kecil dari risikonya', tone: 'down' }
})

function persen(nilai) {
  if (!Number.isFinite(nilai)) return null
  return `${nilai > 0 ? '+' : ''}${nilai.toFixed(1)}%`
}

/** Lebar bar proyeksi, dinormalkan ke rentang prediksi yang tampil. */
function lebarBar(nilai) {
  const angka = props.forecast.map((p) => p.prediksi).filter(Number.isFinite)
  if (angka.length < 2) return 60
  const min = Math.min(...angka)
  const max = Math.max(...angka)
  if (max === min) return 60
  return Math.round(((nilai - min) / (max - min)) * 70 + 25)
}

/** "24 Jul 2026" dipecah dua baris supaya kolom tanggalnya tetap sempit. */
function tanggalDuaBaris(nilai) {
  const teks = formatDate(nilai)
  const pisah = teks.lastIndexOf(' ')
  if (pisah === -1) return { hari: teks, tahun: '' }
  return { hari: teks.slice(0, pisah), tahun: teks.slice(pisah + 1) }
}

const menyalin = ref(false)

/**
 * Membagikan ringkasan sebagai teks, bukan tautan: hasil analisis terikat pada
 * tanggal pipeline, jadi yang berguna dibagikan adalah isinya saat ini.
 */
async function bagikan() {
  const b = props.backend
  if (!b?.llm_summary) {
    notify.info('Belum ada ringkasan untuk dibagikan.')
    return
  }

  const baris = [
    `Analisis Preskriptif ${b.symbol ?? ''} — ${b.company_name ?? ''}`.trim(),
    `Rekomendasi: ${b.recommendation ?? '—'}`,
    props.levels
      ? `Entry ${formatNumber(props.levels.entry)} · Target ${formatNumber(props.levels.target)} · Stop loss ${formatNumber(props.levels.stopLoss)}`
      : null,
    '',
    b.llm_summary.replace(/\*/g, ''),
  ].filter((v) => v !== null)

  try {
    menyalin.value = true
    await navigator.clipboard.writeText(baris.join('\n'))
    notify.success('Ringkasan disalin', 'Tinggal tempel di mana pun kamu perlu.')
  } catch {
    // Clipboard API diblokir di konteks non-HTTPS dan sebagian browser lama.
    notify.error('Gagal menyalin', 'Browser menolak akses papan klip.')
  } finally {
    menyalin.value = false
  }
}
</script>

<template>
  <section class="flex flex-col gap-3.5">
    <!-- Bar judul: identitas panel di kiri, aksi dan waktu data di kanan -->
    <header class="flex flex-wrap items-start justify-between gap-3">
      <h2
        class="flex items-center gap-1.5 rounded-full border-[0.5px] border-border bg-card px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-foreground"
      >
        <Sparkles class="size-3.5 text-[var(--primary)]" aria-hidden="true" />
        Analisis Preskriptif AI
      </h2>

      <div class="flex flex-col items-end gap-1">
        <button
          type="button"
          :disabled="menyalin || !backend?.llm_summary"
          class="flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] font-semibold text-[var(--primary)] transition-colors hover:bg-[var(--primary-soft)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--ring)] disabled:cursor-not-allowed disabled:opacity-50"
          @click="bagikan"
        >
          <Share2 class="size-3.5" aria-hidden="true" />
          Bagikan
        </button>

        <p class="text-[10px] text-muted-foreground">
          Data terakhir diupdate:
          <span class="tabular">{{ backend?.tanggal_analisis ? formatDate(backend.tanggal_analisis) : '—' }}</span>
        </p>
      </div>
    </header>

    <div v-if="loading" class="flex flex-col gap-3.5">
      <div class="h-[180px] animate-pulse rounded-xl bg-muted" />
      <div class="grid gap-3.5 lg:grid-cols-2">
        <div v-for="i in 2" :key="i" class="h-[190px] animate-pulse rounded-xl bg-muted" />
      </div>
    </div>

    <EmptyState
      v-else-if="!hasil"
      title="Belum ada data OHLC"
      description="Analisis muncul setelah emiten ini punya histori harga."
    />

    <template v-else>
      <!-- 0 — Ringkasan AI: naratif panjang, jadi diberi panggung sendiri -->
      <article
        class="rounded-xl border-[0.5px] border-[var(--primary-light)]/50 bg-[var(--background-secondary)] p-4 sm:p-5"
      >
        <div class="flex gap-4 sm:gap-5">
          <!-- Maskot ikut menandai bahwa teks ini tulisan mesin, bukan analis -->
          <svg
            class="hidden size-[84px] shrink-0 sm:block lg:size-[96px]"
            viewBox="0 0 96 96"
            fill="none"
            aria-hidden="true"
          >
            <circle cx="48" cy="10" r="4.5" fill="var(--primary-light)" />
            <path d="M48 14v9" stroke="var(--primary)" stroke-width="3" stroke-linecap="round" />
            <rect x="5" y="40" width="9" height="20" rx="4.5" fill="var(--primary-light)" />
            <rect x="82" y="40" width="9" height="20" rx="4.5" fill="var(--primary-light)" />
            <rect x="14" y="23" width="68" height="56" rx="19" fill="var(--primary)" />
            <rect x="25" y="34" width="46" height="29" rx="12" fill="var(--chart-5)" />
            <circle cx="39" cy="48.5" r="5.5" fill="var(--primary-light)" />
            <circle cx="57" cy="48.5" r="5.5" fill="var(--primary-light)" />
            <rect x="40" y="69" width="16" height="4" rx="2" fill="var(--primary-light)" opacity="0.55" />
          </svg>

          <div class="min-w-0 flex-1">
            <div v-if="backendLoading" class="flex flex-col gap-2">
              <div v-for="i in 5" :key="i" class="h-3 animate-pulse rounded bg-muted" />
            </div>

            <template v-else-if="ringkasan.length">
              <p
                v-for="p in ringkasan"
                :key="p.id"
                class="mb-3 text-[12.5px] leading-[1.75] text-[var(--foreground-body)] last:mb-0"
              >
                <!-- Tag ditutup rapat di baris yang sama: baris baru di dalam
                     elemen ikut jadi spasi dan merusak tanda kutip serta kurung. -->
                <template v-for="(b, i) in p.bagian" :key="i">
                  <strong
                    v-if="b.gaya === 'tebal'"
                    class="font-semibold text-foreground"
                  >{{ b.teks }}</strong>
                  <em
                    v-else-if="b.gaya === 'miring'"
                    class="font-medium not-italic text-foreground"
                  >“{{ b.teks }}”</em>
                  <template v-else>{{ b.teks }}</template>
                </template>
              </p>
            </template>

            <p v-else class="text-[12.5px] text-muted-foreground">
              Ringkasan AI belum tersedia untuk emiten ini.
            </p>

            <p class="mt-4 border-t-[0.5px] border-border pt-2.5 text-[10px] text-muted-foreground">
              Disclaimer: AI tidak 100% akurat. Gunakan analisis ini sebagai referensi tambahan.
            </p>
          </div>
        </div>
      </article>

      <!-- 1 — Keputusan di kiri, angka level di kanan -->
      <div class="grid gap-3.5 lg:grid-cols-2">
        <div class="flex flex-col rounded-xl border-[0.5px] border-border bg-card p-4">
          <div class="mb-3 flex items-baseline justify-between gap-2">
            <p class="text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">
              Rekomendasi AI
            </p>
            <span class="tabular text-[10px] text-muted-foreground">
              {{ hasil.bull }} bullish · {{ hasil.bear }} bearish
            </span>
          </div>

          <div class="rounded-lg border-[0.5px] p-3.5" :class="KELAS_KARTU[nadaAksi]">
            <div class="flex items-center gap-2" :class="KELAS_TEKS[nadaAksi]">
              <component :is="ikonAksi" class="size-5" aria-hidden="true" />
              <span class="text-[22px] font-bold leading-none tracking-tight">{{ hasil.aksi }}</span>
            </div>

            <p class="mt-2 text-[12px] leading-relaxed text-[var(--foreground-body)]">
              {{ SARAN[hasil.aksi] }}
            </p>

            <div v-if="chip.length" class="mt-3 flex flex-wrap gap-1.5">
              <span
                v-for="c in chip"
                :key="c.teks"
                class="tabular rounded px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.03em]"
                :class="
                  c.naik
                    ? 'bg-[var(--up-bg)] text-[var(--color-up-ink)]'
                    : 'bg-[var(--down-bg)] text-[var(--color-down-ink)]'
                "
              >
                {{ c.teks }}
              </span>
            </div>
          </div>

          <p class="mt-3 flex items-start gap-1.5 text-[10px] leading-relaxed text-muted-foreground">
            <Info class="mt-px size-3 shrink-0" aria-hidden="true" />
            <span>
              Pastikan selalu gunakan risk management dan lakukan riset sebelum berinvestasi.
            </span>
          </p>
        </div>

        <div
          v-if="levels"
          class="flex flex-col rounded-xl border-[0.5px] border-border bg-card p-4"
        >
          <p class="mb-3 text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">
            Level Trading
          </p>

          <div class="grid grid-cols-1 gap-2.5 sm:grid-cols-3">
            <div class="rounded-lg border-[0.5px] border-border bg-[var(--background-secondary)] p-3">
              <p class="text-[9px] font-semibold uppercase tracking-[0.06em] text-muted-foreground">
                Entry
              </p>
              <p class="tabular mt-1.5 text-[22px] font-bold leading-none">
                {{ formatNumber(levels.entry) }}
              </p>
              <p class="mt-1.5 text-[10px] text-muted-foreground">Zona masuk ideal</p>
            </div>

            <div class="rounded-lg border-[0.5px] border-[var(--up)]/40 bg-[var(--up-bg)] p-3">
              <p class="text-[9px] font-semibold uppercase tracking-[0.06em] text-[var(--color-up-ink)]">
                Target
              </p>
              <p class="tabular mt-1.5 text-[22px] font-bold leading-none text-[var(--color-up-ink)]">
                {{ formatNumber(levels.target) }}
              </p>
              <p class="tabular mt-1.5 text-[10px] text-muted-foreground">
                {{ persen(levels.persenTarget) ?? '—' }} dari entry
              </p>
            </div>

            <div class="rounded-lg border-[0.5px] border-[var(--down)]/40 bg-[var(--down-bg)] p-3">
              <p class="text-[9px] font-semibold uppercase tracking-[0.06em] text-[var(--color-down-ink)]">
                Stop Loss
              </p>
              <p class="tabular mt-1.5 text-[22px] font-bold leading-none text-[var(--color-down-ink)]">
                {{ formatNumber(levels.stopLoss) }}
              </p>
              <p class="tabular mt-1.5 text-[10px] text-muted-foreground">
                {{ persen(levels.persenStopLoss) ?? '—' }} dari entry
              </p>
            </div>
          </div>

          <div
            v-if="mutuRR"
            class="mt-2.5 flex flex-wrap items-center gap-x-3 gap-y-2 rounded-lg border-[0.5px] border-border px-3 py-2.5"
          >
            <span class="text-[11px] text-muted-foreground">Risk / Reward</span>
            <span class="tabular text-[13px] font-bold">1 : {{ levels.riskReward.toFixed(2) }}</span>
            <StatusPill :label="mutuRR.teks" :tone="mutuRR.tone" />

            <button
              type="button"
              :disabled="backendLoading"
              class="ml-auto flex items-center gap-1.5 rounded-md border-[0.5px] border-border px-2.5 py-1 text-[11px] font-medium text-foreground transition-colors hover:bg-[var(--card-hover)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--ring)] disabled:opacity-60"
              @click="emit('recompute')"
            >
              <RefreshCw class="size-3" :class="{ 'animate-spin': backendLoading }" aria-hidden="true" />
              Hitung ulang RR
            </button>
          </div>
        </div>
      </div>

      <!-- 2 — Strategi per posisi di kiri, angka indikator di kanan -->
      <div class="grid gap-3.5 lg:grid-cols-2">
        <div
          v-if="backend?.new_buyer_strategy?.recommendation || backend?.holding_strategy?.recommendation"
          class="flex flex-col rounded-xl border-[0.5px] border-border bg-card p-4"
        >
          <p class="mb-3 text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">
            Strategi Menurut Posisi
          </p>

          <div class="flex flex-col gap-2.5">
            <div
              v-if="backend.new_buyer_strategy?.recommendation"
              class="flex gap-3 rounded-lg border-[0.5px] border-border bg-[var(--background-secondary)] p-3"
            >
              <span
                class="flex size-8 shrink-0 items-center justify-center rounded-lg bg-card text-muted-foreground"
              >
                <UserPlus class="size-4" aria-hidden="true" />
              </span>

              <div class="min-w-0">
                <p class="text-[10px] text-muted-foreground">Belum punya posisi</p>
                <p class="text-[14px] font-semibold leading-snug">
                  {{ backend.new_buyer_strategy.recommendation }}
                </p>
                <p
                  v-if="backend.new_buyer_strategy.reason"
                  class="mt-1 text-[11px] leading-relaxed text-[var(--foreground-body)]"
                >
                  {{ backend.new_buyer_strategy.reason }}
                </p>
              </div>
            </div>

            <div
              v-if="backend.holding_strategy?.recommendation"
              class="flex gap-3 rounded-lg border-[0.5px] border-border bg-[var(--background-secondary)] p-3"
            >
              <span
                class="flex size-8 shrink-0 items-center justify-center rounded-lg bg-card text-muted-foreground"
              >
                <Wallet class="size-4" aria-hidden="true" />
              </span>

              <div class="min-w-0">
                <p class="text-[10px] text-muted-foreground">Sudah pegang</p>
                <p class="text-[14px] font-semibold leading-snug">
                  {{ backend.holding_strategy.recommendation }}
                </p>
                <p
                  v-if="backend.holding_strategy.reason"
                  class="mt-1 text-[11px] leading-relaxed text-[var(--foreground-body)]"
                >
                  {{ backend.holding_strategy.reason }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div class="flex flex-col rounded-xl border-[0.5px] border-border bg-card p-4">
          <p class="mb-1 text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">
            Ringkasan Teknikal
          </p>

          <ul class="divide-y-[0.5px] divide-border">
            <li
              v-for="ind in indikator"
              :key="ind.key"
              class="flex items-center justify-between gap-3 py-2.5"
            >
              <span class="text-[12px] text-muted-foreground">{{ ind.name }}</span>
              <div class="flex items-center gap-2.5">
                <span class="tabular text-[13px] font-semibold">{{ ind.display }}</span>
                <StatusPill :label="ind.label" :tone="ind.tone" />
              </div>
            </li>
          </ul>
        </div>
      </div>

      <!-- 3 — Proyeksi harga; melebar penuh karena barisnya panjang -->
      <div class="flex flex-col rounded-xl border-[0.5px] border-border bg-card p-4">
        <div class="mb-1 flex items-baseline justify-between gap-2">
          <p class="text-[10px] font-semibold uppercase tracking-[0.08em] text-muted-foreground">
            Prediksi Harga
          </p>
          <span v-if="forecast.length" class="text-[10px] text-muted-foreground">
            Prediksi {{ forecast.length }} hari ke depan
          </span>
        </div>

        <div v-if="forecastLoading" class="flex flex-col gap-1.5 pt-2">
          <div v-for="i in 5" :key="i" class="h-[34px] animate-pulse rounded bg-muted" />
        </div>

        <EmptyState
          v-else-if="!forecast.length"
          title="Proyeksi belum tersedia"
          description="Muncul setelah emiten ini punya histori harga yang cukup."
        />

        <ul v-else class="divide-y-[0.5px] divide-border">
          <li
            v-for="(p, i) in forecast"
            :key="p.tanggal"
            class="flex items-center gap-3 py-2.5"
          >
            <span class="tabular w-[26px] shrink-0 text-[12px] font-bold text-foreground">
              #{{ i + 1 }}
            </span>

            <span class="tabular w-[52px] shrink-0 text-[10px] leading-tight text-muted-foreground">
              {{ tanggalDuaBaris(p.tanggal).hari }}<br />
              {{ tanggalDuaBaris(p.tanggal).tahun }}
            </span>

            <span class="h-2 min-w-0 flex-1 overflow-hidden rounded-full bg-muted">
              <span
                class="block h-full rounded-full bg-[var(--primary)] transition-[width] duration-500"
                :style="{ width: `${lebarBar(p.prediksi)}%` }"
              />
            </span>

            <span class="tabular w-[58px] shrink-0 text-right text-[13px] font-semibold">
              {{ formatNumber(p.prediksi) }}
            </span>

            <span
              v-if="p.lower != null && p.upper != null"
              class="tabular hidden w-[112px] shrink-0 text-right text-[11px] text-muted-foreground sm:block"
            >
              {{ formatNumber(p.lower) }} — {{ formatNumber(p.upper) }}
            </span>
          </li>
        </ul>
      </div>
    </template>
  </section>
</template>
