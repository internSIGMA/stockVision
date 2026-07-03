<script setup>
import { computed } from 'vue'
import { useMarketStore } from '@/stores/market'
import { brokerSummary } from '@/data/market'
import { number, rupiahShort } from '@/utils/format'
import BarChart from '@/components/charts/BarChart.vue'

const market = useMarketStore()
const summary = computed(() => brokerSummary(market.selected))

const netChart = computed(() => {
  const rows = [...summary.value.rows].sort((a, b) => b.netLot - a.netLot)
  return {
    categories: rows.map((r) => r.broker),
    series: [{ name: 'Net lot', data: rows.map((r) => r.netLot) }],
    colors: rows.map((r) => (r.netLot >= 0 ? '#16a34a' : '#dc2626')),
  }
})

const totals = computed(() => {
  const buy = summary.value.buyers.reduce((a, b) => a + b.buyValue, 0)
  const sell = summary.value.sellers.reduce((a, b) => a + Math.abs(b.sellValue), 0)
  return { buy, sell, net: buy - sell }
})
</script>

<template>
  <div>
    <div class="page-intro">
      <h2>Broker Summary — {{ market.selected }}</h2>
      <p>Akumulasi & distribusi per broker hasil crawling Stockbit. Positif = net beli, negatif = net jual.</p>
    </div>

    <div class="top-grid">
      <div class="card mini">
        <span class="mini-label">Total Nilai Beli</span>
        <strong class="mini-val up">{{ rupiahShort(totals.buy) }}</strong>
      </div>
      <div class="card mini">
        <span class="mini-label">Total Nilai Jual</span>
        <strong class="mini-val down">{{ rupiahShort(totals.sell) }}</strong>
      </div>
      <div class="card mini">
        <span class="mini-label">Net Flow</span>
        <strong class="mini-val" :class="totals.net >= 0 ? 'up' : 'down'">{{ rupiahShort(totals.net) }}</strong>
      </div>
    </div>

    <section class="card">
      <div class="card__head">
        <div><h3>Net Lot per Broker</h3><p>Urut dari akumulasi terbesar ke distribusi terbesar</p></div>
      </div>
      <BarChart
        :categories="netChart.categories"
        :series="netChart.series"
        :colors="netChart.colors"
        :distributed="true"
        :height="300"
      />
    </section>

    <div class="two-col">
      <section class="card">
        <div class="card__head"><h3>🟢 Top Net Buyer</h3></div>
        <table class="dtable">
          <thead>
            <tr><th>Broker</th><th class="num">Net Lot</th><th class="num">Net Value</th></tr>
          </thead>
          <tbody>
            <tr v-for="b in summary.buyers" :key="b.broker">
              <td><strong class="strong">{{ b.broker }}</strong> <span class="bname">{{ b.name }}</span></td>
              <td class="num strong">{{ number(b.netLot) }}</td>
              <td class="num" style="color: var(--up)">{{ rupiahShort(b.netValue) }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="card">
        <div class="card__head"><h3>🔴 Top Net Seller</h3></div>
        <table class="dtable">
          <thead>
            <tr><th>Broker</th><th class="num">Net Lot</th><th class="num">Net Value</th></tr>
          </thead>
          <tbody>
            <tr v-for="s in summary.sellers" :key="s.broker">
              <td><strong class="strong">{{ s.broker }}</strong> <span class="bname">{{ s.name }}</span></td>
              <td class="num strong">{{ number(s.netLot) }}</td>
              <td class="num" style="color: var(--down)">{{ rupiahShort(s.netValue) }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>
  </div>
</template>

<style scoped>
.top-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}
.mini {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.mini-label {
  font-size: 12.5px;
  color: var(--text-muted);
}
.mini-val {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.02em;
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
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.bname {
  font-size: 12px;
  color: var(--text-faint);
  margin-left: 6px;
}
@media (max-width: 900px) {
  .top-grid,
  .two-col {
    grid-template-columns: 1fr;
  }
}
</style>
