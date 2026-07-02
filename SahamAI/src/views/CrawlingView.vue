<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { seedCrawlJobs } from '@/data/market'
import { number, timeAgo } from '@/utils/format'

const jobs = ref(seedCrawlJobs())
const now = ref(Date.now())

// Simulate live progress for running jobs + a ticking "last run" clock.
let timer
onMounted(() => {
  timer = setInterval(() => {
    now.value = Date.now()
    jobs.value = jobs.value.map((j) => {
      if (j.status === 'running') {
        const p = (j.progress ?? Math.random() * 40) + Math.random() * 12
        if (p >= 100) {
          return { ...j, status: 'success', progress: 100, records: Math.round(Math.random() * 4000 + 400), lastRun: new Date().toISOString() }
        }
        return { ...j, progress: p }
      }
      return j
    })
  }, 1500)
})
onUnmounted(() => clearInterval(timer))

const stats = computed(() => ({
  total: jobs.value.length,
  success: jobs.value.filter((j) => j.status === 'success').length,
  running: jobs.value.filter((j) => j.status === 'running').length,
  failed: jobs.value.filter((j) => j.status === 'failed').length,
}))

function retry(job) {
  const idx = jobs.value.findIndex((j) => j.id === job.id)
  if (idx !== -1) jobs.value[idx] = { ...jobs.value[idx], status: 'running', progress: 0, error: null }
}
function runAll() {
  jobs.value = jobs.value.map((j) => (j.status !== 'running' ? { ...j, status: 'running', progress: 0, error: null } : j))
}
</script>

<template>
  <div>
    <div class="page-intro head-flex">
      <div>
        <h2>Crawling Monitor</h2>
        <p>Status real-time job crawler per emiten & sumber data.</p>
      </div>
      <button class="btn btn--primary" @click="runAll">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-3-6.7M21 3v6h-6"/></svg>
        Jalankan semua
      </button>
    </div>

    <div class="stat-row">
      <div class="card mini"><span>Total job</span><strong>{{ stats.total }}</strong></div>
      <div class="card mini"><span>Sukses</span><strong class="up">{{ stats.success }}</strong></div>
      <div class="card mini"><span>Berjalan</span><strong class="info">{{ stats.running }}</strong></div>
      <div class="card mini"><span>Gagal</span><strong class="down">{{ stats.failed }}</strong></div>
    </div>

    <section class="card">
      <div class="card__head"><div><h3>Daftar Job</h3><p>Diperbarui otomatis setiap 1,5 detik</p></div></div>
      <div style="overflow-x:auto">
        <table class="dtable">
          <thead>
            <tr>
              <th>Emiten</th><th>Sumber</th><th>Status</th><th style="width:180px">Progress</th>
              <th class="num">Baris</th><th class="num">Durasi</th><th>Terakhir</th><th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="j in jobs" :key="j.id">
              <td class="strong">{{ j.code }}</td>
              <td>{{ j.source }}</td>
              <td>
                <span class="pill" :class="{
                  'pill--up': j.status === 'success',
                  'pill--info': j.status === 'running',
                  'pill--down': j.status === 'failed',
                }">
                  <span class="s-dot" :class="`sd--${j.status}`"></span>{{ j.status }}
                </span>
              </td>
              <td>
                <div v-if="j.status === 'running'" class="bar">
                  <div class="bar-fill" :style="{ width: (j.progress || 0) + '%' }"></div>
                </div>
                <span v-else-if="j.status === 'failed'" class="err">{{ j.error }}</span>
                <span v-else class="ok">Selesai 100%</span>
              </td>
              <td class="num">{{ number(j.records) }}</td>
              <td class="num tabular">{{ (j.durationMs / 1000).toFixed(1) }}s</td>
              <td>{{ timeAgo(j.lastRun) }}</td>
              <td>
                <button v-if="j.status === 'failed'" class="btn btn--ghost sm" @click="retry(j)">Ulangi</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<style scoped>
.head-flex {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
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
.info {
  color: var(--info, #2f7fb0);
}
.s-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  display: inline-block;
}
.sd--success {
  background: var(--up);
}
.sd--running {
  background: var(--info, #2f7fb0);
  animation: blink 1s infinite;
}
.sd--failed {
  background: var(--down);
}
@keyframes blink {
  50% {
    opacity: 0.3;
  }
}
.bar {
  height: 8px;
  background: var(--surface-2);
  border-radius: 999px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  background: var(--info, #2f7fb0);
  border-radius: 999px;
  transition: width 0.5s ease;
}
.err {
  font-size: 12px;
  color: var(--down);
}
.ok {
  font-size: 12px;
  color: var(--up);
}
.btn.sm {
  padding: 5px 10px;
  font-size: 12px;
}
@media (max-width: 900px) {
  .stat-row {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
