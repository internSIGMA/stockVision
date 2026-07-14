<script setup>
import { computed } from 'vue'
import { summarizeIndicators } from '@/utils/technicalIndicators'
import StatusPill from '@/components/ui/StatusPill.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const indikator = computed(() => summarizeIndicators(props.rows))
</script>

<template>
  <section class="flex flex-col rounded-lg border-[0.5px] border-border bg-card">
    <header class="flex items-center justify-between border-b-[0.5px] border-border px-3.5 py-2.5">
      <h2 class="text-[13px] font-medium">Technical</h2>
      <span class="text-[10px] text-muted-foreground">Dihitung dari histori OHLC</span>
    </header>

    <div v-if="loading" class="flex flex-col gap-2 p-3.5">
      <div v-for="i in 6" :key="i" class="h-[30px] animate-pulse rounded bg-muted" />
    </div>

    <EmptyState
      v-else-if="!rows.length"
      title="Belum ada data OHLC"
      description="Jalankan Trigger Crawler untuk mengambil histori harga emiten ini."
    />

    <ul v-else class="divide-y-[0.5px] divide-border">
      <li
        v-for="ind in indikator"
        :key="ind.key"
        class="flex items-center justify-between gap-3 px-3.5 py-2.5"
      >
        <span class="text-[12px] text-muted-foreground">{{ ind.name }}</span>

        <div class="flex items-center gap-2">
          <span class="tabular text-[12px] font-medium">{{ ind.display }}</span>
          <StatusPill :label="ind.label" :tone="ind.tone" />
        </div>
      </li>
    </ul>
  </section>
</template>
