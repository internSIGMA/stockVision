<script setup>
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import {
  ColorType,
  CrosshairMode,
  HistogramSeries,
  LineSeries,
  LineStyle,
  createChart,
} from 'lightweight-charts'
import { useTheme } from '@/composables/useTheme'
import { applyIndicatorTimeframe } from '@/utils/chart'

/**
 * Panel MACD bergaya TradingView: histogram empat nada, garis MACD & signal,
 * garis nol putus-putus, dan legend melayang yang ikut kursor.
 *
 * Memakai lightweight-charts (bukan Chart.js) supaya zoom & pan-nya sama persis
 * dengan Historical Candlestick — satu library, satu perilaku.
 */
const props = defineProps({
  /** Label tanggal 'YYYY-MM-DD', sejajar dengan ketiga deret di bawah. */
  dates: { type: Array, default: () => [] },
  macdLine: { type: Array, default: () => [] },
  signalLine: { type: Array, default: () => [] },
  histogram: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  height: { type: Number, default: 240 },
  /** Jumlah bar yang terlihat saat pertama dibuka; sisanya dijangkau via zoom. */
  jendelaAwal: { type: Number, default: 150 },
  timeframe: { type: String, default: '6M' },
})

const container = ref(null)
const { isDark } = useTheme()

const chart = shallowRef(null)
const seriHist = shallowRef(null)
const seriMacd = shallowRef(null)
const seriSignal = shallowRef(null)
const garisNol = shallowRef(null)

/** '#RGB' / '#RRGGBB' → 'rgba(r,g,b,a)'. Token tema semuanya hex. */
function pudar(hex, alpha) {
  const h = String(hex).replace('#', '')
  const penuh = h.length === 3 ? h.split('').map((c) => c + c).join('') : h
  const n = parseInt(penuh, 16)
  if (Number.isNaN(n)) return hex
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`
}

function warna() {
  const style = getComputedStyle(document.documentElement)
  const ambil = (nama) => style.getPropertyValue(nama).trim()
  return {
    macd: ambil('--primary'),
    // Amber, bukan token --chart-*: seluruh palet chart isinya turunan teal,
    // jadi garis signal akan menyatu dengan garis MACD — parah di dark mode.
    signal: ambil('--warning'),
    naik: ambil('--up'),
    turun: ambil('--down'),
    grid: ambil('--border'),
    text: ambil('--muted-foreground'),
  }
}

/** Pasangkan tanggal & nilai satu deret, buang kosong dan tanggal kembar. */
function rangkai(nilai) {
  const out = []
  let sebelumnya = null
  for (let i = 0; i < nilai.length; i++) {
    const v = nilai[i]
    const t = props.dates[i]
    if (v == null || !t) continue
    const time = String(t).slice(0, 10)
    if (time === sebelumnya) continue
    sebelumnya = time
    out.push({ time, value: Number(v) })
  }
  return out
}

const titikMacd = computed(() => rangkai(props.macdLine))
const titikSignal = computed(() => rangkai(props.signalLine))

/**
 * Histogram empat nada seperti TradingView: warna dari tanda batang, dan
 * pekat/pudarnya dari apakah momentumnya sedang menguat atau melemah.
 * Nada saja tidak pernah jadi satu-satunya pembawa makna — tinggi batang dan
 * sisi garis nol tetap membaca sendiri.
 */
const titikHist = computed(() => {
  void isDark.value // warna ikut token; hitung ulang saat tema berganti
  const w = warna()
  const src = rangkai(props.histogram)
  return src.map((d, i) => {
    const menguat = i === 0 ? true : Math.abs(d.value) >= Math.abs(src[i - 1].value)
    const dasar = d.value >= 0 ? w.naik : w.turun
    return { ...d, color: menguat ? dasar : pudar(dasar, 0.4) }
  })
})

const adaData = computed(() => titikHist.value.length > 0)

function tema() {
  const { grid, text } = warna()
  return {
    layout: {
      background: { type: ColorType.Solid, color: 'transparent' },
      textColor: text,
      fontFamily: "'Spline Sans Mono', monospace",
      fontSize: 10,
      attributionLogo: false,
    },
    grid: { vertLines: { color: grid }, horzLines: { color: grid } },
    rightPriceScale: { borderColor: grid, scaleMargins: { top: 0.12, bottom: 0.12 } },
    timeScale: {
      borderColor: grid,
      rightOffset: 2,
      fixLeftEdge: true,
      fixRightEdge: true,
    },
    crosshair: { mode: CrosshairMode.Normal },
  }
}

/** Garis nol — di MACD justru perpotongan nol yang jadi sinyalnya. */
function pasangGarisNol() {
  const s = seriMacd.value
  if (!s) return
  if (garisNol.value) s.removePriceLine(garisNol.value)
  garisNol.value = s.createPriceLine({
    price: 0,
    color: warna().text,
    lineWidth: 1,
    lineStyle: LineStyle.Dashed,
    axisLabelVisible: false,
    title: '',
  })
}

// ── Legend melayang, mengikuti kursor seperti TradingView ──────────────────
const nilaiMacd = ref(null)
const nilaiSignal = ref(null)
const nilaiHist = ref(null)

const ekor = (arr) => (arr.length ? arr[arr.length - 1].value : null)

function isiLegendTerakhir() {
  nilaiMacd.value = ekor(titikMacd.value)
  nilaiSignal.value = ekor(titikSignal.value)
  nilaiHist.value = ekor(titikHist.value)
}

const fmt = (v) => (v == null ? '—' : v.toFixed(2))

/** Lebar sumbu harga — dipakai menggeser tombol agar tak menutupi labelnya. */
const lebarSkala = ref(0)
function hitungLebarSkala() {
  lebarSkala.value = chart.value?.priceScale('right').width() ?? 0
}

/** Warna angka histogram di legend mengikuti sisi garis nol. */
const kelasHist = computed(() =>
  nilaiHist.value == null
    ? 'text-muted-foreground'
    : nilaiHist.value >= 0
      ? 'text-[var(--color-up-ink)]'
      : 'text-[var(--color-down-ink)]',
)

/**
 * Buka di ekor data, bukan fitContent(): lima tahun histogram yang dijejalkan
 * ke satu layar jadi tidak terbaca. Histori lamanya tetap ada, tinggal zoom out.
 */
function bukaDiEkor() {
  const n = titikHist.value.length
  if (!n) return
  chart.value?.timeScale().setVisibleLogicalRange({
    from: Math.max(0, n - props.jendelaAwal),
    to: n + 2,
  })
}

function applyTimeframe() {
  applyIndicatorTimeframe(chart.value, props.timeframe, titikHist.value)
}

function render() {
  if (!seriHist.value) return
  seriHist.value.setData(titikHist.value)
  seriMacd.value.setData(titikMacd.value)
  seriSignal.value.setData(titikSignal.value)
  pasangGarisNol()
  applyTimeframe()
  isiLegendTerakhir()
  requestAnimationFrame(hitungLebarSkala)
}

onMounted(() => {
  const w = warna()
  chart.value = createChart(container.value, {
    ...tema(),
    height: props.height,
    autoSize: true,
    handleScroll: true,
    handleScale: true,
  })

  // Histogram ditambahkan lebih dulu supaya berada di belakang kedua garis.
  seriHist.value = chart.value.addSeries(HistogramSeries, {
    priceLineVisible: false,
    lastValueVisible: false,
  })

  seriMacd.value = chart.value.addSeries(LineSeries, {
    color: w.macd,
    lineWidth: 2,
    priceLineVisible: false,
    lastValueVisible: false,
  })

  seriSignal.value = chart.value.addSeries(LineSeries, {
    color: w.signal,
    lineWidth: 2,
    lineStyle: LineStyle.Dashed,
    priceLineVisible: false,
    lastValueVisible: false,
  })

  chart.value.subscribeCrosshairMove((param) => {
    if (!param.time) {
      isiLegendTerakhir()
      return
    }
    nilaiMacd.value = param.seriesData.get(seriMacd.value)?.value ?? null
    nilaiSignal.value = param.seriesData.get(seriSignal.value)?.value ?? null
    nilaiHist.value = param.seriesData.get(seriHist.value)?.value ?? null
  })

  render()
})

onBeforeUnmount(() => {
  chart.value?.remove()
  chart.value = null
  seriHist.value = null
  seriMacd.value = null
  seriSignal.value = null
})

watch(titikHist, render)
watch(isDark, () => {
  const w = warna()
  chart.value?.applyOptions(tema())
  seriMacd.value?.applyOptions({ color: w.macd })
  seriSignal.value?.applyOptions({ color: w.signal })
  pasangGarisNol()
})
watch(() => props.timeframe, applyTimeframe)

function resetZoom() {
  applyTimeframe()
}

defineExpose({ resetZoom })
</script>

<template>
  <div class="relative w-full" :style="{ height: `${height}px` }">
    <!-- data-lenis-prevent: Lenis tidak boleh membajak scroll-zoom milik chart. -->
    <div
      ref="container"
      data-lenis-prevent
      class="h-full w-full"
      role="img"
      :aria-label="`Grafik MACD 12, 26, 9. Nilai terakhir MACD ${fmt(nilaiMacd)}, signal ${fmt(nilaiSignal)}, histogram ${fmt(nilaiHist)} — ${nilaiHist >= 0 ? 'momentum bullish' : 'momentum bearish'}.`"
    />

    <!-- Legend melayang ala TradingView -->
    <div
      v-if="adaData"
      class="tabular pointer-events-none absolute left-2 top-1 z-[2] flex flex-wrap items-baseline gap-x-3 gap-y-1 text-[11px] leading-none"
    >
      <div class="flex items-baseline gap-1.5">
        <span class="font-semibold text-foreground">MACD</span>
        <span class="text-muted-foreground">12 26 9 close</span>
      </div>
      <div class="flex items-baseline gap-1">
        <span class="text-muted-foreground">Hist</span>
        <span class="font-semibold" :class="kelasHist">{{ fmt(nilaiHist) }}</span>
      </div>
      <div class="flex items-baseline gap-1">
        <span class="text-muted-foreground">MACD</span>
        <span class="font-semibold text-[var(--primary)]">{{ fmt(nilaiMacd) }}</span>
      </div>
      <div class="flex items-baseline gap-1">
        <span class="text-muted-foreground">Signal</span>
        <span class="font-semibold text-[var(--warning)]">{{ fmt(nilaiSignal) }}</span>
      </div>
    </div>

    <button
      v-if="adaData"
      type="button"
      class="absolute top-1 z-[2] rounded border-[0.5px] border-border bg-card/80 px-1.5 py-0.5 text-[10px] text-muted-foreground backdrop-blur transition-colors hover:bg-[var(--card-hover)] hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[var(--ring)]"
      :style="{ right: `${lebarSkala + 8}px` }"
      @click="resetZoom"
    >
      Reset zoom
    </button>

    <div v-if="loading" class="absolute inset-0 z-[3] animate-pulse rounded-lg bg-muted" />

    <p
      v-else-if="!adaData"
      class="absolute inset-0 z-[3] flex items-center justify-center bg-card text-[11px] text-muted-foreground"
    >
      Data MACD belum cukup untuk digambar.
    </p>
  </div>
</template>
