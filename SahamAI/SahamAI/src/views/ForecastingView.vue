<script setup>
import { computed, ref } from 'vue'
import { useMarketStore } from '@/stores/market'
import { forecast } from '@/data/market'
import { rupiah, pct } from '@/utils/format'
import AreaChart from '@/components/charts/AreaChart.vue'

const market = useMarketStore()
const horizons = [
  { label: '10 hari', days: 10 },
  { label: '20 hari', days: 20 },
  { label: '40 hari', days: 40 },
]
const horizon = ref(horizons[1])

const fc = computed(() => forecast(market.selected, horizon.value.days))

const series = computed(() => {
  const hist = fc.value.history.slice(-60).map((d) => ({ x: d.x, y: d.close }))
  return [
    { name: 'Historis', color: '#0f3d3c', data: hist },
    { name: 'Forecast', color: '#2f7fb0', dashed: true, fill: false, data: fc.value.points.map((p) => ({ x: p.x, y: p.mid })) },
    { name: 'Upper', color: '#a9c7dd', width: 1, fill: false, data: fc.value.points.map((p) => ({ x: p.x, y: p.upper })) },
    { name: 'Lower', color: '#a9c7dd', width: 1, fill: false, data: fc.value.points.map((p) => ({ x: p.x, y: p.lower })) },
  ]
})

const last = computed(() => fc.value.history.at(-1).close)
const bias = computed(() => (fc.value.slope > 0 ? 'Naik' : 'Turun'))
</script>

<template>
  <div>
    <div class="page-intro">
      <h2>Forecasting — {{ market.selected }}</h2>
      <p>Proyeksi harga ke depan beserta rentang keyakinan. Model demo: regresi tren linier + noise band.</p>
    </div>

    <div class="metric-row">
      <div class="card mini"><span>Harga terakhir</span><strong>{{ rupiah(last) }}</strong></div>
      <div class="card mini"><span>Proyeksi akhir horizon</span><strong>{{ rupiah(fc.projected) }}</strong></div>
      <div class="card mini"><span>Estimasi perubahan</span><strong :class="fc.changePct >= 0 ? 'up' : 'down'">{{ pct(fc.changePct) }}</strong></div>
      <div class="card mini"><span>Bias tren</span><strong :class="fc.slope >= 0 ? 'up' : 'down'">{{ bias }}</strong></div>
    </div>

    <section class="card">
      <div class="card__head">
        <div><h3>Proyeksi Harga</h3><p>Garis putus-putus = prediksi, area abu = rentang keyakinan</p></div>
        <div class="range-tabs">
          <button v-for="h in horizons" :key="h.label" :class="{ active: h.label === horizon.label }" @click="horizon = h">{{ h.label }}</button>
        </div>
      </div>
      <AreaChart :series="series" type="line" :height="400" />
    </section>

    <p class="disclaimer">⚠️ Model forecasting di frontend ini bersifat ilustratif. Di produksi, prediksi sebaiknya berasal dari model backend (mis. ARIMA/LSTM) melalui API.</p>
  </div>
</template>

<style scoped>
.metric-row {
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
.disclaimer {
  margin-top: 16px;
  font-size: 12.5px;
  color: var(--text-faint);
}
@media (max-width: 900px) {
  .metric-row {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
