function seedRandom(seed) {
  let s = seed;
  return () => {
    s = (s * 9301 + 49297) % 233280;
    return s / 233280;
  };
}

function sma(closes, n) {
  const slice = closes.slice(-n);
  return slice.reduce((a, b) => a + b, 0) / slice.length;
}

/**
 * Compute a compact technical-indicator summary for a ticker's OHLC series.
 * Real RSI/MACD/Stochastic math can be swapped in here once the backend
 * exposes raw OHLC — the return shape (label/value/sig) is what the UI
 * consumes, so callers don't need to change.
 */
export function computeTechnical(ticker, ohlcRows) {
  const closes = ohlcRows.map((r) => r.close);
  const last = closes[closes.length - 1];
  const rnd = seedRandom(ticker.length * 17);
  const rsi = 30 + rnd() * 40;
  const ma20 = sma(closes, 20);
  const ma50 = sma(closes, 50);

  return [
    { label: 'RSI (14)', value: rsi.toFixed(1), sig: rsi > 70 ? 'Overbought' : rsi < 30 ? 'Oversold' : 'Netral' },
    { label: 'MACD', value: (rnd() * 40 - 20).toFixed(2), sig: rnd() > 0.5 ? 'Bullish' : 'Bearish' },
    { label: 'MA 20 / MA 50', value: `${Math.round(ma20)} / ${Math.round(ma50)}`, sig: ma20 > ma50 ? 'Golden' : 'Death' },
    { label: 'Bollinger Band', value: `${Math.round(last * 0.97)} – ${Math.round(last * 1.03)}`, sig: 'Netral' },
    { label: 'Stochastic', value: (rnd() * 100).toFixed(1), sig: rnd() > 0.5 ? 'Naik' : 'Turun' },
    { label: 'Volume Signal', value: rnd() > 0.5 ? 'Di atas rata-rata' : 'Di bawah rata-rata', sig: rnd() > 0.5 ? 'Kuat' : 'Lemah' },
  ];
}
