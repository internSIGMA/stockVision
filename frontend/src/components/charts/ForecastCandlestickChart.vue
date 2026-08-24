<script setup>
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { CandlestickSeries, ColorType, createChart } from 'lightweight-charts'
import { useTheme } from '@/composables/useTheme'
import { formatDate, formatNumber } from '@/utils/format'

const props = defineProps({
  /** Baris OHLC historis dari /api/data/ohlc, urut tanggal ASC. */
  rows: { type: Array, default: () => [] },
  /** Titik proyeksi dari /api/data/forecast: { tanggal, open, prediksi, lower, upper }. */
  points: { type: Array, default: () => [] },
  height: { type: Number, default: 320 },
})

const container = ref(null)
const { isDark } = useTheme()

const chart = shallowRef(null)
const seriesAktual = shallowRef(null)
const seriesProyeksi = shallowRef(null)

function warna() {
  const style = getComputedStyle(document.documentElement)
  const ambil = (nama) => style.getPropertyValue(nama).trim()
  return {
    up: ambil('--up'),
    down: ambil('--down'),
    proyeksi: ambil('--primary'),
    proyeksiLight: ambil('--primary-light'),
    grid: ambil('--border'),
    text: ambil('--muted-foreground'),
  }
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
    timeScale: { borderColor: grid, maxBarSpacing: 1e4 },
    crosshair: { mode: 0 },
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

/**
 * Batang proyeksi memakai warna brand (teal), bukan hijau/merah histori aktual,
 * supaya langsung kebeda sekilas — arah naik/turun tetap kebaca lewat gelap/terangnya.
 */
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

/**
 * Titik proyeksi belum tentu punya `open` dari backend — kalau kosong, dipakai
 * close hari sebelumnya (proyeksi atau histori) supaya candle tetap terbentuk,
 * bukan angka karangan baru.
 */
function toForecastData(points, hargaAcuan) {
  let acuan = hargaAcuan

  return points
    .map((p) => {
      const close = Number(p.prediksi)
      const open = p.open != null ? Number(p.open) : acuan
      const low = p.lower != null ? Number(p.lower) : Math.min(open ?? close, close)
      const high = p.upper != null ? Number(p.upper) : Math.max(open ?? close, close)

      if (Number.isFinite(close)) acuan = close

      return {
        time: p.tanggal,
        open: open ?? close,
        high: Math.max(high, open ?? close, close),
        low: Math.min(low, open ?? close, close),
        close,
      }
    })
    .filter((d) => !Number.isNaN(d.open) && !Number.isNaN(d.close))
}

function render() {
  if (!seriesAktual.value || !seriesProyeksi.value) return

  const historis = toChartData(props.rows)
  seriesAktual.value.setData(historis)

  const hargaAcuan = historis.length ? historis[historis.length - 1].close : null
  seriesProyeksi.value.setData(toForecastData(props.points, hargaAcuan))

  chart.value?.timeScale().fitContent()
}

// ==========================================================
// TOOLTIP HOVER
// ==========================================================

/** Batang yang sedang disorot: { time, open, high, low, close, proyeksi }. */
const bar = shallowRef(null)
const posisi = ref({ x: 0, y: 0 })

const UKURAN_TOOLTIP = { lebar: 132, tinggi: 122 }
const JARAK_KURSOR = 14

const gaya = computed(() => {
  const lebarChart = container.value?.clientWidth ?? 0
  const tinggiChart = container.value?.clientHeight ?? 0

  let x = posisi.value.x + JARAK_KURSOR
  let y = posisi.value.y + JARAK_KURSOR

  if (x + UKURAN_TOOLTIP.lebar > lebarChart) {
    x = posisi.value.x - UKURAN_TOOLTIP.lebar - JARAK_KURSOR
  }

  if (y + UKURAN_TOOLTIP.tinggi > tinggiChart) {
    y = posisi.value.y - UKURAN_TOOLTIP.tinggi - JARAK_KURSOR
  }

  return {
    left: `${Math.max(0, x)}px`,
    top: `${Math.max(0, y)}px`,
  }
})

const kelasArah = computed(() =>
  bar.value && bar.value.close >= bar.value.open ? 'text-up' : 'text-down',
)

const harga = (v) => formatNumber(v)

function pantauKursor(param) {
  if (!param.time || !param.point || !seriesAktual.value || !seriesProyeksi.value) {
    bar.value = null
    return
  }

  const dataProyeksi = param.seriesData.get(seriesProyeksi.value)
  if (dataProyeksi) {
    bar.value = { ...dataProyeksi, proyeksi: true }
    posisi.value = { x: param.point.x, y: param.point.y }
    return
  }

  const dataAktual = param.seriesData.get(seriesAktual.value)
  if (!dataAktual) {
    bar.value = null
    return
  }

  bar.value = { ...dataAktual, proyeksi: false }
  posisi.value = { x: param.point.x, y: param.point.y }
}

onMounted(() => {
  chart.value = createChart(container.value, {
    ...tema(),
    height: props.height,
    autoSize: true,
    handleScroll: true,
    handleScale: true,
  })

  seriesAktual.value = chart.value.addSeries(CandlestickSeries, temaAktual())
  seriesProyeksi.value = chart.value.addSeries(CandlestickSeries, temaProyeksi())

  chart.value.subscribeCrosshairMove(pantauKursor)

  render()
})

onBeforeUnmount(() => {
  chart.value?.remove()
  chart.value = null
  seriesAktual.value = null
  seriesProyeksi.value = null
  bar.value = null
})

watch(() => [props.rows, props.points], render, { deep: false })
watch(isDark, () => {
  chart.value?.applyOptions(tema())
  seriesAktual.value?.applyOptions(temaAktual())
  seriesProyeksi.value?.applyOptions(temaProyeksi())
})

function resetZoom() {
  chart.value?.timeScale().fitContent()
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
      aria-label="Grafik candlestick histori dan proyeksi harga"
    />

    <div
      v-if="bar"
      class="tabular pointer-events-none absolute z-[3] w-[132px] rounded-md border-[0.5px] border-border bg-card/95 px-2 py-1.5 text-[10px] leading-tight shadow-sm backdrop-blur"
      :style="gaya"
    >
      <p class="mb-1 flex items-center justify-between gap-2 font-medium text-foreground">
        {{ formatDate(bar.time) }}
        <span v-if="bar.proyeksi" class="rounded-full bg-muted px-1.5 py-0.5 text-[9px] font-normal text-muted-foreground">
          Proyeksi
        </span>
      </p>

      <dl class="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5">
        <dt class="text-muted-foreground">Open</dt>
        <dd class="text-right text-foreground">{{ harga(bar.open) }}</dd>

        <dt class="text-muted-foreground">High</dt>
        <dd class="text-right text-foreground">{{ harga(bar.high) }}</dd>

        <dt class="text-muted-foreground">Low</dt>
        <dd class="text-right text-foreground">{{ harga(bar.low) }}</dd>

        <dt class="text-muted-foreground">Close</dt>
        <dd class="text-right font-medium" :class="kelasArah">
          {{ harga(bar.close) }}
        </dd>
      </dl>
    </div>
  </div>
</template>
