<script setup>
import { computed } from 'vue'
import { Activity } from '@lucide/vue'
import { parseRingkasan } from '@/utils/prescriptive'
import { formatCompact, formatDate, formatNumber, formatPercent, trendClass } from '@/utils/format'
import StatusPill from '@/components/ui/StatusPill.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const props = defineProps({
  /** Baris diagnostic_results untuk emiten aktif — dari useDiagnostic. */
  backend: { type: Object, default: null },
  backendLoading: { type: Boolean, default: false },
  /** Empat temuan yang sudah dinormalkan useDiagnostic. */
  temuan: { type: Array, default: () => [] },
})

const ringkasan = computed(() => parseRingkasan(props.backend?.llm_diagnostic_summary))

const fundamental = computed(() => {
  const f = props.backend?.fundamental_context
  if (!f) return []
  return [
    { nama: 'Beta', teks: formatNumber(f.beta, { decimals: 2 }) },
    { nama: 'PE', teks: f.trailing_pe == null ? '—' : `${formatNumber(f.trailing_pe, { decimals: 1 })}x` },
    // ROE disimpan sebagai rasio (-0.0116), bukan persen — dikali 100 di sini.
    { nama: 'ROE', teks: f.roe == null ? '—' : formatPercent(f.roe * 100, 1) },
  ]
})

/** Satu formatter untuk semua metrik supaya panelnya tetap satu bentuk. */
function tampilkan(metrik) {
  const { nilai, format } = metrik
  if (nilai == null || nilai === '' || nilai === '-') return '—'

  switch (format) {
    case 'angka':
      return formatNumber(nilai, { decimals: 2 })
    case 'angka2':
      return formatNumber(nilai, { decimals: 2 })
    case 'persen':
      return formatPercent(nilai, 2)
    case 'rupiahRingkas':
      return `Rp ${formatCompact(nilai)}`
    case 'ringkas':
      return formatCompact(nilai)
    default:
      return String(nilai)
  }
}

/** Hanya metrik berarah yang diberi warna; kode broker dan volume tidak. */
function warnaMetrik(metrik) {
  if (metrik.format === 'persen' || metrik.format === 'rupiahRingkas') {
    return trendClass(metrik.nilai)
  }
  return 'text-foreground'
}
</script>

<template>
  <div
    class="flex h-full flex-col gap-4 rounded-xl border-[0.5px] border-[var(--primary-light)]/50 bg-[var(--background-secondary)] p-4 sm:p-5"
  >
    <!-- Bar judul disamakan dengan panel preskriptif supaya keduanya terbaca sepasang -->
    <header class="flex flex-wrap items-start justify-between gap-3">
      <h2
        class="flex items-center rounded-full border-[0.5px] border-border bg-card px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-foreground"
      >
        Analisis Diagnostik
      </h2>

      <p class="text-[10px] text-muted-foreground">
        Data terakhir diupdate:
        <span class="tabular">
          {{ backend?.tanggal_analisis ? formatDate(backend.tanggal_analisis) : '—' }}
        </span>
      </p>
    </header>

    <div v-if="backendLoading" class="flex flex-col gap-2">
      <div v-for="i in 8" :key="i" class="h-3 animate-pulse rounded bg-muted" />
    </div>

    <EmptyState
      v-else-if="!backend"
      :icon="Activity"
      title="Diagnostik belum tersedia"
      description="Emiten ini belum masuk hasil pipeline diagnostik terakhir."
    />

    <template v-else>
      <div v-if="ringkasan.length" class="flex gap-4 sm:gap-5">
        <!-- Maskot AI -->
        <svg
          class="hidden size-[64px] shrink-0 sm:block lg:size-[76px]"
          viewBox="0 0 96 96"
          fill="none"
          aria-hidden="true"
        >
          <circle cx="48" cy="10" r="4.5" fill="var(--primary-light)" />
          <path d="M48 14v9" stroke="var(--primary)" stroke-width="3" stroke-linecap="round" />
          <rect x="5" y="40" width="9" height="20" rx="4.5" fill="var(--primary-light)" />
          <rect x="82" y="40" width="9" height="20" rx="4.5" fill="var(--primary-light)" />
          <rect x="14" y="23" width="68" height="56" rx="19" fill="var(--primary)" />
          <rect x="25" y="34" width="46" height="29" rx="12" fill="var(--chart-5)" />
          <circle cx="39" cy="48.5" r="5.5" fill="var(--primary-light)" />
          <circle cx="57" cy="48.5" r="5.5" fill="var(--primary-light)" />
          <rect x="40" y="69" width="16" height="4" rx="2" fill="var(--primary-light)" opacity="0.55" />
        </svg>

        <div class="min-w-0 flex-1">
          <p
            v-for="p in ringkasan"
            :key="p.id"
            class="mb-3 text-[12.5px] leading-[1.75] text-[var(--foreground-body)] last:mb-0"
          >
            <template v-for="(b, i) in p.bagian" :key="i">
              <strong
                v-if="b.gaya === 'tebal'"
                class="font-semibold text-foreground"
              >{{ b.teks }}</strong>
              <em
                v-else-if="b.gaya === 'miring'"
                class="font-medium not-italic text-foreground"
              >“{{ b.teks }}”</em>
              <template v-else>{{ b.teks }}</template>
            </template>
          </p>
        </div>
      </div>

      <!-- Pertanyaan yang dijawab panel ini, dinyatakan terang-terangan:
           preskriptif menjawab "harus apa", diagnostik menjawab "kenapa". -->
      <div class="flex flex-col gap-2.5 border-t-[0.5px] border-border pt-4 mt-1">
        <p class="-mt-1 text-[11px] italic leading-relaxed text-muted-foreground mb-1">
          Kenapa harganya bergerak begini? Empat temuan di bawah menelusuri sebabnya.
        </p>

        <ul class="flex flex-col gap-2.5">
          <li
            v-for="t in temuan"
            :key="t.key"
            class="rounded-lg border-[0.5px] border-border bg-card p-3"
          >
            <div class="flex flex-wrap items-center justify-between gap-2">
              <span class="text-[12px] font-semibold text-foreground">{{ t.judul }}</span>
              <StatusPill :label="t.label" :tone="t.tone" />
            </div>

            <dl class="mt-2.5 flex flex-wrap gap-x-4 gap-y-1.5">
              <div v-for="m in t.metrik" :key="m.nama" class="flex items-baseline gap-1.5">
                <dt class="text-[10px] text-muted-foreground">{{ m.nama }}</dt>
                <dd class="tabular text-[12px] font-semibold" :class="warnaMetrik(m)">
                  {{ tampilkan(m) }}
                </dd>
              </div>
            </dl>
          </li>
        </ul>
      </div>

      <!-- Konteks fundamental: bukan temuan, tapi latar yang membuat temuan terbaca -->
      <div
        v-if="fundamental.length"
        class="flex flex-wrap gap-x-4 gap-y-1.5 rounded-lg border-[0.5px] border-border px-3 py-2.5 mt-1"
      >
        <span class="text-[10px] font-semibold uppercase tracking-[0.06em] text-muted-foreground">
          Konteks Fundamental
        </span>
        <div v-for="f in fundamental" :key="f.nama" class="flex items-baseline gap-1.5">
          <span class="text-[10px] text-muted-foreground">{{ f.nama }}</span>
          <span class="tabular text-[12px] font-semibold">{{ f.teks }}</span>
        </div>
      </div>

      <p class="mt-auto border-t-[0.5px] border-border pt-2.5 text-[10px] text-muted-foreground">
        Diagnostik menjelaskan sebab, bukan rekomendasi beli atau jual.
      </p>
    </template>
  </div>
</template>
