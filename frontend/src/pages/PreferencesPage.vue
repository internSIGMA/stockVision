<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight } from '@lucide/vue'
import { useAuthStore } from '@/stores/auth'
import { getStockSummary, getOhlcHistory } from '@/api/StockVision'
import RecommendationCard from '@/components/onboarding/RecommendationCard.vue'
import { useNotify } from '@/composables/useNotify'

/**
 * Tepat tiga emiten: cukup untuk dibandingkan di Stream, dan tidak lebih
 * supaya halamannya tetap satu keputusan singkat.
 */
const JUMLAH_PILIH = 3

const router = useRouter()
const authStore = useAuthStore()
const notify = useNotify()

const emiten = ref([
  { ticker: 'BBCA', name: 'Bank Central Asia', sector: 'Perbankan' },
  { ticker: 'BBRI', name: 'Bank Rakyat Indonesia', sector: 'Perbankan' },
  { ticker: 'BBNI', name: 'Bank Negara Indonesia', sector: 'Perbankan' },
  { ticker: 'BMRI', name: 'Bank Mandiri', sector: 'Perbankan' },
  { ticker: 'BJBR', name: 'Bank BJB', sector: 'Perbankan' },
])

const loading = ref(true)
const menyimpan = ref(false)
const terpilih = ref(new Set())

const jumlah = computed(() => terpilih.value.size)
const cukup = computed(() => jumlah.value === JUMLAH_PILIH)
const penuh = computed(() => jumlah.value >= JUMLAH_PILIH)

const keterangan = computed(() => {
  if (cukup.value) {
    return `${jumlah.value} emiten dipilih · Siap disimpan.`
  }

  const kurang = JUMLAH_PILIH - jumlah.value
  return (
    `${jumlah.value} emiten dipilih · ` +
    `Pilih ${kurang} emiten lagi — tepat ${JUMLAH_PILIH} emiten untuk melanjutkan.`
  )
})

/**
 * Watchlist lama dimuat HANYA supaya simpan nanti menimpa watchlist yang sudah
 * ada, bukan membuat yang baru tiap login. Pilihannya sendiri sengaja dibiarkan
 * kosong: halaman ini muncul di tiap login, dan penggunalah yang memilih.
 */
async function muatWatchlistLama() {
  try {
    if (!authStore.watchlists.length) await authStore.fetchWatchlists()
  } catch {
    // Gagal memuat bukan alasan menahan halaman; simpan nanti akan membuat
    // watchlist baru kalau yang lama memang tidak terbaca.
  }
}

async function muatDataPasar() {
  const tugas = emiten.value.map(async (e) => {
    const [ringkas, ohlc] = await Promise.all([
      getStockSummary(e.ticker).catch(() => null),
      getOhlcHistory(e.ticker).catch(() => []),
    ])

    e.price = ringkas?.harga ?? 0
    e.changePct = ringkas?.perubahan_persen ?? 0
    e.sparkline = ohlc?.length ? ohlc.slice(-20).map((d) => d.close) : []
  })

  await Promise.all(tugas)
}

onMounted(async () => {
  loading.value = true
  await muatWatchlistLama()
  await muatDataPasar()
  loading.value = false
})

function toggle(ticker) {
  if (terpilih.value.has(ticker)) {
    terpilih.value.delete(ticker)
  } else {
    /*
     * Batas atas ditegakkan di sini, bukan dengan menonaktifkan kartunya:
     * kartu yang mati tidak menjelaskan apa-apa, sedangkan pesan ini
     * memberi tahu apa yang harus dilepas dulu.
     */
    if (penuh.value) {
      notify.info(
        `Maksimal ${JUMLAH_PILIH} emiten`,
        'Lepas salah satu pilihan dulu sebelum menambah yang baru.',
      )
      return
    }

    terpilih.value.add(ticker)
  }
  // Set bukan reactive per-elemen; ganti referensinya agar computed ikut jalan.
  terpilih.value = new Set(terpilih.value)
}

async function simpan() {
  if (!cukup.value || menyimpan.value) return

  const pilihan = Array.from(terpilih.value)
  menyimpan.value = true

  try {
    // Emiten utama harus salah satu yang dipantau; kalau yang lama tidak ikut
    // terpilih, Stream akan membuka emiten yang tidak ada di watchlist.
    const utamaLama = authStore.user?.defaultTicker
    const utama = pilihan.includes(utamaLama) ? utamaLama : pilihan[0]

    await authStore.saveWatchlist(pilihan, 'Watchlist Saya')
    await authStore.setEmitenUtama(utama)

    notify.success('Preferensi disimpan', `${pilihan.length} emiten kini dipantau.`)
    router.push('/stream')
  } catch (error) {
    notify.error('Gagal menyimpan', error?.message || 'Coba sesaat lagi.')
  } finally {
    menyimpan.value = false
  }
}
</script>

<template>
  <div class="flex min-h-full justify-center bg-[var(--background-secondary)] px-4 py-8 sm:px-6 sm:py-12">
    <div
      class="flex h-fit w-full max-w-[760px] flex-col overflow-hidden rounded-2xl bg-card shadow-xl"
    >
      <!-- Aksen tipis di puncak panel, penanda halaman pilihan -->
      <div class="flex justify-center pt-5">
        <span class="h-1 w-14 rounded-full bg-[var(--primary)]" aria-hidden="true" />
      </div>

      <header class="flex flex-col items-center px-6 pb-6 pt-5 text-center sm:px-10">
        <h1 class="text-[19px] font-bold tracking-tight sm:text-[21px]">
          Pilih emiten yang ingin kamu pantau
        </h1>
        <p class="mt-2 text-[13px] text-muted-foreground">
          Pilih tepat {{ JUMLAH_PILIH }} emiten. Pilihan ini bisa diubah kapan saja.
        </p>
      </header>

      <div v-if="loading" class="flex flex-col items-center justify-center px-6 pb-12">
        <div
          class="size-8 animate-spin rounded-full border-4 border-muted border-t-[var(--primary)]"
        />
        <p class="mt-4 text-[13px] text-muted-foreground">Mengambil data pasar terkini...</p>
      </div>

      <div v-else class="flex flex-col items-center px-6 pb-2 sm:px-10">
        <!-- Baris dibiarkan membungkus dan rata tengah: lima kartu jatuh jadi
             3 + 2, dan sisa satu kartu di baris akhir tidak menempel ke kiri. -->
        <div class="flex w-full flex-wrap justify-center gap-4">
          <div
            v-for="e in emiten"
            :key="e.ticker"
            class="w-full shrink-0 sm:w-[calc(50%-8px)] md:w-[204px]"
          >
            <RecommendationCard
              :ticker="e.ticker"
              :name="e.name"
              :sector="e.sector"
              :price="e.price"
              :change-pct="e.changePct"
              :sparkline="e.sparkline"
              :selected="terpilih.has(e.ticker)"
              @toggle="toggle(e.ticker)"
            />
          </div>
        </div>
      </div>

      <footer class="px-6 pb-7 pt-5 sm:px-10">
        <button
          type="button"
          :disabled="!cukup || menyimpan"
          class="flex w-full items-center justify-center gap-2 rounded-xl bg-[var(--primary)] px-4 py-3.5 text-[15px] font-bold text-primary-foreground shadow-sm transition-colors hover:bg-[var(--primary-hover)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--primary)] disabled:cursor-not-allowed disabled:opacity-50"
          @click="simpan"
        >
          {{ menyimpan ? 'Menyimpan...' : 'Mulai Pantau' }}
          <ArrowRight v-if="!menyimpan" class="size-4" aria-hidden="true" />
        </button>

        <p class="mt-3 text-center text-[11px] text-muted-foreground" role="status">
          {{ keterangan }}
        </p>
      </footer>
    </div>
  </div>
</template>
