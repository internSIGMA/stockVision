/**
 * Data forecasting TIRUAN — dipakai hanya selama endpoint backend belum ada,
 * supaya kartu Forecasting bisa dirakit dan direview tanpa menunggu backend.
 *
 * INI BUKAN MODEL PERAMALAN. Tidak ada ARIMA/Prophet/LSTM di sini, dan angkanya
 * tidak boleh dipercaya sebagai proyeksi apa pun — cuma garis datar berombak
 * yang berangkat dari harga penutupan terakhir supaya bentuk chart-nya masuk
 * akal. Setiap kali dipakai, UI WAJIB menandainya sebagai data contoh.
 *
 * TODO: hapus file ini begitu endpoint forecasting backend tersedia.
 */

/** Deterministik: ticker yang sama selalu menghasilkan angka yang sama. */
function seedDari(ticker) {
  return String(ticker || '')
    .split('')
    .reduce((acc, ch) => acc + ch.charCodeAt(0), 0)
}

/** Melewati Sabtu & Minggu — bursa tidak buka. */
function hariBursaBerikutnya(dari) {
  const d = new Date(dari)
  do {
    d.setDate(d.getDate() + 1)
  } while (d.getDay() === 0 || d.getDay() === 6)
  return d
}

/**
 * @param {string} ticker
 * @param {Array} ohlc baris OHLC asli — dipakai hanya untuk titik berangkatnya
 * @param {number} horizon jumlah hari bursa ke depan
 */
export function buatForecastPlaceholder(ticker, ohlc = [], horizon = 7) {
  const terakhir = ohlc.length ? ohlc[ohlc.length - 1] : null
  const hargaAwal = Number(terakhir?.close)
  if (!terakhir || Number.isNaN(hargaAwal) || hargaAwal <= 0) return null

  const seed = seedDari(ticker)
  // Arah ditentukan huruf ticker-nya, bukan data — sekali lagi: ini bukan sinyal.
  const arah = seed % 2 === 0 ? 1 : -1
  const driftHarian = arah * (0.0015 + (seed % 5) * 0.0004)

  let tanggal = new Date(String(terakhir.tanggal).slice(0, 10))
  let harga = hargaAwal
  const points = []

  for (let i = 1; i <= horizon; i++) {
    tanggal = hariBursaBerikutnya(tanggal)

    // Ombak kecil supaya garisnya tidak lurus sempurna dan jelas bukan data asli.
    const ombak = Math.sin((seed + i) * 1.7) * 0.002
    harga = harga * (1 + driftHarian + ombak)

    // Ketidakpastian melebar makin jauh ke depan — itu satu-satunya sifat
    // "forecast" yang sengaja ditiru di sini.
    const lebar = harga * 0.012 * Math.sqrt(i)

    points.push({
      tanggal: tanggal.toISOString().slice(0, 10),
      prediksi: Math.round(harga),
      lower: Math.round(harga - lebar),
      upper: Math.round(harga + lebar),
    })
  }

  return {
    symbol: ticker,
    model: 'Placeholder',
    horizon,
    confidence: null,
    trend: null,
    points,
  }
}
