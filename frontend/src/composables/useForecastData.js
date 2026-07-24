import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useMarketStore } from '@/stores/market'
import { getForecast } from '@/api/StockVision'

/** Pilihan horizon yang ditawarkan — disaring lagi sesuai panjang data backend. */
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
 * Satu baris proyeksi dari /api/data/forecast berbentuk OHLCV:
 * { symbol, tanggal, open, high, low, close, volume }. `close` jadi garis
 * proyeksi, sedangkan `low`/`high` jadi pita rentang — keduanya dihitung model
 * di backend, jadi tidak ada angka yang dikarang di sisi frontend.
 */
function normalPoints(raw) {
  const list = Array.isArray(raw) ? raw : []

  return list
    .map((p) => ({
      tanggal: String(ambil(p, 'tanggal', 'date', 'ds') ?? '').slice(0, 10),
      prediksi: toNumber(
        ambil(p, 'prediksi', 'yhat', 'predicted_close', 'prediction', 'value', 'close'),
      ),
      lower: toNumber(ambil(p, 'lower', 'yhat_lower', 'lower_bound', 'low', 'lo')),
      upper: toNumber(ambil(p, 'upper', 'yhat_upper', 'upper_bound', 'high', 'hi')),
      volume: toNumber(ambil(p, 'volume', 'vol')),
    }))
    .filter((p) => p.tanggal && p.prediksi != null)
    .sort((a, b) => a.tanggal.localeCompare(b.tanggal))
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
 * Forecasting untuk emiten aktif, seluruhnya dari /api/data/forecast.
 *
 * Backend mengembalikan satu deret utuh per emiten dan mengabaikan parameter
 * hari, jadi ganti horizon hanya memotong deret yang sudah ada — tidak ada
 * request ulang, dan tidak ada tombol horizon yang datanya tidak tersedia.
 *
 * @param {object} options
 * @param {import('vue').Ref<Array>} options.ohlc histori asli — jadi titik
 *   berangkat garis proyeksi dan pembanding untuk arah tren.
 */
export function useForecastData(options = {}) {
  const { ohlc } = options

  const market = useMarketStore()
  const { selectedTicker } = storeToRefs(market)

  const horizon = ref(HORIZON_PILIHAN[0])
  const data = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  const semuaPoints = computed(() => data.value?.points ?? [])

  /** Hanya tawarkan horizon yang benar-benar tertutup data backend. */
  const horizonTersedia = computed(() => {
    const n = semuaPoints.value.length
    if (!n) return []

    const muat = HORIZON_PILIHAN.filter((h) => h <= n)
    return muat.length ? muat : [n]
  })

  const points = computed(() => semuaPoints.value.slice(0, horizon.value))
  const hasData = computed(() => points.value.length > 0)

  /** Ada pita rentang hanya kalau SEMUA titik punya batas atas & bawah. */
  const hasBand = computed(
    () => hasData.value && points.value.every((p) => p.lower != null && p.upper != null),
  )

  const terakhir = computed(() => points.value[points.value.length - 1] ?? null)

  /** Rentang terlebar sepanjang horizon, langsung dari kolom low/high backend. */
  const rentang = computed(() => {
    if (!hasBand.value) return null
    return {
      bawah: Math.min(...points.value.map((p) => p.lower)),
      atas: Math.max(...points.value.map((p) => p.upper)),
    }
  })

  /** Rata-rata volume proyeksi; null kalau backend tidak mengirim kolomnya. */
  const volumeRata = computed(() => {
    const vol = points.value.map((p) => p.volume).filter((v) => v != null)
    if (!vol.length) return null
    return vol.reduce((a, b) => a + b, 0) / vol.length
  })

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

  const trend = computed(() =>
    hasData.value ? normalTrend(data.value?.raw, points.value, hargaAcuan.value) : null,
  )

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
      const raw = await getForecast(ticker)
      if (id !== requestId) return

      const daftar = normalPoints(
        ambil(raw, 'predictions', 'forecast', 'forecasts', 'results', 'data') ?? raw,
      )

      if (!daftar.length) throw new Error('Belum ada data proyeksi untuk emiten ini.')

      data.value = {
        symbol: ambil(raw, 'symbol', 'ticker') ?? ticker,
        points: daftar,
        raw,
      }

      // Turunkan horizon kalau pilihan sekarang melebihi data yang ada.
      const opsi = HORIZON_PILIHAN.filter((h) => h <= daftar.length)
      if (!opsi.includes(horizon.value)) horizon.value = opsi[opsi.length - 1] ?? daftar.length
    } catch (err) {
      if (id !== requestId) return
      data.value = null
      error.value = err.message
    } finally {
      if (id === requestId) isLoading.value = false
    }
  }

  function setHorizon(n) {
    // Backend mengirim satu deret utuh, jadi ini murni memotong — tanpa fetch.
    if (horizonTersedia.value.includes(n)) horizon.value = n
  }

  watch(selectedTicker, load)
  onMounted(load)

  return {
    horizon,
    horizonTersedia,
    data,
    points,
    hasData,
    hasBand,
    terakhir,
    rentang,
    volumeRata,
    hargaAcuan,
    perubahanPersen,
    trend,
    isLoading,
    error,
    setHorizon,
    reload: load,
  }
}
