<script setup>
import { computed, ref } from 'vue'
import { useMarketStore } from '@/stores/market'
import { generateOHLC, sma } from '@/data/market'
import { rupiah, number, pct } from '@/utils/format'
import CandleChart from '@/components/charts/CandleChart.vue'
import BarChart from '@/components/charts/BarChart.vue'

const market = useMarketStore()
const ranges = [
  { label: '1B', days: 22 },
  { label: '3B', days: 66 },
  { label: '6B', days: 120 },
]
const range = ref(ranges[1])
const showMA = ref(true)

const ohlc = computed(() => generateOHLC(market.selected, range.value.days))

const overlays = computed(() => {
  if (!showMA.value) return []
  const ma20 = sma(ohlc.value, 20)
  const ma50 = sma(ohlc.value, 50)
  return [
    { name: 'MA20', color: '#2f7fb0', data: ohlc.value.map((d, i) => ({ x: d.x, y: ma20[i] })) },
    { name: 'MA50', color: '#d9a300', data: ohlc.value.map((d, i) => ({ x: d.x, y: ma50[i] })) },
  ]
})

const volumeChart = computed(() => ({
  categories: ohlc.value.map((d) => d.date),
  series: [{ name: 'Volume', data: ohlc.value.map((d) => Math.round(d.volume / 1000)) }],
}))

const stats = computed(() => {
  const s = ohlc.value
  const closes = s.map((d) => d.close)
  return {
    last: s[s.length - 1].close,
    high: Math.max(...s.map((d) => d.high)),
    low: Math.min(...s.map((d) => d.low)),
    avgVol: s.reduce((a, b) => a + b.volume, 0) / s.length,
    change: ((closes[closes.length - 1] - closes[0]) / closes[0]) * 100,
  }
})
</script>

<template>
  <div>
    <div class="page-intro">
      <h2>Harga Emiten — {{ market.selected }}</h2>
      <p>Data harga harian (OHLCV) hasil crawling. Terakhir {{ rupiah(stats.last) }}.</p>
    </div>

    <div class="stat-row">
      <div class="card mini"><span>Tertinggi ({{ range.label }})</span><strong>{{ rupiah(stats.high) }}</strong></div>
      <div class="card mini"><span>Terendah ({{ range.label }})</span><strong>{{ rupiah(stats.low) }}</strong></div>
      <div class="card mini"><span>Rata-rata Volume</span><strong>{{ number(Math.round(stats.avgVol)) }}</strong></div>
      <div class="card mini"><span>Perubahan periode</span><strong :class="stats.change >= 0 ? 'up' : 'down'">{{ pct(stats.change) }}</strong></div>
    </div>

    <section class="card">
      <div class="card__head">
        <div><h3>Candlestick + Moving Average</h3><p>Klik toggle untuk overlay MA20 / MA50</p></div>
        <div class="controls">
          <label class="check">
            <input type="checkbox" v-model="showMA" /> MA
          </label>
          <div class="range-tabs">
            <button v-for="r in ranges" :key="r.label" :class="{ active: r.label === range.label }" @click="range = r">
              {{ r.label }}
            </button>
          </div>
        </div>
      </div>
      <CandleChart :ohlc="ohlc" :overlays="overlays" :height="360" />
    </section>

    <section class="card">
      <div class="card__head"><div><h3>Volume Transaksi (ribuan lembar)</h3></div></div>
      <BarChart :categories="volumeChart.categories" :series="volumeChart.series" :colors="['#0f3d3c']" :height="200" />
    </section>
  </div>
</template>

<style scoped>
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.mini {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.mini span {
  font-size: 12px;
  color: var(--text-muted);
}
.mini strong {
  font-size: 19px;
  font-weight: 700;
  letter-spacing: -0.01em;
}
.up {
  color: var(--up);
}
.down {
  color: var(--down);
}
.card {
  margin-bottom: 16px;
}
.controls {
  display: flex;
  align-items: center;
  gap: 14px;
}
.check {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
}
.check input {
  accent-color: var(--brand);
}
.range-tabs {
  display: flex;
  gap: 4px;
  background: var(--surface-2);
  padding: 4px;
  border-radius: 10px;
}
.range-tabs button {
  padding: 6px 12px;
  border-radius: 7px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text-muted);
}
.range-tabs button.active {
  background: var(--surface);
  color: var(--brand);
  box-shadow: var(--shadow);
}
@media (max-width: 900px) {
  .stat-row {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
