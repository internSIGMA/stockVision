<script setup>
import { ref, computed, onMounted } from 'vue';
import { ClipboardList, RefreshCw } from 'lucide-vue-next';
import { getCrawlLogs, TICKERS } from '../lib/mockApi.js';
import { useNotify } from '../composables/useNotify.js';
import StatusPill from '../components/StatusPill.vue';
import EmptyState from '../components/EmptyState.vue';

const logs = ref([]);
const loading = ref(true);
const statusFilter = ref('ALL');
const tickerFilter = ref('ALL');
const notify = useNotify();

async function load() {
  loading.value = true;
  logs.value = await getCrawlLogs({ limit: 50 });
  loading.value = false;
}

async function refresh() {
  await load();
  notify.success('Log crawl diperbarui.');
}

onMounted(load);

const filtered = computed(() =>
  logs.value.filter(
    (l) =>
      (statusFilter.value === 'ALL' || l.status === statusFilter.value) &&
      (tickerFilter.value === 'ALL' || l.target_ticker === tickerFilter.value)
  )
);
</script>

<template>
  <div class="card card-pad">
    <div class="card-head">
      <div>
        <div class="card-title"><ClipboardList :size="15" /> Crawl Jobs Logs</div>
        <div class="card-sub">Log catatan pekerjaan crawling data yang berhasil diproses oleh scheduler.</div>
      </div>
      <button class="btn" @click="refresh"><RefreshCw :size="13" /> Refresh Logs</button>
    </div>

    <div class="filter-bar">
      <select v-model="statusFilter" aria-label="Filter status">
        <option value="ALL">Semua Status</option>
        <option value="SUCCESS">SUCCESS</option>
        <option value="FAILED">FAILED</option>
        <option value="SKIP">SKIP</option>
      </select>
      <select v-model="tickerFilter" aria-label="Filter ticker">
        <option value="ALL">Semua Ticker</option>
        <option v-for="t in TICKERS" :key="t" :value="t">{{ t }}</option>
      </select>
    </div>

    <div v-if="loading" class="skel-stack">
      <div v-for="i in 6" :key="i" class="skel skel-row"></div>
    </div>
    <EmptyState v-else-if="filtered.length === 0" text="Belum ada riwayat crawl." />
    <div v-else class="table-wrap" style="max-height: 560px;">
      <table>
        <thead>
          <tr>
            <th scope="col">Job ID</th><th scope="col">Job Type</th><th scope="col">Target Ticker</th>
            <th scope="col">Target Date</th><th scope="col">Status</th><th scope="col">Records</th>
            <th scope="col">Created At</th><th scope="col">Error Message</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in filtered" :key="row.job_id">
            <td class="td-link">{{ row.job_id }}</td>
            <td class="td-mono job-type">{{ row.job_type }}</td>
            <td style="font-weight: 700;">{{ row.target_ticker }}</td>
            <td class="td-mono">{{ row.target_date }}</td>
            <td><StatusPill :status="row.status" /></td>
            <td class="td-mono">{{ row.records_count }}</td>
            <td class="td-mono">{{ row.created_at }}</td>
            <td>
              <span v-if="row.error_message" class="err-text" :title="row.error_message">{{ row.error_message }}</span>
              <span v-else style="color: var(--ink-faint);">-</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.job-type { font-weight: 700; text-transform: uppercase; }
.skel-stack { display: flex; flex-direction: column; gap: 8px; }
.skel-row { height: 34px; }
</style>
