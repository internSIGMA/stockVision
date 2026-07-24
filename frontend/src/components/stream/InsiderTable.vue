<script setup>
import { computed } from 'vue'
import { Users } from '@lucide/vue'
import { formatCompact, formatDate } from '@/utils/format'
import StatusPill from '@/components/ui/StatusPill.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const MAKS = 30

const terbaru = computed(() =>
  props.rows
    .slice()
    .sort((a, b) => new Date(b.tanggal) - new Date(a.tanggal))
    .slice(0, MAKS),
)

/** Backend memakai istilah beli/jual pada kolom `aksi`. */
function aksiLabel(aksi) {
  const a = String(aksi || '').toLowerCase()
  if (a.includes('buy') || a.includes('beli')) return 'BUY'
  if (a.includes('sell') || a.includes('jual')) return 'SELL'
  return String(aksi || '—').toUpperCase()
}
</script>

<template>
  <section class="flex min-w-0 flex-col rounded-lg border-[0.5px] border-border bg-card">
    <header class="flex items-center gap-2 border-b-[0.5px] border-border px-3.5 py-2.5">
      <Users class="size-3.5 text-muted-foreground" aria-hidden="true" />
      <h2 class="text-[13px] font-medium">Insider Transactions</h2>
      <span class="tabular ml-auto text-[10px] text-muted-foreground">
        {{ terbaru.length }} transaksi terakhir
      </span>
    </header>

    <div v-if="loading" class="flex flex-col gap-1.5 p-3.5">
      <div v-for="i in 6" :key="i" class="h-[24px] animate-pulse rounded bg-muted" />
    </div>

    <EmptyState
      v-else-if="!terbaru.length"
      title="Belum ada transaksi insider"
      description="Data majorholder untuk emiten ini belum tersedia di database."
    />

    <!-- data-lenis-prevent: tabel punya scroll sendiri, jangan dibajak Lenis. -->
    <div v-else class="max-h-[320px] overflow-auto" data-lenis-prevent>
      <table class="w-full border-collapse text-[11px]">
        <thead class="sticky top-0 z-10 bg-card">
          <tr class="border-b-[0.5px] border-border text-left text-muted-foreground">
            <th scope="col" class="whitespace-nowrap px-3 py-2 font-medium">Date</th>
            <th scope="col" class="whitespace-nowrap px-3 py-2 font-medium">Ticker</th>
            <th scope="col" class="whitespace-nowrap px-3 py-2 font-medium">Insider Name</th>
            <th scope="col" class="whitespace-nowrap px-3 py-2 font-medium">Action</th>
            <th scope="col" class="whitespace-nowrap px-3 py-2 text-right font-medium">Shares</th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="(row, i) in terbaru"
            :key="row.id_trx ?? `${row.symbol}-${row.tanggal}-${i}`"
            class="border-b-[0.5px] border-border last:border-0 hover:bg-accent/50"
          >
            <td class="tabular whitespace-nowrap px-3 py-2 text-muted-foreground">
              {{ formatDate(row.tanggal) }}
            </td>
            <td class="tabular whitespace-nowrap px-3 py-2 font-medium">{{ row.symbol }}</td>
            <td class="max-w-[180px] truncate px-3 py-2" :title="row.nama">{{ row.nama || '—' }}</td>
            <td class="px-3 py-2">
              <StatusPill :label="aksiLabel(row.aksi)" />
            </td>
            <td class="tabular whitespace-nowrap px-3 py-2 text-right">
              {{ formatCompact(row.perubahan) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
