# SahamScope — Frontend

Front-end (Vue 3) untuk aplikasi crawling & analisis data saham dari Stockbit.
Fokus emiten: **BBRI, BBCA, BBNI**.

> ⚠️ Ini **frontend saja**. Seluruh data (broker summary, harga harian, insider
> activity, status crawler, forecasting) masih **mock** yang dihasilkan di
> `src/data/market.js`. Backend crawler Python tinggal disambungkan dengan
> mengganti fungsi-fungsi di sana / `src/services/authService.js` menjadi
> pemanggilan API.

## Menjalankan

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # build produksi ke dist/
```

**Login demo:** `analis@sahamscope.id` / `password123`
(atau klik tombol "Isi kredensial demo" di halaman login)

## Fitur

| Halaman | Isi |
|---|---|
| **Login** | Validasi field, format email, kredensial salah + sisa percobaan, lockout, simulasi error jaringan, state loading |
| **Dashboard** | Ringkasan 3 emiten pantauan, statistik crawler, candlestick, top net buyer, insider terbaru, status job |
| **Broker Summary** | Net lot per broker, top buyer/seller, net flow (bandarmology) |
| **Harga Emiten** | Candlestick OHLC + MA20/MA50, volume, filter periode |
| **Insider / Backdoor** | Tabel transaksi orang dalam, filter beli/jual, deteksi net distribusi |
| **Technical Analysis** | 4 tab: Descriptive, Diagnostic (RSI + sinyal), Predictive (forecast band), Prescriptive (rekomendasi + target/stop) |
| **Forecasting** | Proyeksi harga + confidence band, pilihan horizon |
| **Crawling Monitor** | Status job real-time, progress bar, retry, run-all |
| **Watchlist Crawler** | CRUD emiten yang di-crawl (sumber data, interval, aktif/nonaktif) — persist ke localStorage |

## Struktur

```
src/
  views/         Halaman (Login, Dashboard, Broker, Prices, Insider, Technical, Forecasting, Crawling, Watchlist)
  layout/        AppLayout + Sidebar + Topbar (chrome bersama)
  components/
    ui/          StatCard
    charts/      CandleChart, AreaChart, BarChart (wrapper ApexCharts) + chartTheme
  stores/        auth.js, market.js (Pinia)
  services/      authService.js (mock auth: error, lockout, network)
  data/          market.js (generator data mock — TITIK SAMBUNG API)
  utils/         format.js (rupiah, angka, persen, timeAgo)
  router/        route + auth guard
```

## Menyambung ke backend nanti

- **Auth:** ganti `login()` di `src/services/authService.js` dengan `fetch`/axios ke endpoint login.
- **Data pasar:** ganti fungsi di `src/data/market.js` (`generateOHLC`, `brokerSummary`,
  `insiderActivity`, `seedCrawlJobs`, `forecast`) agar memanggil API crawler.
  Bentuk return sudah didokumentasikan lewat penggunaannya di komponen.
