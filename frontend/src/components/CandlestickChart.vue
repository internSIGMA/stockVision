<script setup>
import { computed } from 'vue';

const props = defineProps({
  rows: { type: Array, required: true }, // [{open,high,low,close}, ...]
});

const W = 900;
const H = 260;
const PAD = 30;

const bars = computed(() => {
  const vals = props.rows;
  if (!vals.length) return [];
  const highs = vals.map((v) => v.high);
  const lows = vals.map((v) => v.low);
  const max = Math.max(...highs);
  const min = Math.min(...lows);
  const span = max - min || 1;
  const bw = (W - PAD * 2) / vals.length;
  const y = (val) => H - PAD - ((val - min) / span) * (H - PAD * 2);

  return vals.map((v, i) => ({
    x: PAD + i * bw + bw / 2,
    bw: bw * 0.6,
    yHigh: y(v.high),
    yLow: y(v.low),
    yOpen: y(v.open),
    yClose: y(v.close),
    up: v.close >= v.open,
  }));
});
</script>

<template>
  <svg :viewBox="`0 0 ${W} ${H}`" class="candle-svg" preserveAspectRatio="none">
    <line
      v-for="i in 4"
      :key="'grid' + i"
      x1="0" :x2="W"
      :y1="((H - 30) * i) / 4 + 10" :y2="((H - 30) * i) / 4 + 10"
      stroke="var(--border)" stroke-width="1"
    />
    <g v-for="(b, i) in bars" :key="i">
      <line :x1="b.x" :x2="b.x" :y1="b.yHigh" :y2="b.yLow" :stroke="b.up ? 'var(--up)' : 'var(--down)'" stroke-width="1" />
      <rect
        :x="b.x - b.bw / 2"
        :y="Math.min(b.yOpen, b.yClose)"
        :width="b.bw"
        :height="Math.max(1, Math.abs(b.yClose - b.yOpen))"
        :fill="b.up ? 'var(--up)' : 'var(--down)'"
      />
    </g>
  </svg>
</template>

<style scoped>
.candle-svg { width: 100%; height: 260px; display: block; }
</style>
