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

const UP = '#16a34a'
const DOWN = '#dc2626'

const terakhir = computed(() => props.rows.slice(-props.limit))

/** Sumbu Y dalam miliar rupiah — angka mentahnya terlalu panjang untuk dibaca. */
const MILIAR = 1e9

const chartData = computed(() => {
  const rows = terakhir.value
  const values = rows.map((r) => Number(r.foreign_flow) || 0)

  return {
    labels: rows.map((r) => String(r.tanggal).slice(0, 10)),
    datasets: [
      {
        label: 'Foreign Flow',
        data: values,
        backgroundColor: values.map((v) => (v >= 0 ? UP : DOWN)),
        borderWidth: 0,
        borderRadius: 1,
      },
    ],
  }
})

const chartOptions = computed(() => {
  const grid = isDark.value ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.06)'
  const text = isDark.value ? '#a1a1a1' : '#737373'

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
