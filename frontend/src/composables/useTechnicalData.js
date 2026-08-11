import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useMarketStore } from '@/stores/market'
import { getTechnicalIndicators } from '@/api/StockVision'
import { macdHistory, rsiHistory } from '@/utils/technicalIndicators'

/**
 * Deret RSI(14) & MACD(12,26,9) untuk emiten yang sedang aktif.
 *
 * Sumber utamanya /api/data/technical — tabel idxsaham.macd_rsi yang diisi
 * crawler yfinance. Emiten yang belum pernah masuk jadwal crawler bisa saja
 * dijawab kosong; supaya chart-nya tidak blank, deretnya dihitung ulang di
 * browser dari histori OHLC (yang harganya juga dari yfinance). `sumber`
 * memberi tahu UI mana yang sedang dipakai.
 *
 * @param {import('vue').Ref<Array>} ohlc baris OHLC untuk jalur cadangan
 */
export function useTechnicalData(ohlc) {
  const market = useMarketStore()
  const { selectedTicker } = storeToRefs(market)

  const rows = ref([])
  const loading = ref(false)
  const error = ref(null)

  /** Ganti ticker cepat bisa membuat response lama datang belakangan. */
  let requestId = 0

  async function load() {
    const ticker = selectedTicker.value
    if (!ticker) {
      rows.value = []
      return
    }

    const id = ++requestId
    loading.value = true
    error.value = null

    try {
      const data = await getTechnicalIndicators(ticker)
      if (id !== requestId) return
      rows.value = Array.isArray(data) ? data : []
    } catch (err) {
      if (id !== requestId) return
      rows.value = []
      error.value = err.message
    } finally {
      if (id === requestId) loading.value = false
    }
  }

  const angka = (v) => (v == null || v === '' || Number.isNaN(Number(v)) ? null : Number(v))

  /** Deret dari backend, dipakai hanya kalau MACD-nya benar-benar terisi. */
  const dariBackend = computed(() => {
    const baris = rows.value
    if (!baris.length) return null

    const signalLine = baris.map((r) => angka(r.macd_signal))
    // Kolomnya ada tapi seluruhnya null terjadi kalau crawler menyimpan histori
    // yang lebih pendek dari 34 hari — itu belum layak digambar.
    if (!signalLine.some((v) => v != null)) return null

    return {
      tanggal: baris.map((r) => String(r.tanggal).slice(0, 10)),
      rsi: baris.map((r) => angka(r.rsi14)),
      macd: {
        macdLine: baris.map((r) => angka(r.macd)),
        signalLine,
        histogram: baris.map((r) => angka(r.macd_histogram)),
      },
    }
  })

  /** Jalur cadangan: hitung sendiri dari harga penutupan OHLC. */
  const dariOhlc = computed(() => {
    const valid = (ohlc?.value || []).filter((r) => Number.isFinite(Number(r.close)))
    if (valid.length < 35) return null

    const closes = valid.map((r) => Number(r.close))
    return {
      tanggal: valid.map((r) => String(r.tanggal).slice(0, 10)),
      rsi: rsiHistory(closes),
      macd: macdHistory(closes),
    }
  })

  const deret = computed(() => dariBackend.value || dariOhlc.value)
  const sumber = computed(() => (dariBackend.value ? 'yfinance' : dariOhlc.value ? 'lokal' : null))

  watch(selectedTicker, load)
  onMounted(load)

  return { deret, sumber, loading, error, reload: load }
}
