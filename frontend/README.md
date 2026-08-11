# StockVision — Frontend 📈

Antarmuka pengguna (Frontend) untuk aplikasi dashboard analisis & crawling data saham pasar Indonesia (IDX).

Aplikasi dibangun sebagai **halaman stream tunggal (single-page stream)** yang responsif dengan fitur visualisasi grafik interaktif, pemantauan aliran dana asing, analisis teknikal, serta manajemen akun & watchlist.

---

## 🚀 Prasyarat & Cara Menjalankan

### Prasyarat
- **Node.js 20+**
- **npm** (atau pnpm/yarn)

### Menjalankan Dev Server
```bash
cd frontend
npm install
npm run dev
```
Dev server akan berjalan di `http://localhost:5173`. Frontend terhubung ke backend Flask via `VITE_API_URL` (default: `http://localhost:8080`).

### Build Produksi
```bash
npm run build
```
Hasil build tersimpan di direktori `dist/`.

---

## 🛠️ Tech Stack Frontend

- **Framework**: Vue 3 (Composition API) + Vite 6
- **State Management**: Pinia
- **Routing**: Vue Router
- **Styling**: Tailwind CSS v4 + shadcn-vue (`reka-ui`) + Lucide Icons
- **Grafik & Visualisasi**: Chart.js + `lightweight-charts`
- **UX & Animasi**: Lenis Smooth Scroll + `vue-sonner` (Toast Notifications)
- **Tipografi**: **Archivo** (Heading/UI) & **Spline Sans Mono** (Angka & Data Tabular)

---

## 📈 Emiten Terdukung

Sistem backend dan frontend secara resmi mendukung 5 emiten utama IDX:
`BBCA` · `BBNI` · `BBRI` · `BMRI` · `BJBR`

---

## 🔑 Akun Demo

Backend menyediakan akun demo secara otomatis:
- `admin@sahamscope.id` / `admin123` (Admin Role, Watchlist: BBCA, BMRI)
- `dewi@sahamscope.id` / `password123` (Watchlist: BBNI, BBCA, BBRI, BMRI)

---

## 📂 Struktur Direktori Frontend

```text
frontend/src/
├── api/              # Klien HTTP Axios & kontrak API (StockVision.js)
├── components/
│   ├── charts/       # CandlestickChart, ForeignFlowChart, ForecastChart
│   ├── stream/       # Komponen kartu penyusun halaman Stream
│   └── ui/           # Komponen UI (shadcn-vue, StatCard, EmptyState, StatusPill)
├── composables/      # Logic composables (useEmitenData, useForecastData, useAuthReset, dll)
├── pages/            # Halaman StreamPage, LoginPage, ForgotPasswordPage, dll
├── stores/           # Store Pinia (auth.js, market.js)
├── utils/            # Helper format angka/rupiah, kalkulasi indikator teknikal, export CSV
└── vite.config.js
```

---

## 🔗 Integrasi Backend API

Seluruh panggilan API dikelola di `src/api/StockVision.js` dan composables. Untuk panduan lengkap spesifikasi endpoint backend, lihat **[Panduan Integrasi REST API](../docs/api-integration.md)**.
