/**
 * Mock market data layer for SahamScope.
 *
 * Everything here stands in for what the Python crawler would scrape from
 * Stockbit (broker summary, daily prices, insider/backdoor activity). Data
 * is generated deterministically per ticker via a seeded PRNG so charts stay
 * stable across reloads. Swap these functions for real API calls later —
 * the components only depend on the return shapes.
 */

// --- Seeded PRNG (mulberry32) -------------------------------------------
function mulberry32(seed) {
  return function () {
    seed |= 0
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function seedFromString(str) {
  let h = 1779033703 ^ str.length
  for (let i = 0; i < str.length; i++) {
    h = Math.imul(h ^ str.charCodeAt(i), 3432918353)
    h = (h << 13) | (h >>> 19)
  }
  return h >>> 0
}

// --- Emiten universe ----------------------------------------------------
// Focus: bank stocks (BBCA, BBNI, BBRI, BMRI, BJBR). Extra large caps fill
// out the market-summary table & heatmap.
export const emitens = [
  { code: 'BBCA', name: 'Bank Central Asia', sector: 'Perbankan', base: 9875 },
  { code: 'BBNI', name: 'Bank Negara Indonesia', sector: 'Perbankan', base: 5450 },
  { code: 'BBRI', name: 'Bank Rakyat Indonesia', sector: 'Perbankan', base: 4680 },
  { code: 'BMRI', name: 'Bank Mandiri', sector: 'Perbankan', base: 6300 },
  { code: 'BJBR', name: 'Bank Jabar Banten', sector: 'Perbankan', base: 1180 },
  { code: 'TLKM', name: 'Telkom Indonesia', sector: 'Telekomunikasi', base: 2870 },
  { code: 'ASII', name: 'Astra International', sector: 'Konsumer', base: 4900 },
  { code: 'ANTM', name: 'Aneka Tambang', sector: 'Energi', base: 1560 },
  { code: 'ADRO', name: 'Adaro Energy', sector: 'Energi', base: 2450 },
  { code: 'GOTO', name: 'GoTo Gojek Tokopedia', sector: 'Teknologi', base: 62 },
  { code: 'PTBA', name: 'Bukit Asam', sector: 'Energi', base: 2680 },
  { code: 'PTPP', name: 'PP (Persero)', sector: 'Properti', base: 460 },
  { code: 'SMRA', name: 'Summarecon Agung', sector: 'Properti', base: 585 },
  { code: 'ASRI', name: 'Alam Sutera Realty', sector: 'Properti', base: 178 },
  { code: 'CTRA', name: 'Ciputra Development', sector: 'Properti', base: 1180 },
  { code: 'INCO', name: 'Vale Indonesia', sector: 'Energi', base: 3620 },
  { code: 'INDF', name: 'Indofood Sukses Makmur', sector: 'Konsumer', base: 6725 },
  { code: 'MAPI', name: 'Mitra Adiperkasa', sector: 'Konsumer', base: 1490 },
  { code: 'SMGR', name: 'Semen Indonesia', sector: 'Konsumer', base: 3900 },
]

// The five banks we prioritise across the app.
export const FOCUS_CODES = ['BBCA', 'BBNI', 'BBRI', 'BMRI', 'BJBR']

export function getEmiten(code) {
  return emitens.find((e) => e.code === code) || emitens[0]
}

// --- Daily OHLCV series -------------------------------------------------
export function generateOHLC(code, days = 120) {
  const e = getEmiten(code)
  const rand = mulberry32(seedFromString(code))
  const out = []
  let price = e.base * 0.82 // start below current, trend up toward base
  const drift = (e.base - price) / days
  const start = new Date()
  start.setDate(start.getDate() - days)

  for (let i = 0; i < days; i++) {
    const d = new Date(start)
    d.setDate(start.getDate() + i)
    if (d.getDay() === 0 || d.getDay() === 6) continue // skip weekends

    const vol = e.base * 0.018
    const open = price
    const move = drift + (rand() - 0.5) * vol
    const close = Math.max(50, open + move)
    const high = Math.max(open, close) + rand() * vol * 0.6
    const low = Math.min(open, close) - rand() * vol * 0.6
    const volume = Math.round((0.8 + rand()) * 45_000_000)

    out.push({
      x: d.getTime(),
      date: d.toISOString().slice(0, 10),
      open: Math.round(open),
      high: Math.round(high),
      low: Math.round(low),
      close: Math.round(close),
      volume,
    })
    price = close
  }
  return out
}

export function latestQuote(code) {
  const s = generateOHLC(code, 40)
  const last = s[s.length - 1]
  const prev = s[s.length - 2]
  const change = last.close - prev.close
  return {
    code,
    name: getEmiten(code).name,
    price: last.close,
    change,
    changePct: (change / prev.close) * 100,
    volume: last.volume,
    high: last.high,
    low: last.low,
  }
}

// --- Market overview (for the "Markets Today" dashboard) ----------------
export function marketOverview() {
  const quotes = emitens.map((e) => ({ ...latestQuote(e.code), sector: e.sector }))
  const sorted = [...quotes].sort((a, b) => b.changePct - a.changePct)
  const avg = quotes.reduce((a, q) => a + q.changePct, 0) / quotes.length

  // Aggregate by sector.
  const bySector = {}
  for (const q of quotes) {
    ;(bySector[q.sector] ??= []).push(q.changePct)
  }
  const sectors = Object.entries(bySector)
    .map(([sector, arr]) => ({ sector, changePct: arr.reduce((a, b) => a + b, 0) / arr.length }))
    .sort((a, b) => b.changePct - a.changePct)

  return {
    quotes,
    sentiment: avg >= 0 ? 'Bullish' : 'Bearish',
    avgChange: avg,
    topStock: sorted[0],
    worstStock: sorted[sorted.length - 1],
    hottestSector: sectors[0],
    worstSector: sectors[sectors.length - 1],
    sectors,
    // Index proxy: cap-weighted-ish average of the five banks.
    index: {
      code: 'IHSG',
      value: 7300 + avg * 40,
      changePct: avg,
    },
  }
}

// --- Trading terminal: tick size, order book, done trades ---------------
export function tickSize(price) {
  if (price < 200) return 1
  if (price < 500) return 2
  if (price < 2000) return 5
  if (price < 5000) return 10
  return 25
}

export function terminalStats(code) {
  const s = generateOHLC(code, 2)
  const last = s[s.length - 1]
  const prev = s[s.length - 2] ?? last
  const rand = mulberry32(seedFromString(code + 'term'))
  const change = last.close - prev.close
  const bidRatio = Math.round(35 + rand() * 40) // % lot on bid side
  return {
    code,
    last: last.close,
    prev: prev.close,
    open: last.open,
    high: last.high,
    low: last.low,
    avg: Math.round((last.high + last.low + last.close) / 3),
    change,
    changePct: (change / prev.close) * 100,
    freq: Math.round(1200 + rand() * 26000),
    value: Math.round((0.4 + rand()) * 8e11), // rupiah
    volume: last.volume,
    bidRatio,
  }
}

export function orderBook(code, levels = 7) {
  const st = terminalStats(code)
  const step = tickSize(st.last)
  const rand = mulberry32(seedFromString(code + 'ob'))
  const bids = []
  const offers = []
  for (let i = 0; i < levels; i++) {
    const bidPrice = st.last - step * (i + 1)
    const offerPrice = st.last + step * i
    bids.push({ price: bidPrice, lot: Math.round((0.5 + rand()) * 9000) })
    offers.push({ price: offerPrice, lot: Math.round((0.5 + rand()) * 9000) })
  }
  const totalBid = bids.reduce((a, b) => a + b.lot, 0)
  const totalOffer = offers.reduce((a, b) => a + b.lot, 0)
  return { bids, offers, totalBid, totalOffer }
}

export function doneTrades(code, n = 12) {
  const st = terminalStats(code)
  const step = tickSize(st.last)
  const rand = mulberry32(seedFromString(code + 'dt'))
  const out = []
  let t = Date.now()
  for (let i = 0; i < n; i++) {
    const side = rand() > 0.5 ? 'buy' : 'sell'
    const price = st.last + step * (Math.floor(rand() * 5) - 2)
    t -= Math.round(rand() * 90000)
    out.push({
      time: new Date(t).toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      price,
      lot: Math.round((0.2 + rand()) * 1500),
      side,
    })
  }
  return out
}

// --- Broker summary (bandarmology) --------------------------------------
const BROKERS = [
  { code: 'BK', name: 'J.P. Morgan Sekuritas' },
  { code: 'CC', name: 'Mandiri Sekuritas' },
  { code: 'YP', name: 'Mirae Asset Sekuritas' },
  { code: 'AK', name: 'UBS Sekuritas' },
  { code: 'ZP', name: 'Maybank Sekuritas' },
  { code: 'RX', name: 'Macquarie Sekuritas' },
  { code: 'DR', name: 'RHB Sekuritas' },
  { code: 'KZ', name: 'CLSA Sekuritas' },
]

export function brokerSummary(code) {
  const rand = mulberry32(seedFromString(code + 'broker'))
  const q = latestQuote(code)
  const rows = BROKERS.map((b) => {
    const buyLot = Math.round(rand() * 90_000)
    const sellLot = Math.round(rand() * 90_000)
    const netLot = buyLot - sellLot
    return {
      broker: b.code,
      name: b.name,
      buyLot,
      sellLot,
      netLot,
      buyValue: buyLot * 100 * q.price,
      sellValue: sellLot * 100 * q.price,
      netValue: netLot * 100 * q.price,
    }
  })
  const buyers = [...rows].filter((r) => r.netLot > 0).sort((a, b) => b.netLot - a.netLot)
  const sellers = [...rows].filter((r) => r.netLot < 0).sort((a, b) => a.netLot - b.netLot)
  return { rows, buyers, sellers }
}

// --- Insider / backdoor activity ----------------------------------------
const INSIDERS = [
  { name: 'Sunarso', role: 'Direktur Utama' },
  { name: 'Catur Budi Harto', role: 'Wakil Direktur Utama' },
  { name: 'PT Danareksa (Persero)', role: 'Pemegang Saham >5%' },
  { name: 'Viviana Dyah Ayu R.K.', role: 'Direktur Keuangan' },
  { name: 'Agus Sudiarto', role: 'Komisaris' },
]

export function insiderActivity(code) {
  const rand = mulberry32(seedFromString(code + 'insider'))
  const q = latestQuote(code)
  const out = []
  for (let i = 0; i < 8; i++) {
    const p = INSIDERS[Math.floor(rand() * INSIDERS.length)]
    const type = rand() > 0.45 ? 'buy' : 'sell'
    const shares = Math.round((0.1 + rand()) * 2_500_000) * 100
    const price = Math.round(q.price * (0.95 + rand() * 0.1))
    const d = new Date()
    d.setDate(d.getDate() - Math.floor(rand() * 45))
    out.push({
      date: d.toISOString().slice(0, 10),
      name: p.name,
      role: p.role,
      type,
      shares,
      price,
      value: shares * price,
      purpose: type === 'buy' ? 'Akumulasi' : 'Divestasi',
    })
  }
  return out.sort((a, b) => b.date.localeCompare(a.date))
}

// --- Technical indicators ------------------------------------------------
export function sma(series, period) {
  const out = []
  for (let i = 0; i < series.length; i++) {
    if (i < period - 1) {
      out.push(null)
      continue
    }
    let sum = 0
    for (let j = i - period + 1; j <= i; j++) sum += series[j].close
    out.push(+(sum / period).toFixed(2))
  }
  return out
}

export function rsi(series, period = 14) {
  const out = []
  let gains = 0
  let losses = 0
  for (let i = 1; i < series.length; i++) {
    const diff = series[i].close - series[i - 1].close
    const g = Math.max(0, diff)
    const l = Math.max(0, -diff)
    if (i <= period) {
      gains += g
      losses += l
      out.push(null)
      if (i === period) {
        gains /= period
        losses /= period
        const rs = losses === 0 ? 100 : gains / losses
        out[out.length - 1] = +(100 - 100 / (1 + rs)).toFixed(1)
      }
    } else {
      gains = (gains * (period - 1) + g) / period
      losses = (losses * (period - 1) + l) / period
      const rs = losses === 0 ? 100 : gains / losses
      out.push(+(100 - 100 / (1 + rs)).toFixed(1))
    }
  }
  out.unshift(null)
  return out
}

// --- Forecast (simple linear trend + noise band) ------------------------
export function forecast(code, horizon = 20) {
  const series = generateOHLC(code, 120)
  const n = series.length
  const ys = series.map((s) => s.close)
  // Least-squares slope over last 30 points.
  const win = ys.slice(-30)
  const m = win.length
  const xs = win.map((_, i) => i)
  const meanX = xs.reduce((a, b) => a + b, 0) / m
  const meanY = win.reduce((a, b) => a + b, 0) / m
  let num = 0
  let den = 0
  xs.forEach((x, i) => {
    num += (x - meanX) * (win[i] - meanY)
    den += (x - meanX) ** 2
  })
  const slope = num / den
  const intercept = meanY - slope * meanX

  const rand = mulberry32(seedFromString(code + 'fc'))
  const last = series[n - 1]
  const points = []
  for (let i = 1; i <= horizon; i++) {
    const d = new Date(last.x)
    d.setDate(d.getDate() + i)
    const mid = intercept + slope * (m - 1 + i)
    const spread = mid * 0.012 * Math.sqrt(i)
    points.push({
      x: d.getTime(),
      date: d.toISOString().slice(0, 10),
      mid: Math.round(mid),
      lower: Math.round(mid - spread - rand() * mid * 0.005),
      upper: Math.round(mid + spread + rand() * mid * 0.005),
    })
  }
  const projected = points[points.length - 1].mid
  const changePct = ((projected - last.close) / last.close) * 100
  return { history: series, points, projected, changePct, slope }
}

// --- Crawling job status (for the monitor page) -------------------------
export const crawlSources = ['Broker Summary', 'Harga Harian', 'Insider Activity']

export function seedCrawlJobs() {
  const rand = mulberry32(20260702)
  const jobs = []
  const codes = ['BBRI', 'BBCA', 'BBNI']
  const statuses = ['success', 'success', 'success', 'running', 'failed']
  for (const code of codes) {
    for (const source of crawlSources) {
      const status = statuses[Math.floor(rand() * statuses.length)]
      const minsAgo = Math.floor(rand() * 240)
      const last = new Date(Date.now() - minsAgo * 60000)
      jobs.push({
        id: `${code}-${source}`.replace(/\s+/g, '-').toLowerCase(),
        code,
        source,
        status,
        records: status === 'failed' ? 0 : Math.round(rand() * 4800 + 200),
        durationMs: Math.round(rand() * 8000 + 800),
        lastRun: last.toISOString(),
        nextRunMins: Math.round(rand() * 30 + 5),
        error: status === 'failed' ? 'HTTP 429 — rate limited oleh sumber' : null,
      })
    }
  }
  return jobs
}
