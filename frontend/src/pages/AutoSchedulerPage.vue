<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { Clock, RefreshCw, Calendar, CheckCircle2, Zap, Target, Loader2 } from 'lucide-vue-next';
import {
  getSchedulerStatus,
  toggleScheduler,
  triggerSchedulerManual,
  getSchedulerHistory,
} from '../lib/mockApi.js';
import { useAuthStore } from '../store/auth.js';
import { useNotify } from '../composables/useNotify.js';
import StatCard from '../components/StatCard.vue';
import StatusPill from '../components/StatusPill.vue';
import EmptyState from '../components/EmptyState.vue';

const auth = useAuthStore();
const notify = useNotify();

const status = ref(null);
const history = ref([]);
const loadingHistory = ref(true);
const triggering = ref(false);
const now = ref(new Date());
let clockTimer = null;

async function loadStatus() {
  status.value = await getSchedulerStatus();
}
async function loadHistory() {
  loadingHistory.value = true;
  history.value = await getSchedulerHistory();
  loadingHistory.value = false;
}

async function refreshAll() {
  await Promise.all([loadStatus(), loadHistory()]);
  notify.success('Status scheduler diperbarui.');
}

async function handleToggle() {
  const next = !status.value.active;
  await toggleScheduler(next);
  await loadStatus();
  notify.info(next ? 'Scheduler dijalankan.' : 'Scheduler dihentikan.');
}

async function handleManualTrigger() {
  triggering.value = true;
  await triggerSchedulerManual();
  await Promise.all([loadStatus(), loadHistory()]);
  triggering.value = false;
  notify.success('Crawl manual selesai dijalankan.');
}

function fmtTs(d) {
  return d.toISOString().slice(0, 10) + ' ' + d.toTimeString().slice(0, 8) + ' WIB';
}

onMounted(() => {
  loadStatus();
  loadHistory();
  clockTimer = setInterval(() => (now.value = new Date()), 1000);
});
onBeforeUnmount(() => clearInterval(clockTimer));

const nextRun = computed(() => (status.value?.active ? '14:30 WIB' : 'Tidak dijadwalkan'));
const lastResult = computed(() => (history.value.length ? history.value[0].detail : 'Belum pernah berjalan'));
</script>

<template>
  <div>
    <div class="page-head">
      <div>
        <div class="card-title" style="font-size: 16px;"><Clock :size="16" /> Auto Crawling Scheduler</div>
        <div class="card-sub">Crawling otomatis setiap 30 menit pada jam bursa, hanya di hari trading.</div>
      </div>
      <button class="btn" @click="refreshAll"><RefreshCw :size="13" /> Refresh</button>
    </div>

    <div v-if="status" class="grid-4">
      <div class="card stat-card">
        <div class="stat-label">Scheduler Status</div>
        <div class="stat-value" :style="{ color: status.active ? 'var(--up)' : 'var(--ink-muted)' }">
          <span class="live-dot" :class="status.active ? 'on' : 'off'"></span>{{ status.active ? 'RUNNING' : 'STOPPED' }}
        </div>
        <button class="btn btn-block" style="margin-top: 10px;" @click="handleToggle">
          {{ status.active ? 'Stop' : 'Start' }}
        </button>
      </div>

      <StatCard label="Hari Trading" :value="status.is_trading_day ? 'YA' : 'TIDAK'" sub="Jam Bursa: 08:45 - 16:15 WIB" />

      <div class="card stat-card">
        <div class="stat-label">Jam Bursa</div>
        <span class="market-pill" :class="status.market_open ? 'pill-success' : 'pill-idle'">
          ● {{ status.market_open ? 'BUKA' : 'TUTUP' }}
        </span>
        <div class="stat-sub" style="margin-top: 8px;">{{ fmtTs(now) }}</div>
      </div>

      <div class="card stat-card">
        <div class="stat-label">Statistik Crawl</div>
        <div class="stat-triplet">
          <div><div class="mono big up-text">{{ status.stats.total }}</div><div class="stat-sub">Total</div></div>
          <div><div class="mono big up-text">{{ status.stats.success }}</div><div class="stat-sub">Sukses</div></div>
          <div><div class="mono big skip-text">{{ status.stats.skip }}</div><div class="stat-sub">Skip</div></div>
        </div>
      </div>
    </div>

    <div class="grid-3 section-gap">
      <div class="card card-pad">
        <div class="mini-label"><Clock :size="14" /> Interval</div>
        <div class="mini-value">{{ status?.interval_minutes ?? 30 }} menit</div>
      </div>
      <div class="card card-pad">
        <div class="mini-label"><Calendar :size="14" /> Next Run</div>
        <div class="mini-value">{{ nextRun }}</div>
      </div>
      <div class="card card-pad">
        <div class="mini-label"><CheckCircle2 :size="14" /> Last Result</div>
        <div class="mini-value">{{ lastResult }}</div>
      </div>
    </div>

    <div class="grid-2b section-gap">
      <div class="card card-pad">
        <div class="card-title"><Zap :size="15" /> Manual Trigger</div>
        <div class="card-sub" style="margin: 6px 0 14px;">Jalankan crawl sekarang juga tanpa menunggu scheduler (bypass jam bursa).</div>
        <button class="btn btn-primary btn-block" :disabled="triggering" @click="handleManualTrigger">
          <Loader2 v-if="triggering" :size="14" class="spin" />
          <Zap v-else :size="14" />
          {{ triggering ? 'Memproses...' : 'Trigger Crawl Sekarang' }}
        </button>
      </div>

      <div class="card card-pad">
        <div class="card-title"><Target :size="15" /> Target Emiten</div>
        <div class="card-sub" style="margin: 6px 0 14px;">Emiten yang akan di-crawl otomatis (Stock Info + Insider Activity).</div>
        <div class="target-grid">
          <div v-for="t in auth.user.watchlist" :key="t" class="target-card">
            <div class="avatar">{{ t[0] }}</div>
            <div><div class="t">{{ t }}</div><div class="s">Stock Info + OHLC</div></div>
          </div>
        </div>
      </div>
    </div>

    <div class="card card-pad section-gap">
      <div class="card-head">
        <div class="card-title">🗓 Riwayat Eksekusi Scheduler</div>
        <span class="badge">{{ history.length }} entries</span>
      </div>
      <div v-if="loadingHistory" class="skel-stack">
        <div v-for="i in 5" :key="i" class="skel skel-row"></div>
      </div>
      <EmptyState v-else-if="history.length === 0" text="Belum ada riwayat eksekusi scheduler." />
      <div v-else class="table-wrap" style="max-height: 320px;">
        <table>
          <thead><tr><th scope="col">Waktu</th><th scope="col">Status</th><th scope="col">Detail</th><th scope="col">Emiten</th></tr></thead>
          <tbody>
            <tr v-for="(h, i) in history" :key="i">
              <td class="td-mono">{{ h.time }}</td>
              <td><StatusPill :status="h.status" /></td>
              <td>{{ h.detail }}</td>
              <td class="td-mono">{{ h.emiten }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-head { display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 16px; }
.stat-card { padding: 14px 16px; }
.stat-label { font-size: 11px; font-weight: 700; letter-spacing: .06em; color: var(--ink-muted); text-transform: uppercase; }
.stat-value { font-family: var(--font-mono); font-size: 21px; font-weight: 600; margin-top: 6px; }
.stat-sub { font-size: 11.5px; color: var(--ink-muted); margin-top: 4px; font-family: var(--font-mono); }
.market-pill {
  font-family: var(--font-mono); font-size: 11px; font-weight: 700; padding: 2.5px 8px; border-radius: 20px;
  display: inline-block; margin-top: 6px;
}
.pill-idle { background: var(--surface-sunken); color: var(--ink-muted); }
.stat-triplet { display: flex; gap: 14px; margin-top: 6px; }
.big { font-size: 19px; font-weight: 700; }
.skip-text { color: var(--skip); }
.mini-label { display: flex; align-items: center; gap: 6px; font-size: 11px; font-weight: 700; letter-spacing: .06em; color: var(--ink-muted); text-transform: uppercase; }
.mini-value { font-size: 16px; font-weight: 600; margin-top: 8px; }
.target-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 10px; }
.target-card { display: flex; align-items: center; gap: 10px; padding: 9px 10px; border: 1px solid var(--border); border-radius: 9px; background: var(--surface); }
.avatar { width: 32px; height: 32px; border-radius: 50%; background: var(--primary-bg); color: var(--primary); display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 13px; flex: none; }
.target-card .t { font-weight: 700; font-size: 13px; }
.target-card .s { font-size: 11px; color: var(--ink-muted); }
.spin { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.skel-stack { display: flex; flex-direction: column; gap: 8px; }
.skel-row { height: 30px; }
</style>
