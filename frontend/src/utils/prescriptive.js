/**
 * Rekomendasi aksi (BELI / TAHAN / JUAL) dari indikator teknikal.
 *
 * Perhitungan indikatornya sendiri TIDAK diulang di sini — semuanya dipinjam
 * dari technicalIndicators.js yang sudah dipakai komponen Technical. Modul ini
 * hanya menambahkan dua hal yang belum ada: tren aliran dana asing dan
 * penilaian gabungan yang menghasilkan satu kata keputusan.
 */
import {
  bollingerBands,
  macd,
  movingAverage,
  rsi,
} from '@/utils/technicalIndicators'

/** Sesi terakhir yang dipakai untuk menilai arah dana asing. */
const SESI_ASING = 5

/**
 * Net foreign flow beberapa sesi terakhir, dari selisih foreign_buy dan
 * foreign_sell.
 *
 * Kolom foreign_flow SENGAJA tidak dipakai sebagai cadangan: isinya angka
 * kumulatif yang terus membesar (−56,2 T → −56,4 T → −56,5 T di baris
 * berurutan), bukan arus harian. Menjumlahkannya bersama selisih harian akan
 * menenggelamkan sinyalnya. Baris tanpa buy/sell dilewati, dan hasilnya null
 * kalau tidak ada satu pun angka — dibedakan dari 0 yang berarti seimbang.
 */
export function foreignFlowTrend(rows, sesi = SESI_ASING) {
  if (!Array.isArray(rows) || !rows.length) return null

  const nilai = rows
    .slice(-sesi)
    .map((r) => {
      const beli = Number(r.foreign_buy)
      const jual = Number(r.foreign_sell)
      return Number.isFinite(beli) && Number.isFinite(jual) ? beli - jual : null
    })
    .filter((v) => v !== null)

  if (!nilai.length) return null
  return nilai.reduce((a, b) => a + b, 0)
}

/**
 * Menimbang sinyal bullish lawan bearish. Tiap sinyal menyumbang bobot;
 * sinyal ekstrem (oversold/overbought) berbobot dua karena paling menentukan.
 * Sinyal yang datanya tidak tersedia tidak ikut menimbang sama sekali,
 * bukan dianggap netral — supaya emiten tanpa data asing tidak tertarik turun.
 */
export function buildRecommendation(rows) {
  if (!Array.isArray(rows) || !rows.length) return null

  const closes = rows.map((r) => Number(r.close)).filter(Number.isFinite)
  if (!closes.length) return null

  const close = closes[closes.length - 1]
  const nilaiRsi = rsi(rows)
  const hasilMacd = macd(rows)
  const ma20 = movingAverage(rows, 20)
  const bb = bollingerBands(rows)
  const asing = foreignFlowTrend(rows)

  let bull = 0
  let bear = 0
  const alasan = []

  if (nilaiRsi !== null) {
    if (nilaiRsi < 30) {
      bull += 2
      alasan.push('RSI oversold')
    } else if (nilaiRsi < 45) {
      bull += 1
      alasan.push('RSI condong bawah')
    } else if (nilaiRsi > 70) {
      bear += 2
      alasan.push('RSI overbought')
    } else if (nilaiRsi > 55) {
      bear += 1
      alasan.push('RSI condong atas')
    }
  }

  // Histogram (MACD - garis sinyal) yang menentukan arah, bukan nilai MACD-nya
  // sendiri — itu yang bikin persilangan terbaca.
  if (hasilMacd) {
    if (hasilMacd.histogram > 0) {
      bull += 1
      alasan.push('MACD di atas garis sinyal')
    } else {
      bear += 1
      alasan.push('MACD di bawah garis sinyal')
    }
  }

  if (ma20 !== null) {
    if (close > ma20) {
      bull += 1
      alasan.push('harga di atas MA20')
    } else {
      bear += 1
      alasan.push('harga di bawah MA20')
    }
  }

  if (bb) {
    if (close < bb.lower) {
      bull += 1
      alasan.push('harga menembus batas bawah Bollinger')
    } else if (close > bb.upper) {
      bear += 1
      alasan.push('harga menembus batas atas Bollinger')
    }
  }

  if (asing !== null) {
    if (asing > 0) {
      bull += 1
      alasan.push('asing net beli')
    } else if (asing < 0) {
      bear += 1
      alasan.push('asing net jual')
    }
  }

  const total = bull + bear
  const rasio = total ? bull / total : 0.5

  let aksi = 'TAHAN'
  if (rasio >= 0.65) aksi = 'BELI'
  else if (rasio <= 0.35) aksi = 'JUAL'

  return {
    aksi,
    bull,
    bear,
    rasio,
    alasan,
    close,
    rsi: nilaiRsi,
    macd: hasilMacd,
    ma20,
    bollinger: bb,
    foreignFlow: asing,
  }
}

/**
 * Ringkasan dari LLM datang ber-markdown ringan: **tebal** untuk subjek dan
 * *miring* untuk istilah teknikal, dengan baris kosong sebagai pemisah alinea.
 *
 * Dipecah jadi token, bukan disuntik lewat v-html: teksnya berasal dari model,
 * jadi tidak boleh ada jalan masuk HTML ke halaman. Template merender tiap
 * token sebagai <strong>/<em>/teks biasa.
 *
 * → [{ id, bagian: [{ teks, gaya: 'tebal' | 'miring' | null }] }]
 */
export function parseRingkasan(teks) {
  if (!teks) return []

  return String(teks)
    .split(/\n{2,}/)
    .map((p) => p.trim())
    .filter(Boolean)
    .map((paragraf, i) => ({
      id: i,
      bagian: paragraf
        .split(/(\*\*[^*]+\*\*|\*[^*\n]+\*)/g)
        .filter(Boolean)
        .map((potong) => {
          if (potong.startsWith('**') && potong.endsWith('**')) {
            return { teks: potong.slice(2, -2), gaya: 'tebal' }
          }
          if (potong.startsWith('*') && potong.endsWith('*')) {
            return { teks: potong.slice(1, -1), gaya: 'miring' }
          }
          return { teks: potong, gaya: null }
        }),
    }))
}

/** Kalimat saran yang menyertai keputusan. */
export const SARAN = {
  BELI:
    'Mayoritas sinyal teknikal condong bullish. Pertimbangkan masuk bertahap ' +
    'dengan batas rugi yang sudah ditentukan di awal.',
  TAHAN:
    'Sinyal teknikal masih campuran. Tunggu konfirmasi arah sebelum menambah ' +
    'atau mengurangi posisi.',
  JUAL:
    'Mayoritas sinyal teknikal condong bearish. Pertimbangkan mengurangi ' +
    'eksposur atau memperketat batas rugi.',
}
