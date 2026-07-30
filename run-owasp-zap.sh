#!/bin/bash

# Pastikan folder zap-reports ada
mkdir -p zap-reports

TARGET_URL=${1:-"http://localhost:80"}
REPORT_NAME="zap_report_$(date +%Y%m%d_%H%M%S).html"

echo "=========================================="
echo "Memulai OWASP ZAP Baseline Security Scan"
echo "Target: $TARGET_URL"
echo "=========================================="

docker run --rm \
  -v "$(pwd)/zap-reports:/zap/wrk/:rw" \
  --network="host" \
  ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
  -t "$TARGET_URL" \
  -r "$REPORT_NAME"

echo ""
echo "=========================================="
echo "Pemindaian Selesai!"
echo "Laporan keamanan tersimpan di: zap-reports/$REPORT_NAME"
echo "=========================================="
