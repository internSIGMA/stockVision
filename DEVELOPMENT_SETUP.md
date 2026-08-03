# Panduan Setup Pengembangan Lokal (Development Guide) - StockVision

Dokumen ini berisi panduan resmi bagi anggota tim untuk menjalankan aplikasi **StockVision** di komputer/laptop lokal menggunakan **Docker Compose**, sambil terhubung secara langsung ke **Shared Database PostgreSQL** yang berada di Server (`10.1.8.108`).

---

## 🎯 Ringkasan Arsitektur Development

```
+-------------------------------------------------------------+
|                     LAPTOP LOKAL (DEV)                      |
|                                                             |
|   +-----------------------+     +-----------------------+   |
|   |  Frontend (Vue 3)     |     |  Backend (Flask API)  |   |
|   |  http://localhost:80  | --> | http://localhost:8080 |   |
|   +-----------------------+     +-----------+-----------+   |
+---------------------------------------------|---------------+
                                              |
                          (Koneksi Database)  | (Port 5434)
                                              v
+-------------------------------------------------------------+
|                    REMOTE SERVER (10.1.8.108)               |
|                                                             |
|   +-----------------------------------------------------+   |
|   |             PostgreSQL (stockvision_db)             |   |
|   |             Database: stockVision                   |   |
|   +-----------------------------------------------------+   |
+-------------------------------------------------------------+
```

Dengan arsitektur ini:
* **Pengembangan Cepat**: Perubahan kode Flask (Backend) & Vue 3 (Frontend) di laptop Anda akan langsung *Hot-Reload* secara otomatis.
* **Data Terpusat**: Seluruh anggota tim membaca dan menulis data ke database yang sama di server `10.1.8.108`.

---

## 📋 Prasyarat Lengkap

Sebelum memulai, pastikan perangkat lokal Anda telah terpasang:
1. **Git**: Untuk mengklon repositori proyek.
2. **Docker & Docker Compose**: Untuk menjalankan layanan secara terisolasi.
3. **Koneksi Jaringan**: Terhubung ke jaringan LAN/VPN tempat server `10.1.8.108` berada.

---

## 🚀 Langkah Demi Langkah Setup Lokal

### 1. Klon Repositori Proyek
Buka terminal di laptop Anda dan klon repositori:
```bash
git clone https://github.com/SIGMA-StockVision/stockVision.git
cd stockVision
git checkout main_dply
```

---

### 2. Buat Berkas `.env` Lokal
Buat berkas `.env` di direktori utama proyek (`/stockVision/.env`):

```bash
cat << 'EOF' > .env
# ============================================================
# DATABASE CONFIGURATION (Menunjuk ke Server Shared DB 10.1.8.108)
# ============================================================
DB_HOST=10.1.8.108
DB_PORT=5434
DB_NAME=stockVision
DB_USER=stockvision
DB_PASSWORD=stockvision_pass

# ============================================================
# STOCKBIT & CREDENTIALS
# ============================================================
STOCKBIT_USERNAME=winssss
STOCKBIT_PASSWORD=Sigma#2026
STOCKBIT_PLAYER_ID=zmFLRX6p-zWkZ-HQr1-HNFjg5TaMDir
STOCKBIT_ACCESS_TOKEN=eyJhbGciOiJSUzI1NiIsImtpZCI6ImExNWQ5OGE2LTdkYzgtNDM3NS05NDk0LTEyOWJlM2RlODVkNCIsInR5cCI6IkpXVCJ9...

# ============================================================
# SMTP CONFIGURATION
# ============================================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=sigmaadmin2026@gmail.com
SMTP_PASSWORD=Sigmaaa#2026
SMTP_FROM=sigmaadmin2026@gmail.com
EOF
```

---

### 3. Jalankan Kontainer Backend & Frontend
Jalankan kontainer `backend` dan `frontend` di laptop Anda (**tidak perlu memicu kontainer DB lokal**):

```bash
docker compose up -d --build backend frontend
```

---

### 4. Verifikasi Layanan di Laptop Lokal

1. **Cek Status Kontainer**:
   ```bash
   docker compose ps
   ```
   * `stockvision_backend`: Status `Up` (Port 8080)
   * `stockvision_frontend`: Status `Up` (Port 80 atau 5173)

2. **Cek Koneksi Backend ke Server DB**:
   ```bash
   curl -i http://localhost:8080/health
   ```
   *(Harus mengembalikan HTTP 200 OK)*

3. **Uji Query Data Saham Real dari Server DB**:
   ```bash
   curl -i "http://localhost:8080/api/data/stock-info?symbol=BBCA"
   ```

4. **Buka Aplikasi di Browser**:
   * Akses Frontend: **`http://localhost`**

---

## 🗄️ Akses Database via Aplikasi GUI (DBeaver / TablePlus / DataGrip)

Jika Anda ingin melihat atau mengelola tabel database secara langsung dari laptop:

| Parameter | Nilai / Value |
| :--- | :--- |
| **Host / IP** | `10.1.8.108` |
| **Port** | `5434` |
| **Database** | `stockVision` |
| **User** | `stockvision` |
| **Password** | `stockvision_pass` |

---

## 🛠️ Troubleshooting (Kendala Sering Terjadi)

### 1. `Connection timed out` saat Akses Database Server
* **Penyebab**: Laptop Anda belum terhubung ke jaringan LAN/VPN server, atau IP server berubah.
* **Solusi**: 
  - Pastikan `ping 10.1.8.108` mengembalikan balasan (reply).
  - Pastikan port `5434` terbuka di firewall server.

### 2. `Connection refused` di Port 8080 saat Pertama Kali Dinyalakan
* **Penyebab**: Backend sedang menjalankan inisialisasi awal kalender bursa (`python db/trading_date.py`).
* **Solusi**: Tunggu 10–15 detik, periksa log dengan `docker compose logs -f backend`.

---

## 📄 Referensi Berkas Terkait
* **[DOCKER.md](file:///home/bintang/Documents/02_Pekerjaan/Proyek/stockVision/DOCKER.md)**: Panduan lengkap Docker & Deployment Server.
* **[OWASP_ZAP.md](file:///home/bintang/Documents/02_Pekerjaan/Proyek/stockVision/OWASP_ZAP.md)**: Panduan audit keamanan otomatis.
* **[README.md](file:///home/bintang/Documents/02_Pekerjaan/Proyek/stockVision/README.md)**: Ringkasan proyek StockVision.
