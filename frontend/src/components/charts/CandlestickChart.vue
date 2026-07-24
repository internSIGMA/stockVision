<script setup>
import { onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { CandlestickSeries, ColorType, createChart } from 'lightweight-charts'
import { useTheme } from '@/composables/useTheme'

const props = defineProps({
  /** Baris OHLC dari /api/data/ohlc, urut tanggal ASC. */
  rows: { type: Array, default: () => [] },
  height: { type: Number, default: 340 },
})

const container = ref(null)
const { isDark } = useTheme()

// shallowRef: objek chart dari library tidak boleh dibungkus proxy reaktif Vue.
const chart = shallowRef(null)
const series = shallowRef(null)

const UP = '#16a34a'
const DOWN = '#dc2626'

function tema() {
  const grid = isDark.value ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'
  const text = isDark.value ? '#a1a1a1' : '#737373'
  return {
    layout: {
      background: { type: ColorType.Solid, color: 'transparent' },
      textColor: text,
      fontFamily: "'Spline Sans Mono', monospace",
      fontSize: 10,
      // lightweight-charts v5 menempelkan logo TradingView di pojok chart secara default.
      attributionLogo: false,
    },
    grid: { vertLines: { color: grid }, horzLines: { color: grid } },
    rightPriceScale: { borderColor: grid },
    timeScale: { borderColor: grid },
    crosshair: { mode: 0 },
  }
}

/** Backend mengirim tanggal ISO; lightweight-charts butuh 'YYYY-MM-DD'. */
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

function render() {
  if (!series.value) return
  series.value.setData(toChartData(props.rows))
  chart.value?.timeScale().fitContent()
}

onMounted(() => {
  chart.value = createChart(container.value, {
    ...tema(),
    height: props.height,
    autoSize: true,
    handleScroll: true,
    handleScale: true,
  })

  series.value = chart.value.addSeries(CandlestickSeries, {
    upColor: UP,
    downColor: DOWN,
    borderUpColor: UP,
    borderDownColor: DOWN,
    wickUpColor: UP,
    wickDownColor: DOWN,
  })

  render()
})

onBeforeUnmount(() => {
  chart.value?.remove()
  chart.value = null
  series.value = null
})

watch(() => props.rows, render, { deep: false })
watch(isDark, () => chart.value?.applyOptions(tema()))

function resetZoom() {
  chart.value?.timeScale().fitContent()
}

defineExpose({ resetZoom })
</script>

<template>
  <!-- data-lenis-prevent: Lenis tidak boleh membajak scroll-zoom milik chart. -->
  <div
    ref="container"
    data-lenis-prevent
    class="w-full"
    :style="{ height: `${height}px` }"
    role="img"
    aria-label="Grafik candlestick harga historis"
  />
</template>
