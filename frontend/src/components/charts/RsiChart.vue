<script setup>
import { computed, onBeforeUnmount, onMounted, ref, shallowRef, watch } from 'vue'
import { ColorType, CrosshairMode, LineSeries, LineStyle, createChart } from 'lightweight-charts'
import { useTheme } from '@/composables/useTheme'

/**
 * Panel RSI bergaya TradingView: garis RSI, zona 30–70 diarsir, dan legend
 * melayang di kiri atas yang ikut kursor.
 *
 * Yang digambar hanya deret yang benar-benar dikirim backend. Tabel
 * idxsaham.macd_rsi cuma punya satu kolom RSI (rsi14), jadi panel ini pun cuma
 * punya satu garis — tidak ada rata-rata bergerak yang dikarang di browser.
 *
 * Memakai lightweight-charts (bukan Chart.js) supaya zoom & pan-nya sama persis
 * dengan Historical Candlestick — satu library, satu perilaku.
 */
const props = defineProps({
  /** Label tanggal 'YYYY-MM-DD', sejajar dengan `data`. */
  dates: { type: Array, default: () => [] },
  /** Deret RSI — null di depan selama periode belum penuh. */
  data: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  height: { type: Number, default: 240 },
  /** Periode RSI, dipakai untuk label legend saja. */
  periode: { type: Number, default: 14 },
  /** Jumlah bar yang terlihat saat pertama dibuka; sisanya dijangkau via zoom. */
  jendelaAwal: { type: Number, default: 150 },
})

const container = ref(null)
const { isDark } = useTheme()

// shallowRef: objek library tidak boleh dibungkus proxy reaktif Vue.
const chart = shallowRef(null)
const seriRsi = shallowRef(null)
const garisBatas = shallowRef([])

/** Pasangkan tanggal & nilai, buang yang kosong, buang tanggal kembar. */
const titik = computed(() => {
  const out = []
  let sebelumnya = null
  for (let i = 0; i < props.data.length; i++) {
    const v = props.data[i]
    const t = props.dates[i]
    if (v == null || !t) continue
    const time = String(t).slice(0, 10)
    if (time === sebelumnya) continue
    sebelumnya = time
    out.push({ time, value: Number(v) })
  }
  return out
})

const adaData = computed(() => titik.value.length > 0)

function warna() {
  const style = getComputedStyle(document.documentElement)
  const ambil = (nama) => style.getPropertyValue(nama).trim()
  return {
    rsi: ambil('--primary'),
    naik: ambil('--up'),
    turun: ambil('--down'),
    grid: ambil('--border'),
    text: ambil('--muted-foreground'),
    zona: ambil('--primary-soft'),
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
    // Skala dikunci 0–100: RSI memang tidak pernah keluar rentang itu, dan
    // dengan begitu posisi arsiran zona tidak bergeser saat di-zoom.
    rightPriceScale: { borderColor: grid, scaleMargins: { top: 0.08, bottom: 0.08 } },
    timeScale: { borderColor: grid, rightOffset: 2 },
    crosshair: { mode: CrosshairMode.Normal },
  }
}

/** Garis 70 / 50 / 30 — batas baca RSI, digambar sebagai price line native. */
function pasangGarisBatas() {
  const s = seriRsi.value
  if (!s) return
  garisBatas.value.forEach((g) => s.removePriceLine(g))
  const { naik, turun, grid } = warna()
  garisBatas.value = [
    { price: 70, color: turun, lineStyle: LineStyle.Dashed, title: 'Overbought' },
    { price: 50, color: grid, lineStyle: LineStyle.Dotted, title: '' },
    { price: 30, color: naik, lineStyle: LineStyle.Dashed, title: 'Oversold' },
  ].map((g) =>
    s.createPriceLine({ ...g, lineWidth: 1, axisLabelVisible: true, lineVisible: true }),
  )
}

// ── Legend melayang, mengikuti kursor seperti TradingView ──────────────────
const nilaiRsi = ref(null)

function isiLegendTerakhir() {
  nilaiRsi.value = titik.value.length ? titik.value[titik.value.length - 1].value : null
}

const fmt = (v) => (v == null ? '—' : v.toFixed(2))

// ── Arsiran zona 30–70 ────────────────────────────────────────────────────
const zona = ref({ atas: 0, tinggi: 0, kanan: 0, tampil: false })

function hitungZona() {
  const s = seriRsi.value
  if (!s) return
  const y70 = s.priceToCoordinate(70)
  const y30 = s.priceToCoordinate(30)
  if (y70 == null || y30 == null) {
    zona.value = { ...zona.value, tampil: false }
    return
  }
  zona.value = {
    atas: y70,
    tinggi: y30 - y70,
    // Dipotong di tepi plot supaya tidak merembes ke belakang label sumbu harga.
    kanan: chart.value?.priceScale('right').width() ?? 0,
    tampil: true,
  }
}

/**
 * Buka di ekor data, bukan fitContent(): lima tahun RSI yang dijejalkan ke satu
 * layar cuma jadi rambut. Histori lamanya tetap ada, tinggal di-zoom out.
 */
function bukaDiEkor() {
  const n = titik.value.length
  if (!n) return
  chart.value?.timeScale().setVisibleLogicalRange({
    from: Math.max(0, n - props.jendelaAwal),
    to: n + 2,
  })
}

function render() {
  if (!seriRsi.value) return
  seriRsi.value.setData(titik.value)
  pasangGarisBatas()
  bukaDiEkor()
  isiLegendTerakhir()
  requestAnimationFrame(hitungZona)
}

let pengamatUkuran = null

onMounted(() => {
  const w = warna()
  chart.value = createChart(container.value, {
    ...tema(),
    height: props.height,
    autoSize: true,
    handleScroll: true,
    handleScale: true,
  })

  seriRsi.value = chart.value.addSeries(LineSeries, {
    color: w.rsi,
    lineWidth: 2,
    priceLineVisible: false,
    lastValueVisible: false,
    autoscaleInfoProvider: () => ({ priceRange: { minValue: 0, maxValue: 100 } }),
  })

  chart.value.subscribeCrosshairMove((param) => {
    if (!param.time) {
      isiLegendTerakhir()
      return
    }
    nilaiRsi.value = param.seriesData.get(seriRsi.value)?.value ?? null
  })

  pengamatUkuran = new ResizeObserver(() => hitungZona())
  pengamatUkuran.observe(container.value)

  render()
})

onBeforeUnmount(() => {
  pengamatUkuran?.disconnect()
  pengamatUkuran = null
  chart.value?.remove()
  chart.value = null
  seriRsi.value = null
})

watch(titik, render)
watch(isDark, () => {
  const w = warna()
  chart.value?.applyOptions(tema())
  seriRsi.value?.applyOptions({ color: w.rsi })
  pasangGarisBatas()
})

function resetZoom() {
  bukaDiEkor()
  requestAnimationFrame(hitungZona)
}

defineExpose({ resetZoom })
</script>

<template>
  <div class="relative w-full" :style="{ height: `${height}px` }">
    <!-- Arsiran zona netral 30–70; di bawah kanvas supaya tidak menutupi garis. -->
    <div
      v-show="zona.tampil && adaData"
      class="pointer-events-none absolute left-0 z-0 bg-[var(--primary-soft)] opacity-60"
      :style="{ top: `${zona.atas}px`, height: `${zona.tinggi}px`, right: `${zona.kanan}px` }"
      aria-hidden="true"
    />

    <!-- data-lenis-prevent: Lenis tidak boleh membajak scroll-zoom milik chart. -->
    <div
      ref="container"
      data-lenis-prevent
      class="relative z-[1] h-full w-full"
      role="img"
      :aria-label="`Grafik RSI ${periode} periode. Nilai terakhir ${fmt(nilaiRsi)}. Batas overbought 70 dan oversold 30 ditandai garis putus-putus.`"
    />

    <!-- Legend melayang ala TradingView -->
    <div
      v-if="adaData"
      class="tabular pointer-events-none absolute left-2 top-1 z-[2] flex flex-wrap items-baseline gap-x-3 gap-y-1 text-[11px] leading-none"
    >
      <div class="flex items-baseline gap-1.5">
        <span class="font-semibold text-foreground">RSI</span>
        <span class="text-muted-foreground">{{ periode }} close</span>
      </div>
      <div class="flex items-baseline gap-1">
        <span class="text-muted-foreground">RSI</span>
        <span class="font-semibold text-[var(--primary)]">{{ fmt(nilaiRsi) }}</span>
      </div>
    </div>

    <button
      v-if="adaData"
      type="button"
      class="absolute top-1 z-[2] rounded border-[0.5px] border-border bg-card/80 px-1.5 py-0.5 text-[10px] text-muted-foreground backdrop-blur transition-colors hover:bg-[var(--card-hover)] hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[var(--ring)]"
      :style="{ right: `${zona.kanan + 8}px` }"
      @click="resetZoom"
    >
      Reset zoom
    </button>

    <div v-if="loading" class="absolute inset-0 z-[3] animate-pulse rounded-lg bg-muted" />

    <p
      v-else-if="!adaData"
      class="absolute inset-0 z-[3] flex items-center justify-center bg-card text-[11px] text-muted-foreground"
    >
      Data RSI belum cukup untuk digambar.
    </p>
  </div>
</template>
