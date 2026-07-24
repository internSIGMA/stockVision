<script setup>
import { computed } from 'vue'

/** Garis tren mini tanpa sumbu — dipakai di kartu Trending Stocks. */
const props = defineProps({
  values: { type: Array, default: () => [] },
  width: { type: Number, default: 56 },
  height: { type: Number, default: 18 },
})

const naik = computed(() => {
  const v = props.values
  return v.length < 2 ? true : v[v.length - 1] >= v[0]
})

const points = computed(() => {
  const v = props.values.map(Number).filter((n) => !Number.isNaN(n))
  if (v.length < 2) return ''

  const min = Math.min(...v)
  const max = Math.max(...v)
  const span = max - min || 1
  const stepX = props.width / (v.length - 1)

  // Sisakan 1px di atas & bawah supaya stroke tidak terpotong bounding box.
  const usable = props.height - 2

  return v
    .map((n, i) => {
      const x = i * stepX
      const y = 1 + usable - ((n - min) / span) * usable
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
})
</script>

<template>
  <svg
    v-if="points"
    :width="width"
    :height="height"
    :viewBox="`0 0 ${width} ${height}`"
    fill="none"
    aria-hidden="true"
    class="shrink-0 overflow-visible"
  >
    <polyline
      :points="points"
      :stroke="naik ? 'var(--color-up)' : 'var(--color-down)'"
      stroke-width="1"
      stroke-linecap="round"
      stroke-linejoin="round"
    />
  </svg>
  <div v-else :style="{ width: `${width}px`, height: `${height}px` }" aria-hidden="true" />
</template>
