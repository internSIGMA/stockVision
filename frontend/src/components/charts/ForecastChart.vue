<script setup>
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from 'chart.js'
import { useTheme } from '@/composables/useTheme'
import { formatDate, formatNumber } from '@/utils/format'

// Filler yang membuat area antar-dataset (confidence band) bisa terisi.
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Filler, Tooltip, Legend)

const props = defineProps({
  /** Baris OHLC asli (urut ASC) — bagian historis. */
  rows: { type: Array, default: () => [] },
  /** Titik proyeksi ternormalisasi: [{ tanggal, prediksi, lower, upper }]. */
  points: { type: Array, default: () => [] },
  /** Gambar pita confidence hanya kalau semua titik punya lower & upper. */
  showBand: { type: Boolean, default: false },
  height: { type: Number, default: 320 },
  /** Ekor histori yang ditampilkan — kalau semua, proyeksinya jadi tak terlihat. */
  limit: { type: Number, default: 60 },
})

const { isDark } = useTheme()

const AKTUAL = '#525252'
const AKTUAL_GELAP = '#d4d4d4'
const PROYEKSI = '#7c3aed'
const BAND = 'rgba(124, 58, 237, 0.12)'

const historis = computed(() => props.rows.slice(-props.limit))

/**
 * Sumbu X = histori + proyeksi disambung. Deret proyeksi diisi null sepanjang
 * bagian historis, KECUALI di titik sambungannya: di sana nilainya disamakan
 * dengan harga penutupan terakhir supaya garis putus-putusnya menyambung mulus
 * dan tidak melayang terputus.
 */
const chartData = computed(() => {
  const aktual = historis.value.map((r) => Number(r.close))
  const sambungan = aktual.length ? aktual.length - 1 : 0
  const hargaSambung = aktual.length ? aktual[aktual.length - 1] : null

  const labels = [
    ...historis.value.map((r) => String(r.tanggal).slice(0, 10)),
    ...props.points.map((p) => p.tanggal),
  ]

  const kosong = new Array(aktual.length).fill(null)
  const isiSetelahSambungan = (nilai) => {
    const deret = [...kosong, ...nilai]
    if (hargaSambung != null && deret.length > sambungan) deret[sambungan] = hargaSambung
    return deret
  }

  const datasets = []

  // Band digambar lebih dulu supaya berada di belakang garis.
  if (props.showBand && props.points.length) {
    datasets.push(
      {
        label: 'Batas atas',
        data: isiSetelahSambungan(props.points.map((p) => p.upper)),
        borderColor: 'transparent',
        backgroundColor: BAND,
        pointRadius: 0,
        borderWidth: 0,
        fill: '+1', // isi sampai dataset berikutnya (batas bawah)
        tension: 0.25,
      },
      {
        label: 'Batas bawah',
        data: isiSetelahSambungan(props.points.map((p) => p.lower)),
        borderColor: 'transparent',
        pointRadius: 0,
        borderWidth: 0,
        fill: false,
        tension: 0.25,
      },
    )
  }

  datasets.push(
    {
      label: 'Harga aktual',
      data: [...aktual, ...new Array(props.points.length).fill(null)],
      borderColor: isDark.value ? AKTUAL_GELAP : AKTUAL,
      borderWidth: 1.5,
      pointRadius: 0,
      pointHoverRadius: 3,
      fill: false,
      tension: 0.15,
    },
    {
      label: 'Proyeksi',
      data: isiSetelahSambungan(props.points.map((p) => p.prediksi)),
      borderColor: PROYEKSI,
      borderWidth: 1.5,
      borderDash: [4, 3],
      pointRadius: 0,
      pointHoverRadius: 3,
      fill: false,
      tension: 0.25,
    },
  )

  return { labels, datasets }
})

const chartOptions = computed(() => {
  const grid = isDark.value ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'
  const text = isDark.value ? '#a1a1a1' : '#737373'
  const mono = { family: "'Spline Sans Mono', monospace", size: 9 }

  const cariTitik = (label) => props.points.find((p) => p.tanggal === label)

  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 150 },
    interaction: { mode: 'index', intersect: false },
    plugins: {
      legend: {
        display: true,
        position: 'bottom',
        labels: {
          color: text,
          boxWidth: 8,
          boxHeight: 8,
          usePointStyle: true,
          font: { family: "'Archivo', sans-serif", size: 10 },
          // Batas atas/bawah cuma pembentuk pita — jangan ramaikan legenda.
          filter: (item) => !item.text.startsWith('Batas'),
        },
      },
      tooltip: {
        callbacks: {
          title: (items) => formatDate(items[0]?.label),
          label: (ctx) => {
            if (ctx.dataset.label.startsWith('Batas')) return null
            return `${ctx.dataset.label}: ${formatNumber(ctx.parsed.y)}`
          },
          afterBody: (items) => {
            const titik = cariTitik(items[0]?.label)
            if (!titik || titik.lower == null || titik.upper == null) return null
            return `Rentang: ${formatNumber(titik.lower)} – ${formatNumber(titik.upper)}`
          },
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        border: { color: grid },
        ticks: { color: text, font: mono, maxRotation: 0, autoSkipPadding: 24 },
      },
      y: {
        grid: { color: grid },
        border: { display: false },
        ticks: { color: text, font: mono, callback: (v) => formatNumber(v) },
      },
    },
  }
})
</script>

<template>
  <div
    class="w-full"
    :style="{ height: `${height}px` }"
    role="img"
    aria-label="Grafik proyeksi harga: garis solid harga aktual, garis putus-putus proyeksi"
  >
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
