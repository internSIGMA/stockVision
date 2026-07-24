import { computed, ref } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { getOhlcHistory, SUPPORTED_TICKERS } from '@/api/StockVision'

/** Jumlah candle yang dirender di mock jendela. */
const JUMLAH_CANDLE = 40

/** Panjang jendela penilaian performa (dalam baris data, ~ hari bursa). */
const JENDELA_PERFORMA = 30

function toNumber(v) {
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

/** Baris valid = punya keempat harga OHLC. */
function bersihkan(rows) {
  return (Array.isArray(rows) ? rows : [])
    .map((r) => ({
      tanggal: String(r.tanggal).slice(0, 10),
      open: toNumber(r.open),
      high: toNumber(r.high),
      low: toNumber(r.low),
      close: toNumber(r.close),
    }))
    .filter((r) => r.open != null && r.high != null && r.low != null && r.close != null)
}

/**
 * Persentase perubahan close sepanjang `JENDELA_PERFORMA` baris terakhir.
 * Dipakai untuk memilih emiten "paling bagus" bagi pengunjung tanpa akun.
 */
function performa(rows) {
  if (rows.length < 2) return null
  const jendela = rows.slice(-JENDELA_PERFORMA)
  const awal = jendela[0].close
  const akhir = jendela[jendela.length - 1].close
  if (!awal) return null
  return ((akhir - awal) / awal) * 100
}

/**
 * Emiten sorotan untuk landing page:
 *   - sudah login  → emiten utama (default_ticker) user
 *   - belum login  → emiten dengan performa terbaik di antara yang didukung
 *
 * Selalu mengembalikan data OHLC nyata dari backend, tidak ada ilustrasi statis.
 */
export function useLandingSpotlight() {
  const auth = useAuthStore()

  const ticker = ref(null)
  const rows = ref([])
  const perubahanPersen = ref(null)
  const isRekomendasi = ref(false)
  const loading = ref(true)
  const error = ref('')

  /** Candle ternormalisasi 0–100% terhadap rentang harga jendela tampilan. */
  const candles = computed(() => {
    const window = rows.value.slice(-JUMLAH_CANDLE)
    if (!window.length) return []

    const min = Math.min(...window.map((r) => r.low))
    const max = Math.max(...window.map((r) => r.high))
    const span = max - min || 1
    const pct = (v) => ((v - min) / span) * 100

    return window.map((r) => {
      const atasBody = Math.max(r.open, r.close)
      const bawahBody = Math.min(r.open, r.close)
      return {
        tanggal: r.tanggal,
        naik: r.close >= r.open,
        wickBottom: pct(r.low),
        wickHeight: Math.max(pct(r.high) - pct(r.low), 0.5),
        bodyBottom: pct(bawahBody),
        bodyHeight: Math.max(pct(atasBody) - pct(bawahBody), 1.5),
      }
    })
  })

  const hargaTerakhir = computed(() => rows.value[rows.value.length - 1]?.close ?? null)

  // Filter from/to backend rusak (SQL "tanggal" ambiguous karena JOIN), jadi
  // ambil histori penuh lalu potong sendiri di sisi klien.
  async function muatSatu(symbol) {
    return bersihkan(await getOhlcHistory(symbol))
  }

  /** Pilih emiten dengan performa tertinggi; abaikan yang datanya kosong/gagal. */
  async function pilihRekomendasi() {
    const hasil = await Promise.allSettled(SUPPORTED_TICKERS.map(muatSatu))

    let terbaik = null
    hasil.forEach((r, i) => {
      if (r.status !== 'fulfilled' || !r.value.length) return
      const skor = performa(r.value)
      if (skor == null) return
      if (!terbaik || skor > terbaik.skor) {
        terbaik = { symbol: SUPPORTED_TICKERS[i], rows: r.value, skor }
      }
    })
    return terbaik
  }

  async function muat() {
    loading.value = true
    error.value = ''

    try {
      if (auth.isLoggedIn) {
        // Emiten kesukaan user; kalau kosong, jatuh ke jalur rekomendasi.
        const favorit = auth.emitenUtama
        const data = await muatSatu(favorit)
        if (data.length) {
          ticker.value = favorit
          rows.value = data
          perubahanPersen.value = performa(data)
          isRekomendasi.value = false
          return
        }
      }

      const rekomendasi = await pilihRekomendasi()
      if (!rekomendasi) {
        error.value = 'Belum ada data pasar yang bisa ditampilkan.'
        rows.value = []
        return
      }

      ticker.value = rekomendasi.symbol
      rows.value = rekomendasi.rows
      perubahanPersen.value = rekomendasi.skor
      isRekomendasi.value = true
    } catch (err) {
      error.value = err.message
      rows.value = []
    } finally {
      loading.value = false
    }
  }

  muat()

  return {
    ticker,
    rows,
    candles,
    hargaTerakhir,
    perubahanPersen,
    isRekomendasi,
    loading,
    error,
    reload: muat,
  }
}
