# Panduan Deployment Otomatis (CI/CD) - StockVision

Dokumen ini menjelaskan konfigurasi dan alur kerja (*workflow*) CI/CD menggunakan GitHub Actions untuk melakukan deployment aplikasi **StockVision** secara otomatis ke Virtual Machine (VM) Google Cloud Platform (GCP).

---

## 1. Alur Kerja (Workflow) Deployment

Workflow didefinisikan pada file [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml). Proses deployment akan otomatis terpicu setiap kali terjadi push ke branch **`main_dply`**.

### Tahapan Deployment di VM GCP:
1. **Masuk ke Direktori Proyek**: Berpindah ke folder proyek menggunakan path yang tersimpan di GitHub Secrets.
2. **Pembaruan Kode (Git)**:
   * Mengambil pembaruan dari remote branch `main_dply`.
   * Melakukan reset lokal (`git reset --hard`) agar kode di server sama persis dengan repositori GitHub.
3. **Membangun Ulang & Menjalankan Container (Docker)**:
   * Menghentikan container yang sedang berjalan (`docker compose down`).
   * Membangun ulang (*build*) image (jika ada perubahan Dockerfile/kode) dan menjalankan container baru di latar belakang (`docker compose up -d --build`).
4. **Pembersihan Disk (Pruning)**:
   * Menghapus image lama yang tidak digunakan lagi (`docker image prune -f`) untuk mencegah kepenuhan ruang penyimpanan (*disk space*) di VM.

---

## 2. Konfigurasi GitHub Secrets

Agar GitHub Actions dapat mengakses VM GCP Anda melalui SSH, Anda perlu mendaftarkan kredensial berikut pada menu **Settings -> Secrets and variables -> Actions** di repositori GitHub:

| Nama Secret | Deskripsi | Contoh Nilai |
| :--- | :--- | :--- |
| `GCP_VM_IP` | Alamat IP Publik dari VM GCP Anda. | `xx.xx.xx.xx` |
| `GCP_VM_USER` | Username SSH untuk masuk ke VM. | `xxxxx` |
| `GCP_SSH_KEY` | Private SSH Key yang berpasangan dengan public key di VM (`~/.ssh/authorized_keys`). | `-----BEGIN OPENSSH PRIVATE KEY----- ...` |
| `GCP_PROJECT_PATH` | Path absolut folder proyek tempat repositori berada di VM GCP. | `/home/xxxx` |


