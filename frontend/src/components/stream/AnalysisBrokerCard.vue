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
  return {
    tertinggi: highs.length ? Math.max(...highs) : null,
    terendah: lows.length ? Math.min(...lows) : null,
    volumeRata: volumes.length ? volumes.reduce((a, b) => a + b, 0) / volumes.length : null,

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

/**
 * Bar dinormalkan ke nilai terbesar di kolomnya masing-masing, bukan ke nilai
 * gabungan buy+sell, supaya kolom yang totalnya kecil tidak tampil rata gepeng.
 * Daftar sudah terurut menurun, jadi puncaknya selalu elemen pertama.
 */
function puncak(daftar) {
  return Math.abs(Number(daftar[0]?.nilai_rp) || 0)
}

const puncakBuy = computed(() => puncak(topBuy.value))
const puncakSell = computed(() => puncak(topSell.value))

/** Minimal 2% supaya broker bernilai kecil tetap terlihat, bukan hilang sama sekali. */
function lebarBar(nilai, maks) {
  if (!maks) return 0
  return Math.max(2, (Math.abs(Number(nilai) || 0) / maks) * 100)
}
</script>

<template>
  <section class="flex flex-col rounded-lg border-[0.5px] border-border bg-card">
    <header class="flex items-center justify-between border-b-[0.5px] border-border px-3.5 py-2.5">
      <h2 class="text-[13px] font-medium">Analysis &amp; Broker Summary</h2>
      <span
        v-if="ringkasan"
        class="tabular rounded-full border-[0.5px] border-border px-2 py-0.5 text-[10px] text-muted-foreground"
      >
        {{ formatNumber(ringkasan.hari) }} hari
      </span>
    </header>

    <div v-if="loading" class="flex flex-col gap-2 p-3.5">
      <div v-for="i in 6" :key="i" class="h-[26px] animate-pulse rounded bg-muted" />
    </div>

    <template v-else>
      <!-- Ringkasan turunan dari OHLC -->
      <dl
        v-if="ringkasan"
        class="grid grid-cols-1 gap-3 border-b-[0.5px] border-border p-3.5 sm:grid-cols-3"
      >
        <div class="rounded-lg border-[0.5px] border-border bg-[var(--background-secondary)] p-3">
          <dt class="text-[10px] uppercase tracking-[0.06em] text-muted-foreground">Tertinggi</dt>
          <dd class="tabular mt-1 text-[20px] font-bold leading-none">
            {{ formatNumber(ringkasan.tertinggi) }}
          </dd>
        </div>
        <div class="rounded-lg border-[0.5px] border-border bg-[var(--background-secondary)] p-3">
          <dt class="text-[10px] uppercase tracking-[0.06em] text-muted-foreground">Terendah</dt>
          <dd class="tabular mt-1 text-[20px] font-bold leading-none">
            {{ formatNumber(ringkasan.terendah) }}
          </dd>
        </div>
        <div class="rounded-lg border-[0.5px] border-border bg-[var(--background-secondary)] p-3">
          <dt class="text-[10px] uppercase tracking-[0.06em] text-muted-foreground">
            Rata-rata Volume
          </dt>
          <dd class="tabular mt-1 text-[20px] font-bold leading-none">
            {{ formatCompact(ringkasan.volumeRata) }}
          </dd>
        </div>
      </dl>

      <EmptyState
        v-if="!broker.length"
        title="Belum ada data broker"
        description="Aktivitas broker belum tersedia untuk emiten ini."
      />

      <template v-else>
        <div class="grid grid-cols-1 gap-3 p-3.5 sm:grid-cols-2">
          <!-- Top Buy -->
          <div class="min-w-0 rounded-lg border-[0.5px] border-border bg-[var(--background-secondary)] p-3">
            <p class="mb-3 flex items-center gap-1.5 text-[10px] uppercase tracking-[0.06em] text-[var(--color-up-ink)]">
              <span class="size-1.5 shrink-0 rounded-full bg-[var(--up)]" aria-hidden="true" />
              Top Buy
            </p>
            <ul class="flex flex-col gap-2">
              <li
                v-for="(b, i) in buyTampil"
                :key="`buy-${b.broker_code}-${i}`"
                class="flex items-center gap-2.5"
              >
                <span class="tabular w-[28px] shrink-0 truncate text-[11px] font-medium">
                  {{ b.broker_code }}
                </span>

                <!-- Bar mengisi ruang sisa, jadi kode dan nilai tidak lagi
                     terpisah jurang kosong saat kartunya melebar. -->
                <span class="h-1.5 min-w-0 flex-1 overflow-hidden rounded-full bg-muted">
                  <span
                    class="block h-full rounded-full bg-[var(--up)] transition-[width] duration-500"
                    :style="{ width: `${lebarBar(b.nilai_rp, puncakBuy)}%` }"
                  />
                </span>

                <span class="tabular w-[64px] shrink-0 text-right text-[11px] text-[var(--color-up-ink)]">
                  {{ formatCompact(b.nilai_rp) }}
                </span>
              </li>
            </ul>
          </div>

          <!-- Top Sell -->
          <div class="min-w-0 rounded-lg border-[0.5px] border-border bg-[var(--background-secondary)] p-3">
            <p class="mb-3 flex items-center gap-1.5 text-[10px] uppercase tracking-[0.06em] text-[var(--color-down-ink)]">
              <span class="size-1.5 shrink-0 rounded-full bg-[var(--down)]" aria-hidden="true" />
              Top Sell
            </p>
            <ul class="flex flex-col gap-2">
              <li
                v-for="(b, i) in sellTampil"
                :key="`sell-${b.broker_code}-${i}`"
                class="flex items-center gap-2.5"
              >
                <span class="tabular w-[28px] shrink-0 truncate text-[11px] font-medium">
                  {{ b.broker_code }}
                </span>

                <!-- Bar mengisi ruang sisa, jadi kode dan nilai tidak lagi
                     terpisah jurang kosong saat kartunya melebar. -->
                <span class="h-1.5 min-w-0 flex-1 overflow-hidden rounded-full bg-muted">
                  <span
                    class="block h-full rounded-full bg-[var(--down)] transition-[width] duration-500"
                    :style="{ width: `${lebarBar(b.nilai_rp, puncakSell)}%` }"
                  />
                </span>

                <span class="tabular w-[64px] shrink-0 text-right text-[11px] text-[var(--color-down-ink)]">
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
