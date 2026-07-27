<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { CalendarClock, Clock, Loader2, RefreshCw, Target, Zap } from '@lucide/vue'
import {
  getSchedulerStatus,
  toggleScheduler,
  triggerSchedulerNow,
} from '@/api/StockVision'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { useNotify } from '@/composables/useNotify'
import { useAuthStore } from '@/stores/auth'
import { formatNumber } from '@/utils/format'
import TrendingStocksStrip from '@/components/shared/TrendingStocksStrip.vue'
import StatusPill from '@/components/ui/StatusPill.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { Button } from '@/components/ui/button'

const REFRESH_MS = 5000

const auth = useAuthStore()
const notify = useNotify()

const data = ref(null)
const loading = ref(true)
const memuatUlang = ref(false)
const error = ref(null)

const memicu = ref(false)
const mengubah = ref(false)

const scheduler = computed(() => data.value?.scheduler ?? null)
const market = computed(() => data.value?.market ?? null)
const history = computed(() => data.value?.history ?? [])

/** Scheduler mengabarkan target-nya sendiri; watchlist user hanya cadangan. */
const targets = computed(() => {
  const t = data.value?.targets
  return Array.isArray(t) && t.length ? t : auth.watchlist
})

const berjalan = computed(() => !!scheduler.value?.running)
const hariTrading = computed(() => !!market.value?.is_trading_day)
const jamBursaBuka = computed(() => !!market.value?.is_trading_hours)

// Jam dinding lokal: backend hanya mengirim waktu saat response dibuat,
// jadi detiknya akan membeku kalau tidak diticking sendiri.
const sekarang = ref(new Date())
let jam = null
onMounted(() => {
  jam = setInterval(() => (sekarang.value = new Date()), 1000)
})
onUnmounted(() => clearInterval(jam))

const waktuWib = computed(() => {
  const d = sekarang.value
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
})

async function muat({ manual = false } = {}) {
  if (manual) memuatUlang.value = true
  try {
    data.value = await getSchedulerStatus()
    error.value = null
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
    memuatUlang.value = false
  }
}

onMounted(() => muat())
useAutoRefresh(muat, REFRESH_MS, computed(() => !memicu.value))

/** Backend tidak punya /scheduler/toggle — ON/OFF dipetakan ke start/stop. */
async function ubahAktif() {
  if (mengubah.value) return

  const nyalakan = !berjalan.value
  mengubah.value = true
  try {
    await toggleScheduler(nyalakan)
    notify.success(nyalakan ? 'Scheduler dijalankan' : 'Scheduler dihentikan')
    await muat()
  } catch (err) {
    notify.error('Gagal mengubah scheduler', err.message)
  } finally {
    mengubah.value = false
  }
}

async function picuManual() {
  if (memicu.value) return

  memicu.value = true
  try {
    await triggerSchedulerNow()
    notify.success('Crawl manual selesai')
    await muat()
  } catch (err) {
    notify.error('Crawl manual gagal', err.message)
  } finally {
    memicu.value = false
  }
}

function nilai(row, ...keys) {
  for (const k of keys) {
    if (row?.[k] !== undefined && row[k] !== null) return row[k]
  }
  return null
}
</script>

<template>
  <div class="flex flex-col gap-4 p-4">
    <TrendingStocksStrip />

    <!-- Header -->
    <header class="flex flex-wrap items-center gap-3">
      <div class="flex items-center gap-2">
        <Clock class="size-4 text-muted-foreground" aria-hidden="true" />
        <div>
          <h1 class="text-[16px] font-semibold tracking-[-0.01em]">Auto Crawling Scheduler</h1>
          <p class="mt-0.5 text-[11px] text-muted-foreground">
            Crawling otomatis pada jam bursa, hanya di hari trading.
          </p>
        </div>
      </div>

      <Button
        variant="outline"
        size="sm"
        class="ml-auto"
        :disabled="memuatUlang"
        @click="muat({ manual: true })"
      >
        <RefreshCw class="size-3.5" :class="{ 'animate-spin': memuatUlang }" />
        Refresh
      </Button>
    </header>

    <div v-if="loading" class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <div v-for="i in 4" :key="i" class="h-[124px] animate-pulse rounded-lg bg-muted" />
    </div>

    <EmptyState v-else-if="error" title="Gagal memuat status scheduler" :description="error">
      <template #action>
        <Button variant="outline" size="sm" @click="muat({ manual: true })">Coba lagi</Button>
      </template>
    </EmptyState>

    <template v-else>
      <!-- 3 stat card -->
      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
        <!-- Status + Start/Stop -->
        <div class="flex flex-col rounded-lg border-[0.5px] border-border bg-card p-3.5">
          <p class="text-[10px] uppercase tracking-[0.06em] text-muted-foreground">
            Scheduler Status
          </p>
          <p
            class="mt-1.5 flex items-center gap-1.5 text-[19px] font-semibold leading-none"
            :class="berjalan ? 'text-up' : 'text-muted-foreground'"
          >
            <span aria-hidden="true">●</span>
            {{ berjalan ? 'RUNNING' : 'STOPPED' }}
          </p>

          <Button
            :variant="berjalan ? 'destructive' : 'default'"
            size="sm"
            class="mt-3 w-full"
            :disabled="mengubah"
            @click="ubahAktif"
          >
            {{ mengubah ? '…' : berjalan ? 'Stop' : 'Start' }}
          </Button>
        </div>

        <!-- Sesi bursa: hari trading + status buka/tutup + jam & waktu berjalan -->
        <div class="flex flex-col rounded-lg border-[0.5px] border-border bg-card p-3.5">
          <p class="text-[10px] uppercase tracking-[0.06em] text-muted-foreground">Sesi Bursa</p>

          <div class="mt-1.5 flex items-center gap-2">
            <span
              class="text-[19px] font-semibold leading-none"
              :class="hariTrading ? 'text-up' : 'text-muted-foreground'"
            >
              {{ hariTrading ? 'YA' : 'TIDAK' }}
            </span>
            <span class="text-[11px] text-muted-foreground">hari trading</span>
            <StatusPill
              class="ml-auto"
              :label="jamBursaBuka ? 'BUKA' : 'TUTUP'"
              :tone="jamBursaBuka ? 'up' : 'neutral'"
            />
          </div>

          <p class="tabular mt-2 text-[11px] text-muted-foreground">
            Jam Bursa: {{ market?.market_hours || '—' }}
          </p>
          <p class="tabular mt-0.5 text-[11px] text-muted-foreground" role="status">
            {{ waktuWib }} WIB
          </p>
        </div>

        <!-- Statistik -->
        <div class="flex flex-col rounded-lg border-[0.5px] border-border bg-card p-3.5">
          <p class="text-[10px] uppercase tracking-[0.06em] text-muted-foreground">
            Statistik Crawl
          </p>
          <dl class="mt-1.5 grid grid-cols-3 gap-2">
            <div>
              <dd class="tabular text-[19px] font-semibold leading-none">
                {{ formatNumber(scheduler?.total_runs) }}
              </dd>
              <dt class="mt-1 text-[10px] text-muted-foreground">Total</dt>
            </div>
            <div>
              <dd class="tabular text-[19px] font-semibold leading-none text-up">
                {{ formatNumber(scheduler?.total_success) }}
              </dd>
              <dt class="mt-1 text-[10px] text-muted-foreground">Sukses</dt>
            </div>
            <div>
              <dd class="tabular text-[19px] font-semibold leading-none text-skip">
                {{ formatNumber(scheduler?.total_skipped) }}
              </dd>
              <dt class="mt-1 text-[10px] text-muted-foreground">Skip</dt>
            </div>
          </dl>
        </div>
      </div>

      <!-- Manual trigger + target emiten -->
      <div class="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_2fr]">
        <section class="flex flex-col rounded-lg border-[0.5px] border-border bg-card">
          <header class="flex items-center gap-2 border-b-[0.5px] border-border px-3.5 py-2.5">
            <Zap class="size-3.5 text-muted-foreground" aria-hidden="true" />
            <h2 class="text-[13px] font-medium">Manual Trigger</h2>
          </header>

          <div class="flex flex-1 flex-col gap-3 p-3.5">
            <p class="text-[12px] leading-relaxed text-muted-foreground">
              Jalankan crawl sekarang juga tanpa menunggu scheduler (bypass jam bursa).
            </p>

            <Button
              class="mt-auto w-full"
              :disabled="memicu || scheduler?.crawl_in_progress"
              @click="picuManual"
            >
              <Loader2 v-if="memicu" class="size-4 animate-spin" />
              <Zap v-else class="size-4" />
              {{ memicu ? 'Menjalankan crawl…' : 'Trigger Crawl Sekarang' }}
            </Button>

            <p
              v-if="scheduler?.crawl_in_progress && !memicu"
              class="text-[11px] text-muted-foreground"
              role="status"
            >
              Scheduler sedang meng-crawl — tunggu sampai selesai.
            </p>
          </div>
        </section>

        <section class="flex flex-col rounded-lg border-[0.5px] border-border bg-card">
          <header class="flex items-center gap-2 border-b-[0.5px] border-border px-3.5 py-2.5">
            <Target class="size-3.5 text-muted-foreground" aria-hidden="true" />
            <h2 class="text-[13px] font-medium">Target Emiten</h2>
          </header>

          <div class="flex flex-col gap-3 p-3.5">
            <p class="text-[12px] leading-relaxed text-muted-foreground">
              Emiten yang akan di-crawl otomatis (Stock Info + OHLC).
            </p>

            <EmptyState v-if="!targets.length" title="Belum ada target emiten" />

            <ul v-else class="grid grid-cols-2 gap-2 sm:grid-cols-3">
              <li
                v-for="t in targets"
                :key="t"
                class="flex items-center gap-2 rounded-md border-[0.5px] border-border px-2.5 py-2"
              >
                <span
                  class="flex size-7 shrink-0 items-center justify-center rounded-full bg-[var(--color-info-bg)] text-[11px] font-semibold text-[var(--color-info-ink)]"
                  aria-hidden="true"
                >
                  {{ t.charAt(0) }}
                </span>
                <div class="min-w-0">
                  <p class="tabular truncate text-[12px] font-semibold">{{ t }}</p>
                  <p class="truncate text-[10px] text-muted-foreground">Stock Info + OHLC</p>
                </div>
              </li>
            </ul>
          </div>
        </section>
      </div>

      <!-- Riwayat -->
      <section class="rounded-lg border-[0.5px] border-border bg-card">
        <header class="flex items-center gap-2 border-b-[0.5px] border-border px-3.5 py-2.5">
          <CalendarClock class="size-3.5 text-muted-foreground" aria-hidden="true" />
          <h2 class="text-[13px] font-medium">Riwayat Eksekusi Scheduler</h2>
          <span
            class="tabular ml-auto rounded-full border-[0.5px] border-border px-2 py-0.5 text-[10px] text-muted-foreground"
          >
            {{ history.length }} entries
          </span>
        </header>

        <EmptyState
          v-if="!history.length"
          title="Belum ada riwayat eksekusi scheduler."
          description="Riwayat akan muncul setelah scheduler berjalan."
        />

        <div v-else class="max-h-[320px] overflow-auto" data-lenis-prevent>
          <table class="w-full border-collapse text-[11px]">
            <thead class="sticky top-0 z-10 bg-card">
              <tr class="border-b-[0.5px] border-border text-left text-muted-foreground">
                <th scope="col" class="whitespace-nowrap px-3 py-2 font-medium">Waktu</th>
                <th scope="col" class="whitespace-nowrap px-3 py-2 font-medium">Status</th>
                <th scope="col" class="px-3 py-2 font-medium">Detail</th>
                <th scope="col" class="whitespace-nowrap px-3 py-2 font-medium">Emiten</th>
              </tr>
            </thead>

            <tbody>
              <tr
                v-for="(h, i) in history"
                :key="i"
                class="border-b-[0.5px] border-border last:border-0 hover:bg-accent/50"
              >
                <td class="tabular whitespace-nowrap px-3 py-2 text-muted-foreground">
                  {{ nilai(h, 'timestamp', 'waktu', 'time', 'created_at') ?? '—' }}
                </td>
                <td class="px-3 py-2">
                  <StatusPill
                    :label="String(nilai(h, 'status', 'result') ?? '—').toUpperCase()"
                  />
                </td>
                <td
                  class="max-w-[280px] truncate px-3 py-2 text-muted-foreground"
                  :title="nilai(h, 'message', 'detail', 'keterangan') ?? ''"
                >
                  {{ nilai(h, 'message', 'detail', 'keterangan') ?? '—' }}
                </td>
                <td class="tabular whitespace-nowrap px-3 py-2">
                  {{ nilai(h, 'symbol', 'ticker', 'target', 'emiten') ?? 'ALL' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>
