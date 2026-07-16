#!/bin/bash
# Pastikan Anda telah membuka SSH tunnel di terminal lain sebelum menjalankan ini:
# ssh -L 9000:localhost:9000 bintang@<GCP_VM_IP>

echo "Mulai pemindaian kode lokal..."

# Pastikan file .env dibaca jika ada token di dalamnya
if [ -f .env ]; then
  export $(cat .env | grep -v '#' | xargs)
fi

# Token SonarQube diambil dari argument atau dari env variable SONAR_TOKEN
TOKEN=${1:-$SONAR_TOKEN}

if [ -z "$TOKEN" ]; then
  echo "Error: Token SonarQube tidak ditemukan!"
  echo "Gunakan: ./run-sonar-local.sh <SONAR_TOKEN>"
  exit 1
fi

docker run --rm \
  -v "$(pwd):/usr/src" \
  sonarsource/sonar-scanner-cli \
  -Dsonar.host.url="http://host.docker.internal:9000" \
  -Dsonar.token="$TOKEN"

echo "Pemindaian selesai. Silakan periksa di http://localhost:9000"
