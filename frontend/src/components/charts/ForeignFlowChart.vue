<script setup>
import { computed } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Title,
  Tooltip,
} from 'chart.js'
import { useTheme } from '@/composables/useTheme'
import { formatNumber } from '@/utils/format'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const props = defineProps({
  /** Baris OHLC — foreign_flow ikut di response yang sama. */
  rows: { type: Array, default: () => [] },
  height: { type: Number, default: 300 },
  /** Batasi ke N hari terakhir agar bar tidak jadi rambut halus. */
  limit: { type: Number, default: 60 },
})

const { isDark } = useTheme()

/**
 * Palet diambil dari CSS variable supaya chart ikut token di globals.css.
 * isDark ikut dibaca agar computed ini dihitung ulang saat tema berganti —
 * getComputedStyle sendiri bukan sumber reaktif buat Vue.
 */
const palet = computed(() => {
  void isDark.value
  const style = getComputedStyle(document.documentElement)
  const ambil = (nama) => style.getPropertyValue(nama).trim()
  return {
    up: ambil('--up'),
    down: ambil('--down'),
    grid: ambil('--border'),
    text: ambil('--muted-foreground'),
  }
})

const terakhir = computed(() => props.rows.slice(-props.limit))

/** Sumbu Y dalam miliar rupiah — angka mentahnya terlalu panjang untuk dibaca. */
const MILIAR = 1e9

/**
 * Selisih beli dan jual asing, dihitung dari kolom foreign_buy/foreign_sell.
 *
 * Kolom foreign_flow milik backend TIDAK sama dengan selisih itu — untuk BBCA
 * 15 Jul 2026 isinya -56,5 T sementara buy-sell hanya -61,2 M, dan nilainya
 * berulang persis antar tanggal. Jadi kolom itu hanya dipakai sebagai cadangan
 * saat buy/sell kosong.
 */
function alirAsing(r) {
  const beli = Number(r.foreign_buy)
  const jual = Number(r.foreign_sell)
  if (Number.isFinite(beli) && Number.isFinite(jual)) return beli - jual
  return Number(r.foreign_flow) || 0
}

const chartData = computed(() => {
  const rows = terakhir.value
  const values = rows.map(alirAsing)
  const { up, down } = palet.value

  return {
    labels: rows.map((r) => String(r.tanggal).slice(0, 10)),
    datasets: [
      {
        label: 'Foreign Flow',
        data: values,
        backgroundColor: values.map((v) => (v >= 0 ? up : down)),
        borderWidth: 0,
        borderRadius: 1,
      },
    ],
  }
})

const chartOptions = computed(() => {
  const { grid, text } = palet.value

  return {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 150 },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          label: (ctx) => `${formatNumber(ctx.parsed.y)} IDR`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        border: { color: grid },
        ticks: {
          color: text,
          font: { family: "'Spline Sans Mono', monospace", size: 9 },
          maxRotation: 0,
          autoSkipPadding: 24,
        },
      },
      y: {
        grid: { color: grid },
        border: { display: false },
        ticks: {
          color: text,
          font: { family: "'Spline Sans Mono', monospace", size: 9 },
          callback: (v) => `${(v / MILIAR).toFixed(1)}B`,
        },
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
    aria-label="Grafik aktivitas foreign flow harian dalam rupiah"
  >
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>
