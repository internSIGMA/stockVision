import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useMarketStore } from '@/stores/market'
import { getForecast } from '@/api/StockVision'
import { buatForecastPlaceholder } from '@/utils/forecastPlaceholder'

export const HORIZON_PILIHAN = [7, 14, 30]

/** Nama field backend belum pasti — ambil yang pertama ketemu. */
function ambil(obj, ...keys) {
  for (const k of keys) {
    const v = obj?.[k]
    if (v != null) return v
  }
  return null
}

function toNumber(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

/**
 * Confidence bisa datang sebagai 0.82 atau 82. Angka <= 1 diperlakukan sebagai
 * pecahan; sisanya sudah dalam persen.
 */
function normalConfidence(raw) {
  const n = toNumber(raw)
  if (n == null) return null
  return n <= 1 ? Math.round(n * 100) : Math.round(n)
}

function normalPoints(raw) {
  const list = Array.isArray(raw) ? raw : []

  return list
    .map((p) => ({
      tanggal: String(ambil(p, 'tanggal', 'date', 'ds') ?? '').slice(0, 10),
      prediksi: toNumber(ambil(p, 'prediksi', 'yhat', 'predicted_close', 'prediction', 'value', 'close')),
      lower: toNumber(ambil(p, 'lower', 'yhat_lower', 'lower_bound', 'lo')),
      upper: toNumber(ambil(p, 'upper', 'yhat_upper', 'upper_bound', 'hi')),
    }))
    .filter((p) => p.tanggal && p.prediksi != null)
}

/**
 * Arah tren dipakai apa adanya kalau backend mengirimnya. Kalau tidak, arah
 * disimpulkan dari deret yang backend kirim sendiri — ini cuma mendeskripsikan
 * hasil, bukan meramal.
 */
function normalTrend(raw, points, hargaAcuan) {
  const dariBackend = ambil(raw, 'trend', 'arah', 'direction')
  if (typeof dariBackend === 'string' && dariBackend.trim()) {
    return dariBackend.trim().toUpperCase()
  }

  const awal = hargaAcuan ?? points[0]?.prediksi
  const akhir = points[points.length - 1]?.prediksi
  if (awal == null || akhir == null) return null

  const delta = (akhir - awal) / awal
  if (delta > 0.01) return 'NAIK'
  if (delta < -0.01) return 'TURUN'
  return 'SIDEWAYS'
}

/**
 * Forecasting untuk emiten aktif. Dimuat ulang saat ticker atau horizon berubah.
 *
 * @param {object} options
 * @param {import('vue').Ref<Array>} options.ohlc histori asli — jadi titik
 *   berangkat garis proyeksi, dan bahan placeholder selama backend belum ada.
 */
export function useForecastData(options = {}) {
  const { ohlc } = options

  const market = useMarketStore()
  const { selectedTicker } = storeToRefs(market)

  const horizon = ref(HORIZON_PILIHAN[0])
  const data = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  /** true = angka di layar adalah data contoh, bukan proyeksi backend. */
  const isPlaceholder = ref(false)

  const points = computed(() => data.value?.points ?? [])
  const hasData = computed(() => points.value.length > 0)

  /** Ada confidence band hanya kalau SEMUA titik punya batas atas & bawah. */
  const hasBand = computed(
    () => hasData.value && points.value.every((p) => p.lower != null && p.upper != null),
  )

  const terakhir = computed(() => points.value[points.value.length - 1] ?? null)

  const hargaAcuan = computed(() => {
    const rows = ohlc?.value ?? []
    return rows.length ? toNumber(rows[rows.length - 1].close) : null
  })

  /** Selisih proyeksi akhir terhadap harga penutupan terakhir, dalam persen. */
  const perubahanPersen = computed(() => {
    const awal = hargaAcuan.value
    const akhir = terakhir.value?.prediksi
    if (awal == null || akhir == null || awal === 0) return null
    return ((akhir - awal) / awal) * 100
  })

  const confidenceLabel = computed(() => {
    const c = data.value?.confidence
    if (c == null) return null
    if (c >= 80) return 'High'
    if (c >= 60) return 'Medium'
    return 'Low'
  })

  /**
   * Jatuh ke data contoh. Mengembalikan false kalau histori belum ada, karena
   * placeholder butuh harga penutupan terakhir sebagai titik berangkat.
   */
  function pakaiPlaceholder() {
    const contoh = buatForecastPlaceholder(selectedTicker.value, ohlc?.value ?? [], horizon.value)
    if (!contoh) return false

    contoh.trend = normalTrend(null, contoh.points, hargaAcuan.value)
    data.value = contoh
    isPlaceholder.value = true
    error.value = null
    return true
  }

  // Ganti ticker cepat bisa membuat response lama datang belakangan — buang.
  let requestId = 0

  async function load() {
    const ticker = selectedTicker.value
    if (!ticker) {
      data.value = null
      return
    }

    const id = ++requestId
    isLoading.value = true
    error.value = null

    try {
      const raw = await getForecast(ticker, { horizon: horizon.value })
      if (id !== requestId) return

      const daftar = normalPoints(
        ambil(raw, 'predictions', 'forecast', 'forecasts', 'results', 'data') ?? raw,
      )

      if (!daftar.length) throw new Error('Data forecasting kosong')

      data.value = {
        symbol: ambil(raw, 'symbol', 'ticker') ?? ticker,
        model: ambil(raw, 'model', 'model_name', 'algoritma'),
        horizon: toNumber(ambil(raw, 'horizon', 'days')) ?? horizon.value,
        confidence: normalConfidence(ambil(raw, 'confidence', 'confidence_level', 'akurasi')),
        trend: normalTrend(raw, daftar, hargaAcuan.value),
        points: daftar,
      }
      isPlaceholder.value = false
    } catch (err) {
      if (id !== requestId) return

      // Endpoint belum ada → tampilkan data contoh, tapi JANGAN diam-diam:
      // isPlaceholder dipakai UI untuk memasang penanda yang terlihat.
      if (!pakaiPlaceholder()) {
        data.value = null
        isPlaceholder.value = false
        error.value = err.message
      }
    } finally {
      if (id === requestId) isLoading.value = false
    }
  }

  function setHorizon(n) {
    if (horizon.value === n) return
    horizon.value = n
    load()
  }

  watch(selectedTicker, load)

  /**
   * Histori datang belakangan (fetch-nya paralel). Kalau saat itu kita sedang
   * memakai data contoh, bangun ulang — titik berangkatnya baru tersedia
   * sekarang. Backend yang sungguhan tidak ikut di-fetch ulang.
   */
  watch(
    () => ohlc?.value?.length ?? 0,
    (jumlah) => {
      if (!jumlah || isLoading.value) return
      if (isPlaceholder.value || !data.value) pakaiPlaceholder()
    },
  )

  onMounted(load)

  return {
    horizon,
    data,
    points,
    hasData,
    hasBand,
    terakhir,
    hargaAcuan,
    perubahanPersen,
    confidenceLabel,
    isPlaceholder,
    isLoading,
    error,
    setHorizon,
    reload: load,
  }
}
