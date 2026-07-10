# Panduan Integrasi Docker - StockVision

Dokumen ini berisi panduan resmi untuk mengonfigurasi, menjalankan, dan mengoperasikan ekosistem **StockVision** menggunakan Docker dan Docker Compose dalam mode pengembangan (*development mode*).

---

## 1. Prasyarat Sistem

Sebelum memulai proses instalasi, pastikan sistem Anda telah memenuhi prasyarat berikut:
* Docker Engine (Versi 20.10 atau yang lebih baru)
* Docker Compose (Versi 2.0 atau yang lebih baru)

---

## 2. Prosedur Inisialisasi Layanan

Jalankan perintah berikut pada direktori utama (root) proyek untuk membangun (*build*) image dan menjalankan seluruh container di latar belakang (*detached mode*):

```bash
docker compose up --build -d
```

---

## 3. Alamat Akses Layanan

Setelah seluruh container berhasil dijalankan dan berstatus aktif, layanan dapat diakses melalui protokol HTTP pada alamat berikut:

* **Antarmuka Pengguna (Vite Dev Server)**: [http://localhost:5173](http://localhost:5173) (Port `5173`)
* **Layanan REST API (Flask)**: [http://localhost:8080](http://localhost:8080) (Port `8080`)

---

## 4. Fitur Hot-Reloading

Untuk memfasilitasi proses pengembangan perangkat lunak, direktori lokal `./frontend` telah dipetakan (*bind mount*) ke dalam container. Setiap modifikasi kode sumber yang dilakukan pada direktori `frontend/src` akan secara langsung dideteksi oleh Vite, kemudian memicu pembaruan tampilan (*hot-reload*) pada peramban web secara instan.

---

## 5. Instruksi Operasional Tambahan

Berikut adalah daftar perintah baris (*command line*) untuk pemeliharaan dan pemantauan kontainer:

### Memantau Log Aktivitas Container
```bash
# Menampilkan seluruh log aktivitas container secara real-time
docker compose logs -f

# Menampilkan log aktivitas khusus untuk container frontend
docker compose logs -f frontend
```

### Menghentikan Operasional Container
```bash
# Menghentikan jalannya seluruh container
docker compose down
```

### Membangun Ulang Container Tertentu
Apabila terdapat pembaruan pada berkas konfigurasi (misalnya perubahan pada `Dockerfile`), Anda dapat membangun ulang container tertentu dengan perintah:
```bash
docker compose up --build -d frontend
```
