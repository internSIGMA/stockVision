<script setup>
import { computed, ref } from 'vue'
import { formatCompact, formatNumber } from '@/utils/format'
import EmptyState from '@/components/ui/EmptyState.vue'

/**
 * Gabungan Analysis + Broker Summary.
 *
 * Catatan: backend tidak punya endpoint fundamental (hanya stock-info, ohlc,
 * majorholder, broker-activity), jadi bagian "Analysis" di sini adalah ringkasan
 * yang diturunkan dari histori OHLC yang memang ada — bukan data fundamental.
 */
const props = defineProps({
  ohlc: { type: Array, default: () => [] },
  broker: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const RINGKAS = 5

const semua = ref(false)

const ringkasan = computed(() => {
  const rows = props.ohlc
  if (!rows.length) return null

  const highs = rows.map((r) => Number(r.high)).filter((n) => !Number.isNaN(n))
  const lows = rows.map((r) => Number(r.low)).filter((n) => !Number.isNaN(n))
  const volumes = rows.map((r) => Number(r.volume) || 0)
  const flows = rows.map((r) => Number(r.foreign_flow) || 0)

  return {
    tertinggi: highs.length ? Math.max(...highs) : null,
    terendah: lows.length ? Math.min(...lows) : null,
    volumeRata: volumes.length ? volumes.reduce((a, b) => a + b, 0) / volumes.length : null,
    flowTotal: flows.reduce((a, b) => a + b, 0),
    hari: rows.length,
  }
})

/** broker_activity dikelompokkan per broker; aksi BUY/SELL dari backend. */
function urut(aksi) {
  return props.broker
    .filter((b) => String(b.aksi).toUpperCase() === aksi)
    .slice()
    .sort((a, b) => Math.abs(Number(b.nilai_rp) || 0) - Math.abs(Number(a.nilai_rp) || 0))
}

const topBuy = computed(() => urut('BUY'))
const topSell = computed(() => urut('SELL'))

const buyTampil = computed(() => (semua.value ? topBuy.value : topBuy.value.slice(0, RINGKAS)))
const sellTampil = computed(() => (semua.value ? topSell.value : topSell.value.slice(0, RINGKAS)))

const bisaDiperluas = computed(
  () => topBuy.value.length > RINGKAS || topSell.value.length > RINGKAS,
)
</script>

<template>
  <section class="flex flex-col rounded-lg border-[0.5px] border-border bg-card">
    <header class="flex items-center justify-between border-b-[0.5px] border-border px-3.5 py-2.5">
      <h2 class="text-[13px] font-medium">Analysis &amp; Broker Summary</h2>
      <span v-if="ringkasan" class="tabular text-[10px] text-muted-foreground">
        {{ ringkasan.hari }} hari
      </span>
    </header>

    <div v-if="loading" class="flex flex-col gap-2 p-3.5">
      <div v-for="i in 6" :key="i" class="h-[26px] animate-pulse rounded bg-muted" />
    </div>

    <template v-else>
      <!-- Ringkasan turunan dari OHLC -->
      <dl v-if="ringkasan" class="grid grid-cols-2 gap-x-3 gap-y-2.5 border-b-[0.5px] border-border p-3.5">
        <div>
          <dt class="text-[10px] uppercase tracking-[0.06em] text-muted-foreground">Tertinggi</dt>
          <dd class="tabular mt-0.5 text-[13px] font-medium">
            {{ formatNumber(ringkasan.tertinggi) }}
          </dd>
        </div>
        <div>
          <dt class="text-[10px] uppercase tracking-[0.06em] text-muted-foreground">Terendah</dt>
          <dd class="tabular mt-0.5 text-[13px] font-medium">
            {{ formatNumber(ringkasan.terendah) }}
          </dd>
        </div>
        <div>
          <dt class="text-[10px] uppercase tracking-[0.06em] text-muted-foreground">
            Rata-rata Volume
          </dt>
          <dd class="tabular mt-0.5 text-[13px] font-medium">
            {{ formatCompact(ringkasan.volumeRata) }}
          </dd>
        </div>
        <div>
          <dt class="text-[10px] uppercase tracking-[0.06em] text-muted-foreground">
            Total Foreign Flow
          </dt>
          <dd
            class="tabular mt-0.5 text-[13px] font-medium"
            :class="ringkasan.flowTotal >= 0 ? 'text-up' : 'text-down'"
          >
            {{ formatCompact(ringkasan.flowTotal) }}
          </dd>
        </div>
      </dl>

      <EmptyState
        v-if="!broker.length"
        title="Belum ada data broker"
        description="Aktivitas broker belum tersedia untuk emiten ini."
      />

      <template v-else>
        <div class="grid grid-cols-2 divide-x-[0.5px] divide-border">
          <!-- Top Buy -->
          <div class="min-w-0 p-3.5">
            <p class="mb-2 text-[10px] uppercase tracking-[0.06em] text-[var(--color-up-ink)]">
              Top Buy
            </p>
            <ul class="flex flex-col gap-1.5">
              <li
                v-for="(b, i) in buyTampil"
                :key="`buy-${b.broker_code}-${i}`"
                class="flex items-center justify-between gap-2"
              >
                <span class="tabular truncate text-[11px] font-medium">{{ b.broker_code }}</span>
                <span class="tabular shrink-0 text-[11px] text-[var(--color-up-ink)]">
                  {{ formatCompact(b.nilai_rp) }}
                </span>
              </li>
            </ul>
          </div>

          <!-- Top Sell -->
          <div class="min-w-0 p-3.5">
            <p class="mb-2 text-[10px] uppercase tracking-[0.06em] text-[var(--color-down-ink)]">
              Top Sell
            </p>
            <ul class="flex flex-col gap-1.5">
              <li
                v-for="(b, i) in sellTampil"
                :key="`sell-${b.broker_code}-${i}`"
                class="flex items-center justify-between gap-2"
              >
                <span class="tabular truncate text-[11px] font-medium">{{ b.broker_code }}</span>
                <span class="tabular shrink-0 text-[11px] text-[var(--color-down-ink)]">
                  {{ formatCompact(b.nilai_rp) }}
                </span>
              </li>
            </ul>
          </div>
        </div>

        <!-- Perluas di tempat: daftarnya pendek, tidak perlu modal. -->
        <button
          v-if="bisaDiperluas"
          type="button"
          class="border-t-[0.5px] border-border py-2 text-[11px] text-muted-foreground transition-colors hover:text-foreground"
          :aria-expanded="semua"
          @click="semua = !semua"
        >
          {{ semua ? 'Tampilkan lebih sedikit' : 'Lihat semua →' }}
        </button>
      </template>
    </template>
  </section>
</template>
