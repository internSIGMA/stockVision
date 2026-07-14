/**
 * Indikator teknikal murni — dihitung di frontend dari histori OHLC
 * (/api/data/ohlc), karena backend tidak menyediakan endpoint indikator.
 *
 * Semua fungsi menerima array baris OHLC urut tanggal ASC (sesuai response
 * backend) dan mengembalikan null bila datanya belum cukup panjang. Tidak ada
 * yang melempar error — halaman cukup menampilkan "—" saat hasilnya null.
 */

/** Ambil satu kolom numerik, buang baris yang nilainya tidak terpakai. */
function series(rows, key) {
  return (rows || []).map((r) => Number(r[key])).filter((n) => !Number.isNaN(n))
}

/** Simple moving average pada nilai terakhir. */
export function sma(values, period) {
  if (!values || values.length < period) return null
  const window = values.slice(-period)
  return window.reduce((a, b) => a + b, 0) / period
}

/** Deret EMA penuh — dibutuhkan MACD yang meng-EMA-kan hasil EMA. */
function emaSeries(values, period) {
  if (!values || values.length < period) return []
  const k = 2 / (period + 1)
  // Seed dengan SMA periode pertama agar nilai awal tidak bias ke titik pertama.
  let prev = values.slice(0, period).reduce((a, b) => a + b, 0) / period
  const out = [prev]
  for (let i = period; i < values.length; i++) {
    prev = values[i] * k + prev * (1 - k)
    out.push(prev)
  }
  return out
}

export function ema(values, period) {
  const s = emaSeries(values, period)
  return s.length ? s[s.length - 1] : null
}

/**
 * RSI dengan smoothing Wilder (bukan rata-rata sederhana).
 * → 0..100
 */
export function rsi(rows, period = 14) {
  const closes = series(rows, 'close')
  if (closes.length < period + 1) return null

  let gain = 0
  let loss = 0
  for (let i = 1; i <= period; i++) {
    const diff = closes[i] - closes[i - 1]
    if (diff >= 0) gain += diff
    else loss -= diff
  }
  gain /= period
  loss /= period

  for (let i = period + 1; i < closes.length; i++) {
    const diff = closes[i] - closes[i - 1]
    gain = (gain * (period - 1) + (diff > 0 ? diff : 0)) / period
    loss = (loss * (period - 1) + (diff < 0 ? -diff : 0)) / period
  }

  // Harga yang benar-benar datar tidak punya arah — netral, bukan overbought.
  if (gain === 0 && loss === 0) return 50
  if (loss === 0) return 100
  return 100 - 100 / (1 + gain / loss)
}

/** → { macd, signal, histogram } */
export function macd(rows, fast = 12, slow = 26, signalPeriod = 9) {
  const closes = series(rows, 'close')
  if (closes.length < slow + signalPeriod) return null

  const fastSeries = emaSeries(closes, fast)
  const slowSeries = emaSeries(closes, slow)

  // EMA cepat mulai lebih awal — sejajarkan ke ekor agar indeksnya sepadan.
  const offset = fastSeries.length - slowSeries.length
  const macdLine = slowSeries.map((slowVal, i) => fastSeries[i + offset] - slowVal)

  const signalSeries = emaSeries(macdLine, signalPeriod)
  if (!signalSeries.length) return null

  const macdValue = macdLine[macdLine.length - 1]
  const signalValue = signalSeries[signalSeries.length - 1]
  return { macd: macdValue, signal: signalValue, histogram: macdValue - signalValue }
}

/** Moving average harga penutupan. */
export function movingAverage(rows, period = 20) {
  return sma(series(rows, 'close'), period)
}

/** → { upper, middle, lower, bandwidth } */
export function bollingerBands(rows, period = 20, multiplier = 2) {
  const closes = series(rows, 'close')
  if (closes.length < period) return null

  const window = closes.slice(-period)
  const middle = window.reduce((a, b) => a + b, 0) / period
  const variance = window.reduce((acc, v) => acc + (v - middle) ** 2, 0) / period
  const deviation = Math.sqrt(variance)

  const upper = middle + multiplier * deviation
  const lower = middle - multiplier * deviation
  return { upper, middle, lower, bandwidth: middle ? ((upper - lower) / middle) * 100 : 0 }
}

/** Stochastic oscillator → { k, d } */
export function stochastic(rows, period = 14, smoothing = 3) {
  if (!rows || rows.length < period + smoothing - 1) return null

  const kValues = []
  for (let i = rows.length - smoothing; i < rows.length; i++) {
    const window = rows.slice(i - period + 1, i + 1)
    const highest = Math.max(...window.map((r) => Number(r.high)))
    const lowest = Math.min(...window.map((r) => Number(r.low)))
    const close = Number(rows[i].close)
    const range = highest - lowest
    kValues.push(range === 0 ? 50 : ((close - lowest) / range) * 100)
  }

  const k = kValues[kValues.length - 1]
  const d = kValues.reduce((a, b) => a + b, 0) / kValues.length
  return { k, d }
}

/** Volume terakhir dibanding rata-ratanya → { ratio, latest, average } */
export function volumeSignal(rows, period = 20) {
  const volumes = series(rows, 'volume')
  if (volumes.length < period) return null

  const average = sma(volumes, period)
  const latest = volumes[volumes.length - 1]
  if (!average) return null
  return { ratio: latest / average, latest, average }
}

// ============================================================
// Interpretasi — mengubah angka mentah jadi label untuk UI
// ============================================================

/** Nada dipakai untuk mewarnai StatusPill: 'up' | 'down' | 'neutral'. */
function reading(value, label, tone) {
  return { value, label, tone }
}

export function rsiReading(value) {
  if (value == null) return reading(null, '—', 'neutral')
  if (value >= 70) return reading(value, 'Overbought', 'down')
  if (value <= 30) return reading(value, 'Oversold', 'up')
  return reading(value, 'Netral', 'neutral')
}

export function macdReading(result) {
  if (!result) return reading(null, '—', 'neutral')
  const bullish = result.histogram > 0
  return reading(result.macd, bullish ? 'Bullish' : 'Bearish', bullish ? 'up' : 'down')
}

export function maReading(value, close) {
  if (value == null || close == null) return reading(null, '—', 'neutral')
  const above = close > value
  return reading(value, above ? 'Di atas MA' : 'Di bawah MA', above ? 'up' : 'down')
}

export function bollingerReading(result, close) {
  if (!result || close == null) return reading(null, '—', 'neutral')
  if (close >= result.upper) return reading(result.upper, 'Tembus atas', 'down')
  if (close <= result.lower) return reading(result.lower, 'Tembus bawah', 'up')
  return reading(result.middle, 'Dalam band', 'neutral')
}

export function stochasticReading(result) {
  if (!result) return reading(null, '—', 'neutral')
  if (result.k >= 80) return reading(result.k, 'Overbought', 'down')
  if (result.k <= 20) return reading(result.k, 'Oversold', 'up')
  return reading(result.k, 'Netral', 'neutral')
}

export function volumeReading(result) {
  if (!result) return reading(null, '—', 'neutral')
  if (result.ratio >= 1.5) return reading(result.ratio, 'Volume tinggi', 'up')
  if (result.ratio <= 0.5) return reading(result.ratio, 'Volume rendah', 'down')
  return reading(result.ratio, 'Volume normal', 'neutral')
}

/**
 * Enam indikator sekaligus, sudah dalam bentuk siap-render.
 * → [{ key, name, display, label, tone }]
 */
export function summarizeIndicators(rows) {
  const close = rows?.length ? Number(rows[rows.length - 1].close) : null

  const rsiValue = rsi(rows)
  const macdValue = macd(rows)
  const maValue = movingAverage(rows, 20)
  const bbValue = bollingerBands(rows)
  const stochValue = stochastic(rows)
  const volValue = volumeSignal(rows)

  const fmt = (n, digits = 2) =>
    n == null || Number.isNaN(n) ? '—' : Number(n).toLocaleString('id-ID', {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    })

  const r = rsiReading(rsiValue)
  const m = macdReading(macdValue)
  const ma = maReading(maValue, close)
  const bb = bollingerReading(bbValue, close)
  const st = stochasticReading(stochValue)
  const vol = volumeReading(volValue)

  return [
    { key: 'rsi', name: 'RSI (14)', display: fmt(r.value), label: r.label, tone: r.tone },
    { key: 'macd', name: 'MACD (12,26,9)', display: fmt(m.value), label: m.label, tone: m.tone },
    { key: 'ma', name: 'MA (20)', display: fmt(ma.value, 0), label: ma.label, tone: ma.tone },
    { key: 'bb', name: 'Bollinger (20,2)', display: fmt(bb.value, 0), label: bb.label, tone: bb.tone },
    { key: 'stoch', name: 'Stochastic (14,3)', display: fmt(st.value), label: st.label, tone: st.tone },
    {
      key: 'volume',
      name: 'Volume Signal',
      display: vol.value == null ? '—' : `${fmt(vol.value)}×`,
      label: vol.label,
      tone: vol.tone,
    },
  ]
}
