import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useMarketStore } from '@/stores/market'
import { getPrescriptive } from '@/api/StockVision'

/**
 * Hasil prescriptive dari backend untuk emiten yang sedang dibuka.
 *
 * Berdiri sendiri seperti useForecastData: tabel prescriptive_results diisi
 * oleh pipeline terjadwal, jadi emiten yang belum pernah dianalisis wajar
 * kosong dan itu tidak boleh menjatuhkan bagian lain di panel.
 */
export function usePrescriptive() {
  const market = useMarketStore()
  const { selectedTicker } = storeToRefs(market)

  const data = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  /** Setiap muat punya token sendiri supaya response lama tidak menimpa. */
  let requestId = 0

  async function load() {
    const ticker = selectedTicker.value
    if (!ticker) {
      data.value = null
      error.value = null
      return
    }

    const id = ++requestId
    isLoading.value = true
    error.value = null

    try {
      const hasil = await getPrescriptive(ticker)
      if (id !== requestId) return
      data.value = hasil
    } catch (err) {
      if (id !== requestId) return
      data.value = null
      error.value = err.message
    } finally {
      if (id === requestId) isLoading.value = false
    }
  }

  const hasData = computed(() => Boolean(data.value))

  /** Level trading; null kalau backend belum punya angkanya. */
  const tradingLevels = computed(() => {
    const t = data.value?.trade_setup
    if (!t) return null

    const entry = t.entry_price
    const target = t.target_price
    const stopLoss = t.stop_loss

    const persen = (nilai) =>
      entry && Number.isFinite(nilai) ? ((nilai - entry) / entry) * 100 : null

    return {
      entry,
      target,
      stopLoss,
      support: t.support_price,
      resistance: t.resistance_price,
      riskReward: t.risk_reward_ratio,
      persenTarget: persen(target),
      persenStopLoss: persen(stopLoss),
    }
  })

  watch(selectedTicker, load)
  onMounted(load)

  return { data, hasData, tradingLevels, isLoading, error, reload: load }
}
