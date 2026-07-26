import { generateOHLC, latestQuote, emitens, FOCUS_CODES } from '../data/market.js';

const TICKERS = ['BBCA', 'BBNI', 'BBRI', 'BMRI', 'BJBR', 'TLKM', 'ASII', 'ANTM'];

function seededValue(code, key, fallback = 0) {
  const str = `${code}:${key}`;
  let hash = 2166136261;
  for (let i = 0; i < str.length; i += 1) {
    hash ^= str.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return Math.abs(hash % 1000) / 1000 + fallback;
}

function getSummary(ticker) {
  const quote = latestQuote(ticker);
  return Promise.resolve({
    ticker,
    price: quote.price,
    change: quote.change,
    change_pct: quote.changePct,
    volume: quote.volume,
    spark: generateOHLC(ticker, 14).map((d) => d.close),
  });
}

function getOhlc(ticker, { days = 90 } = {}) {
  return Promise.resolve(generateOHLC(ticker, days));
}

function getInsiderTransactions(ticker) {
  return Promise.resolve([
    { date: '2026-07-15', ticker, insider_name: 'Director A', action: 'BUY', shares: 50000 },
    { date: '2026-07-14', ticker, insider_name: 'CEO B', action: 'SELL', shares: 120000 },
  ]);
}

function getBrokerSummary(ticker) {
  return Promise.resolve({
    ticker,
    top_buy: [
      { code: 'MIRA', value: 28000000000 },
      { code: 'BCA', value: 19000000000 },
    ],
    top_sell: [
      { code: 'TRI', value: 24000000000 },
      { code: 'BTPN', value: 15000000000 },
    ],
  });
}

function getFundamental(ticker) {
  return Promise.resolve({
    ticker,
    per: 10 + seededValue(ticker, 'per', 0),
    pbv: 1.4 + seededValue(ticker, 'pbv', 0),
    dividend_yield: 4 + seededValue(ticker, 'dy', 0),
    consensus: 'BUY',
  });
}

function getSchedulerStatus() {
  return Promise.resolve({
    active: true,
    is_trading_day: true,
    market_open: true,
    interval_minutes: 30,
    stats: { total: 120, success: 108, skip: 12 },
  });
}

function toggleScheduler(next) {
  return Promise.resolve({ active: next });
}

function triggerSchedulerManual() {
  return Promise.resolve({ ok: true });
}

function getSchedulerHistory() {
  return Promise.resolve([
    { time: '2026-07-16 09:30:00', status: 'SUCCESS', detail: 'Crawl selesai', emiten: 'BBCA' },
    { time: '2026-07-16 08:45:00', status: 'SKIP', detail: 'Diluar jam bursa', emiten: 'BBNI' },
  ]);
}

function getCrawlLogs({ limit = 50 } = {}) {
  return Promise.resolve(
    Array.from({ length: Math.min(limit, 6) }, (_, i) => ({
      job_id: `JOB-${i + 1}`,
      job_type: 'STOCK_INFO',
      target_ticker: TICKERS[i % TICKERS.length],
      target_date: '2026-07-16',
      status: i % 2 === 0 ? 'SUCCESS' : 'FAILED',
      records_count: 120 + i,
      created_at: '2026-07-16 09:30:00',
      error_message: i % 2 === 0 ? '' : 'Timeout saat mengambil data',
    }))
  );
}

export {
  TICKERS,
  getSummary,
  getOhlc,
  getInsiderTransactions,
  getBrokerSummary,
  getFundamental,
  getSchedulerStatus,
  toggleScheduler,
  triggerSchedulerManual,
  getSchedulerHistory,
  getCrawlLogs,
  emitens,
  FOCUS_CODES,
};
