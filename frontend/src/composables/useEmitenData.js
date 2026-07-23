import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useMarketStore } from '@/stores/market'
import {
  getStockSummary,
  getOhlcHistory,
  getInsiderTransactions,
  getBrokerActivity,
} from '@/api/StockVision'

/**
 * Data emiten yang sedang aktif (market.selectedTicker), dimuat ulang otomatis
 * setiap ticker berganti.
 *
 * Tiap potongan data diambil independen dan kegagalannya ditahan di tempat:
 * /api/data/stock-info menjawab 404 untuk emiten yang belum pernah di-crawl,
 * dan itu bukan alasan untuk mengosongkan chart atau tabel yang lain.
 *
 * @param {object} options potongan mana yang perlu diambil
 * @example const { summary, ohlc, loading } = useEmitenData({ insider: true })
 */
export function useEmitenData(options = {}) {
  const {
    summary: wantSummary = true,
    ohlc: wantOhlc = true,
    insider: wantInsider = false,
    broker: wantBroker = false,
  } = options

  const market = useMarketStore()
  const { selectedTicker } = storeToRefs(market)

  const summary = ref(null)
  const ohlc = ref([])
  const insider = ref([])
  const broker = ref([])

  const loading = ref(false)
  const errors = ref({})

  /** Pesan error pertama yang ada — cukup untuk banner di halaman. */
  const error = computed(() => Object.values(errors.value)[0] || null)

  /** Baris OHLC terakhir; sumber harga penutupan untuk indikator. */
  const latest = computed(() => (ohlc.value.length ? ohlc.value[ohlc.value.length - 1] : null))

  /**
   * Setiap load punya token sendiri. Ganti ticker dengan cepat bisa membuat
   * response lama datang belakangan — token ini yang membuangnya.
   */
  let requestId = 0

  async function load() {
    const ticker = selectedTicker.value
    if (!ticker) {
      summary.value = null
      ohlc.value = []
      insider.value = []
      broker.value = []
      return
    }

    const id = ++requestId
    loading.value = true
    errors.value = {}

    const tasks = []

    const run = (key, promise, onOk, fallback) =>
      tasks.push(
        promise
          .then((data) => {
            if (id === requestId) onOk(data)
          })
          .catch((err) => {
            if (id !== requestId) return
            fallback()
            errors.value = { ...errors.value, [key]: err.message }
          }),
      )

    if (wantSummary) {
      run(
        'summary',
        getStockSummary(ticker),
        (d) => (summary.value = d),
        () => (summary.value = null),
      )
    }
    if (wantOhlc) {
      run(
        'ohlc',
        getOhlcHistory(ticker),
        (d) => (ohlc.value = Array.isArray(d) ? d : []),
        () => (ohlc.value = []),
      )
    }
    if (wantInsider) {
      run(
        'insider',
        getInsiderTransactions(ticker),
        (d) => (insider.value = Array.isArray(d) ? d : []),
        () => (insider.value = []),
      )
    }
    if (wantBroker) {
      run(
        'broker',
        getBrokerActivity(ticker),
        (d) => (broker.value = Array.isArray(d) ? d : []),
        () => (broker.value = []),
      )
    }

    await Promise.all(tasks)
    if (id === requestId) loading.value = false
  }

  watch(selectedTicker, load)
  onMounted(load)

  return {
    ticker: selectedTicker,
    summary,
    ohlc,
    insider,
    broker,
    latest,
    loading,
    error,
    errors,
    reload: load,
  }
}
