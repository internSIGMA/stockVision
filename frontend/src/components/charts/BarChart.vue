<script setup>
import { computed } from 'vue'
import { COLORS, baseChart, axisStyle, gridStyle } from './chartTheme'

const props = defineProps({
  categories: { type: Array, required: true },
  series: { type: Array, required: true }, // [{ name, data:[] }]
  height: { type: Number, default: 300 },
  horizontal: { type: Boolean, default: false },
  colors: { type: Array, default: () => [COLORS.brand] },
  distributed: { type: Boolean, default: false },
  yFormatter: { type: Function, default: null },
})

const options = computed(() => ({
  chart: { ...baseChart, type: 'bar' },
  colors: props.colors,
  plotOptions: {
    bar: {
      horizontal: props.horizontal,
      borderRadius: 5,
      columnWidth: '55%',
      barHeight: '62%',
      distributed: props.distributed,
    },
  },
  dataLabels: { enabled: false },
  xaxis: { categories: props.categories, ...axisStyle() },
  yaxis: {
    labels: {
      style: { colors: COLORS.text, fontSize: '11px' },
      formatter: props.yFormatter || ((v) => new Intl.NumberFormat('id-ID').format(Math.round(v))),
    },
  },
  grid: gridStyle,
  legend: { show: !props.distributed && props.series.length > 1, position: 'top', horizontalAlign: 'left', labels: { colors: COLORS.text } },
  tooltip: { theme: 'dark' },
}))
</script>

<template>
  <apexchart type="bar" :height="height" :options="options" :series="series" />
</template>
