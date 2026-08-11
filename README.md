# StockVision 📈

Dashboard pasar saham Indonesia (IDX) berbasis **Flask API (Backend)** dan **Vue 3 (Frontend)**. Aplikasi ini melakukan crawling data pasar saham IDX (Stockbit) dan menampilkannya sebagai halaman *stream* yang responsif dan interaktif.

---

## 📖 Dokumentasi Terpusat

Seluruh panduan teknis dan operasional telah dirapikan di direktori **[`docs/`](docs/README.md)**:

- 🚀 **[Setup & Development Lokal](docs/development.md)** — Panduan instalasi native, Docker Compose, & basis data.
- 📡 **[Integrasi REST API](docs/api-integration.md)** — Spesifikasi endpoint backend & kontrak data frontend.
- 🛡️ **[Audit Keamanan OWASP ZAP](docs/security.md)** — Pengujian DAST otomatis untuk Frontend & Backend.
- 🔍 **[Analisis Kode SonarQube](docs/sonarqube.md)** — Analisis kualitas kode & SAST dengan SonarCloud.
- 🚀 **[Deployment CI/CD](docs/deployment.md)** — Otomatisasi deployment GitHub Actions ke GCP VM.

---

## 💻 Tech Stack

- **Backend**: Flask 3, psycopg2 (PostgreSQL), SQLite (Watchlist), APScheduler Worker, python-dotenv
- **Frontend**: Vue 3, Vite 6, Pinia, Vue Router, Tailwind CSS v4, shadcn-vue (`reka-ui`), Chart.js, `lightweight-charts`, Lenis
- **Tipografi**: Archivo (Heading/UI) & Spline Sans Mono (Data Angka)

---

## 📈 Emiten Terdukung & Akun Demo

### Emiten (IDX)
`BBCA` · `BBNI` · `BBRI` · `BMRI` · `BJBR`

### Akun Demo (Disemai otomatis di database)
| Email | Password | Watchlist Demo |
|---|---|---|
| `admin@sahamscope.id` | `admin123` | BBCA · BMRI (Admin Role) |
| `dewi@sahamscope.id` | `password123` | BBNI · BBCA · BBRI · BMRI |

---

## ⚡ Quick Start (Pengembangan Lokal)

### 1. Konfigurasi `.env`
Buat berkas `.env` di root proyek:
```env
DB_HOST=db_host
DB_PORT=5434
DB_NAME=stockVision
DB_USER=stockvision
DB_PASSWORD=<password>

STOCKBIT_USERNAME=<username>
STOCKBIT_PASSWORD=<password>
STOCKBIT_PLAYER_ID=<player_id>
```

### 2. Jalankan via Docker Compose
```bash
docker compose up -d --build backend frontend
```
- **Backend API**: `http://localhost:8080`
- **Frontend**: `http://localhost:5173` (Vite) / `http://localhost` (Docker)

*(Untuk panduan setup manual tanpa Docker, lihat [docs/development.md](docs/development.md))*

---

## 📁 Struktur Proyek

```text
stockVision/
├── docs/                     # Dokumentasi teknis terpusat
├── backend/                  # Flask REST API & Crawler Engine
│   ├── app.py                # Entrypoint Flask & Crawler Worker
│   ├── data_routes.py        # Endpoint /api/data/* (PostgreSQL)
│   ├── user.py               # User, Watchlist, & Reset Password
│   ├── scheduler.py          # APScheduler Crawling Worker
│   └── db/database.sql       # DDL Skema PostgreSQL
├── frontend/                 # Single-Page Stream Vue 3
│   ├── src/api/              # Axios Client & Kontrak API
│   ├── src/components/       # Charts, Stream Cards, & UI Components
│   └── src/pages/            # Stream Page, Login, & Password Reset
├── .github/workflows/        # CI/CD Workflows (Deploy & OWASP ZAP)
└── docker-compose.yml        # Orchestration Development & Production
```

---

## 📌 Catatan Operasional

1. **Forecasting Endpoint**: Kartu forecasting pada antarmuka frontend saat ini menggunakan data contoh (placeholder) bertanda khusus hingga model ML terintegrasi penuh.
2. **Reset Password (Mode Simulasi)**: Endpoint `send-code` saat ini mengembalikan `simulated: true` dengan `debug_code` untuk kemudahan pengujian tanpa server SMTP aktif.
