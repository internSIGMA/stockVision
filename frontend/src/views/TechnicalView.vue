<script setup>
import { computed, ref } from 'vue'
import { useMarketStore } from '@/stores/market'
import { generateOHLC, sma, rsi, forecast } from '@/data/market'
import { rupiah, pct, number } from '@/utils/format'
import CandleChart from '@/components/charts/CandleChart.vue'
import AreaChart from '@/components/charts/AreaChart.vue'

const market = useMarketStore()

const tabs = [
  { key: 'descriptive', label: 'Descriptive', q: 'Apa yang terjadi?' },
  { key: 'diagnostic', label: 'Diagnostic', q: 'Kenapa terjadi?' },
  { key: 'predictive', label: 'Predictive', q: 'Apa yang akan terjadi?' },
  { key: 'prescriptive', label: 'Prescriptive', q: 'Apa yang sebaiknya dilakukan?' },
]
const tab = ref('descriptive')

const ohlc = computed(() => generateOHLC(market.selected, 120))
const closes = computed(() => ohlc.value.map((d) => d.close))
const ma20arr = computed(() => sma(ohlc.value, 20))
const ma50arr = computed(() => sma(ohlc.value, 50))
const rsiArr = computed(() => rsi(ohlc.value, 14))
const fc = computed(() => forecast(market.selected, 20))

const maOverlays = computed(() => [
  { name: 'MA20', color: '#2f7fb0', data: ohlc.value.map((d, i) => ({ x: d.x, y: ma20arr.value[i] })) },
  { name: 'MA50', color: '#d9a300', data: ohlc.value.map((d, i) => ({ x: d.x, y: ma50arr.value[i] })) },
])

// --- Descriptive metrics ---
const descriptive = computed(() => {
  const c = closes.value
  const ret = ((c[c.length - 1] - c[0]) / c[0]) * 100
  const rets = c.slice(1).map((v, i) => (v - c[i]) / c[i])
  const mean = rets.reduce((a, b) => a + b, 0) / rets.length
  const vol = Math.sqrt(rets.reduce((a, b) => a + (b - mean) ** 2, 0) / rets.length) * Math.sqrt(252) * 100
  const last = ohlc.value[ohlc.value.length - 1]
  const trend = ma20arr.value.at(-1) > ma50arr.value.at(-1) ? 'Uptrend' : 'Downtrend'
  return {
    ret, vol, trend,
    high: Math.max(...ohlc.value.map((d) => d.high)),
    low: Math.min(...ohlc.value.map((d) => d.low)),
    avgVol: ohlc.value.reduce((a, b) => a + b.volume, 0) / ohlc.value.length,
    last: last.close,
  }
})

// --- Diagnostic signals ---
const diagnostic = computed(() => {
  const rsiNow = rsiArr.value.at(-1)
  const ma20 = ma20arr.value.at(-1)
  const ma50 = ma50arr.value.at(-1)
  const signals = []
  if (rsiNow > 70) signals.push({ tone: 'down', text: `RSI ${rsiNow} — kondisi overbought, rawan koreksi.` })
  else if (rsiNow < 30) signals.push({ tone: 'up', text: `RSI ${rsiNow} — kondisi oversold, potensi rebound.` })
  else signals.push({ tone: 'neutral', text: `RSI ${rsiNow} — momentum netral.` })

  if (ma20 > ma50) signals.push({ tone: 'up', text: 'MA20 di atas MA50 (Golden Cross) — bias bullish.' })
  else signals.push({ tone: 'down', text: 'MA20 di bawah MA50 (Death Cross) — bias bearish.' })

  const volTrend = ohlc.value.slice(-5).reduce((a, b) => a + b.volume, 0) / 5
  const volAvg = ohlc.value.reduce((a, b) => a + b.volume, 0) / ohlc.value.length
  if (volTrend > volAvg * 1.15) signals.push({ tone: 'up', text: 'Volume 5 hari terakhir naik signifikan — minat beli meningkat.' })
  else signals.push({ tone: 'neutral', text: 'Volume relatif stabil terhadap rata-rata.' })

  return { rsiNow, signals }
})

const rsiSeries = computed(() => [
  { name: 'RSI (14)', color: '#7c5cd6', fill: false, data: ohlc.value.map((d, i) => ({ x: d.x, y: rsiArr.value[i] })) },
])
const rsiAnnotations = computed(() => ({
  yaxis: [
    { y: 70, borderColor: '#dc2626', strokeDashArray: 4, label: { text: 'Overbought 70', style: { color: '#fff', background: '#dc2626' } } },
    { y: 30, borderColor: '#16a34a', strokeDashArray: 4, label: { text: 'Oversold 30', style: { color: '#fff', background: '#16a34a' } } },
  ],
}))

// --- Predictive: forecast band ---
const predictiveSeries = computed(() => {
  const hist = fc.value.history.slice(-40).map((d) => ({ x: d.x, y: d.close }))
  return [
    { name: 'Harga historis', color: '#0f3d3c', data: hist },
    { name: 'Proyeksi', color: '#2f7fb0', dashed: true, fill: false, data: fc.value.points.map((p) => ({ x: p.x, y: p.mid })) },
    { name: 'Batas atas', color: '#cbd5dd', width: 1, fill: false, data: fc.value.points.map((p) => ({ x: p.x, y: p.upper })) },
    { name: 'Batas bawah', color: '#cbd5dd', width: 1, fill: false, data: fc.value.points.map((p) => ({ x: p.x, y: p.lower })) },
  ]
})

// --- Prescriptive recommendation ---
const prescriptive = computed(() => {
  const rsiNow = rsiArr.value.at(-1)
  const bull = ma20arr.value.at(-1) > ma50arr.value.at(-1)
  const fcUp = fc.value.changePct > 1
  let score = 0
  if (bull) score += 1
  if (fcUp) score += 1
  if (rsiNow < 70) score += 1
  if (rsiNow < 30) score += 1

  let action, tone, reason
  if (score >= 3) {
    action = 'BUY / ACCUMULATE'
    tone = 'up'
    reason = 'Tren bullish, momentum belum jenuh, dan proyeksi harga positif.'
  } else if (score === 2) {
    action = 'HOLD'
    tone = 'neutral'
    reason = 'Sinyal campuran — tahan posisi dan tunggu konfirmasi arah.'
  } else {
    action = 'REDUCE / SELL'
    tone = 'down'
    reason = 'Tren melemah atau momentum jenuh, risiko koreksi meningkat.'
  }
  const last = descriptive.value.last
  return {
    action, tone, reason,
    entry: last,
    target: Math.round(fc.value.projected),
    stop: Math.round(last * 0.94),
    confidence: 55 + score * 10,
  }
})
</script>

<template>
  <div>
    <div class="page-intro">
      <h2>Technical Analysis — {{ market.selected }}</h2>
      <p>Empat lapis analitik: dari deskripsi kondisi hingga rekomendasi aksi.</p>
    </div>

    <div class="tabs">
      <button v-for="t in tabs" :key="t.key" :class="{ active: tab === t.key }" @click="tab = t.key">
        <strong>{{ t.label }}</strong>
        <span>{{ t.q }}</span>
      </button>
    </div>

    <!-- Descriptive -->
    <div v-if="tab === 'descriptive'">
      <div class="metric-row">
        <div class="card mini"><span>Return 120 hari</span><strong :class="descriptive.ret >= 0 ? 'up' : 'down'">{{ pct(descriptive.ret) }}</strong></div>
        <div class="card mini"><span>Volatilitas (annualized)</span><strong>{{ descriptive.vol.toFixed(1) }}%</strong></div>
        <div class="card mini"><span>Tren saat ini</span><strong :class="descriptive.trend === 'Uptrend' ? 'up' : 'down'">{{ descriptive.trend }}</strong></div>
        <div class="card mini"><span>Rata-rata volume</span><strong>{{ number(Math.round(descriptive.avgVol)) }}</strong></div>
      </div>
      <section class="card">
        <div class="card__head"><div><h3>Ringkasan Pergerakan Harga</h3><p>Candlestick dengan MA20 & MA50</p></div></div>
        <CandleChart :ohlc="ohlc" :overlays="maOverlays" :height="360" />
      </section>
    </div>

    <!-- Diagnostic -->
    <div v-else-if="tab === 'diagnostic'">
      <section class="card">
        <div class="card__head"><div><h3>Temuan Diagnostik</h3><p>Faktor yang menjelaskan pergerakan terakhir</p></div></div>
        <ul class="signals">
          <li v-for="(s, i) in diagnostic.signals" :key="i">
            <span class="dot" :class="`dot--${s.tone}`"></span>{{ s.text }}
          </li>
        </ul>
      </section>
      <section class="card">
        <div class="card__head"><div><h3>Relative Strength Index (RSI 14)</h3></div></div>
        <AreaChart :series="rsiSeries" type="line" :height="280" :annotations="rsiAnnotations" :y-formatter="(v) => v.toFixed(0)" />
      </section>
    </div>

    <!-- Predictive -->
    <div v-else-if="tab === 'predictive'">
      <div class="metric-row">
        <div class="card mini"><span>Harga saat ini</span><strong>{{ rupiah(descriptive.last) }}</strong></div>
        <div class="card mini"><span>Proyeksi 20 hari</span><strong>{{ rupiah(fc.projected) }}</strong></div>
        <div class="card mini"><span>Estimasi perubahan</span><strong :class="fc.changePct >= 0 ? 'up' : 'down'">{{ pct(fc.changePct) }}</strong></div>
      </div>
      <section class="card">
        <div class="card__head"><div><h3>Proyeksi Harga + Confidence Band</h3><p>Model tren linier (least-squares) atas 30 hari terakhir · ilustrasi</p></div></div>
        <AreaChart :series="predictiveSeries" type="line" :height="360" />
      </section>
    </div>

    <!-- Prescriptive -->
    <div v-else>
      <div class="rec card" :class="`rec--${prescriptive.tone}`">
        <div class="rec-badge">{{ prescriptive.action }}</div>
        <p class="rec-reason">{{ prescriptive.reason }}</p>
        <div class="rec-meta">
          <div><span>Entry</span><strong>{{ rupiah(prescriptive.entry) }}</strong></div>
          <div><span>Target</span><strong class="up">{{ rupiah(prescriptive.target) }}</strong></div>
          <div><span>Stop loss</span><strong class="down">{{ rupiah(prescriptive.stop) }}</strong></div>
          <div><span>Confidence</span><strong>{{ prescriptive.confidence }}%</strong></div>
        </div>
      </div>
      <section class="card">
        <div class="card__head"><div><h3>Dasar Rekomendasi</h3></div></div>
        <ul class="signals">
          <li v-for="(s, i) in diagnostic.signals" :key="i"><span class="dot" :class="`dot--${s.tone}`"></span>{{ s.text }}</li>
          <li><span class="dot" :class="fc.changePct >= 0 ? 'dot--up' : 'dot--down'"></span>Proyeksi model: {{ pct(fc.changePct) }} dalam 20 hari.</li>
        </ul>
        <p class="disclaimer">⚠️ Rekomendasi dihasilkan otomatis dari indikator teknikal dan bersifat ilustratif — bukan ajakan jual/beli.</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.tabs {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 18px;
}
.tabs button {
  text-align: left;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 14px 16px;
  transition: border-color 0.14s, box-shadow 0.14s;
}
.tabs button.active {
  border-color: var(--brand);
  box-shadow: 0 0 0 3px rgba(15, 61, 60, 0.08);
}
.tabs strong {
  display: block;
  font-size: 14.5px;
  color: var(--text);
}
.tabs span {
  font-size: 12px;
  color: var(--text-muted);
}
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
.card {
  margin-bottom: 16px;
}
.signals {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.signals li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 14px;
  color: var(--text);
}
.dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  margin-top: 5px;
  flex-shrink: 0;
}
.dot--up {
  background: var(--up);
}
.dot--down {
  background: var(--down);
}
.dot--neutral {
  background: var(--text-faint);
}
.rec {
  border-left: 5px solid var(--text-faint);
}
.rec--up {
  border-left-color: var(--up);
}
.rec--down {
  border-left-color: var(--down);
}
.rec--neutral {
  border-left-color: var(--amber, #d9a300);
}
.rec-badge {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.01em;
}
.rec--up .rec-badge {
  color: var(--up);
}
.rec--down .rec-badge {
  color: var(--down);
}
.rec--neutral .rec-badge {
  color: #b45309;
}
.rec-reason {
  color: var(--text-muted);
  margin: 8px 0 18px;
  font-size: 14px;
}
.rec-meta {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.rec-meta div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.rec-meta span {
  font-size: 12px;
  color: var(--text-faint);
}
.rec-meta strong {
  font-size: 18px;
  font-weight: 700;
}
.disclaimer {
  margin-top: 16px;
  font-size: 12.5px;
  color: var(--text-faint);
}
@media (max-width: 900px) {
  .tabs,
  .metric-row,
  .rec-meta {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
