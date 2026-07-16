<script setup>
import { computed } from 'vue'
import { COLORS, baseChart, axisStyle, gridStyle } from './chartTheme'

const props = defineProps({
  series: { type: Array, required: true }, // [{ name, data:[{x,y}], color, dashed, fill }]
  height: { type: Number, default: 300 },
  type: { type: String, default: 'area' }, // 'area' | 'line'
  datetime: { type: Boolean, default: true },
  yFormatter: { type: Function, default: null },
  annotations: { type: Object, default: null },
  opposite: { type: Boolean, default: false },
})

const options = computed(() => ({
  chart: { ...baseChart, type: props.type },
  colors: props.series.map((s) => s.color || COLORS.brand),
  stroke: {
    width: props.series.map((s) => (s.width != null ? s.width : 2.5)),
    curve: 'smooth',
    dashArray: props.series.map((s) => (s.dashed ? 5 : 0)),
  },
  // For line charts the stroke must stay fully opaque — fill.opacity of 0
  // would hide the line entirely. Only area charts use per-series fill.
  fill:
    props.type === 'area'
      ? {
          type: 'gradient',
          gradient: { shadeIntensity: 0.3, opacityFrom: 0.28, opacityTo: 0.02, stops: [0, 100] },
          opacity: props.series.map((s) => (s.fill === false ? 0 : 1)),
        }
      : { type: 'solid', opacity: 1 },
  xaxis: { type: props.datetime ? 'datetime' : 'category', ...axisStyle() },
  yaxis: {
    opposite: props.opposite,
    labels: {
      style: { colors: COLORS.text, fontSize: '11px' },
      formatter: props.yFormatter || ((v) => new Intl.NumberFormat('id-ID').format(Math.round(v))),
    },
  },
  grid: gridStyle,
  legend: { show: props.series.length > 1, position: 'top', horizontalAlign: 'left', markers: { radius: 4 }, labels: { colors: COLORS.text } },
  dataLabels: { enabled: false },
  tooltip: { theme: 'dark', x: props.datetime ? { format: 'dd MMM yyyy' } : undefined },
  annotations: props.annotations || {},
}))
</script>

<template>
  <apexchart :type="type" :height="height" :options="options" :series="series" />
</template>
