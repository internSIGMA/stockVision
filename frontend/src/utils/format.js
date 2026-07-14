/**
 * Formatter tampilan, semua ber-locale id-ID.
 *
 * Nilai kosong selalu jadi em-dash, bukan "0" — angka nol yang sah dan data
 * yang belum ada tidak boleh terlihat sama.
 */

const KOSONG = '—'

function isKosong(n) {
  return n == null || n === '' || Number.isNaN(Number(n))
}

/** 9875 → "9.875" */
export function formatNumber(n, opts = {}) {
  if (isKosong(n)) return KOSONG
  return new Intl.NumberFormat('id-ID', {
    minimumFractionDigits: opts.decimals ?? 0,
    maximumFractionDigits: opts.decimals ?? 0,
  }).format(Number(n))
}

/**
 * Angka besar dipadatkan agar muat di kartu sempit:
 * 12.300.000.000.000 → "12,3 T", 4.500.000 → "4,5 jt"
 */
export function formatCompact(n) {
  if (isKosong(n)) return KOSONG

  const num = Number(n)
  const abs = Math.abs(num)
  const tanda = num < 0 ? '-' : ''

  const satu = (nilai, suffix) =>
    `${tanda}${nilai.toLocaleString('id-ID', { maximumFractionDigits: 1 })} ${suffix}`

  if (abs >= 1e12) return satu(abs / 1e12, 'T')
  if (abs >= 1e9) return satu(abs / 1e9, 'M')
  if (abs >= 1e6) return satu(abs / 1e6, 'jt')
  if (abs >= 1e3) return satu(abs / 1e3, 'rb')
  return `${tanda}${abs.toLocaleString('id-ID', { maximumFractionDigits: 0 })}`
}

/** 1.28 → "+1,28%" — tanda plus eksplisit supaya arah terbaca tanpa warna. */
export function formatPercent(n, decimals = 2) {
  if (isKosong(n)) return KOSONG

  const num = Number(n)
  const tanda = num > 0 ? '+' : ''
  return `${tanda}${num.toLocaleString('id-ID', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })}%`
}

/** "2026-07-14" → "14 Jul 2026" */
export function formatDate(value) {
  if (!value) return KOSONG

  const d = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(d.getTime())) return KOSONG

  return d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', year: 'numeric' })
}

/** Warna arah harga. Nol dianggap netral, bukan naik. */
export function trendClass(n) {
  if (isKosong(n) || Number(n) === 0) return 'text-muted-foreground'
  return Number(n) > 0 ? 'text-up' : 'text-down'
}
