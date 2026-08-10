# Indeks Dokumentasi StockVision 📈

Selamat datang di dokumentasi resmi **StockVision**. Pilih panduan di bawah ini sesuai kebutuhan pengembangan, integrasi, audit, atau deployment aplikasi.

---

## 📚 Daftar Panduan

| Dokumen | Deskripsi | Target Pembaca |
| :--- | :--- | :--- |
| **[Setup & Development](development.md)** | Panduan instalasi lokal, konfigurasi `.env`, penggunaan Docker Compose, serta inisialisasi basis data PostgreSQL & kalender bursa. | Pengembang Backend & Frontend |
| **[Integrasi REST API](api-integration.md)** | Spesifikasi lengkap endpoint REST API backend, autentikasi, crawler, scheduler, serta kontrak data untuk frontend. | Tim Frontend & Integrator API |
| **[Audit Keamanan OWASP ZAP](security.md)** | Panduan pengujian keamanan otomatis DAST untuk Frontend UI & Backend REST API menggunakan OWASP ZAP. | DevOps & Security Tester |
| **[Analisis Kode SonarQube](sonarqube.md)** | Panduan analisis kualitas kode & SAST (Static Application Security Testing) menggunakan SonarQube / SonarCloud. | Pengembang & Security Lead |
| **[Deployment CI/CD](deployment.md)** | Panduan otomatisasi deployment menggunakan GitHub Actions ke Virtual Machine (VM) Google Cloud Platform (GCP). | DevOps & Release Manager |

---

## 🏗️ Ringkasan Arsitektur Proyek

```text
stockVision/
├── backend/                  # Flask REST API + APScheduler Crawler Worker
├── frontend/                 # Vue 3 + Vite + Tailwind CSS v4 + Pinia Single-Page Stream
├── docs/                     # Dokumentasi teknis terpusat
├── .github/workflows/        # CI/CD Deployment & OWASP ZAP Scanning
└── docker-compose.yml        # Konfigurasi container development & produksi
```
