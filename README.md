# StockVision 📈

Dashboard pasar saham Indonesia (IDX). Backend **Flask + PostgreSQL** melakukan crawling dan menyediakan API; frontend **Vue 3 + Vite** menampilkannya sebagai satu halaman *stream* yang panjang.

---

## Tech Stack

**Backend** — Flask 3, psycopg2 (PostgreSQL), SQLite (watchlist), APScheduler-style worker manual, python-dotenv
**Frontend** — Vue 3, Vite 6, Pinia, Vue Router, Tailwind CSS v4, shadcn-vue (reka-ui), Chart.js, lightweight-charts, Lenis, vue-sonner

Font: **Archivo** (heading/UI) dan **Spline Sans Mono** (semua angka & data tabular).

---

## Prasyarat

- **Python 3.11+**
- **Node.js 20+**
- Akses ke database PostgreSQL StockVision (kredensial ada di `.env`, lihat di bawah)

---

## Setup

### 1. Konfigurasi environment

Buat file `.env` di root proyek (file ini **tidak** ikut di-commit — lihat `.gitignore`):

```env
# Database
DB_HOST=<host-postgres>
DB_PORT=5432
DB_NAME=stockVision
DB_USER=<user>
DB_PASSWORD=<password>

# Kredensial Stockbit (untuk crawler)
STOCKBIT_USERNAME=<username>
STOCKBIT_PASSWORD=<password>
STOCKBIT_PLAYER_ID=<player-id>
```

### 2. Backend (port 8080)

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

pip install -r backend/requirements.txt

cd backend
python app.py
```

Backend jalan di `http://localhost:8080`. Saat start pertama, tabel `idxsaham.users` dibuat otomatis lengkap dengan akun demo.

### 3. Frontend (port 5173)

```bash
cd frontend
npm install
npm run dev
```

Frontend jalan di `http://localhost:5173` dan menembak backend lewat `VITE_API_URL` (lihat `frontend/.env`, default `http://localhost:8080`).

Build produksi: `npm run build`.

---

## Akun demo

Disemai otomatis oleh backend ke tabel `idxsaham.users`:

| Email | Password | Watchlist |
|---|---|---|
| `fariz@sahamscope.id` | `password123` | BBCA · BMRI |
| `dewi@sahamscope.id` | `password123` | BBNI · BBCA · BBRI · BMRI |

---

## Emiten yang didukung

Backend **menolak emiten di luar daftar ini dengan HTTP 400**:

```
BBCA · BBNI · BBRI · BMRI · BJBR
```

---

## Struktur proyek

```text
stockVision/
├── .env                      # kredensial — TIDAK di-commit
├── backend/
│   ├── app.py                # entrypoint Flask + worker crawler
│   ├── data_routes.py        # /api/data/* — baca dari PostgreSQL
│   ├── user.py               # user, watchlist, login, reset password
│   ├── scheduler.py          # penjadwal crawling otomatis
│   ├── db/database.sql       # skema DDL
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── api/              # kontrak API (StockVision.js) + instance axios
    │   ├── components/
    │   │   ├── charts/       # CandlestickChart, ForeignFlowChart, ForecastChart
    │   │   ├── stream/       # kartu-kartu penyusun halaman Stream
    │   │   └── ui/           # shadcn-vue + StatCard, EmptyState, StatusPill
    │   ├── composables/      # useEmitenData, useForecastData, useAuthReset, …
    │   ├── pages/            # StreamPage, LoginPage, ForgotPasswordPage, …
    │   ├── stores/           # Pinia: auth, market
    │   └── utils/            # format, technicalIndicators, export
    └── vite.config.js
```

---

## API

### Data pasar (baca dari PostgreSQL)

| Endpoint | Keterangan |
|---|---|
| `GET /api/data/stock-info?symbol=` | Snapshot harga terakhir |
| `GET /api/data/ohlc?symbol=` | Histori OHLC + foreign flow (urut tanggal ASC) |
| `GET /api/data/majorholder?symbol=` | Transaksi insider |
| `GET /api/data/broker-activity?symbol=` | Aktivitas broker |

### Crawl (menembak Stockbit, lalu simpan ke DB)

`GET /stock-info` · `GET /ohlc` · `GET /majorholder` · `GET /broker-activity` · `GET /crawl-status`

> Endpoint crawl memakai **GET**, bukan POST, dan bisa memakan waktu lama.

### Scheduler

`GET /scheduler/status` · `POST /scheduler/{start,stop,pause,resume,trigger}`

### User & watchlist

| Endpoint | Keterangan |
|---|---|
| `POST /users/login` | `{ email, password }` |
| `GET /users/{id}/watchlists` | Daftar watchlist |
| `POST /users/{id}/watchlists` | Buat watchlist |
| `PUT /users/{id}/watchlists/{wid}` | Ubah watchlist |
| `PUT /users/{id}` | Ubah user (mis. `default_ticker`) |

### Reset password

Alur tiga langkah, kode berlaku **5 menit**:

| Endpoint | Payload | Balasan |
|---|---|---|
| `POST /users/reset-password/send-code` | `{ email }` | `{ message, simulated, debug_code? }` |
| `POST /users/reset-password/verify-code` | `{ email, code }` | `{ message, token }` |
| `POST /users/reset-password/reset` | `{ token, password }` | `{ message }` |

Kode verifikasi = **6 karakter alfanumerik huruf besar**. Password baru minimal **6 karakter**.

---

## Fitur frontend

- **Stream** — satu halaman scroll: trending, watchlist, statistik harga, candlestick, forecasting, foreign flow, ringkasan teknikal, insider, dan histori.
- **Crawl Logs** — riwayat eksekusi crawler.
- **Auto Scheduler** — kendali penjadwal crawling.
- **Login + Reset Password** — alur 3 langkah (email → kode → password baru).
- **Dark mode** dan **smooth scroll** (Lenis, otomatis nonaktif bila pengguna meminta *reduced motion*).

---

## Catatan & keterbatasan

Dua hal yang perlu diketahui sebelum menilai tampilan aplikasi:

**1. Endpoint forecasting belum ada.** Backend belum menyediakan `/api/data/forecast`. Selama itu 404, kartu *Forecasting* di Stream menampilkan **data placeholder** — ditandai jelas dengan banner *"Data contoh"*, dan kolom Model berbunyi `Placeholder`. Angka-angkanya **bukan proyeksi sungguhan** dan tidak boleh dipakai sebagai dasar keputusan. Titik sambungnya ada di `frontend/src/composables/useForecastData.js`; begitu backend siap, cukup arahkan `getForecast()` ke path yang benar.

**2. SMTP belum dikonfigurasi.** Endpoint `send-code` membalas `simulated: true` dan menitipkan kodenya lewat `debug_code`, supaya alur reset password tetap bisa diuji tanpa email sungguhan. Halaman reset menampilkan kode itu di banner *"Mode simulasi"*. Banner tersebut hilang sendiri begitu SMTP aktif.

Kode reset disimpan **di memori proses Flask**, jadi me-restart backend akan membatalkan semua kode yang sedang beredar.
