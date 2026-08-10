# Panduan Setup Pengembangan Lokal (Development Guide)

Dokumen ini berisi panduan untuk menyiapkan dan menjalankan aplikasi **StockVision** di komputer lokal, baik menggunakan **Docker Compose** maupun menjalankan layanan backend & frontend secara langsung (native).

---

## 🎯 Ringkasan Arsitektur Development

Aplikasi dapat dijalankan dengan dua skenario basis data:

1. **Remote Shared Database (Default)**: Terhubung langsung ke Shared Database PostgreSQL di server (`10.1.8.108`).
2. **Local Database**: Menjalankan kontainer PostgreSQL lokal melalui Docker Compose.

```
+-------------------------------------------------------------+
|                     LAPTOP LOKAL (DEV)                      |
|                                                             |
|   +-----------------------+     +-----------------------+   |
|   |  Frontend (Vue 3)     |     |  Backend (Flask API)  |   |
|   |  http://localhost:5173| --> | http://localhost:8080 |   |
|   +-----------------------+     +-----------+-----------+   |
+---------------------------------------------|---------------+
                                              |
                          (Koneksi Database)  | (Port 5434 / 5432)
                                              v
+-------------------------------------------------------------+
|                     POSTGRESQL DATABASE                     |
|                                                             |
|   +-----------------------------------------------------+   |
|   | Remote Server (10.1.8.108) atau Docker DB Lokal     |   |
|   +-----------------------------------------------------+   |
+-------------------------------------------------------------+
```

---

## 📋 Prasyarat Sistem

- **Python 3.11+** (jika running native)
- **Node.js 20+** & **npm** (jika running native)
- **Docker Engine (20.10+)** & **Docker Compose (2.0+)** (jika running via Docker)
- **Koneksi LAN/VPN** (jika menggunakan Shared DB server `10.1.8.108`)

---

## ⚙️ Konfigurasi Environment (`.env`)

Buat berkas `.env` di root direktori proyek (berkas ini diabaikan oleh Git):

```env
# Database Configuration
# - Skenario A (Remote DB Server): DB_HOST=db_host, DB_PORT=5434
# - Skenario B (Docker DB Lokal): DB_HOST=db (di dalam container) atau localhost, DB_PORT=5433 (di luar container)
DB_HOST=db_host
DB_PORT=5434
DB_NAME=stockVision
DB_USER=stockvision
DB_PASSWORD=<password_db>

# Kredensial Stockbit (untuk Crawler API)
STOCKBIT_USERNAME=<username_stockbit>
STOCKBIT_PASSWORD=<password_stockbit>
STOCKBIT_PLAYER_ID=<player_id_stockbit>
```

---

## 🚀 Opsi 1: Menjalankan via Docker Compose (Rekomendasi)

### 1. Jalankan Kontainer Backend & Frontend
Menjalankan backend & frontend terisolasi dengan hot-reload:

```bash
docker compose up -d --build backend frontend
```

> **Catatan:** Jika ingin menggunakan database PostgreSQL lokal via Docker, jalankan tanpa menentukan nama service:
> ```bash
> docker compose up -d --build
> ```
> *Saat container `db` pertama kali dinyalakan, Docker secara otomatis mengeksekusi DDL [`backend/db/database.sql`](../backend/db/database.sql) melalui mounting `/docker-entrypoint-initdb.d/init.sql`.*

### 2. Generasi Kalender Trading (Khusus DB Lokal)
Jika menggunakan DB lokal baru, jalankan seeder kalender bursa IDX:

```bash
# Generasi Kalender Trading IDX (default tahun berjalan / 2026)
docker compose exec backend python db/trading_date.py 2026
```

---

## 💻 Opsi 2: Menjalankan Secara Native (Tanpa Docker)

### 1. Backend (Flask API - Port 8080)
```bash
# Virtualenv setup
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate        # Windows

# Install dependensi
pip install -r backend/requirements.txt

# Jalankan server Flask
cd backend
python app.py
```

### 2. Frontend (Vue 3 / Vite - Port 5173)
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Verifikasi Layanan

1. **Cek Status Health Check Backend**:
   ```bash
   curl -i http://localhost:8080/health
   # Ekspektasi: HTTP 200 OK
   ```

2. **Uji Data Stock Info**:
   ```bash
   curl -i "http://localhost:8080/api/data/stock-info?symbol=BBCA"
   ```

3. **Akses Frontend**:
   Buka peramban di `http://localhost:5173` (Native/Vite) atau `http://localhost` (Docker Nginx jika dikonfigurasi).

---

## 🛠️ Pemeliharaan & Troubleshooting Docker

### Log Monitoring
```bash
# Pantau log seluruh kontainer
docker compose logs -f

# Pantau log spesifik backend
docker compose logs -f backend
```

### Menghentikan Container
```bash
docker compose down
```

### Trouble: `Connection Refused` pada Port 8080 saat awal start
- **Penyebab**: Backend sedang menjalankan inisialisasi awal kalender bursa (`python db/trading_date.py`).
- **Solusi**: Tunggu 10–15 detik, lalu cek kembali log backend (`docker compose logs -f backend`).
