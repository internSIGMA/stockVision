#!/bin/bash

# Pastikan folder zap-reports ada
mkdir -p zap-reports

TARGET_MODE=${1:-"all"}

run_frontend_scan() {
    local report_name="zap_frontend_$(date +%Y%m%d_%H%M%S).html"
    echo "=========================================="
    echo "Memulai OWASP ZAP Scan - Frontend (Port 80)"
    echo "Target: http://localhost:80"
    echo "=========================================="

    docker run --rm \
      -v "$(pwd)/zap-reports:/zap/wrk/:rw" \
      --network="host" \
      ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
      -t "http://localhost:80" \
      -r "$report_name" -m 2 || true

    echo "Laporan Frontend tersimpan di: zap-reports/$report_name"
}

run_backend_scan() {
    local report_name="zap_backend_$(date +%Y%m%d_%H%M%S).html"
    echo "=========================================="
    echo "Memulai OWASP ZAP Baseline Scan - Backend (Port 8080)"
    echo "Target: http://localhost:8080"
    echo "=========================================="

    docker run --rm \
      -v "$(pwd)/zap-reports:/zap/wrk/:rw" \
      --network="host" \
      ghcr.io/zaproxy/zaproxy:stable zap-baseline.py \
      -t "http://localhost:8080" \
      -r "$report_name" -m 2 || true

    echo "Laporan Backend tersimpan di: zap-reports/$report_name"
}

case "$TARGET_MODE" in
    frontend)
        run_frontend_scan
        ;;
    backend)
        run_backend_scan
        ;;
    all)
        run_frontend_scan
        echo ""
        run_backend_scan
        ;;
    *)
        echo "Penggunaan: $0 [frontend|backend|all]"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Pemindaian OWASP ZAP Selesai!"
echo "=========================================="
