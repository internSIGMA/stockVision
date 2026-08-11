# Panduan Analisis Kualitas Kode & Keamanan - SonarQube / SonarCloud

Dokumen ini menjelaskan konfigurasi dan cara menjalankan analisis kualitas kode serta analisis keamanan statis (**SAST - Static Application Security Testing**) pada proyek **StockVision** menggunakan **SonarQube / SonarCloud**.

---

## 1. Konfigurasi `sonar-project.properties`

Konfigurasi SonarQube didefinisikan pada berkas [`sonar-project.properties`](../sonar-project.properties) di root direktori proyek:

```properties
# Metadata Proyek SonarCloud
sonar.organization=internsigma
sonar.projectKey=internSIGMA_stockVision
sonar.projectName=StockVision
sonar.projectVersion=1.0.0

# Alamat Server SonarCloud
sonar.host.url=https://sonarcloud.io

# Jalur Sumber Kode Yang Dianalisis
sonar.sources=backend,frontend/src

# Berkas Yang Dikecualikan Dari Analisis
sonar.exclusions=**/node_modules/**,**/venv/**,**/tests/**,**/*.spec.js,backend/db/database.sql,frontend/dist/**

# Konfigurasi Encoding & Bahasa
sonar.sourceEncoding=UTF-8
sonar.python.version=3.10
sonar.javascript.environments=browser
```

---

## 2. Menjalankan Analisis Lokal

Anda dapat melakukan pemindaian kualitas kode secara lokal sebelum melakukan *commit* atau *push*.

### Opsi A: Menggunakan Docker (Rekomendasi - Tanpa Install SonarScanner)

Pastikan Anda telah memiliki `SONAR_TOKEN` dari dashboard SonarCloud/SonarQube Anda:

```bash
docker run --rm \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli \
  -Dsonar.token=<YOUR_SONAR_TOKEN>
```

### Opsi B: Menggunakan SonarScanner CLI Lokal

Jika `sonar-scanner` telah terpasang di sistem operasi Anda:

```bash
sonar-scanner -Dsonar.token=<YOUR_SONAR_TOKEN>
```

---

## 3. Integrasi GitHub Actions (CI/CD Pipeline)

Untuk mengotomatiskan pemindaian SonarCloud pada setiap *Pull Request* atau *Push* ke branch utama, Anda dapat menambahkan workflow GitHub Actions di `.github/workflows/sonar.yml`:

```yaml
name: SonarCloud Code Analysis

on:
  push:
    branches:
      - main
      - main_dply
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  sonarcloud:
    name: SonarCloud Scan
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Mengambil seluruh riwayat Git untuk analisis blame & duplikasi yang akurat

      - name: SonarCloud Scan
        uses: SonarSource/sonarcloud-github-action@v3.1.0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

> **Catatan:** Daftarkan `SONAR_TOKEN` pada menu **Settings -> Secrets and variables -> Actions** di repositori GitHub Anda.

---

## 📊 4. Metrik Yang Diuji SonarQube

- **Bugs & Code Smells**: Mendeteksi kesalahan logika, *bad practice*, serta kode yang sulit dirawat di Python & Vue/JS.
- **Vulnerabilities & Security Hotspots**: Mengidentifikasi potensi celah keamanan statis pada backend & frontend.
- **Code Duplication**: Melacak persentase duplikasi kode di seluruh repositori.
