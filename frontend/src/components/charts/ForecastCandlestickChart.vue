<script setup>
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import {
  CandlestickSeries,
  ColorType,
  createChart,
  LineSeries,
  HistogramSeries,
  CrosshairMode,
} from 'lightweight-charts'
import { useTheme } from '@/composables/useTheme'
import { applyChartTimeframe } from '@/utils/chart'
import { formatCompact, formatDate, formatNumber } from '@/utils/format'

const props = defineProps({
  /** Baris OHLC historis dari /api/data/ohlc, urut tanggal ASC. */
  rows: { type: Array, default: () => [] },
  /** Titik proyeksi dari /api/data/forecast: { tanggal, open, prediksi, lower, upper }. */
  points: { type: Array, default: () => [] },
  height: { type: Number, default: 420 },
  timeframe: { type: String, default: '6M' },
})

const container = ref(null)
const { isDark } = useTheme()

const chart = shallowRef(null)
const seriesAktual = shallowRef(null)
const seriesForecastBounds = shallowRef(null)
const seriesForecastLine = shallowRef(null)
const seriesVolume = shallowRef(null)

const showHist = ref(true)
const showForecast = ref(true)
const showVolume = ref(true)

function warna() {
  const style = getComputedStyle(document.documentElement)
  const ambil = (nama) => style.getPropertyValue(nama).trim()
  return {
    card: ambil('--card'),
    up: ambil('--up'),
    down: ambil('--down'),
    proyeksi: ambil('--warning'),
    proyeksiLight: ambil('--warning'),
    grid: ambil('--border'),
    text: ambil('--muted-foreground'),
  }
}

function pudar(hex, alpha) {
  const h = String(hex).replace('#', '')
  const penuh = h.length === 3 ? h.split('').map((c) => c + c).join('') : h
  const n = parseInt(penuh, 16)
  if (Number.isNaN(n)) return hex
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`
}

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
    rightPriceScale: {
      borderColor: grid,
      scaleMargins: { top: 0.08, bottom: 0.22 },
    },
    timeScale: {
      borderColor: grid,
      maxBarSpacing: 1e4,
      rightOffset: 0,
      fixLeftEdge: true,
      fixRightEdge: true,
    },
    crosshair: { mode: CrosshairMode.Normal },
  }
}

function temaAktual() {
  const { up, down } = warna()
  return {
    upColor: up,
    downColor: down,
    borderUpColor: up,
    borderDownColor: down,
    wickUpColor: up,
    wickDownColor: down,
  }
}

function toChartData(rows) {
  return rows
    .map((r) => ({
      time: String(r.tanggal).slice(0, 10),
      open: Number(r.open),
      high: Number(r.high),
      low: Number(r.low),
      close: Number(r.close),
    }))
    .filter((d) => !Number.isNaN(d.open) && !Number.isNaN(d.close))
}

function toForecastData(points, hargaAcuan) {
  const line = []
  const bounds = []

  for (const p of points) {
    const close = Number(p.prediksi)
    const low = p.lower != null ? Number(p.lower) : close
    const high = p.upper != null ? Number(p.upper) : close

    if (!Number.isFinite(close)) continue

    const t = String(p.tanggal).slice(0, 10)
    line.push({ time: t, value: close })
    bounds.push({
      time: t,
      open: high,
      high: high,
      low: low,
      close: low,
    })
  }

  return { line, bounds }
}

function toVolumeData(rows) {
  const w = warna()
  return rows
    .map((r) => {
      const isUp = Number(r.close) >= Number(r.open)
      const dasar = isUp ? w.up : w.down
      return {
        time: String(r.tanggal).slice(0, 10),
        value: Number(r.volume) || 0,
        color: pudar(dasar, 0.45),
      }
    })
    .filter((d) => !Number.isNaN(d.value))
}

const dataAktual = computed(() => toChartData(props.rows))
const dataProyeksi = computed(() => {
  const hargaAcuan = dataAktual.value.length ? dataAktual.value[dataAktual.value.length - 1].close : null
  return toForecastData(props.points, hargaAcuan)
})
const dataVolume = computed(() => toVolumeData(props.rows))

function updateVisibility() {
  if (seriesAktual.value) seriesAktual.value.applyOptions({ visible: showHist.value })
  if (seriesForecastBounds.value) seriesForecastBounds.value.applyOptions({ visible: showForecast.value })
  if (seriesForecastLine.value) seriesForecastLine.value.applyOptions({ visible: showForecast.value })
  if (seriesVolume.value) seriesVolume.value.applyOptions({ visible: showVolume.value })
}

function applyTimeframe() {
  applyChartTimeframe(
    chart.value,
    props.timeframe,
    dataAktual.value,
    showForecast.value,
    dataProyeksi.value.line
  )
}

// ── Hover & Legend ────────────────────────────────────────────────────────
const legendData = ref(null)

function updateLastLegend() {
  const data = {}
  if (dataAktual.value.length) data.aktual = dataAktual.value[dataAktual.value.length - 1]
  if (dataVolume.value.length) data.volume = dataVolume.value[dataVolume.value.length - 1].value
  if (dataProyeksi.value.line.length) {
    data.forecast = dataProyeksi.value.line[dataProyeksi.value.line.length - 1].value
  }
  legendData.value = data
}

function render() {
  if (!seriesAktual.value) return

  seriesAktual.value.setData(dataAktual.value)
  seriesForecastBounds.value.setData(dataProyeksi.value.bounds)
  seriesForecastLine.value.setData(dataProyeksi.value.line)
  seriesVolume.value.setData(dataVolume.value)

  updateVisibility()
  updateLastLegend()
  applyTimeframe()
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

  // Add volume series first so it's behind candles
  seriesVolume.value = chart.value.addSeries(HistogramSeries, {
    priceScaleId: 'volume',
    priceLineVisible: false,
    lastValueVisible: false,
    priceFormat: {
      type: 'volume',
    },
  })

  chart.value.priceScale('volume').applyOptions({
    visible: false,
    scaleMargins: {
      top: 0.80,
      bottom: 0.02,
    },
  })

  seriesAktual.value = chart.value.addSeries(CandlestickSeries, temaAktual())

  seriesForecastBounds.value = chart.value.addSeries(CandlestickSeries, {
    upColor: pudar(w.proyeksi, 0.35),
    downColor: pudar(w.proyeksi, 0.35),
    borderVisible: false,
    wickVisible: false,
    priceLineVisible: false,
    lastValueVisible: false,
  })

  seriesForecastLine.value = chart.value.addSeries(LineSeries, {
    color: w.proyeksi,
    lineWidth: 2,
    pointMarkersVisible: true,
    pointMarkersRadius: 4,
    priceLineVisible: false,
    lastValueVisible: false,
  })

  chart.value.subscribeCrosshairMove((param) => {
    if (!param.time || param.point.x < 0 || param.point.y < 0) {
      updateLastLegend()
      return
    }

    const data = {}
    const act = param.seriesData.get(seriesAktual.value)
    if (act) data.aktual = act

    const vol = param.seriesData.get(seriesVolume.value)
    if (vol) data.volume = vol.value

    const fcLine = param.seriesData.get(seriesForecastLine.value)
    if (fcLine) data.forecast = fcLine.value

    legendData.value = data
  })

  render()
})

onBeforeUnmount(() => {
  chart.value?.remove()
  chart.value = null
})

watch(() => [props.rows, props.points], render, { deep: false })
watch(isDark, () => {
  chart.value?.applyOptions(tema())
  seriesAktual.value?.applyOptions(temaAktual())

  const w = warna()
  seriesForecastBounds.value?.applyOptions({
    upColor: pudar(w.proyeksi, 0.35),
    downColor: pudar(w.proyeksi, 0.35),
  })
  seriesForecastLine.value?.applyOptions({ color: w.proyeksi })
  render()
})

watch([showHist, showForecast, showVolume], updateVisibility)
watch(() => props.timeframe, applyTimeframe)

function resetZoom() {
  chart.value?.timeScale().fitContent()
}

defineExpose({ resetZoom })
</script>

<template>
  <div class="flex flex-col gap-2 w-full">
    <!-- Legenda Info Baris -->
    <div class="flex flex-wrap items-center gap-x-6 gap-y-1 min-h-[24px]">
      <div v-if="legendData?.aktual && showHist" class="text-[12px] font-mono flex items-center">
        <span class="font-bold mr-1 text-foreground">O</span><span class="mr-3">{{ formatNumber(legendData.aktual.open) }}</span>
        <span class="font-bold mr-1 text-foreground">H</span><span class="mr-3">{{ formatNumber(legendData.aktual.high) }}</span>
        <span class="font-bold mr-1 text-foreground">L</span><span class="mr-3">{{ formatNumber(legendData.aktual.low) }}</span>
        <span class="font-bold mr-1 text-foreground">C</span><span>{{ formatNumber(legendData.aktual.close) }}</span>
      </div>

      <div v-if="legendData?.volume != null && showVolume" class="text-[12px] font-mono text-muted-foreground flex items-center">
        <span class="font-bold mr-1">Vol</span><span>{{ formatCompact(legendData.volume) }}</span>
      </div>

      <div v-if="legendData?.forecast && showForecast" class="text-[12px] font-mono text-[var(--warning)] flex items-center">
        <span class="font-bold mr-1">Forecast</span><span>{{ formatNumber(legendData.forecast) }}</span>
      </div>
    </div>

    <!-- Chart Canvas -->
    <div class="relative w-full" :style="{ height: `${height}px` }">
      <div
        ref="container"
        data-lenis-prevent
        class="h-full w-full"
        role="img"
        aria-label="Grafik candlestick harga historis, proyeksi, dan volume transaksi"
      />
    </div>

    <!-- Toggles Visibilitas Layer -->
    <div class="flex flex-col xl:flex-row xl:items-center gap-3 border-t-[0.5px] border-border pt-4 mt-2 w-full">
      <span class="text-base font-medium text-muted-foreground shrink-0">Tampilkan:</span>

      <div class="flex flex-wrap w-full items-center rounded-lg border-[0.5px] border-border bg-muted/40 p-1 shadow-inner flex-1 gap-1">
        <!-- 1. Historical -->
        <button
          type="button"
          class="flex-1 flex items-center justify-center gap-1.5 rounded-md px-2 py-1.5 text-sm font-medium transition-all duration-200 cursor-pointer min-w-[130px] whitespace-nowrap"
          :class="showHist ? 'bg-background text-foreground shadow-sm ring-1 ring-border/50' : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'"
          @click="showHist = !showHist"
        >
          <div class="h-2 w-2 rounded-full shrink-0" :class="showHist ? 'bg-primary' : 'bg-muted'" />
          Historical
        </button>

        <!-- 2. Forecast -->
        <button
          v-if="points.length"
          type="button"
          class="flex-1 flex items-center justify-center gap-1.5 rounded-md px-2 py-1.5 text-sm font-medium transition-all duration-200 cursor-pointer min-w-[130px] whitespace-nowrap"
          :class="showForecast ? 'bg-background text-foreground shadow-sm ring-1 ring-border/50' : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'"
          @click="showForecast = !showForecast"
        >
          <div class="h-2 w-2 rounded-full shrink-0" :class="showForecast ? 'bg-[var(--warning)]' : 'bg-muted'" />
          Forecast
        </button>

        <!-- 3. Volume -->
        <button
          type="button"
          class="flex-1 flex items-center justify-center gap-1.5 rounded-md px-2 py-1.5 text-sm font-medium transition-all duration-200 cursor-pointer min-w-[130px] whitespace-nowrap"
          :class="showVolume ? 'bg-background text-foreground shadow-sm ring-1 ring-border/50' : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'"
          @click="showVolume = !showVolume"
        >
          <div class="h-2 w-2 rounded-full shrink-0" :class="showVolume ? 'bg-foreground' : 'bg-muted'" />
          Volume
        </button>
      </div>
    </div>
  </div>
</template>
