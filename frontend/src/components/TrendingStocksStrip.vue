<script setup>
import { ref, computed, onMounted } from 'vue';
import { TICKERS, getSummary } from '../lib/mockApi.js';
import { useMarketStore } from '../store/market.js';

const market = useMarketStore();
const items = ref([]);
const loading = ref(true);

onMounted(async () => {
  const results = await Promise.all(TICKERS.map((t) => getSummary(t)));
  items.value = results;
  loading.value = false;
});

function fmt(n) {
  return Math.round(n).toLocaleString('id-ID');
}

function sparklinePath(values, w = 140, h = 22) {
  if (!values.length) return '';
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const step = w / (values.length - 1 || 1);
  return values.map((v, i) => `${i === 0 ? 'M' : 'L'}${(i * step).toFixed(1)},${(h - ((v - min) / span) * h).toFixed(1)}`).join(' ');
}
</script>

<template>
  <div class="trend-strip-wrap">
    <div v-if="loading" class="trend-strip">
      <div v-for="i in 8" :key="i" class="skel trend-skel"></div>
    </div>
    <div v-else class="trend-strip">
      <button
        v-for="it in items"
        :key="it.ticker"
        type="button"
        class="trend-card"
        :class="{ active: it.ticker === market.selectedTicker }"
        @click="market.setTicker(it.ticker)"
      >
        <div class="tk">{{ it.ticker }}</div>
        <div class="px">Rp {{ fmt(it.price) }}</div>
        <div class="chg" :class="it.change >= 0 ? 'up-text' : 'down-text'">
          {{ it.change >= 0 ? '+' : '' }}{{ it.change_pct.toFixed(2) }}%
        </div>
        <svg viewBox="0 0 140 22" preserveAspectRatio="none" aria-hidden="true">
          <path :d="sparklinePath(it.spark)" fill="none" :stroke="it.change >= 0 ? 'var(--up)' : 'var(--down)'" stroke-width="1.6" />
        </svg>
      </button>
    </div>
  </div>
</template>

<style scoped>
.trend-strip-wrap { border-bottom: 1px solid var(--border); background: var(--surface); }
.trend-strip { max-width: 1400px; margin: 0 auto; padding: 12px 20px; display: flex; gap: 10px; overflow-x: auto; }
.trend-card {
  flex: none; width: 150px; padding: 10px 12px; border-radius: 10px; border: 1px solid var(--border);
  background: var(--surface); cursor: pointer; transition: all .15s ease; text-align: left; font-family: inherit; color: inherit;
}
.trend-card:hover { border-color: var(--border-strong); }
.trend-card.active { border-color: var(--primary); background: var(--primary-bg); box-shadow: 0 0 0 1px var(--primary) inset; }
.tk { font-weight: 700; font-size: 13px; }
.px { font-family: var(--font-mono); font-size: 12.5px; color: var(--ink-muted); margin-top: 2px; }
.chg { font-family: var(--font-mono); font-size: 11.5px; font-weight: 600; margin-top: 1px; }
.trend-card svg { width: 100%; height: 22px; display: block; margin-top: 4px; }
.trend-skel { flex: none; width: 150px; height: 78px; border-radius: 10px; }
</style>
