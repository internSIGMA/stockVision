// Shared Indonesian-locale formatting helpers.

export function rupiah(n, opts = {}) {
  if (n == null || isNaN(n)) return '-'
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: opts.decimals ?? 0,
  }).format(n)
}

// Compact rupiah for large values: Rp 12,3 T / Rp 4,5 M / Rp 320 jt
export function rupiahShort(n) {
  if (n == null || isNaN(n)) return '-'
  const abs = Math.abs(n)
  const sign = n < 0 ? '-' : ''
  if (abs >= 1e12) return `${sign}Rp ${(abs / 1e12).toFixed(1)} T`
  if (abs >= 1e9) return `${sign}Rp ${(abs / 1e9).toFixed(1)} M`
  if (abs >= 1e6) return `${sign}Rp ${(abs / 1e6).toFixed(0)} jt`
  if (abs >= 1e3) return `${sign}Rp ${(abs / 1e3).toFixed(0)} rb`
  return `${sign}Rp ${abs.toFixed(0)}`
}

export function number(n) {
  if (n == null || isNaN(n)) return '-'
  return new Intl.NumberFormat('id-ID').format(n)
}

export function pct(n, decimals = 2) {
  if (n == null || isNaN(n)) return '-'
  const s = n > 0 ? '+' : ''
  return `${s}${n.toFixed(decimals)}%`
}

export function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'baru saja'
  if (mins < 60) return `${mins} menit lalu`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs} jam lalu`
  return `${Math.floor(hrs / 24)} hari lalu`
}
