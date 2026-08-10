<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getStockSummary, getOhlcHistory } from '@/api/StockVision'
import RecommendationCard from '@/components/onboarding/RecommendationCard.vue'

const router = useRouter()
const authStore = useAuthStore()

// 5 emiten rekomendasi teratas
const recommendations = ref([
  { ticker: 'BBCA', name: 'Bank Central Asia', sector: 'Perbankan' },
  { ticker: 'BBRI', name: 'Bank Rakyat Indonesia', sector: 'Perbankan' },
  { ticker: 'BBNI', name: 'Bank Negara Indonesia', sector: 'Perbankan' },
  { ticker: 'BMRI', name: 'Bank Mandiri', sector: 'Perbankan' },
  { ticker: 'TLKM', name: 'Telkom Indonesia', sector: 'Infrastruktur' },
])

const loading = ref(true)
const selectedTickers = ref(new Set()) // Kosong pada awalnya

async function loadData() {
  loading.value = true
  const tasks = recommendations.value.map(async (rec) => {
    try {
      const [summary, ohlc] = await Promise.all([
        getStockSummary(rec.ticker).catch(() => null),
        getOhlcHistory(rec.ticker).catch(() => []),
      ])

      rec.price = summary?.harga || 0
      rec.changePct = summary?.perubahan_persen || 0

      // Ekstrak closing price untuk sparkline (ambil 20 data terakhir jika ada)
      if (ohlc && ohlc.length) {
        rec.sparkline = ohlc.slice(-20).map(d => d.close)
      } else {
        rec.sparkline = []
      }
    } catch (err) {
      console.error(`Gagal memuat data untuk ${rec.ticker}`, err)
    }
  })

  await Promise.all(tasks)
  loading.value = false
}

onMounted(() => {
  loadData()
})

function toggleSelection(ticker) {
  if (selectedTickers.value.has(ticker)) {
    selectedTickers.value.delete(ticker)
  } else {
    selectedTickers.value.add(ticker)
  }
}

async function lanjutKeStream() {
  // Simpan penanda bahwa user sudah melewati onboarding
  if (authStore.user) {
    localStorage.setItem(`onboarded_${authStore.user.id}`, 'true')
  }

  // Jadikan emiten yang dipilih pertama sebagai emiten utama
  const selectedArray = Array.from(selectedTickers.value)
  if (selectedArray.length > 0) {
    const utama = selectedArray[0]
    await authStore.setEmitenUtama(utama)
    // Update daftar pantau dengan yang dipilih
    await authStore.saveWatchlist(selectedArray, 'Watchlist Saya')
  }

  router.push('/stream')
}
</script>

<template>
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-[var(--background-secondary)] p-4 sm:p-6">
    <div class="flex w-full max-w-[700px] flex-col overflow-hidden rounded-2xl bg-card shadow-xl">
      <!-- Header -->
      <div class="flex flex-col items-center border-b-[0.5px] border-border p-6 text-center sm:p-8">
        <h1 class="text-2xl font-bold tracking-tight">Rekomendasi Emiten Terbaik</h1>
        <p class="mt-2 text-sm text-muted-foreground">
          Pilih emiten yang ingin Anda pantau untuk memulai perjalanan investasi Anda.
        </p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex flex-col items-center justify-center p-12">
        <div class="h-8 w-8 animate-spin rounded-full border-4 border-muted border-t-[var(--primary)]"></div>
        <p class="mt-4 text-sm text-muted-foreground">Mengambil data pasar terkini...</p>
      </div>

      <!-- Cards -->
      <div v-else class="flex flex-col items-center bg-[var(--background-secondary)]/30 p-6 sm:p-8">
        <div class="flex w-full max-w-[640px] flex-wrap justify-center gap-4">
          <div
            v-for="rec in recommendations"
            :key="rec.ticker"
            class="w-full sm:w-[calc(50%-8px)] md:w-[200px] shrink-0"
          >
            <RecommendationCard
              :ticker="rec.ticker"
              :name="rec.name"
              :sector="rec.sector"
              :price="rec.price"
              :change-pct="rec.changePct"
              :sparkline="rec.sparkline"
              :selected="selectedTickers.has(rec.ticker)"
              @toggle="toggleSelection(rec.ticker)"
            />
          </div>
        </div>
      </div>

      <!-- Footer & Action -->
      <div class="border-t-[0.5px] border-border p-6 sm:p-8">
        <button
          type="button"
          :disabled="selectedTickers.size < 3"
          class="flex w-full items-center justify-center rounded-lg bg-[var(--primary)] px-4 py-3.5 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-[var(--primary-hover)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--primary)] disabled:cursor-not-allowed disabled:opacity-50"
          @click="lanjutKeStream"
        >
          {{ selectedTickers.size < 3 ? `Pilih minimal ${3 - selectedTickers.size} emiten lagi` : 'Lanjut ke Beranda' }}
        </button>
      </div>
    </div>
  </div>
</template>
