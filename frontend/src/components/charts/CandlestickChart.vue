<script setup>
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { CandlestickSeries, ColorType, createChart } from 'lightweight-charts'
import { useTheme } from '@/composables/useTheme'
import { formatDate, formatNumber } from '@/utils/format'

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

/** Palet diambil dari CSS variable supaya chart ikut token di globals.css. */
function warna() {
  const style = getComputedStyle(document.documentElement)
  const ambil = (nama) => style.getPropertyValue(nama).trim()
  return {
    up: ambil('--up'),
    down: ambil('--down'),
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
      // lightweight-charts v5 menempelkan logo TradingView di pojok chart secara default.
      attributionLogo: false,
    },
    grid: { vertLines: { color: grid }, horzLines: { color: grid } },
    rightPriceScale: { borderColor: grid },
    // Default maxBarSpacing = setengah lebar chart, artinya viewport tidak pernah
    // bisa memuat < 2 batang — 1D jadi ikut menampilkan batang sebelumnya.
    timeScale: { borderColor: grid, maxBarSpacing: 1e4 },
    crosshair: { mode: 0 },
  }
}

function temaSeri() {
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

// ==========================================================
// TOOLTIP HOVER
// ==========================================================

/** Batang yang sedang disorot: { time, open, high, low, close }. */
const bar = shallowRef(null)
const posisi = ref({ x: 0, y: 0 })

const UKURAN_TOOLTIP = { lebar: 132, tinggi: 108 }
const JARAK_KURSOR = 14

/**
 * Tooltip digeser ke sisi lain kursor begitu mepet tepi kanan/bawah,
 * supaya isinya tidak pernah terpotong bingkai chart.
 */
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

/** Hijau saat close >= open, merah kalau sebaliknya. */
const kelasArah = computed(() =>
  bar.value && bar.value.close >= bar.value.open ? 'text-up' : 'text-down',
)

const harga = (v) => formatNumber(v)

function pantauKursor(param) {
  // Di luar area plot, param.time kosong — sembunyikan tooltip.
  if (!param.time || !param.point || !series.value) {
    bar.value = null
    return
  }

  const data = param.seriesData.get(series.value)
  if (!data) {
    bar.value = null
    return
  }

  bar.value = data
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

  series.value = chart.value.addSeries(CandlestickSeries, temaSeri())

  chart.value.subscribeCrosshairMove(pantauKursor)

  render()
})

onBeforeUnmount(() => {
  chart.value?.remove()
  chart.value = null
  series.value = null
  bar.value = null
})

watch(() => props.rows, render, { deep: false })
watch(isDark, () => {
  chart.value?.applyOptions(tema())
  series.value?.applyOptions(temaSeri())
})

function resetZoom() {
  chart.value?.timeScale().fitContent()
}

// ==========================================================
// RENTANG WAKTU (1D, 5D, 1M, ...)
// ==========================================================

/**
 * 1D/5D dihitung dalam jumlah batang (hari bursa) karena itu yang diharapkan
 * pengguna; sisanya dalam hari kalender mundur dari batang terakhir.
 * YTD punya batasnya sendiri.
 */
const RENTANG_BATANG = { '1D': 1, '5D': 5 }
const RENTANG_HARI = { '1M': 30, '3M': 91, '6M': 182, '1Y': 365 }

/**
 * Menggeser viewport ke rentang yang diminta.
 *
 * Memakai logical range (indeks batang) alih-alih visible range tanggal supaya
 * hari libur bursa tidak menyisakan ruang kosong di ujung chart, dan supaya
 * rentang yang lebih panjang dari data yang ada tetap bisa diklik — viewport
 * cukup dijepit ke batang paling awal.
 */
function setRange(key) {
  const data = toChartData(props.rows)
  if (!chart.value || !data.length) return

  const total = data.length
  const akhir = data[total - 1].time

  let jumlah
  if (RENTANG_BATANG[key]) {
    jumlah = RENTANG_BATANG[key]
  } else {
    let batas
    if (key === 'YTD') {
      batas = `${akhir.slice(0, 4)}-01-01`
    } else {
      const hari = RENTANG_HARI[key]
      if (hari == null) return
      const d = new Date(`${akhir}T00:00:00Z`)
      d.setUTCDate(d.getUTCDate() - hari)
      batas = d.toISOString().slice(0, 10)
    }
    const mulai = data.findIndex((d) => d.time >= batas)
    jumlah = mulai < 0 ? 1 : total - mulai
  }

  jumlah = Math.min(Math.max(jumlah, 1), total)

  // Batang ke-i menempati [i - 0.5, i + 0.5], jadi rentang ini persis `jumlah` batang.
  chart.value.timeScale().setVisibleLogicalRange({
    from: total - jumlah - 0.5,
    to: total - 0.5,
  })
}

defineExpose({ resetZoom, setRange })
</script>

<template>
  <div class="relative w-full" :style="{ height: `${height}px` }">
    <!-- data-lenis-prevent: Lenis tidak boleh membajak scroll-zoom milik chart. -->
    <div
      ref="container"
      data-lenis-prevent
      class="h-full w-full"
      role="img"
      aria-label="Grafik candlestick harga historis"
    />

    <!--
      pointer-events-none: tooltip tidak boleh menghalangi kursor, kalau tidak
      crosshair akan kehilangan jejak begitu tooltip lewat di bawah kursor.
    -->
    <div
      v-if="bar"
      class="tabular pointer-events-none absolute z-[3] w-[132px] rounded-md border-[0.5px] border-border bg-card/95 px-2 py-1.5 text-[10px] leading-tight shadow-sm backdrop-blur"
      :style="gaya"
    >
      <p class="mb-1 font-medium text-foreground">
        {{ formatDate(bar.time) }}
      </p>

      <dl class="grid grid-cols-[auto_1fr] gap-x-2 gap-y-0.5">
        <dt class="text-muted-foreground">Open</dt>
        <dd class="text-right text-foreground">{{ harga(bar.open) }}</dd>

        <dt class="text-muted-foreground">High</dt>
        <dd class="text-right text-foreground">{{ harga(bar.high) }}</dd>

        <dt class="text-muted-foreground">Low</dt>
        <dd class="text-right text-foreground">{{ harga(bar.low) }}</dd>

        <dt class="text-muted-foreground">Close</dt>
        <dd class="flex flex-col items-end text-right font-medium" :class="kelasArah">
          <span>{{ harga(bar.close) }}</span>
          <span class="text-[9px] font-normal opacity-80" :class="kelasArah">
            {{ bar.close >= bar.open ? 'Bullish' : 'Bearish' }}
          </span>
        </dd>
      </dl>
    </div>
  </div>
</template>
