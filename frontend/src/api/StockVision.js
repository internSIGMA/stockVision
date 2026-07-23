import api from './index'

/**
 * Kontrak API StockVision — dipetakan dari kode backend Flask yang sudah ada.
 *
 * Backend punya DUA keluarga endpoint:
 *   - /api/data/*  → membaca data yang sudah tersimpan di PostgreSQL (cepat)
 *   - /ohlc, /stock-info, /majorholder, /broker-activity (tanpa prefix)
 *                  → menjalankan crawl ke Stockbit lalu menyimpan ke DB (lambat)
 * Endpoint crawl memakai method GET, bukan POST.
 */

/** Backend menolak emiten di luar daftar ini dengan HTTP 400. */
export const SUPPORTED_TICKERS = ['BBCA', 'BBNI', 'BBRI', 'BMRI', 'BJBR']

export function isSupported(ticker) {
  return SUPPORTED_TICKERS.includes(String(ticker || '').toUpperCase())
}

/** Crawl bisa memakan waktu lama karena menembak sumber eksternal. */
const CRAWL_TIMEOUT = 120000

// ============================================================
// DATA MARKET (baca dari DB)
// ============================================================

/**
 * Snapshot harga terakhir.
 * → { symbol, nama, tanggal, waktu_update, harga, harga_sebelumnya, perubahan,
 *     perubahan_persen, volume, rata_rata, bid_price, bid_volume,
 *     offer_price, offer_volume, status_pasar }
 * Mengembalikan 404 jika emiten belum pernah di-crawl.
 */
export function getStockSummary(ticker) {
  return api.get('/api/data/stock-info', { params: { symbol: ticker } })
}

/**
 * Histori OHLC + foreign flow (urut tanggal ASC).
 * → [{ symbol, tanggal, open, high, low, close, volume,
 *      foreign_buy, foreign_sell, foreign_flow }]
 */
export function getOhlcHistory(ticker, params = {}) {
  return api.get('/api/data/ohlc', { params: { symbol: ticker, ...params } })
}

/** Foreign flow berasal dari response OHLC yang sama — tidak ada endpoint terpisah. */
export async function getForeignFlow(ticker, params = {}) {
  const rows = await getOhlcHistory(ticker, params)
  return rows.map((r) => ({
    tanggal: r.tanggal,
    foreign_buy: r.foreign_buy,
    foreign_sell: r.foreign_sell,
    foreign_flow: r.foreign_flow,
  }))
}

/**
 * Insider / majorholder activity.
 * → [{ id_trx, nama, symbol, tanggal, aksi, sebelumnya, sebelumnya_persen,
 *      sekarang, sekarang_persen, perubahan, perubahan_persen, harga,
 *      sumber, kewarganegaraan, broker, badge }]
 */
export function getInsiderTransactions(ticker, params = {}) {
  return api.get('/api/data/majorholder', { params: { symbol: ticker, ...params } })
}

/**
 * Broker activity.
 * → [{ symbol, broker_code, broker_type, tanggal, nilai_rp, lot,
 *      avg_price, frekuensi, aksi }]
 */
export function getBrokerActivity(ticker, params = {}) {
  return api.get('/api/data/broker-activity', { params: { symbol: ticker, ...params } })
}

// ============================================================
// FORECASTING
// ============================================================

/**
 * Proyeksi harga dari model time-series di backend.
 *
 * TODO: sambungkan ke endpoint forecasting backend. Path dan bentuk response
 * di bawah BELUM ada di backend — pemanggilnya (useForecastData.js) menormalkan
 * hasilnya dengan `??` multi key-name dan jatuh ke data placeholder saat
 * endpoint membalas 404, jadi begitu backend siap idealnya cuma path ini yang
 * perlu diubah.
 *
 * Bentuk yang diharapkan (semua field opsional kecuali deret prediksinya):
 * → { symbol, model, horizon, confidence, trend,
 *     predictions: [{ tanggal, prediksi, lower, upper }] }
 */
export function getForecast(ticker, params = {}) {
  return api.get('/api/data/forecast', { params: { symbol: ticker, ...params } })
}

// ============================================================
// CRAWL (memicu crawler, lalu simpan ke DB)
// ============================================================

export function crawlStockInfo(ticker) {
  return api.get('/stock-info', { params: { symbol: ticker }, timeout: CRAWL_TIMEOUT })
}

export function crawlOhlc(ticker, params = {}) {
  return api.get('/ohlc', { params: { symbol: ticker, ...params }, timeout: CRAWL_TIMEOUT })
}

/** Majorholder di-crawl per rentang tanggal untuk seluruh pasar, bukan per emiten. */
export function crawlMajorholder(params = {}) {
  return api.get('/majorholder', { params, timeout: CRAWL_TIMEOUT })
}

export function crawlBrokerActivity(params = {}) {
  return api.get('/broker-activity', { params, timeout: CRAWL_TIMEOUT })
}

/** Crawl satu emiten: snapshot harga + histori OHLC. */
export function triggerCrawl(ticker) {
  return Promise.all([crawlStockInfo(ticker), crawlOhlc(ticker)])
}

/**
 * Crawl banyak emiten. Dijalankan berurutan agar tidak membanjiri crawler,
 * dan tidak berhenti saat satu emiten gagal.
 * → [{ ticker, ok, error }]
 */
export async function triggerCrawlAll(tickers = SUPPORTED_TICKERS) {
  const results = []
  for (const ticker of tickers) {
    try {
      await triggerCrawl(ticker)
      results.push({ ticker, ok: true, error: null })
    } catch (err) {
      results.push({ ticker, ok: false, error: err.message })
    }
  }
  return results
}

/**
 * Riwayat crawling (tabel crawl_logs), terbaru dulu.
 * → [{ id, job_type, target, tanggal_target, status, records_count,
 *      error_message, created_at }]
 * status: SUCCESS | FAILED | SKIP
 */
export function getCrawlLogs(params = {}) {
  return api.get('/crawl-status', { params: { limit: 50, ...params } })
}

// ============================================================
// SCHEDULER
// ============================================================

/**
 * → { scheduler: { running, paused, interval_minutes, crawl_in_progress,
 *                  last_run, last_result, next_run, total_runs,
 *                  total_success, total_skipped },
 *     market:    { current_time_wib, is_trading_day, day_info,
 *                  is_trading_hours, market_hours, next_trading_day },
 *     targets:   [...],
 *     history:   [...] }  // 10 eksekusi terakhir
 */
export function getSchedulerStatus() {
  return api.get('/scheduler/status')
}

export function startScheduler() {
  return api.post('/scheduler/start')
}

export function stopScheduler() {
  return api.post('/scheduler/stop')
}

export function pauseScheduler() {
  return api.post('/scheduler/pause')
}

export function resumeScheduler() {
  return api.post('/scheduler/resume')
}

/** Backend tidak punya /scheduler/toggle — ON/OFF dipetakan ke start/stop. */
export function toggleScheduler(enabled) {
  return enabled ? startScheduler() : stopScheduler()
}

export function triggerSchedulerManual() {
  return api.post('/scheduler/trigger', null, { timeout: CRAWL_TIMEOUT })
}

// ============================================================
// USER & WATCHLIST
// ============================================================

/** → { id, email, username, name, role, default_ticker } | 401 */
export async function loginUser(email, password) {
  const baseUrl =
    import.meta.env.VITE_API_BASE_URL ||
    'http://127.0.0.1:8080'

  const response = await fetch(`${baseUrl}/users/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email,
      password,
    }),
  })

  let data = {}

  try {
    data = await response.json()
  } catch {
    data = {}
  }

  if (!response.ok) {
    throw new Error(
      data.error ||
      data.message ||
      'Login gagal. Periksa email dan kata sandi.',
    )
  }

  return data
}

/**
 * Login menggunakan Google Identity Services.
 *
 * idToken berasal dari response.credential milik Google.
 * → { id, email, username, name, role, access_role, default_ticker }
 */
export async function loginWithGoogle(idToken) {
  const baseUrl =
    import.meta.env.VITE_API_BASE_URL ||
    'http://127.0.0.1:8080'

  const response = await fetch(`${baseUrl}/users/google-login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      id_token: idToken,
    }),
  })

  let data = {}

  try {
    data = await response.json()
  } catch {
    data = {}
  }

  if (!response.ok) {
    throw new Error(
      data.error ||
      data.message ||
      'Login dengan Google gagal.',
    )
  }

  return data
}

// ------------------------------------------------------------
// RESET PASSWORD (backend/user.py — sudah diverifikasi)
//
// Alur: send-code → verify-code (dapat token) → reset (pakai token).
// Kode berlaku 5 menit dan disimpan di memori proses Flask, jadi restart
// backend membatalkan kode yang sedang beredar.
// ------------------------------------------------------------

/**
 * Kirim kode verifikasi 6 karakter (huruf besar + angka) ke email.
 * → { message, simulated, debug_code? } | 404 kalau email tidak terdaftar
 *
 * simulated=true berarti SMTP belum dikonfigurasi dan backend menitipkan
 * kodenya lewat debug_code supaya flow tetap bisa diuji tanpa email sungguhan.
 */
export function requestResetCode(email) {
  return api.post('/users/reset-password/send-code', { email })
}

/** Tukar kode dengan token sekali pakai. → { message, token } | 400 */
export function verifyResetCode(email, code) {
  return api.post('/users/reset-password/verify-code', { email, code })
}

/** Simpan password baru. Backend hanya butuh token + password. → { message } | 400 */
export function resetPassword({ token, password }) {
  return api.post('/users/reset-password/reset', { token, password })
}

/** → [{ id, name, symbols: [...] }] */
export function getWatchlists(userId) {
  return api.get(`/users/${userId}/watchlists`)
}

export function updateWatchlist(userId, watchlistId, payload) {
  return api.put(`/users/${userId}/watchlists/${watchlistId}`, payload)
}

export function createWatchlist(userId, payload) {
  return api.post(`/users/${userId}/watchlists`, payload)
}

export function deleteWatchlist(userId, watchlistId) {
  return api.delete(`/users/${userId}/watchlists/${watchlistId}`)
}

/** Emiten utama tersimpan sebagai kolom default_ticker di tabel users. */
export function updateUser(userId, payload) {
  return api.put(`/users/${userId}`, payload)
}
