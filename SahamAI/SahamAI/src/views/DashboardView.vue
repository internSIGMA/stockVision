<script setup>
import { computed, ref } from 'vue'
import { useMarketStore } from '@/stores/market'
import { getEmiten, terminalStats, orderBook, doneTrades, generateOHLC } from '@/data/market'
import { number, rupiahShort, pct } from '@/utils/format'
import CandleChart from '@/components/charts/CandleChart.vue'
import BrokerSummaryView from './BrokerSummaryView.vue'
import PricesView from './PricesView.vue'
import TechnicalView from './TechnicalView.vue'
import ForecastingView from './ForecastingView.vue'
import InsiderView from './InsiderView.vue'
import CrawlingView from './CrawlingView.vue'
import WatchlistView from './WatchlistView.vue'

const market = useMarketStore()

// The single merged navigation bar (previously the top blue bar) now lives
// here, in the "purple" position below the chart/order buttons.
const tabs = [
  { key: 'emiten', label: 'Emiten' },
  { key: 'broker', label: 'Broker Summary' },
  { key: 'price', label: 'Daily Price' },
  { key: 'technical', label: 'Technical' },
  { key: 'analysis', label: 'Analysis' },
  { key: 'insider', label: 'Insider' },
  { key: 'crawling', label: 'Crawling' },
  { key: 'watchlist', label: 'Watchlist' },
]
const tab = ref('emiten')

const viewMap = {
  broker: BrokerSummaryView,
  price: PricesView,
  technical: TechnicalView,
  analysis: ForecastingView,
  insider: InsiderView,
  crawling: CrawlingView,
  watchlist: WatchlistView,
}

// Big chart + order buttons only on the Emiten tab (avoids duplicate charts
// on Daily Price / Technical which render their own).
const showTerminal = computed(() => tab.value === 'emiten')

const timeframes = [
  { l: '1D', d: 2 }, { l: '5D', d: 5 }, { l: '1M', d: 22 }, { l: '3M', d: 66 },
  { l: '6M', d: 120 }, { l: '1Y', d: 200 }, { l: '3Y', d: 260 }, { l: '5Y', d: 300 }, { l: '10Y', d: 360 },
]
const tf = ref(timeframes[2])

const em = computed(() => getEmiten(market.selected))
const st = computed(() => terminalStats(market.selected))
const ob = computed(() => orderBook(market.selected))
const trades = computed(() => doneTrades(market.selected))
const ohlc = computed(() => generateOHLC(market.selected, tf.value.d))
const up = computed(() => st.value.change >= 0)

const leftStats = computed(() => [
  { label: 'FREQ', value: number(st.value.freq) },
  { label: 'VALUE', value: rupiahShort(st.value.value) },
  { label: 'BID RATIO', value: st.value.bidRatio + '%' },
  { label: 'PREV', value: number(st.value.prev) },
  { label: 'OPEN', value: number(st.value.open) },
  { label: 'HIGH', value: number(st.value.high) },
  { label: 'LOW', value: number(st.value.low) },
  { label: 'AVG', value: number(st.value.avg) },
])
const maxLot = computed(() =>
  Math.max(...ob.value.bids.map((b) => b.lot), ...ob.value.offers.map((o) => o.lot)),
)

// Emiten tab sub-panels.
const subTabs = ['Orderbook', 'Done Summary']
const sub = ref('Orderbook')

const toast = ref('')
let toastTimer
function order(kind) {
  toast.value = `${kind} ${market.selected} — fitur order hanya demo.`
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = ''), 2600)
}
</script>

<template>
  <div class="term">
    <!-- Ticker header (always shown for context) -->
    <div class="thead">
      <div class="ticker">
        <span class="star" :class="{ on: market.favorites.includes(market.selected) }">★</span>
        <div>
          <div class="t-code">{{ market.selected }}<span class="t-name">{{ em.name }}</span></div>
          <div class="t-sector">{{ em.sector }}</div>
        </div>
      </div>
      <div class="price-block">
        <span class="t-price tabular" :class="up ? 'up' : 'down'">{{ number(st.last) }}</span>
        <span class="t-chg tabular" :class="up ? 'up' : 'down'">
          {{ up ? '▲' : '▼' }} {{ Math.abs(st.change) }} ({{ pct(st.changePct) }})
        </span>
      </div>
      <div v-if="showTerminal" class="tfs">
        <button v-for="t in timeframes" :key="t.l" :class="{ active: t.l === tf.l }" @click="tf = t">{{ t.l }}</button>
        <span class="charting">Charting</span>
      </div>
    </div>

    <!-- Terminal: chart + stat rail + order buttons (Emiten tab only) -->
    <template v-if="showTerminal">
      <div class="chart-row">
        <div class="rail">
          <div v-for="s in leftStats" :key="s.label" class="rail-row">
            <span class="rl">{{ s.label }}</span>
            <span class="rv tabular">{{ s.value }}</span>
          </div>
        </div>
        <div class="chart card">
          <CandleChart :ohlc="ohlc" :height="360" />
        </div>
      </div>

      <div class="orders">
        <button class="ob-btn buy-out" @click="order('Simple Buy')"><span>⤢</span> Simple Buy</button>
        <button class="ob-btn buy-solid" @click="order('Fast Buy')"><span>⚡</span> Fast Buy</button>
        <button class="ob-btn sell-out" @click="order('Fast Sell')"><span>⚡</span> Fast Sell</button>
        <button class="ob-btn sell-solid" @click="order('Simple Sell')"><span>⤡</span> Simple Sell</button>
      </div>

      <transition name="fade"><div v-if="toast" class="toast">{{ toast }}</div></transition>
    </template>

    <!-- MERGED NAV BAR (all menu items, in the "purple" position) -->
    <nav class="mainbar">
      <div class="mainbar-scroll">
        <button v-for="t in tabs" :key="t.key" class="mtab" :class="{ active: tab === t.key }" @click="tab = t.key">
          {{ t.label }}
        </button>
      </div>
    </nav>

    <!-- Content -->
    <div class="tabcontent">
      <!-- Emiten: orderbook / done summary -->
      <div v-if="tab === 'emiten'" class="card panels">
        <nav class="subtabs">
          <button v-for="p in subTabs" :key="p" :class="{ active: sub === p }" @click="sub = p">{{ p }}</button>
        </nav>

        <div v-if="sub === 'Orderbook'" class="orderbook">
          <div class="ob-col">
            <div class="ob-head"><span>BID LOT</span><span>BID</span></div>
            <div v-for="(b, i) in ob.bids" :key="i" class="ob-line">
              <div class="bar bid-bar" :style="{ width: (b.lot / maxLot) * 100 + '%' }"></div>
              <span class="lot tabular">{{ number(b.lot) }}</span>
              <span class="prc tabular up">{{ number(b.price) }}</span>
            </div>
            <div class="ob-total">Total Bid <strong class="up tabular">{{ number(ob.totalBid) }}</strong></div>
          </div>
          <div class="ob-col">
            <div class="ob-head"><span>OFFER</span><span>OFFER LOT</span></div>
            <div v-for="(o, i) in ob.offers" :key="i" class="ob-line">
              <div class="bar offer-bar" :style="{ width: (o.lot / maxLot) * 100 + '%' }"></div>
              <span class="prc tabular down">{{ number(o.price) }}</span>
              <span class="lot tabular">{{ number(o.lot) }}</span>
            </div>
            <div class="ob-total">Total Offer <strong class="down tabular">{{ number(ob.totalOffer) }}</strong></div>
          </div>
        </div>

        <div v-else class="done">
          <table class="dtable">
            <thead><tr><th>Waktu</th><th class="num">Harga</th><th class="num">Lot</th><th class="num">Sisi</th></tr></thead>
            <tbody>
              <tr v-for="(t, i) in trades" :key="i">
                <td class="tabular">{{ t.time }}</td>
                <td class="num tabular" :class="t.side === 'buy' ? 'up' : 'down'">{{ number(t.price) }}</td>
                <td class="num tabular">{{ number(t.lot) }}</td>
                <td class="num"><span class="pill" :class="t.side === 'buy' ? 'pill--up' : 'pill--down'">{{ t.side === 'buy' ? 'BELI' : 'JUAL' }}</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Other tabs render their full page -->
      <component v-else :is="viewMap[tab]" />
    </div>

    <!-- Favorites bar -->
    <div class="favbar">
      <span class="fav-label">★ FAVORIT {{ market.favorites.length }}</span>
      <div class="fav-scroll">
        <button
          v-for="q in market.favoriteQuotes"
          :key="q.code"
          class="fav"
          :class="{ active: q.code === market.selected }"
          @click="market.select(q.code)"
        >
          <span class="fav-code">{{ q.code }}</span>
          <span class="fav-chg tabular" :class="q.change >= 0 ? 'up' : 'down'">{{ pct(q.changePct) }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.term {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.up {
  color: var(--up);
}
.down {
  color: var(--down);
}

/* Ticker header */
.thead {
  display: flex;
  align-items: center;
  gap: 26px;
  flex-wrap: wrap;
}
.ticker {
  display: flex;
  align-items: center;
  gap: 12px;
}
.star {
  font-size: 20px;
  color: var(--text-faint);
}
.star.on {
  color: #f5b301;
}
.t-code {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.02em;
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.t-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-muted);
}
.t-sector {
  font-size: 12px;
  color: var(--text-faint);
}
.price-block {
  display: flex;
  flex-direction: column;
}
.t-price {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.02em;
}
.t-chg {
  font-size: 13px;
  font-weight: 700;
}
.tfs {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
  flex-wrap: wrap;
}
.tfs button {
  font-size: 12.5px;
  font-weight: 700;
  color: var(--text-muted);
  padding: 6px 10px;
  border-radius: 8px;
}
.tfs button.active {
  background: var(--brand);
  color: #04211e;
}
.charting {
  font-size: 12.5px;
  font-weight: 700;
  color: var(--brand);
  text-decoration: underline;
  margin-left: 10px;
}

/* Chart row */
.chart-row {
  display: grid;
  grid-template-columns: 160px 1fr;
  gap: 14px;
}
.rail {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.rail-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 11px 12px;
  border-bottom: 1px solid var(--border);
}
.rl {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--text-faint);
}
.rv {
  font-size: 13.5px;
  font-weight: 700;
}
.chart {
  padding: 12px;
  min-width: 0;
}

/* Order buttons */
.orders {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.ob-btn {
  padding: 13px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  border: 1.5px solid transparent;
  transition: filter 0.14s;
}
.ob-btn:hover {
  filter: brightness(1.12);
}
.buy-out {
  border-color: var(--brand);
  color: var(--brand);
  background: rgba(22, 184, 166, 0.08);
}
.buy-solid {
  background: var(--brand);
  color: #04211e;
}
.sell-out {
  border-color: var(--down);
  color: var(--down);
  background: rgba(239, 71, 87, 0.08);
}
.sell-solid {
  background: var(--down);
  color: #fff;
}
.toast {
  align-self: center;
  background: var(--surface-2);
  border: 1px solid var(--border);
  color: var(--text);
  padding: 10px 16px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
}

/* Merged nav bar (purple position) */
.mainbar {
  display: flex;
  justify-content: center;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 8px;
  position: sticky;
  top: 68px;
  z-index: 20;
}
.mainbar-scroll {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
  max-width: 100%;
}
.mainbar-scroll::-webkit-scrollbar {
  display: none;
}
.mtab {
  white-space: nowrap;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-muted);
  padding: 9px 16px;
  border-radius: 9px;
  border: 1px solid transparent;
  transition: color 0.14s, background 0.14s, border-color 0.14s;
}
.mtab:hover {
  color: var(--text);
  background: var(--surface-2);
}
.mtab.active {
  color: var(--text);
  background: var(--surface-2);
  border-color: var(--border);
}

/* Content */
.tabcontent {
  min-height: 200px;
}
.panels {
  padding: 0;
}
.subtabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid var(--border);
  padding: 6px 8px;
}
.subtabs button {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-muted);
  padding: 9px 14px;
  border-radius: 8px;
}
.subtabs button.active {
  color: var(--text);
  background: var(--surface-2);
}

/* Orderbook */
.orderbook {
  display: grid;
  grid-template-columns: 1fr 1fr;
  padding: 12px;
}
.ob-col {
  padding: 0 10px;
}
.ob-head {
  display: flex;
  justify-content: space-between;
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--text-faint);
  padding: 4px 0 8px;
}
.ob-line {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 8px;
  font-size: 13px;
  overflow: hidden;
  border-radius: 6px;
}
.bar {
  position: absolute;
  top: 0;
  bottom: 0;
  z-index: 0;
}
.bid-bar {
  right: 0;
  background: rgba(22, 199, 132, 0.12);
}
.offer-bar {
  left: 0;
  background: rgba(239, 71, 87, 0.12);
}
.ob-line .lot,
.ob-line .prc {
  position: relative;
  z-index: 1;
  font-weight: 700;
}
.ob-line .lot {
  color: var(--text-muted);
}
.ob-total {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-faint);
  padding: 10px 8px 4px;
  border-top: 1px solid var(--border);
  margin-top: 6px;
}
.done {
  padding: 6px 14px 14px;
}

/* Favorites bar */
.favbar {
  position: sticky;
  bottom: 0;
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--surface);
  border-top: 1px solid var(--border);
  padding: 10px 14px;
  margin: 8px -24px -24px;
}
.fav-label {
  font-size: 11.5px;
  font-weight: 800;
  color: #f5b301;
  flex-shrink: 0;
}
.fav-scroll {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 2px;
}
.fav {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 13px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--bg);
  flex-shrink: 0;
}
.fav.active {
  border-color: var(--brand);
  background: rgba(22, 184, 166, 0.08);
}
.fav-code {
  font-size: 12.5px;
  font-weight: 700;
  color: var(--text);
}
.fav-chg {
  font-size: 11.5px;
  font-weight: 700;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 820px) {
  .chart-row {
    grid-template-columns: 1fr;
  }
  .rail {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0;
  }
  .orders {
    grid-template-columns: 1fr 1fr;
  }
  .orderbook {
    grid-template-columns: 1fr;
  }
  .mainbar {
    justify-content: flex-start;
    top: 62px;
  }
  .favbar {
    margin: 8px -16px -16px;
  }
}
</style>
