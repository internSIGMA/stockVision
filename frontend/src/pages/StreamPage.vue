<script setup>
import { ref, computed } from 'vue';
import { Plus, Settings, Building2, Star, Users } from 'lucide-vue-next';
import { useMarketStore } from '../store/market.js';
import { useAuthStore } from '../store/auth.js';
import { useEmitenData } from '../composables/useEmitenData.js';

import EmitenHeader from '../components/EmitenHeader.vue';
import StatCard from '../components/StatCard.vue';
import StatusPill from '../components/StatusPill.vue';
import EmptyState from '../components/EmptyState.vue';
import CandlestickChart from '../components/CandlestickChart.vue';
import ForeignFlowChart from '../components/ForeignFlowChart.vue';
import Sheet from '../components/ui/Sheet.vue';
import WatchlistManagerPage from './WatchlistManagerPage.vue';

const market = useMarketStore();
const auth = useAuthStore();
const sheetOpen = ref(false);

const { ohlc, summary, insider, broker, fundamental, technical } = useEmitenData(
  () => market.selectedTicker,
  { ohlc: true, summary: true, insider: true, broker: true, fundamental: true, technical: true, days: 90 }
);

const dailyRecords = computed(() => [...ohlc.value].reverse().slice(0, 60));

function fmtRp(n) {
  return 'Rp ' + Math.round(n).toLocaleString('id-ID');
}
function fmtNum(n) {
  return Math.round(n).toLocaleString('id-ID');
}
const marketStatus = computed(() => {
  const h = new Date().getHours();
  return h >= 9 && h < 16 ? 'OPEN' : 'CLOSED';
});
</script>

<template>
  <div>
    <EmitenHeader :ticker="market.selectedTicker" />

    <div class="grid-2 section-gap">
      <!-- LEFT: watchlist & focus emiten -->
      <div class="card card-pad">
        <div class="wl-select-row">
          <select class="wl-select">
            <option>Daftar Pantau Utama</option>
          </select>
          <button class="icon-btn" title="Tambah watchlist baru"><Plus :size="15" /></button>
          <button class="icon-btn" title="Kelola watchlist" @click="sheetOpen = true"><Settings :size="15" /></button>
        </div>

        <div class="card-title" style="margin-bottom: 2px;"><Building2 :size="15" /> Focus Emiten</div>
        <div class="card-sub" style="margin-bottom: 10px;">
          Emiten dalam daftar pantau kamu — klik untuk ganti fokus, klik bintang untuk menandai emiten utama.
        </div>

        <div
          v-for="t in auth.user.watchlist"
          :key="t"
          class="wl-item"
          :class="{ active: t === market.selectedTicker }"
          @click="market.setTicker(t)"
        >
          <span class="mono item-name">{{ t }}</span>
          <button
            class="star-btn"
            :class="{ fav: t === auth.user.emitenUtama }"
            :aria-label="`Tandai ${t} sebagai emiten utama`"
            @click.stop="auth.setEmitenUtama(t)"
          >
            <Star :size="16" :fill="t === auth.user.emitenUtama ? 'currentColor' : 'none'" />
          </button>
        </div>
      </div>

      <!-- RIGHT: promo banner + 4 stat cards -->
      <div>
        <div class="promo-banner">
          <div>
            <span class="promo-badge">STOCKVISION PRO FEATURES</span>
            <div class="promo-title">Analisis mendalam, sinyal lebih cepat</div>
            <div class="promo-desc">Buka indikator lanjutan dan peringatan real-time untuk seluruh watchlist kamu.</div>
          </div>
          <button class="btn promo-cta">Upgrade</button>
        </div>

        <div v-if="summary" class="grid-4" style="margin-top: 12px;">
          <StatCard
            label="Last Price & Change"
            :value="fmtRp(summary.price)"
            :sub="(summary.change >= 0 ? '+' : '') + fmtNum(summary.change) + ' (' + summary.change_pct.toFixed(2) + '%)'"
          />
          <StatCard label="Best Bid" :value="fmtRp(summary.price - 5)" sub="Lot: 120" />
          <StatCard label="Best Offer" :value="fmtRp(summary.price + 5)" sub="Lot: 85" />
          <StatCard
            label="Volume & Market Status"
            :value="fmtNum(summary.volume)"
            :flag="marketStatus"
            :flag-tone="marketStatus === 'OPEN' ? 'up' : 'muted'"
          />
        </div>
      </div>
    </div>

    <div class="card card-pad section-gap">
      <div class="card-head">
        <div>
          <div class="card-title">Historical Candlestick — {{ market.selectedTicker }}</div>
          <div class="card-sub">ApexCharts dengan data real-time terambil dari database local.</div>
        </div>
        <span class="badge">{{ ohlc.length }} trading days</span>
      </div>
      <CandlestickChart v-if="ohlc.length" :rows="ohlc" />
    </div>

    <div class="card card-pad section-gap">
      <div class="card-head">
        <div class="card-title">Foreign Flow Activity (IDR)</div>
      </div>
      <ForeignFlowChart v-if="ohlc.length" :rows="ohlc" />
    </div>

    <div class="grid-2b section-gap">
      <div class="card card-pad">
        <div class="card-title" style="margin-bottom: 10px;">Technical</div>
        <div v-for="t in technical" :key="t.label" class="tech-row">
          <span class="lbl">{{ t.label }}</span>
          <span class="val mono">{{ t.value }} <span class="sig">· {{ t.sig }}</span></span>
        </div>
      </div>

      <div class="card card-pad">
        <div class="card-title" style="margin-bottom: 6px;">Analysis & Broker Summary</div>
        <div v-if="fundamental" class="card-sub">
          Fundamental ringkas: PER {{ fundamental.per }}x · PBV {{ fundamental.pbv }}x
          · Dividend Yield {{ fundamental.dividend_yield }}% · rating konsensus {{ fundamental.consensus }}.
        </div>
        <template v-if="broker">
          <div class="broker-list-title">Top Buy</div>
          <div v-for="b in broker.top_buy" :key="'buy' + b.code" class="broker-row">
            <span class="code">{{ b.code }}</span><span class="val mono up-text">{{ fmtRp(b.value) }}</span>
          </div>
          <div class="broker-list-title">Top Sell</div>
          <div v-for="b in broker.top_sell" :key="'sell' + b.code" class="broker-row">
            <span class="code">{{ b.code }}</span><span class="val mono down-text">{{ fmtRp(b.value) }}</span>
          </div>
        </template>
        <span class="see-all">Lihat semua →</span>
      </div>
    </div>

    <div class="grid-2b section-gap">
      <div class="card card-pad">
        <div class="card-head">
          <div class="card-title"><Users :size="15" /> Insider Transactions <span class="badge">Global Activity</span></div>
          <span class="badge">{{ insider.length }} recent trades</span>
        </div>
        <div v-if="insider.length" class="table-wrap">
          <table>
            <thead>
              <tr><th scope="col">Date</th><th scope="col">Ticker</th><th scope="col">Insider Name</th><th scope="col">Action</th><th scope="col">Shares</th></tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in insider" :key="i">
                <td class="td-mono">{{ r.date }}</td>
                <td style="font-weight: 700;">{{ r.ticker }}</td>
                <td>{{ r.insider_name }}</td>
                <td><StatusPill :status="r.action" /></td>
                <td class="td-mono">{{ fmtNum(r.shares) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <EmptyState v-else text="Belum ada transaksi insider." />
      </div>

      <div class="card card-pad">
        <div class="card-head"><div class="card-title">📋 Historical Records</div></div>
        <div class="table-wrap">
          <table>
            <thead>
              <tr><th scope="col">Date</th><th scope="col">Open</th><th scope="col">High</th><th scope="col">Low</th><th scope="col">Close</th><th scope="col">Net Flow</th></tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in dailyRecords" :key="i">
                <td class="td-mono">{{ r.date }}</td>
                <td class="td-mono">{{ fmtNum(r.open) }}</td>
                <td class="td-mono">{{ fmtNum(r.high) }}</td>
                <td class="td-mono">{{ fmtNum(r.low) }}</td>
                <td class="td-close">{{ fmtNum(r.close) }}</td>
                <td class="td-mono" :class="r.foreign_flow >= 0 ? 'up-text' : 'down-text'">{{ (r.foreign_flow / 1e9).toFixed(1) }}B</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <Sheet :open="sheetOpen" title="Kelola Watchlist" @close="sheetOpen = false">
      <WatchlistManagerPage @done="sheetOpen = false" />
    </Sheet>
  </div>
</template>

<style scoped>
.wl-select-row { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.wl-select {
  flex: 1; padding: 8px 10px; border-radius: 8px; border: 1px solid var(--border);
  background: var(--paper); color: var(--ink); font-weight: 600; font-size: 13px;
}
.wl-item {
  display: flex; align-items: center; justify-content: space-between; padding: 9px 10px; border-radius: 8px;
  cursor: pointer; border: 1px solid transparent;
}
.wl-item:hover { background: var(--surface-sunken); }
.wl-item.active { background: var(--primary-bg); border-color: color-mix(in srgb, var(--primary) 25%, transparent); }
.item-name { font-weight: 700; font-size: 13.5px; }
.star-btn { background: none; border: none; cursor: pointer; padding: 2px; display: flex; color: var(--border-strong); }
.star-btn.fav { color: var(--skip); }

.promo-banner {
  border-radius: var(--radius); padding: 18px 20px; color: #fff; position: relative; overflow: hidden;
  background: linear-gradient(135deg, #1E2A6E 0%, #2A52E0 55%, #5B7FF0 100%);
  display: flex; align-items: center; justify-content: space-between; gap: 16px; min-height: 96px;
}
.promo-badge { font-family: var(--font-mono); font-size: 10.5px; font-weight: 700; letter-spacing: .06em; background: rgba(255, 255, 255, .16); padding: 3px 9px; border-radius: 20px; display: inline-block; margin-bottom: 8px; }
.promo-title { font-size: 16px; font-weight: 800; letter-spacing: -.01em; }
.promo-desc { font-size: 12px; opacity: .85; margin-top: 3px; max-width: 340px; }
.promo-cta { background: #fff; color: var(--primary); border: none; flex: none; }

.tech-row { display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 13px; }
.tech-row:last-child { border-bottom: none; }
.tech-row .lbl { color: var(--ink-muted); font-weight: 600; }
.tech-row .sig { color: var(--ink-muted); font-weight: 500; }

.broker-list-title { font-size: 11px; font-weight: 700; letter-spacing: .05em; text-transform: uppercase; color: var(--ink-muted); margin: 10px 0 6px; }
.broker-row { display: flex; justify-content: space-between; font-size: 12.5px; padding: 5px 0; border-bottom: 1px dashed var(--border); }
.broker-row:last-child { border-bottom: none; }
.broker-row .code { font-weight: 700; }
.see-all { font-size: 11.5px; font-weight: 600; color: var(--primary); cursor: pointer; margin-top: 6px; display: inline-block; }
</style>
