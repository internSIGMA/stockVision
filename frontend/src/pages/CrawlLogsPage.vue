<script setup>
import { computed, onMounted, ref } from 'vue'
import { ClipboardList, RefreshCw } from '@lucide/vue'
import { getCrawlLogs, SUPPORTED_TICKERS } from '@/api/StockVision'
import { useAutoRefresh } from '@/composables/useAutoRefresh'
import { formatNumber } from '@/utils/format'
import StatusPill from '@/components/ui/StatusPill.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

const REFRESH_MS = 5000
const LIMIT = 50
const SEMUA = '__semua__'

const logs = ref([])
const loading = ref(true)
const memuatUlang = ref(false)
const error = ref(null)

const autoRefresh = ref(true)

const status = ref(SEMUA)
const ticker = ref(SEMUA)
const rentang = ref('semua')

const RENTANG = [
  { key: 'hari-ini', label: 'Hari ini', hari: 1 },
  { key: '7-hari', label: '7 Hari', hari: 7 },
  { key: 'semua', label: 'Semua', hari: null },
]

async function muat({ manual = false } = {}) {
  if (manual) memuatUlang.value = true
  try {
    const data = await getCrawlLogs({ limit: LIMIT })
    // Terbaru di atas — jangan bergantung pada urutan backend.
    logs.value = (Array.isArray(data) ? data : [])
      .slice()
      .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    error.value = null
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
    memuatUlang.value = false
  }
}

onMounted(() => muat())
useAutoRefresh(muat, REFRESH_MS, autoRefresh)

const batas = computed(() => {
  const pilihan = RENTANG.find((r) => r.key === rentang.value)
  if (!pilihan?.hari) return null

  const d = new Date()
  d.setHours(0, 0, 0, 0)
  d.setDate(d.getDate() - (pilihan.hari - 1))
  return d
})

const terfilter = computed(() =>
  logs.value.filter((log) => {
    if (status.value !== SEMUA && log.status !== status.value) return false
    if (ticker.value !== SEMUA && log.target !== ticker.value) return false
    if (batas.value && new Date(log.created_at) < batas.value) return false
    return true
  }),
)

const ringkasan = computed(() => {
  const hitung = { SUCCESS: 0, FAILED: 0, SKIP: 0 }
  for (const log of terfilter.value) if (log.status in hitung) hitung[log.status]++
  return hitung
})

/** Timestamp penuh YYYY-MM-DD HH:mm:ss, bukan tanggal ringkas. */
function waktuPenuh(value) {
  if (!value) return '—'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return String(value)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function tanggalTarget(value) {
  return value ? String(value).slice(0, 10) : '—'
}

/** Job majorholder/broker berlaku untuk seluruh pasar, bukan satu emiten. */
function target(log) {
  return log.target || 'ALL'
}
</script>

<template>
  <div class="flex flex-col gap-4 p-4">
    <section class="rounded-lg border-[0.5px] border-border bg-card">
      <header class="flex flex-wrap items-center gap-3 border-b-[0.5px] border-border px-3.5 py-3">
        <div class="flex items-center gap-2">
          <ClipboardList class="size-4 text-muted-foreground" aria-hidden="true" />
          <div>
            <h1 class="text-[14px] font-medium">Crawl Jobs Logs</h1>
            <p class="mt-0.5 text-[11px] text-muted-foreground">
              Log catatan pekerjaan crawling data yang berhasil diproses oleh scheduler.
            </p>
          </div>
        </div>

        <div class="ml-auto flex items-center gap-3">
          <Button variant="outline" size="sm" :disabled="memuatUlang" @click="muat({ manual: true })">
            <RefreshCw class="size-3.5" :class="{ 'animate-spin': memuatUlang }" />
            Refresh Logs
          </Button>
        </div>
      </header>

      <!-- Filter bar: progressive enhancement, tabelnya bisa panjang. -->
      <div class="flex flex-wrap items-center gap-2 border-b-[0.5px] border-border px-3.5 py-2.5">
        <div class="flex items-center gap-1" role="group" aria-label="Filter rentang waktu">
          <button
            v-for="r in RENTANG"
            :key="r.key"
            type="button"
            class="rounded-full border px-2.5 py-1 text-[11px] transition-colors"
            :class="
              rentang === r.key
                ? 'border-foreground bg-foreground text-background'
                : 'border-border text-muted-foreground hover:text-foreground'
            "
            :aria-pressed="rentang === r.key"
            @click="rentang = r.key"
          >
            {{ r.label }}
          </button>
        </div>

        <Select v-model="status">
          <SelectTrigger class="h-8 w-[150px] min-w-0" aria-label="Filter status">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem :value="SEMUA">Semua status</SelectItem>
            <SelectItem value="SUCCESS">SUCCESS</SelectItem>
            <SelectItem value="FAILED">FAILED</SelectItem>
            <SelectItem value="SKIP">SKIP</SelectItem>
          </SelectContent>
        </Select>

        <Select v-model="ticker">
          <SelectTrigger class="h-8 w-[150px] min-w-0" aria-label="Filter emiten">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem :value="SEMUA">Semua emiten</SelectItem>
            <SelectItem v-for="t in SUPPORTED_TICKERS" :key="t" :value="t">{{ t }}</SelectItem>
          </SelectContent>
        </Select>

        <div class="ml-auto flex items-center gap-2">
          <span
            v-for="s in ['SUCCESS', 'FAILED', 'SKIP']"
            :key="s"
            class="flex items-center gap-1.5"
          >
            <StatusPill :label="s" />
            <span class="tabular text-[12px] font-medium">{{ ringkasan[s] }}</span>
          </span>
        </div>
      </div>

      <div v-if="loading" class="flex flex-col gap-1.5 p-3.5">
        <div v-for="i in 8" :key="i" class="h-[26px] animate-pulse rounded bg-muted" />
      </div>

      <EmptyState v-else-if="error" title="Gagal memuat crawl logs" :description="error">
        <template #action>
          <Button variant="outline" size="sm" @click="muat({ manual: true })">Coba lagi</Button>
        </template>
      </EmptyState>

      <EmptyState
        v-else-if="!terfilter.length"
        title="Belum ada riwayat crawl."
        description="Tidak ada job yang cocok dengan filter ini."
      />

      <div v-else class="overflow-x-auto" data-lenis-prevent>
        <table class="w-full border-collapse text-[11px]">
          <thead>
            <tr class="border-b-[0.5px] border-border text-left text-muted-foreground">
              <th scope="col" class="whitespace-nowrap px-3 py-2 font-medium">Job ID</th>
              <th scope="col" class="whitespace-nowrap px-3 py-2 font-medium">Job Type</th>
              <th scope="col" class="whitespace-nowrap px-3 py-2 font-medium">Target Ticker</th>
              <th scope="col" class="whitespace-nowrap px-3 py-2 font-medium">Target Date</th>
              <th scope="col" class="whitespace-nowrap px-3 py-2 font-medium">Status</th>
              <th scope="col" class="whitespace-nowrap px-3 py-2 text-right font-medium">
                Records
              </th>
              <th scope="col" class="whitespace-nowrap px-3 py-2 font-medium">Created At</th>
              <th scope="col" class="px-3 py-2 font-medium">Error Message</th>
            </tr>
          </thead>

          <tbody>
            <tr
              v-for="log in terfilter"
              :key="log.id"
              class="border-b-[0.5px] border-border last:border-0 hover:bg-accent/50"
            >
              <td class="tabular whitespace-nowrap px-3 py-2 text-muted-foreground">
                {{ log.id }}
              </td>
              <td class="tabular whitespace-nowrap px-3 py-2 font-semibold uppercase">
                {{ log.job_type || '—' }}
              </td>
              <td class="tabular whitespace-nowrap px-3 py-2 font-medium">{{ target(log) }}</td>
              <td class="tabular whitespace-nowrap px-3 py-2 text-muted-foreground">
                {{ tanggalTarget(log.tanggal_target) }}
              </td>
              <td class="px-3 py-2">
                <StatusPill :label="log.status" />
              </td>
              <td class="tabular whitespace-nowrap px-3 py-2 text-right">
                {{ formatNumber(log.records_count) }}
              </td>
              <td class="tabular whitespace-nowrap px-3 py-2 text-muted-foreground">
                {{ waktuPenuh(log.created_at) }}
              </td>
              <td
                class="max-w-[260px] truncate px-3 py-2"
                :class="log.error_message ? 'text-[var(--color-down-ink)]' : 'text-muted-foreground'"
                :title="log.error_message || ''"
              >
                {{ log.error_message || '-' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
