<script setup>
import { computed } from 'vue'
import { COLORS, baseChart, axisStyle, gridStyle } from './chartTheme'

const props = defineProps({
  ohlc: { type: Array, required: true }, // [{x, open, high, low, close}]
  overlays: { type: Array, default: () => [] }, // [{ name, data:[{x,y}], color }]
  height: { type: Number, default: 340 },
})

const series = computed(() => [
  {
    name: 'Harga',
    type: 'candlestick',
    data: props.ohlc.map((d) => ({ x: d.x, y: [d.open, d.high, d.low, d.close] })),
  },
  ...props.overlays.map((o) => ({
    name: o.name,
    type: 'line',
    data: o.data,
    color: o.color,
  })),
])

const options = computed(() => ({
  chart: { ...baseChart, type: 'candlestick' },
  plotOptions: {
    candlestick: {
      colors: { upward: COLORS.up, downward: COLORS.down },
      wick: { useFillColor: true },
    },
  },
  stroke: {
    width: [1, ...props.overlays.map(() => 2)],
    curve: 'smooth',
  },
  xaxis: { type: 'datetime', ...axisStyle() },
  yaxis: {
    tooltip: { enabled: true },
    labels: {
      style: { colors: COLORS.text, fontSize: '11px' },
      formatter: (v) => new Intl.NumberFormat('id-ID').format(Math.round(v)),
    },
  },
  grid: gridStyle,
  legend: { show: props.overlays.length > 0, position: 'top', horizontalAlign: 'left', markers: { radius: 4 }, labels: { colors: COLORS.text } },
  tooltip: { theme: 'dark', x: { format: 'dd MMM yyyy' } },
}))
</script>

<template>
  <apexchart type="candlestick" :height="height" :options="options" :series="series" />
</template>
