# Panduan Audit Keamanan OWASP ZAP - StockVision

Dokumen ini berisi panduan resmi untuk mengoperasikan pengujian keamanan otomatis (**DAST - Dynamic Application Security Testing**) menggunakan **OWASP ZAP** secara terpisah pada **Frontend** dan **Backend API**.

---

## 1. Pemisahan Target Audit

Pengujian keamanan StockVision dibagi menjadi dua komponen independen:

| Komponen Target | URL / Definisi Target | Mode Scan OWASP ZAP | Kerentanan Utama Yang Diuji |
| :--- | :--- | :--- | :--- |
| **Frontend UI** | `http://localhost:80` atau `http://localhost:5173` | `zap-baseline.py` (Baseline Scan) | Cross-Site Scripting (XSS), Content Security Policy (CSP), Sensitive Information Disclosure di JS bundle. |
| **Backend REST API** | `StockVision.postman_collection.json` | `zap-api-scan.py` (API Scan) | SQL Injection, Authentication Bypass, Broken Object Authorization (BOLA), Rate Limiting, Unhandled Errors. |

---

## 2. Pengujian Keamanan Lokal (Development)

### A. Prasyarat
- Docker Engine & Docker Compose dalam keadaan aktif.
- Seluruh container StockVision menyala (`docker compose up -d`).

### B. Menjalankan Skrip `run-owasp-zap.sh`

Gunakan skrip [`run-owasp-zap.sh`](../run-owasp-zap.sh) di root direktori proyek:

```bash
# 1. Scan Khusus Frontend UI
./run-owasp-zap.sh frontend

# 2. Scan Khusus Backend REST API
./run-owasp-zap.sh backend

# 3. Scan Kedua Komponen (Frontend & Backend)
./run-owasp-zap.sh all
```

Laporan HTML hasil pemindaian akan tersimpan otomatis di direktori `zap-reports/`:
- `zap_frontend_YYYYMMDD_HHMMSS.html`
- `zap_backend_YYYYMMDD_HHMMSS.html`

---

## 3. Otomatisasi GitHub Actions (CI/CD)

Workflow GitHub Actions telah dikonfigurasi di berkas [`.github/workflows/zap_scan.yml`](../.github/workflows/zap_scan.yml).

### A. Pemicu Workflow (Triggers)
1. **Manual Dispatch**: Dapat dipicu kapan saja dari tab **Actions -> OWASP ZAP Security Audit -> Run workflow**.
2. **Jadwal Mingguan (Cron)**: Otomatis berjalan setiap hari Minggu pukul 00:00 UTC.

### B. Hasil & Artifact Audit
Setelah workflow selesai di GitHub Actions:
1. Buka tab **Actions** di repositori GitHub Anda.
2. Pilih eksekusi workflow **OWASP ZAP Security Audit** terbaru.
3. Unduh **Artifacts** bernama `owasp-zap-security-reports` yang berisi berkas laporan HTML audit Frontend dan Backend.
