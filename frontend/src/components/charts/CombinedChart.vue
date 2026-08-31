<script setup>
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import {
  CandlestickSeries,
  ColorType,
  createChart,
  LineSeries,
  AreaSeries,
  HistogramSeries,
  LineStyle,
  CrosshairMode
} from 'lightweight-charts'
import { useTheme } from '@/composables/useTheme'
import { applyChartTimeframe } from '@/utils/chart'
import { formatDate, formatNumber } from '@/utils/format'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  points: { type: Array, default: () => [] },
  rsi: { type: Object, default: () => ({ dates: [], rsi: [] }) },
  macd: { type: Object, default: () => ({ dates: [], macdLine: [], signalLine: [], histogram: [] }) },
  height: { type: Number, default: 500 },
  timeframe: { type: String, default: '6M' },
})

const container = ref(null)
const { isDark } = useTheme()

const chart = shallowRef(null)
const seriesAktual = shallowRef(null)
const seriesForecastBounds = shallowRef(null)
const seriesForecastLine = shallowRef(null)
const seriesRsi = shallowRef(null)
const seriesMacd = shallowRef(null)
const seriesSignal = shallowRef(null)
const seriesHist = shallowRef(null)

const showHist = ref(true)
const showForecast = ref(true)
const showRsi = ref(true)
const showMacd = ref(true)

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
    rsi: ambil('--chart-2'),
    macd: ambil('--info'),
    signal: ambil('--warning'),
    naik: ambil('--up'),
    turun: ambil('--down'),
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
    rightPriceScale: { borderColor: grid },
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

function temaProyeksi() {
  const { proyeksi, proyeksiLight } = warna()
  return {
    upColor: proyeksi,
    downColor: proyeksiLight,
    borderUpColor: proyeksi,
    borderDownColor: proyeksiLight,
    wickUpColor: proyeksi,
    wickDownColor: proyeksiLight,
  }
}

// Data processors
function toChartData(rows) {
  return rows.map((r) => ({
    time: String(r.tanggal).slice(0, 10),
    open: Number(r.open),
    high: Number(r.high),
    low: Number(r.low),
    close: Number(r.close),
  })).filter((d) => !Number.isNaN(d.open) && !Number.isNaN(d.close))
}

function toForecastData(points, hargaAcuan) {
  let acuan = hargaAcuan
  const line = []
  const bounds = []

  for (const p of points) {
    const close = Number(p.prediksi)
    const low = p.lower != null ? Number(p.lower) : close
    const high = p.upper != null ? Number(p.upper) : close

    if (!Number.isFinite(close)) continue
    
    line.push({ time: p.tanggal, value: close })
    bounds.push({ 
      time: p.tanggal, 
      open: high,
      high: high,
      low: low,
      close: low
    })
  }

  return { line, bounds }
}

function rangkai(dates, nilai) {
  const out = []
  let sebelumnya = null
  for (let i = 0; i < (nilai?.length || 0); i++) {
    const v = nilai[i]
    const t = dates[i]
    if (v == null || !t) continue
    const time = String(t).slice(0, 10)
    if (time === sebelumnya) continue
    sebelumnya = time
    out.push({ time, value: Number(v) })
  }
  return out
}

const dataAktual = computed(() => toChartData(props.rows))
const dataProyeksi = computed(() => {
  const hargaAcuan = dataAktual.value.length ? dataAktual.value[dataAktual.value.length - 1].close : null
  return toForecastData(props.points, hargaAcuan)
})
const titikRsi = computed(() => rangkai(props.rsi?.dates || [], props.rsi?.rsi || []))
const titikMacd = computed(() => rangkai(props.macd?.dates || [], props.macd?.macdLine || []))
const titikSignal = computed(() => rangkai(props.macd?.dates || [], props.macd?.signalLine || []))
const titikHist = computed(() => {
  const w = warna()
  const src = rangkai(props.macd?.dates || [], props.macd?.histogram || [])
  return src.map((d, i) => {
    const menguat = i === 0 ? true : Math.abs(d.value) >= Math.abs(src[i - 1].value)
    const dasar = d.value >= 0 ? w.naik : w.turun
    return { ...d, color: menguat ? dasar : pudar(dasar, 0.4) }
  })
})

function updateLayout() {
  if (!chart.value) return

  let parts = 0
  let currentTop = 0

  if (showHist.value || showForecast.value) parts += 2
  if (showRsi.value) parts += 1
  if (showMacd.value) parts += 1

  const partSize = parts > 0 ? 1 / parts : 1

  if (showHist.value || showForecast.value) {
    chart.value.priceScale('right').applyOptions({
      visible: true,
      scaleMargins: { top: 0.05, bottom: Math.max(0.05, 1 - (2 * partSize) + 0.05) }
    })
    currentTop += 2 * partSize
  } else {
    chart.value.priceScale('right').applyOptions({ visible: false })
  }

  if (showRsi.value) {
    chart.value.priceScale('rsi').applyOptions({
      visible: true,
      scaleMargins: { top: Math.min(0.95, currentTop + 0.05), bottom: Math.max(0.05, 1 - (currentTop + partSize) + 0.05) }
    })
    currentTop += partSize
  } else {
    chart.value.priceScale('rsi').applyOptions({ visible: false })
  }

  if (showMacd.value) {
    chart.value.priceScale('macd').applyOptions({
      visible: true,
      scaleMargins: { top: Math.min(0.95, currentTop + 0.05), bottom: 0.05 }
    })
  } else {
    chart.value.priceScale('macd').applyOptions({ visible: false })
  }

  // Hide/show series
  if (seriesAktual.value) seriesAktual.value.applyOptions({ visible: showHist.value })
  if (seriesForecastBounds.value) seriesForecastBounds.value.applyOptions({ visible: showForecast.value })
  if (seriesForecastLine.value) seriesForecastLine.value.applyOptions({ visible: showForecast.value })
  if (seriesRsi.value) seriesRsi.value.applyOptions({ visible: showRsi.value })
  if (seriesHist.value) seriesHist.value.applyOptions({ visible: showMacd.value })
  if (seriesMacd.value) seriesMacd.value.applyOptions({ visible: showMacd.value })
  if (seriesSignal.value) seriesSignal.value.applyOptions({ visible: showMacd.value })
}

function render() {
  if (!seriesAktual.value) return

  seriesAktual.value.setData(dataAktual.value)
  seriesForecastBounds.value.setData(dataProyeksi.value.bounds)
  seriesForecastLine.value.setData(dataProyeksi.value.line)
  seriesRsi.value.setData(titikRsi.value)
  seriesHist.value.setData(titikHist.value)
  seriesMacd.value.setData(titikMacd.value)
  seriesSignal.value.setData(titikSignal.value)

  updateLayout()
  updateLastLegend()
  applyTimeframe()
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

const legendData = ref(null)

function updateLastLegend() {
  const data = {}
  if (dataAktual.value.length) data.aktual = dataAktual.value[dataAktual.value.length - 1]
  if (dataProyeksi.value.line.length) data.forecast = dataProyeksi.value.line[dataProyeksi.value.line.length - 1].value
  if (titikRsi.value.length) data.rsi = titikRsi.value[titikRsi.value.length - 1].value
  
  if (titikMacd.value.length) {
    data.macd = {
      macd: titikMacd.value[titikMacd.value.length - 1].value,
      signal: titikSignal.value.length ? titikSignal.value[titikSignal.value.length - 1].value : undefined,
      hist: titikHist.value.length ? titikHist.value[titikHist.value.length - 1].value : undefined,
    }
  }
  
  legendData.value = data
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

  // Add all series
  seriesAktual.value = chart.value.addSeries(CandlestickSeries, temaAktual())
  seriesForecastBounds.value = chart.value.addSeries(CandlestickSeries, {
    upColor: pudar(w.proyeksi, 0.4),
    downColor: pudar(w.proyeksi, 0.4),
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
  
  seriesRsi.value = chart.value.addSeries(LineSeries, {
    color: w.rsi,
    lineWidth: 2,
    priceScaleId: 'rsi',
    priceLineVisible: false,
    lastValueVisible: false,
    autoscaleInfoProvider: () => ({ priceRange: { minValue: 0, maxValue: 100 } }),
  })

  seriesHist.value = chart.value.addSeries(HistogramSeries, {
    priceScaleId: 'macd',
    priceLineVisible: false,
    lastValueVisible: false,
  })
  seriesMacd.value = chart.value.addSeries(LineSeries, {
    color: w.macd,
    lineWidth: 2,
    priceScaleId: 'macd',
    priceLineVisible: false,
    lastValueVisible: false,
  })
  seriesSignal.value = chart.value.addSeries(LineSeries, {
    color: w.signal,
    lineWidth: 2,
    lineStyle: LineStyle.Dashed,
    priceScaleId: 'macd',
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

    const fcLine = param.seriesData.get(seriesForecastLine.value)
    if (fcLine) data.forecast = fcLine.value

    const rsi = param.seriesData.get(seriesRsi.value)
    if (rsi) data.rsi = rsi.value

    const macd = param.seriesData.get(seriesMacd.value)
    const sig = param.seriesData.get(seriesSignal.value)
    const hist = param.seriesData.get(seriesHist.value)
    if (macd) {
      data.macd = { macd: macd.value, signal: sig?.value, hist: hist?.value }
    }

    legendData.value = data
  })

  render()
})

onBeforeUnmount(() => {
  chart.value?.remove()
  chart.value = null
})

watch(() => [props.rows, props.points, props.rsi, props.macd], render, { deep: false })
watch(isDark, () => {
  chart.value?.applyOptions(tema())
  seriesAktual.value?.applyOptions(temaAktual())
  
  const w = warna()
  seriesForecastBounds.value?.applyOptions({ upColor: pudar(w.proyeksi, 0.4), downColor: pudar(w.proyeksi, 0.4) })
  seriesForecastLine.value?.applyOptions({ color: w.proyeksi })
  
  seriesRsi.value?.applyOptions({ color: w.rsi })
  seriesMacd.value?.applyOptions({ color: w.macd })
  seriesSignal.value?.applyOptions({ color: w.signal })
  render()
})

watch([showHist, showForecast, showRsi, showMacd], updateLayout)
watch(() => props.timeframe, applyTimeframe)
</script>

<template>
  <div class="flex flex-col gap-2 w-full">
    <!-- Legenda (Horizontal Bar) -->
    <div class="flex flex-wrap items-center gap-x-6 gap-y-1 min-h-[24px]">
      <div v-if="legendData?.aktual && showHist" class="text-[12px] font-mono flex items-center">
        <span class="font-bold mr-1.5 text-foreground">O</span><span class="mr-3">{{ formatNumber(legendData.aktual.open) }}</span>
        <span class="font-bold mr-1.5 text-foreground">H</span><span class="mr-3">{{ formatNumber(legendData.aktual.high) }}</span>
        <span class="font-bold mr-1.5 text-foreground">L</span><span class="mr-3">{{ formatNumber(legendData.aktual.low) }}</span>
        <span class="font-bold mr-1.5 text-foreground">C</span><span>{{ formatNumber(legendData.aktual.close) }}</span>
      </div>
      
      <div v-if="legendData?.forecast && showForecast" class="text-[12px] font-mono text-[var(--warning)] flex items-center">
        <span class="font-bold mr-1.5">Forecast</span><span>{{ formatNumber(legendData.forecast) }}</span>
      </div>
      
      <div v-if="legendData?.rsi && showRsi" class="text-[12px] font-mono text-[var(--chart-2)] flex items-center">
        <span class="font-bold mr-1.5">RSI(14)</span><span>{{ legendData.rsi.toFixed(2) }}</span>
      </div>

      <div v-if="legendData?.macd && showMacd" class="text-[12px] font-mono text-[var(--info)] flex items-center">
        <span class="font-bold mr-1.5">MACD</span><span class="mr-3">{{ legendData.macd.macd?.toFixed(2) }}</span>
        <span class="font-bold mr-1.5 text-[var(--warning)]">Sig</span><span class="mr-3 text-[var(--warning)]">{{ legendData.macd.signal?.toFixed(2) }}</span>
        <span class="font-bold mr-1.5 text-foreground">Hist</span><span class="text-foreground">{{ legendData.macd.hist?.toFixed(2) }}</span>
      </div>
    </div>

    <div class="relative w-full" :style="{ height: `${height}px` }">

      <div
        ref="container"
        data-lenis-prevent
        class="h-full w-full"
        role="img"
      />
    </div>
    
    <!-- Toggles -->
    <div class="flex flex-col xl:flex-row xl:items-center gap-3 border-t-[0.5px] border-border pt-4 mt-2 w-full">
      <span class="text-base font-medium text-muted-foreground shrink-0">Tampilkan:</span>

      <div class="flex flex-wrap w-full items-center rounded-lg border-[0.5px] border-border bg-muted/40 p-1 shadow-inner flex-1 gap-1">
        <button
          type="button"
          class="flex-1 flex items-center justify-center gap-1.5 rounded-md px-2 py-1.5 text-sm font-medium transition-all duration-200 cursor-pointer min-w-[130px] whitespace-nowrap"
          :class="showHist ? 'bg-background text-foreground shadow-sm ring-1 ring-border/50' : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'"
          @click="showHist = !showHist"
        >
          <div class="h-2 w-2 rounded-full shrink-0" :class="showHist ? 'bg-primary' : 'bg-muted'" />
          Historical
        </button>
        <button
          type="button"
          class="flex-1 flex items-center justify-center gap-1.5 rounded-md px-2 py-1.5 text-sm font-medium transition-all duration-200 cursor-pointer min-w-[130px] whitespace-nowrap"
          :class="showForecast ? 'bg-background text-foreground shadow-sm ring-1 ring-border/50' : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'"
          @click="showForecast = !showForecast"
        >
          <div class="h-2 w-2 rounded-full shrink-0" :class="showForecast ? 'bg-[var(--warning)]' : 'bg-muted'" />
          Forecast
        </button>
        <button
          type="button"
          class="flex-1 flex items-center justify-center gap-1.5 rounded-md px-2 py-1.5 text-sm font-medium transition-all duration-200 cursor-pointer min-w-[130px] whitespace-nowrap"
          :class="showRsi ? 'bg-background text-foreground shadow-sm ring-1 ring-border/50' : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'"
          @click="showRsi = !showRsi"
        >
          <div class="h-2 w-2 rounded-full shrink-0" :class="showRsi ? 'bg-[var(--chart-2)]' : 'bg-muted'" />
          RSI (14)
        </button>
        <button
          type="button"
          class="flex-1 flex items-center justify-center gap-1.5 rounded-md px-2 py-1.5 text-sm font-medium transition-all duration-200 cursor-pointer min-w-[130px] whitespace-nowrap"
          :class="showMacd ? 'bg-background text-foreground shadow-sm ring-1 ring-border/50' : 'text-muted-foreground hover:bg-muted/60 hover:text-foreground'"
          @click="showMacd = !showMacd"
        >
          <div class="h-2 w-2 rounded-full shrink-0" :class="showMacd ? 'bg-[var(--info)]' : 'bg-muted'" />
          MACD (12, 26, 9)
        </button>
      </div>
    </div>
  </div>
</template>
