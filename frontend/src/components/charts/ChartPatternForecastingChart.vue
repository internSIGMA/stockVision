<script setup>
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import {
  CandlestickSeries,
  ColorType,
  createChart,
  createSeriesMarkers,
  HistogramSeries,
  LineSeries,
  LineStyle,
  CrosshairMode,
} from 'lightweight-charts'
import { useTheme } from '@/composables/useTheme'
import { formatDate, formatNumber, formatCompact } from '@/utils/format'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  pattern: { type: Object, default: null },
  height: { type: Number, default: 460 },
  timeframe: { type: String, default: '6M' },
  showGeometry: { type: Boolean, default: true },
})

const emit = defineEmits(['update:showGeometry', 'toggle-layer'])

const container = ref(null)
const { isDark } = useTheme()

// Chart & Series references
const chart = shallowRef(null)
const seriesAktual = shallowRef(null)
const seriesVolume = shallowRef(null)
const seriesForecastBounds = shallowRef(null)
const seriesForecastLine = shallowRef(null)
const seriesSma50 = shallowRef(null)
const seriesSma200 = shallowRef(null)
const geometrySeriesList = shallowRef([])
const markersPlugin = shallowRef(null)
const fibonacciPriceLines = shallowRef([])

// 6 Toggle Layers
const showHist = ref(true)
const showForecast = ref(true)
const showVolume = ref(true)
const showFibonacci = ref(true)
const showSma = ref(true)
const showGeometryLocal = ref(props.showGeometry)

watch(() => props.showGeometry, (val) => {
  if (val !== showGeometryLocal.value) {
    showGeometryLocal.value = val
  }
})

function toggleGeometry() {
  showGeometryLocal.value = !showGeometryLocal.value
  emit('update:showGeometry', showGeometryLocal.value)
}

function warna() {
  const style = getComputedStyle(document.documentElement)
  const ambil = (nama) => style.getPropertyValue(nama).trim()
  return {
    card: ambil('--card') || '#18181b',
    up: ambil('--up') || '#10B981',
    down: ambil('--down') || '#EF4444',
    proyeksi: '#8B5CF6',
    proyeksiLight: '#A78BFA',
    grid: ambil('--border') || 'rgba(255, 255, 255, 0.08)',
    text: ambil('--muted-foreground') || '#94a3b8',
    sma50: '#3B82F6',
    sma200: '#F59E0B',
    fiboTp1: '#10B981',
    fiboTp2: '#06B6D4',
    fiboTp3: '#EAB308',
    fiboBreakout: '#3B82F6',
    fiboStopLoss: '#EF4444',
    fiboSupport: '#14B8A6',
    fiboResistance: '#F43F5E',
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
    grid: {
      vertLines: { color: grid },
      horzLines: { color: grid },
    },
    rightPriceScale: {
      borderColor: grid,
      scaleMargins: { top: 0.08, bottom: 0.2 },
    },
    timeScale: {
      borderColor: grid,
      maxBarSpacing: 1e4,
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

// Transform OHLC data
function toChartData(rows) {
  return (rows || [])
    .map((r) => ({
      time: String(r.tanggal).slice(0, 10),
      open: Number(r.open),
      high: Number(r.high),
      low: Number(r.low),
      close: Number(r.close),
      volume: Number(r.volume || 0),
    }))
    .filter((d) => !Number.isNaN(d.open) && !Number.isNaN(d.close))
    .sort((a, b) => a.time.localeCompare(b.time))
}

// Calculate Simple Moving Average
function calculateSMA(data, period) {
  const results = []
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) continue
    let sum = 0
    for (let j = 0; j < period; j++) {
      sum += data[i - j].close
    }
    results.push({
      time: data[i].time,
      value: sum / period,
    })
  }
  return results
}

// Transform volume histogram data
function toVolumeData(candles) {
  const w = warna()
  return candles.map((c) => ({
    time: c.time,
    value: c.volume,
    color: c.close >= c.open ? pudar(w.up, 0.45) : pudar(w.down, 0.45),
  }))
}

// Helper to normalize any date format to YYYY-MM-DD
function normalizeDate(raw) {
  if (!raw) return null
  if (typeof raw === 'string') {
    const m = raw.match(/^(\d{4})-(\d{2})-(\d{2})/)
    if (m) return `${m[1]}-${m[2]}-${m[3]}`
  }
  try {
    const dt = new Date(raw)
    if (!isNaN(dt.getTime())) return dt.toISOString().slice(0, 10)
  } catch {}
  return String(raw).slice(0, 10)
}

function snapToCandleDate(t, candles) {
  if (!candles || !candles.length || !t) return t
  const candleDates = new Set(candles.map((c) => c.time))
  if (candleDates.has(t)) return t

  const targetTs = new Date(t).getTime()
  if (isNaN(targetTs)) return t

  let closest = candles[0].time
  let minDiff = Math.abs(new Date(candles[0].time).getTime() - targetTs)
  for (let i = 1; i < candles.length; i++) {
    const diff = Math.abs(new Date(candles[i].time).getTime() - targetTs)
    if (diff < minDiff) {
      minDiff = diff
      closest = candles[i].time
    }
  }
  return closest
}

// Transform forecast trajectory & confidence bounds
function toForecastData(pattern, lastCandle) {
  const ft = pattern?.forecast_trajectory
  if (!ft || !Array.isArray(ft.dates) || !Array.isArray(ft.pathway) || !ft.pathway.length) {
    return { line: [], bounds: [] }
  }

  const dates = ft.dates
  const pathway = ft.pathway
  const upper = ft.upper_bound || []
  const lower = ft.lower_bound || []

  const line = []
  const bounds = []

  for (let i = 0; i < dates.length; i++) {
    const t = normalizeDate(dates[i])
    const val = Number(pathway[i])
    if (!t || Number.isNaN(val)) continue

    const hi = upper[i] != null ? Number(upper[i]) : val
    const lo = lower[i] != null ? Number(lower[i]) : val

    line.push({ time: t, value: val })
    bounds.push({
      time: t,
      open: hi,
      high: hi,
      low: lo,
      close: lo,
    })
  }

  // Connect smoothly from the last historical candle if dates don't already overlap
  if (lastCandle && line.length && line[0].time > lastCandle.time) {
    line.unshift({ time: lastCandle.time, value: lastCandle.close })
    bounds.unshift({
      time: lastCandle.time,
      open: lastCandle.close,
      high: lastCandle.close,
      low: lastCandle.close,
      close: lastCandle.close,
    })
  }

  return { line, bounds }
}

// Transform key points into chart markers
function toKeyPointMarkers(pattern, candles) {
  const kps = pattern?.key_points
  if (!Array.isArray(kps) || !kps.length || !candles || !candles.length) return []

  const isBullish = pattern?.directional_bias?.toLowerCase()?.includes('bullish') ?? true
  const markersMap = new Map()

  for (const kp of kps) {
    let t = normalizeDate(kp.date)
    if (!t) continue

    t = snapToCandleDate(t, candles)

    const name = kp.name || 'Key Point'
    const isValley =
      name.toLowerCase().includes('bottom') ||
      name.toLowerCase().includes('trough') ||
      name.toLowerCase().includes('low') ||
      name.toLowerCase().includes('support')
    const isPeak =
      name.toLowerCase().includes('top') ||
      name.toLowerCase().includes('peak') ||
      name.toLowerCase().includes('head') ||
      name.toLowerCase().includes('high') ||
      name.toLowerCase().includes('shoulder') ||
      name.toLowerCase().includes('resistance')

    markersMap.set(t, {
      time: t,
      position: isPeak ? 'aboveBar' : isValley ? 'belowBar' : (isBullish ? 'belowBar' : 'aboveBar'),
      color: '#FACC15', // Bright yellow diamond/circle marker as shown in reference screenshot
      shape: isPeak ? 'arrowDown' : isValley ? 'arrowUp' : 'circle',
      text: name,
      size: 2,
    })
  }

  // Add breakout marker if breakout_date exists
  if (pattern?.timeline?.breakout_date) {
    let bDate = normalizeDate(pattern.timeline.breakout_date)
    if (bDate) {
      bDate = snapToCandleDate(bDate, candles)
      markersMap.set(bDate, {
        time: bDate,
        position: isBullish ? 'aboveBar' : 'belowBar',
        color: '#3B82F6',
        shape: isBullish ? 'arrowUp' : 'arrowDown',
        text: '⚡ Breakout',
        size: 2,
      })
    }
  }

  return Array.from(markersMap.values()).sort((a, b) => a.time.localeCompare(b.time))
}

const dataAktual = computed(() => toChartData(props.rows))
const lastCandle = computed(() => (dataAktual.value.length ? dataAktual.value[dataAktual.value.length - 1] : null))
const dataVolume = computed(() => toVolumeData(dataAktual.value))
const dataSma50 = computed(() => calculateSMA(dataAktual.value, 50))
const dataSma200 = computed(() => calculateSMA(dataAktual.value, 200))
const dataProyeksi = computed(() => toForecastData(props.pattern, lastCandle.value))
const dataMarkers = computed(() => toKeyPointMarkers(props.pattern, dataAktual.value))

// Update Fibonacci Price Lines
function updateFibonacciLines() {
  if (!seriesAktual.value) return

  // Remove existing price lines
  for (const pl of fibonacciPriceLines.value) {
    try {
      seriesAktual.value.removePriceLine(pl)
    } catch {
      // ignore
    }
  }
  fibonacciPriceLines.value = []

  if (!showFibonacci.value || !props.pattern) return

  const p = props.pattern.pricing || {}
  const w = warna()

  const linesToCreate = [
    { price: p.tp1_measured_move, title: '🎯 TP1 Measured Move', color: w.fiboTp1, style: LineStyle.Solid },
    { price: p.tp2_fibo_127, title: '🎯 TP2 Fibo 127.2%', color: w.fiboTp2, style: LineStyle.Dashed },
    { price: p.tp3_fibo_161_golden, title: '👑 TP3 Golden 161.8%', color: w.fiboTp3, style: LineStyle.Dashed },
    { price: p.breakout_level, title: '⚡ Breakout Level', color: w.fiboBreakout, style: LineStyle.LargeDashed },
    { price: p.stop_loss, title: '🛡️ Stop Loss', color: w.fiboStopLoss, style: LineStyle.Solid },
    { price: p.fibo_support, title: 'Fibo Support', color: w.fiboSupport, style: LineStyle.Dotted },
    { price: p.fibo_resistance, title: 'Fibo Resistance', color: w.fiboResistance, style: LineStyle.Dotted },
  ]

  for (const item of linesToCreate) {
    if (item.price != null && Number.isFinite(Number(item.price)) && Number(item.price) > 0) {
      try {
        const pl = seriesAktual.value.createPriceLine({
          price: Number(item.price),
          color: item.color,
          lineWidth: 1,
          lineStyle: item.style,
          axisLabelVisible: true,
          title: item.title,
        })
        fibonacciPriceLines.value.push(pl)
      } catch {
        // ignore
      }
    }
  }
}

// Update Geometry Lines (Neckline, Trendlines, Formations)
function updateGeometryLines() {
  if (!chart.value) return

  // Remove existing geometry line series
  for (const s of geometrySeriesList.value) {
    try {
      chart.value.removeSeries(s)
    } catch {
      // ignore
    }
  }
  geometrySeriesList.value = []

  if (!showGeometryLocal.value || !props.pattern) return

  const lines = props.pattern.geometry_lines || []
  if (!Array.isArray(lines) || !lines.length) return

  for (const g of lines) {
    const xs = g.x || []
    const ys = g.y || []
    if (xs.length < 2 || ys.length < 2) continue

    const lineData = []
    const seenTimes = new Set()
    for (let i = 0; i < Math.min(xs.length, ys.length); i++) {
      let t = normalizeDate(xs[i])
      const v = Number(ys[i])
      if (t && Number.isFinite(v)) {
        t = snapToCandleDate(t, dataAktual.value)
        if (!seenTimes.has(t)) {
          seenTimes.add(t)
          lineData.push({ time: t, value: v })
        }
      }
    }

    if (lineData.length >= 2) {
      lineData.sort((a, b) => a.time.localeCompare(b.time))

      const style = g.style === 'solid' ? LineStyle.Solid : LineStyle.Dashed
      const s = chart.value.addSeries(LineSeries, {
        color: g.color || '#3B82F6',
        lineWidth: 2,
        lineStyle: style,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      })
      s.setData(lineData)
      geometrySeriesList.value.push(s)
    }
  }
}

// Update Key Point Markers
function updateMarkers() {
  if (!markersPlugin.value) return
  if (showGeometryLocal.value && dataMarkers.value.length) {
    markersPlugin.value.setMarkers(dataMarkers.value)
  } else {
    markersPlugin.value.setMarkers([])
  }
}

function updateLayout() {
  if (!chart.value) return

  if (seriesAktual.value) seriesAktual.value.applyOptions({ visible: showHist.value })
  if (seriesVolume.value) seriesVolume.value.applyOptions({ visible: showVolume.value })
  if (seriesForecastBounds.value) seriesForecastBounds.value.applyOptions({ visible: showForecast.value })
  if (seriesForecastLine.value) seriesForecastLine.value.applyOptions({ visible: showForecast.value })
  if (seriesSma50.value) seriesSma50.value.applyOptions({ visible: showSma.value })
  if (seriesSma200.value) seriesSma200.value.applyOptions({ visible: showSma.value })

  for (const s of geometrySeriesList.value) {
    s.applyOptions({ visible: showGeometryLocal.value })
  }

  updateFibonacciLines()
  updateMarkers()
}

function render() {
  if (!seriesAktual.value) return

  seriesAktual.value.setData(dataAktual.value)
  if (seriesVolume.value) seriesVolume.value.setData(dataVolume.value)
  if (seriesSma50.value) seriesSma50.value.setData(dataSma50.value)
  if (seriesSma200.value) seriesSma200.value.setData(dataSma200.value)
  if (seriesForecastBounds.value) seriesForecastBounds.value.setData(dataProyeksi.value.bounds)
  if (seriesForecastLine.value) seriesForecastLine.value.setData(dataProyeksi.value.line)

  updateGeometryLines()
  updateFibonacciLines()
  updateMarkers()
  updateLayout()
  updateLastLegend()
  applyTimeframe()
}

function applyTimeframe() {
  if (!chart.value || !dataAktual.value.length) return

  if (props.timeframe === 'ALL') {
    chart.value.timeScale().fitContent()
    return
  }

  let lastPointTime = dataAktual.value[dataAktual.value.length - 1].time
  if (dataProyeksi.value.line.length) {
    lastPointTime = dataProyeksi.value.line[dataProyeksi.value.line.length - 1].time
  }

  const lastHist = new Date(dataAktual.value[dataAktual.value.length - 1].time)
  let fromDate = new Date(lastHist)

  switch (props.timeframe) {
    case '1D':
      fromDate.setDate(fromDate.getDate() - 1)
      break
    case '5D':
      fromDate.setDate(fromDate.getDate() - 5)
      break
    case '1M':
      fromDate.setMonth(fromDate.getMonth() - 1)
      break
    case '3M':
      fromDate.setMonth(fromDate.getMonth() - 3)
      break
    case '6M':
      fromDate.setMonth(fromDate.getMonth() - 6)
      break
    case '1Y':
      fromDate.setFullYear(fromDate.getFullYear() - 1)
      break
    case 'YTD':
      fromDate = new Date(lastHist.getFullYear(), 0, 1)
      break
  }

  chart.value.timeScale().setVisibleRange({
    from: fromDate.toISOString().split('T')[0],
    to: lastPointTime,
  })
}

// Interactive Legend
const legendData = ref(null)

function updateLastLegend() {
  const data = {}
  if (dataAktual.value.length) {
    const act = dataAktual.value[dataAktual.value.length - 1]
    data.aktual = act
    data.volume = act.volume
  }
  if (dataProyeksi.value.line.length) {
    data.forecast = dataProyeksi.value.line[dataProyeksi.value.line.length - 1].value
  }
  if (dataSma50.value.length) {
    data.sma50 = dataSma50.value[dataSma50.value.length - 1].value
  }
  if (dataSma200.value.length) {
    data.sma200 = dataSma200.value[dataSma200.value.length - 1].value
  }
  if (props.pattern) {
    data.patternName = props.pattern.pattern_name
    data.bias = props.pattern.directional_bias
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

  // 1. Candlestick Series (Historical OHLC)
  seriesAktual.value = chart.value.addSeries(CandlestickSeries, temaAktual())

  // Markers Plugin for Key Points
  markersPlugin.value = createSeriesMarkers(seriesAktual.value, [])

  // 2. Volume Histogram Series (Independent scale at bottom)
  seriesVolume.value = chart.value.addSeries(HistogramSeries, {
    priceFormat: { type: 'volume' },
    priceScaleId: 'volume',
    priceLineVisible: false,
    lastValueVisible: false,
  })
  chart.value.priceScale('volume').applyOptions({
    scaleMargins: { top: 0.82, bottom: 0 },
    visible: false,
  })

  // 3. SMA 50 & SMA 200 Series
  seriesSma50.value = chart.value.addSeries(LineSeries, {
    color: w.sma50,
    lineWidth: 1.5,
    priceLineVisible: false,
    lastValueVisible: false,
    crosshairMarkerVisible: true,
    title: 'SMA 50',
  })

  seriesSma200.value = chart.value.addSeries(LineSeries, {
    color: w.sma200,
    lineWidth: 1.5,
    priceLineVisible: false,
    lastValueVisible: false,
    crosshairMarkerVisible: true,
    title: 'SMA 200',
  })

  // 4. Forecast Bounds & Pathway Line
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
    lineStyle: LineStyle.Dashed,
    pointMarkersVisible: true,
    pointMarkersRadius: 3,
    priceLineVisible: false,
    lastValueVisible: true,
    title: 'Trajectory',
  })

  // Crosshair move subscription
  chart.value.subscribeCrosshairMove((param) => {
    if (!param.time || param.point.x < 0 || param.point.y < 0) {
      updateLastLegend()
      return
    }

    const data = {}
    const act = param.seriesData.get(seriesAktual.value)
    if (act) {
      data.aktual = act
      const vol = param.seriesData.get(seriesVolume.value)
      if (vol) data.volume = vol.value
    }

    const s50 = param.seriesData.get(seriesSma50.value)
    if (s50) data.sma50 = s50.value

    const s200 = param.seriesData.get(seriesSma200.value)
    if (s200) data.sma200 = s200.value

    const fcLine = param.seriesData.get(seriesForecastLine.value)
    if (fcLine) data.forecast = fcLine.value

    if (props.pattern) {
      data.patternName = props.pattern.pattern_name
      data.bias = props.pattern.directional_bias
    }

    legendData.value = data
  })

  render()
})

onBeforeUnmount(() => {
  chart.value?.remove()
  chart.value = null
})

watch(() => [props.rows, props.pattern], render, { deep: true })

watch(showGeometryLocal, () => {
  updateGeometryLines()
  updateMarkers()
  updateLayout()
})

watch(isDark, () => {
  chart.value?.applyOptions(tema())
  seriesAktual.value?.applyOptions(temaAktual())

  const w = warna()
  seriesForecastBounds.value?.applyOptions({
    upColor: pudar(w.proyeksi, 0.35),
    downColor: pudar(w.proyeksi, 0.35),
  })
  seriesForecastLine.value?.applyOptions({ color: w.proyeksi })
  seriesSma50.value?.applyOptions({ color: w.sma50 })
  seriesSma200.value?.applyOptions({ color: w.sma200 })

  updateFibonacciLines()
  updateGeometryLines()
})

watch([showHist, showForecast, showVolume, showFibonacci, showSma, showGeometryLocal], updateLayout)
watch(() => props.timeframe, applyTimeframe)
</script>

<template>
  <div class="flex flex-col gap-2 w-full">
    <!-- Interactive Header Legend -->
    <div class="flex flex-wrap items-center justify-between gap-x-6 gap-y-1.5 min-h-[26px]">
      <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] font-mono">
        <!-- Candlestick OHLC Values -->
        <div v-if="legendData?.aktual && showHist" class="flex items-center">
          <span class="font-bold mr-1 text-muted-foreground">O</span>
          <span class="mr-2.5 text-foreground">{{ formatNumber(legendData.aktual.open) }}</span>
          <span class="font-bold mr-1 text-muted-foreground">H</span>
          <span class="mr-2.5 text-foreground">{{ formatNumber(legendData.aktual.high) }}</span>
          <span class="font-bold mr-1 text-muted-foreground">L</span>
          <span class="mr-2.5 text-foreground">{{ formatNumber(legendData.aktual.low) }}</span>
          <span class="font-bold mr-1 text-muted-foreground">C</span>
          <span class="mr-2.5 font-bold" :class="legendData.aktual.close >= legendData.aktual.open ? 'text-[var(--up)]' : 'text-[var(--down)]'">
            {{ formatNumber(legendData.aktual.close) }}
          </span>
        </div>

        <!-- Volume Value -->
        <div v-if="legendData?.volume != null && showVolume" class="flex items-center text-muted-foreground">
          <span class="font-bold mr-1 text-foreground">Vol</span>
          <span class="tabular text-foreground">{{ formatCompact(legendData.volume) }}</span>
        </div>

        <!-- SMA 50 Value -->
        <div v-if="legendData?.sma50 != null && showSma" class="flex items-center text-[#3B82F6]">
          <span class="font-bold mr-1">SMA50</span>
          <span class="tabular">{{ formatNumber(legendData.sma50) }}</span>
        </div>

        <!-- SMA 200 Value -->
        <div v-if="legendData?.sma200 != null && showSma" class="flex items-center text-[#F59E0B]">
          <span class="font-bold mr-1">SMA200</span>
          <span class="tabular">{{ formatNumber(legendData.sma200) }}</span>
        </div>

        <!-- Trajectory Value -->
        <div v-if="legendData?.forecast != null && showForecast" class="flex items-center text-[#8B5CF6]">
          <span class="font-bold mr-1">📐 Trajectory</span>
          <span class="tabular font-semibold">{{ formatNumber(legendData.forecast) }}</span>
        </div>
      </div>

      <!-- Active Pattern Tag -->
      <div v-if="props.pattern" class="flex items-center gap-1.5 text-[11px] font-sans">
        <span
          class="rounded-md px-2 py-0.5 font-medium text-[10.5px]"
          :class="
            props.pattern.directional_bias?.toLowerCase()?.includes('bullish')
              ? 'bg-[var(--up)]/15 text-[var(--up)] border border-[var(--up)]/30'
              : 'bg-[var(--down)]/15 text-[var(--down)] border border-[var(--down)]/30'
          "
        >
          {{ props.pattern.directional_bias }}
        </span>
        <span class="font-semibold text-foreground">{{ props.pattern.pattern_name }}</span>
      </div>
    </div>

    <!-- Visual Chart Layer Indicators Legend (Sesuai Referensi Gambar) -->
    <div v-if="props.pattern" class="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-[10.5px] text-muted-foreground border-t border-border/40 pt-1.5">
      <!-- Price Candle Indicator -->
      <div class="flex items-center gap-1.5">
        <div class="flex h-3 w-3 items-center justify-center rounded border border-[var(--up)] bg-[var(--down)]/60 text-[8px] font-bold text-white">
          <span class="h-2 w-0.5 bg-[var(--up)]"></span>
        </div>
        <span class="text-foreground">Price</span>
      </div>

      <!-- Geometry Lines Indicators (Neckline, Support, Resistance) -->
      <div
        v-for="(g, idx) in props.pattern.geometry_lines || []"
        :key="idx"
        class="flex items-center gap-1.5"
        :class="{ 'opacity-40': !showGeometryLocal }"
      >
        <span
          class="h-0.5 w-4 rounded"
          :class="g.style === 'solid' ? 'border-none' : 'border-b-2 border-dashed'"
          :style="{ backgroundColor: g.style === 'solid' ? g.color || '#3B82F6' : 'transparent', borderColor: g.color || '#3B82F6' }"
        />
        <span class="text-foreground">{{ g.name }}</span>
      </div>

      <!-- Stop Loss Indicator -->
      <div v-if="props.pattern.pricing?.stop_loss" class="flex items-center gap-1.5">
        <span class="h-2 w-2 rounded-full bg-[var(--down)]" />
        <span class="text-[var(--down)] font-medium">Stop Loss: {{ formatNumber(props.pattern.pricing.stop_loss) }}</span>
      </div>

      <!-- Forecast Trajectory & Confidence Cone Indicator -->
      <div v-if="props.pattern.forecast_trajectory?.pathway?.length" class="flex items-center gap-1.5" :class="{ 'opacity-40': !showForecast }">
        <span class="h-0.5 w-4 border-b-2 border-dashed border-[#8B5CF6]" />
        <span class="text-[#8B5CF6]">Forecast Path &amp; Cone</span>
      </div>

      <!-- Keypoints Label Indicator -->
      <div v-if="props.pattern.key_points?.length" class="flex items-center gap-1.5" :class="{ 'opacity-40': !showGeometryLocal }">
        <span class="h-2 w-2 rounded-full bg-[#FACC15]" />
        <span class="text-[#FACC15]">Key Points</span>
      </div>
    </div>

    <!-- Chart Container -->
    <div class="relative w-full" :style="{ height: `${height}px` }">
      <div
        ref="container"
        data-lenis-prevent
        class="h-full w-full"
        role="img"
      />
    </div>

    <!-- 6 Layer Toggle Buttons -->
    <div class="flex flex-wrap items-center gap-2 border-t-[0.5px] border-border pt-3 mt-1">
      <span class="text-xs font-medium text-muted-foreground mr-1">Tampilkan:</span>

      <!-- 1. Historical -->
      <button
        type="button"
        class="flex items-center gap-1.5 rounded-full border-[0.5px] px-2.5 py-1 text-[11px] transition-colors cursor-pointer"
        :class="showHist ? 'border-primary bg-primary/10 text-primary font-medium' : 'border-border bg-transparent text-muted-foreground hover:bg-card-hover'"
        @click="showHist = !showHist"
      >
        <div class="h-2 w-2 rounded-full" :class="showHist ? 'bg-primary' : 'bg-muted'" />
        Historical
      </button>

      <!-- 2. Forecast -->
      <button
        type="button"
        class="flex items-center gap-1.5 rounded-full border-[0.5px] px-2.5 py-1 text-[11px] transition-colors cursor-pointer"
        :class="showForecast ? 'border-[#8B5CF6] bg-[#8B5CF6]/10 text-[#8B5CF6] font-medium' : 'border-border bg-transparent text-muted-foreground hover:bg-card-hover'"
        @click="showForecast = !showForecast"
      >
        <div class="h-2 w-2 rounded-full" :class="showForecast ? 'bg-[#8B5CF6]' : 'bg-muted'" />
        Forecast Trajectory
      </button>

      <!-- 3. Volume -->
      <button
        type="button"
        class="flex items-center gap-1.5 rounded-full border-[0.5px] px-2.5 py-1 text-[11px] transition-colors cursor-pointer"
        :class="showVolume ? 'border-foreground/40 bg-foreground/10 text-foreground font-medium' : 'border-border bg-transparent text-muted-foreground hover:bg-card-hover'"
        @click="showVolume = !showVolume"
      >
        <div class="h-2 w-2 rounded-full" :class="showVolume ? 'bg-foreground' : 'bg-muted'" />
        Volume
      </button>

      <!-- 4. Fibonacci -->
      <button
        type="button"
        class="flex items-center gap-1.5 rounded-full border-[0.5px] px-2.5 py-1 text-[11px] transition-colors cursor-pointer"
        :class="showFibonacci ? 'border-[#06B6D4] bg-[#06B6D4]/10 text-[#06B6D4] font-medium' : 'border-border bg-transparent text-muted-foreground hover:bg-card-hover'"
        @click="showFibonacci = !showFibonacci"
      >
        <div class="h-2 w-2 rounded-full" :class="showFibonacci ? 'bg-[#06B6D4]' : 'bg-muted'" />
        Fibonacci (TP1-3 / SL)
      </button>

      <!-- 5. SMA 50/200 -->
      <button
        type="button"
        class="flex items-center gap-1.5 rounded-full border-[0.5px] px-2.5 py-1 text-[11px] transition-colors cursor-pointer"
        :class="showSma ? 'border-[#F59E0B] bg-[#F59E0B]/10 text-[#F59E0B] font-medium' : 'border-border bg-transparent text-muted-foreground hover:bg-card-hover'"
        @click="showSma = !showSma"
      >
        <div class="h-2 w-2 rounded-full" :class="showSma ? 'bg-[#F59E0B]' : 'bg-muted'" />
        SMA 50 & 200
      </button>

      <!-- 6. Chart Pattern -->
      <button
        type="button"
        class="flex items-center gap-1.5 rounded-full border-[0.5px] px-2.5 py-1 text-[11px] transition-colors cursor-pointer"
        :class="showGeometryLocal ? 'border-[var(--up)] bg-[var(--up)]/10 text-[var(--up)] font-medium shadow-xs' : 'border-border bg-transparent text-muted-foreground hover:bg-card-hover'"
        @click="toggleGeometry"
      >
        <div class="h-2 w-2 rounded-full" :class="showGeometryLocal ? 'bg-[var(--up)]' : 'bg-muted'" />
        Chart Pattern Geometry
      </button>
    </div>
  </div>
</template>
