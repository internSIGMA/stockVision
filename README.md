# StockVision - SahamAI 📈

SahamAI adalah bagian dari ekosistem **StockVision**, sebuah backend service berbasis **Flask (Python)** dan database **PostgreSQL** yang dirancang untuk melakukan scraping, pemrosesan data, dan penyediaan API analisis aktivitas broker saham di Bursa Efek Indonesia (IDX).

Aplikasi ini mengintegrasikan data dari Stockbit dan RTI untuk merekam data perdagangan, kalender transaksi, data broker, transaksi insider, dan antrian bid/offer saham harian.

---

## 🛠️ Tech Stack & Prasyarat
Sebelum memulai, pastikan lingkungan pengembangan Anda memiliki:
- **Python 3.10+**
- **PostgreSQL 14+**
- **pip** (Python package installer)
- **Google Chrome** (untuk Selenium pada scripts tertentu)

---

## 📂 Struktur Proyek
```text
stockVision/
├── .gitignore               # Daftar file/folder yang dikecualikan dari Git (env, venv, cache)
├── README.md                # Dokumentasi utama proyek (file ini)
├── SOP_GITHUB.md            # Panduan Standar Operasional Prosedur (SOP) Git & GitHub
├── frontend/                # === APLIKASI FRONTEND (VUE / VITE) ===
│   ├── src/                 # Kode sumber Vue (views, components, stores)
│   ├── public/              # Aset statis frontend
│   ├── package.json         # Dependencies Node.js
│   ├── vite.config.js       # Konfigurasi build Vite
│   └── index.html           # Entrypoint HTML
└── backend/                 # === APLIKASI BACKEND (PYTHON / FLASK) ===
    ├── app.py               # Endpoint API utama Flask & worker
    ├── db/                  # Modul database PostgreSQL
    │   ├── database.sql     # Skema DDL Database
    │   └── trading_date.py  # Script generator kalender trading bursa
    ├── scrapers/            # Script scraper & data gathering
    │   ├── bid_offer.py     # Scraper Bid/Offer saham dari RTI
    │   ├── idx_stock.py     # Script pengolahan & export data IDX ke Excel
    │   └── stock.py         # Script Selenium untuk bypass login cookie Stockbit
    └── utils/               # Helper & logik bantuan
        ├── helo.py          # Script testing sederhana
        └── url              # Daftar URL API referensi
```

---

## 🚀 Setup & Instalasi Lokal

### 1. Kloning Repositori
```bash
git clone https://github.com/internSIGMA/stockVision.git
cd stockVision
```

### 2. Buat Virtual Environment & Aktifkan
Sangat disarankan menggunakan virtual environment agar dependencies tidak bentrok dengan library global sistem Anda.

*   **Windows (PowerShell/CMD):**
    ```powershell
    python -m venv venv
    .\venv\Scripts\activate
    ```
*   **macOS / Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

### 3. Instal Dependencies
Instal semua modul yang diperlukan:
```bash
pip install flask requests psycopg2 pandas openpyxl selenium webdriver-manager beautifulsoup4 python-dotenv
```

### 4. Setup Database PostgreSQL
1. Buat database baru di PostgreSQL Anda (misalnya dengan nama `stockVision`).
2. Jalankan query SQL yang ada di dalam file [database.sql](file:///c:/Project/stockVision/stockVision/SahamAI/SahamAI/database.sql) pada database tersebut untuk membuat schema `idxsaham` beserta table dan index yang diperlukan.

### 5. Konfigurasi Variabel Lingkungan (`.env`)
**⚠️ PERINGATAN KEAMANAN:** Jangan pernah melakukan hardcode password/credentials ke dalam file Python (`app.py` atau `idx_stock.py`). 

Buat file `.env` di dalam folder `SahamAI/SahamAI/` dengan format berikut:
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=stockVision
DB_USER=postgres
DB_PASSWORD=PasswordDatabaseAnda

# Stockbit Credentials
STOCKBIT_USERNAME=UsernameStockbitAnda
STOCKBIT_PASSWORD=PasswordStockbitAnda
STOCKBIT_PLAYER_ID=PlayerIdStockbitAnda
```

Kemudian, di dalam file python, muat variabel tersebut menggunakan `python-dotenv`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": int(os.getenv("DB_PORT", 5432)),
}
```

---

## 🏃 Menjalankan Aplikasi

### 💻 1. Menjalankan Server Flask (Backend)
Aktifkan virtual environment dan jalankan file `app.py` di dalam folder `backend`:

*   **Windows (PowerShell):**
    ```powershell
    .\venv\Scripts\python backend/app.py
    ```
*   **macOS / Linux:**
    ```bash
    ./venv/bin/python backend/app.py
    ```
Secara default, API server akan berjalan di `http://127.0.0.1:8080/`.

### 🖥️ 2. Menjalankan Vue/Vite (Frontend)
Jalankan dev server dari dalam folder `frontend`:
```bash
cd frontend
npm run dev
```
Secara default, frontend akan berjalan di `http://localhost:5173/`.

### 🗄️ 3. Menjalankan Scripts Pendukung (Database / Scrapers)
Jalankan script pendukung menggunakan interpreter virtual environment:
*   **Mengisi Kalender Trading:**
    ```bash
    .\venv\Scripts\python backend/db/trading_date.py
    ```
*   **Mengekstrak Data IDX ke Excel:**
    ```bash
    .\venv\Scripts\python backend/scrapers/idx_stock.py
    ```

---

## 🛡️ Standar Operasional Prosedur (SOP) GitHub
Pastikan Anda membaca dan mematuhi panduan di [SOP_GITHUB.md](file:///c:/Project/stockVision/stockVision/SOP_GITHUB.md) sebelum melakukan commit dan push kode Anda ke GitHub untuk menghindari kebocoran kredensial dan menjaga kualitas kode tim.
