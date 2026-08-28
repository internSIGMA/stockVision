import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useMarketStore } from '@/stores/market'
import { getChartPatternForecast } from '@/api/StockVision'

/**
 * Composable untuk mengelola data peramalan berbasis Chart Pattern Recognition.
 * Mengambil data dari endpoint /api/chart-pattern/forecast berdasarkan emiten aktif.
 *
 * @param {object} options
 * @param {import('vue').Ref<Array>} [options.ohlc] Histori candlestick OHLC untuk harga acuan fallback
 */
export function useChartPatternData(options = {}) {
  const { ohlc } = options

  const market = useMarketStore()
  const { selectedTicker } = storeToRefs(market)

  const patterns = ref([])
  const selectedPatternIndex = ref(0)
  const timeframe = ref('1d')
  const isLoading = ref(false)
  const error = ref(null)

  let requestId = 0

  const hasPattern = computed(() => patterns.value.length > 0)

  const selectedPattern = computed(() => {
    if (!patterns.value.length) return null
    const idx = Math.min(Math.max(0, selectedPatternIndex.value), patterns.value.length - 1)
    return patterns.value[idx] ?? null
  })

  // Fallback harga acuan penutupan terakhir dari deret OHLC
  const lastClose = computed(() => {
    const rows = ohlc?.value ?? []
    if (!rows.length) return null
    const c = Number(rows[rows.length - 1].close)
    return Number.isFinite(c) ? c : null
  })

  // Helper properti terpilih
  const patternName = computed(() => selectedPattern.value?.pattern_name ?? '—')
  const patternType = computed(() => selectedPattern.value?.pattern_type ?? 'Reversal')
  const directionalBias = computed(() => selectedPattern.value?.directional_bias ?? 'Bullish')
  const patternStatus = computed(() => selectedPattern.value?.pattern_status ?? 'PENDING_BREAKOUT')
  const qualityScore = computed(() => selectedPattern.value?.quality_score ?? 4)

  const pricing = computed(() => {
    const p = selectedPattern.value?.pricing || {}
    const cur = p.current_price ?? lastClose.value
    return {
      current_price: cur,
      breakout_level: p.breakout_level ?? null,
      target_price: p.target_price ?? null,
      stop_loss: p.stop_loss ?? null,
      expected_return_pct: p.expected_return_pct ?? null,
      potential_risk_pct: p.potential_risk_pct ?? null,
      risk_reward_ratio: p.risk_reward_ratio ?? null,
      tp1_measured_move: p.tp1_measured_move ?? null,
      tp2_fibo_127: p.tp2_fibo_127 ?? null,
      tp3_fibo_161_golden: p.tp3_fibo_161_golden ?? null,
      fibo_support: p.fibo_support ?? null,
      fibo_resistance: p.fibo_resistance ?? null,
      buy_area: p.buy_area ?? {},
      sell_area: p.sell_area ?? {},
    }
  })

  const timeline = computed(() => selectedPattern.value?.timeline || {})
  const forecastTrajectory = computed(() => selectedPattern.value?.forecast_trajectory || {})
  const geometryLines = computed(() => selectedPattern.value?.geometry_lines || [])
  const keyPoints = computed(() => selectedPattern.value?.key_points || [])
  const rulesChecklist = computed(() => selectedPattern.value?.rules_checklist || [])
  const detectionReasons = computed(() => selectedPattern.value?.detection_reasons || [])
  const statisticalNotes = computed(() => selectedPattern.value?.statistical_notes ?? '')
  const description = computed(() => selectedPattern.value?.description ?? '')
  const evaluationMetrics = computed(() => selectedPattern.value?.evaluation_metrics || {})
  const calendarInfo = computed(() => selectedPattern.value?.calendar_info || {})

  async function load() {
    const ticker = selectedTicker.value
    if (!ticker) {
      patterns.value = []
      selectedPatternIndex.value = 0
      return
    }

    const id = ++requestId
    isLoading.value = true
    error.value = null

    try {
      const res = await getChartPatternForecast(ticker, timeframe.value)
      if (id !== requestId) return

      const list = res?.patterns || (Array.isArray(res) ? res : [])
      patterns.value = Array.isArray(list) ? list : []
      selectedPatternIndex.value = 0

      if (!patterns.value.length) {
        error.value = 'Tidak ada pola chart aktif yang terdeteksi untuk emiten ini.'
      }
    } catch (err) {
      if (id !== requestId) return
      patterns.value = []
      selectedPatternIndex.value = 0
      error.value = err?.message || 'Gagal memuat data chart pattern forecasting.'
    } finally {
      if (id === requestId) isLoading.value = false
    }
  }

  function selectPattern(index) {
    if (index >= 0 && index < patterns.value.length) {
      selectedPatternIndex.value = index
    }
  }

  function setTimeframe(tf) {
    if (tf && tf !== timeframe.value) {
      timeframe.value = tf
      load()
    }
  }

  watch(selectedTicker, load)
  onMounted(load)

  return {
    patterns,
    selectedPatternIndex,
    selectedPattern,
    hasPattern,
    timeframe,
    isLoading,
    error,
    patternName,
    patternType,
    directionalBias,
    patternStatus,
    qualityScore,
    pricing,
    timeline,
    forecastTrajectory,
    geometryLines,
    keyPoints,
    rulesChecklist,
    detectionReasons,
    statisticalNotes,
    description,
    evaluationMetrics,
    calendarInfo,
    selectPattern,
    setTimeframe,
    reload: load,
  }
}
