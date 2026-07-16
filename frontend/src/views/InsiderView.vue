<script setup>
import { computed, ref } from 'vue'
import { useMarketStore } from '@/stores/market'
import { insiderActivity } from '@/data/market'
import { number, rupiah, rupiahShort } from '@/utils/format'

const market = useMarketStore()
const filter = ref('all') // all | buy | sell

const all = computed(() => insiderActivity(market.selected))
const rows = computed(() =>
  filter.value === 'all' ? all.value : all.value.filter((t) => t.type === filter.value),
)

const totals = computed(() => {
  const buy = all.value.filter((t) => t.type === 'buy').reduce((a, b) => a + b.value, 0)
  const sell = all.value.filter((t) => t.type === 'sell').reduce((a, b) => a + b.value, 0)
  return { buy, sell, net: buy - sell }
})
</script>

<template>
  <div>
    <div class="page-intro">
      <h2>Insider & Backdoor Activity — {{ market.selected }}</h2>
      <p>Transaksi orang dalam (direksi, komisaris, pemegang saham &gt;5%) hasil crawling laporan keterbukaan informasi.</p>
    </div>

    <div class="alert" v-if="totals.net < 0">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4m0 4h.01M10.3 3.9 2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" stroke-linecap="round" stroke-linejoin="round"/></svg>
      Terdeteksi <strong>net distribusi</strong> oleh orang dalam sebesar {{ rupiahShort(Math.abs(totals.net)) }} — perlu diwaspadai.
    </div>

    <div class="stat-row">
      <div class="card mini"><span>Total Akumulasi Insider</span><strong class="up">{{ rupiahShort(totals.buy) }}</strong></div>
      <div class="card mini"><span>Total Distribusi Insider</span><strong class="down">{{ rupiahShort(totals.sell) }}</strong></div>
      <div class="card mini"><span>Net Insider Flow</span><strong :class="totals.net >= 0 ? 'up' : 'down'">{{ rupiahShort(totals.net) }}</strong></div>
    </div>

    <section class="card">
      <div class="card__head">
        <div><h3>Riwayat Transaksi</h3><p>{{ rows.length }} transaksi</p></div>
        <div class="filter-tabs">
          <button :class="{ active: filter === 'all' }" @click="filter = 'all'">Semua</button>
          <button :class="{ active: filter === 'buy' }" @click="filter = 'buy'">Beli</button>
          <button :class="{ active: filter === 'sell' }" @click="filter = 'sell'">Jual</button>
        </div>
      </div>
      <div style="overflow-x:auto">
        <table class="dtable">
          <thead>
            <tr>
              <th>Tanggal</th><th>Nama</th><th>Jabatan</th><th>Aksi</th>
              <th class="num">Lembar</th><th class="num">Harga</th><th class="num">Nilai</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(t, i) in rows" :key="i">
              <td class="tabular">{{ t.date }}</td>
              <td class="strong">{{ t.name }}</td>
              <td>{{ t.role }}</td>
              <td>
                <span class="pill" :class="t.type === 'buy' ? 'pill--up' : 'pill--down'">
                  {{ t.type === 'buy' ? 'BELI' : 'JUAL' }}
                </span>
                <span class="purpose">{{ t.purpose }}</span>
              </td>
              <td class="num">{{ number(t.shares) }}</td>
              <td class="num">{{ rupiah(t.price) }}</td>
              <td class="num strong">{{ rupiahShort(t.value) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.alert {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #fef3c7;
  color: #92400e;
  border: 1px solid #fde68a;
  border-radius: var(--radius-sm);
  padding: 12px 16px;
  font-size: 13.5px;
  margin-bottom: 16px;
}
.stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
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
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.up {
  color: var(--up);
}
.down {
  color: var(--down);
}
.filter-tabs {
  display: flex;
  gap: 4px;
  background: var(--surface-2);
  padding: 4px;
  border-radius: 10px;
}
.filter-tabs button {
  padding: 6px 14px;
  border-radius: 7px;
  font-size: 12.5px;
  font-weight: 600;
  color: var(--text-muted);
}
.filter-tabs button.active {
  background: var(--surface);
  color: var(--brand);
  box-shadow: var(--shadow);
}
.purpose {
  font-size: 11.5px;
  color: var(--text-faint);
  margin-left: 8px;
}
@media (max-width: 900px) {
  .stat-row {
    grid-template-columns: 1fr;
  }
}
</style>
