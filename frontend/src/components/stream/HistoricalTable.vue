<script setup>
import { computed } from 'vue'
import { ClipboardList, Download } from '@lucide/vue'
import { formatCompact, formatDate, formatNumber } from '@/utils/format'
import EmptyState from '@/components/ui/EmptyState.vue'
import { Button } from '@/components/ui/button'
import { exportToCsv } from '@/utils/export'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  ticker: { type: String, default: '' },
})

/** Terbaru di atas — response backend urut ASC. */
const terbaru = computed(() => props.rows.slice().reverse())

function unduh() {
  exportToCsv(
    terbaru.value.map((r) => ({
      tanggal: String(r.tanggal).slice(0, 10),
      open: r.open,
      high: r.high,
      low: r.low,
      close: r.close,
      volume: r.volume,
      foreign_flow: r.foreign_flow,
    })),
    `${props.ticker || 'ohlc'}-historical.csv`,
  )
}
</script>

<template>
  <section class="flex min-w-0 flex-col rounded-lg border-[0.5px] border-border bg-card">
    <header class="flex items-center gap-2 border-b-[0.5px] border-border px-3.5 py-2.5">
      <ClipboardList class="size-3.5 text-muted-foreground" aria-hidden="true" />
      <h2 class="text-[13px] font-medium">Historical Records</h2>

      <Button
        v-if="terbaru.length"
        variant="ghost"
        size="sm"
        class="ml-auto h-6 px-2 text-[10px]"
        @click="unduh"
      >
        <Download class="size-3" />
        CSV
      </Button>
    </header>

    <div v-if="loading" class="flex flex-col gap-1.5 p-3.5">
      <div v-for="i in 6" :key="i" class="h-[24px] animate-pulse rounded bg-muted" />
    </div>

    <EmptyState
      v-else-if="!terbaru.length"
      title="Belum ada histori harga"
      description="Jalankan Trigger Crawler untuk mengambil data OHLC emiten ini."
    />

    <div v-else class="max-h-[320px] overflow-auto" data-lenis-prevent>
      <table class="w-full border-collapse text-[11px]">
        <thead class="sticky top-0 z-10 bg-card">
          <tr class="border-b-[0.5px] border-border text-left text-muted-foreground">
            <th scope="col" class="whitespace-nowrap px-3 py-2 font-medium">Date</th>
            <th scope="col" class="whitespace-nowrap px-3 py-2 text-right font-medium">Open</th>
            <th scope="col" class="whitespace-nowrap px-3 py-2 text-right font-medium">High</th>
            <th scope="col" class="whitespace-nowrap px-3 py-2 text-right font-medium">Low</th>
            <th scope="col" class="whitespace-nowrap px-3 py-2 text-right font-medium">Close</th>
            <th scope="col" class="whitespace-nowrap px-3 py-2 text-right font-medium">Net Flow</th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="(row, i) in terbaru"
            :key="`${row.tanggal}-${i}`"
            class="border-b-[0.5px] border-border last:border-0 hover:bg-accent/50"
          >
            <td class="tabular whitespace-nowrap px-3 py-2 text-muted-foreground">
              {{ formatDate(row.tanggal) }}
            </td>
            <td class="tabular whitespace-nowrap px-3 py-2 text-right">
              {{ formatNumber(row.open) }}
            </td>
            <td class="tabular whitespace-nowrap px-3 py-2 text-right">
              {{ formatNumber(row.high) }}
            </td>
            <td class="tabular whitespace-nowrap px-3 py-2 text-right">
              {{ formatNumber(row.low) }}
            </td>
            <td class="tabular whitespace-nowrap px-3 py-2 text-right font-semibold text-[var(--color-info-ink)]">
              {{ formatNumber(row.close) }}
            </td>
            <td
              class="tabular whitespace-nowrap px-3 py-2 text-right"
              :class="Number(row.foreign_flow) >= 0 ? 'text-up' : 'text-down'"
            >
              {{ formatCompact(row.foreign_flow) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
