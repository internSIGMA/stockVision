import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useMarketStore } from '@/stores/market'
import { getDiagnostic } from '@/api/StockVision'

/**
 * Hasil diagnostik dari backend untuk emiten yang sedang dibuka.
 *
 * Berdiri sendiri seperti usePrescriptive: tabel diagnostic_results diisi
 * pipeline terjadwal, jadi emiten yang belum pernah dianalisis wajar kosong
 * dan itu tidak boleh menjatuhkan bagian lain di halaman.
 */
export function useDiagnostic() {
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
      const hasil = await getDiagnostic(ticker)
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

  /**
   * Empat temuan diagnostik dalam satu bentuk seragam supaya panelnya bisa
   * merendernya sebagai daftar, bukan empat blok yang ditulis satu per satu.
   *
   * `tone` diturunkan dari status backend — string panjang seperti
   * "HIGH SPIKE (Anomali Lonjakan Volume Sangat Tinggi)" dipakai apa adanya
   * untuk detail, sementara labelnya dipendekkan agar muat di pill.
   */
  const temuan = computed(() => {
    const d = data.value
    if (!d) return []

    const tren = d.trend_diagnostic ?? {}
    const bandar = d.bandarmology_diagnostic ?? {}
    const volume = d.volume_diagnostic ?? {}
    const insider = d.insider_diagnostic ?? {}

    return [
      {
        key: 'tren',
        judul: 'Fase Tren',
        label: ringkasStatus(tren.status),
        tone: toneTren(tren.status),
        detail: tren.status,
        metrik: [
          { nama: 'MA5', nilai: tren.ma5, format: 'angka' },
          { nama: 'MA20', nilai: tren.ma20, format: 'angka' },
          { nama: 'Gap MA', nilai: tren.trend_gap_pct, format: 'persen' },
          { nama: 'Return 20H', nilai: tren.return_20d, format: 'persen' },
        ],
      },
      {
        key: 'bandar',
        judul: 'Bandarmology',
        label: ringkasStatus(bandar.status),
        tone: toneBandar(bandar.status),
        detail: bandar.status,
        metrik: [
          { nama: 'Net Big Money', nilai: bandar.net_big_money_rp, format: 'rupiahRingkas' },
          { nama: 'Top Buyer', nilai: bandar.top_buyers, format: 'teks' },
          { nama: 'Top Seller', nilai: bandar.top_sellers, format: 'teks' },
        ],
      },
      {
        key: 'volume',
        judul: 'Anomali Volume',
        label: ringkasStatus(volume.status),
        tone: toneVolume(volume.vol_zscore),
        detail: volume.status,
        metrik: [
          { nama: 'Volume', nilai: volume.latest_volume, format: 'ringkas' },
          { nama: 'Z-Score', nilai: volume.vol_zscore, format: 'angka2' },
        ],
      },
      {
        key: 'insider',
        judul: 'Aktivitas Insider',
        label: ringkasStatus(insider.status),
        tone: toneInsider(insider.status),
        detail: insider.status,
        metrik: [{ nama: 'Total Transaksi', nilai: insider.total_trxs, format: 'ringkas' }],
      },
    ]
  })

  watch(selectedTicker, load)
  onMounted(load)

  return { data, hasData, temuan, isLoading, error, reload: load }
}

/**
 * Backend mengirim status bergaya "HIGH SPIKE (Anomali Lonjakan Volume ...)".
 * Pill hanya muat beberapa kata, jadi keterangan dalam kurung dibuang dan
 * sisanya dipangkas — teks utuhnya tetap tampil sebagai detail di bawahnya.
 */
function ringkasStatus(status) {
  if (!status) return 'Tidak ada data'
  const inti = String(status).split('(')[0].trim()
  return inti || String(status).trim()
}

function toneTren(status) {
  const s = String(status ?? '').toLowerCase()
  if (s.includes('uptrend')) return 'up'
  if (s.includes('downtrend')) return 'down'
  return 'skip'
}

function toneBandar(status) {
  const s = String(status ?? '').toLowerCase()
  if (s.includes('accumulation')) return 'up'
  if (s.includes('distribution')) return 'down'
  return 'neutral'
}

/**
 * Nada volume dibaca dari z-score, bukan dari teks status: lonjakan volume
 * bukan kabar baik atau buruk dengan sendirinya — yang penting seberapa jauh
 * ia menyimpang dari kebiasaan, jadi warnanya menandai "perlu diperhatikan".
 */
function toneVolume(zscore) {
  const z = Number(zscore)
  if (!Number.isFinite(z)) return 'neutral'
  if (z >= 2) return 'info'
  if (z >= 1) return 'skip'
  if (z <= -1.5) return 'neutral'
  return 'neutral'
}

function toneInsider(status) {
  const s = String(status ?? '').toLowerCase()
  if (s.includes('insider buy')) return 'up'
  if (s.includes('insider sell')) return 'down'
  return 'neutral'
}
