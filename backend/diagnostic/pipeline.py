import logging
import time

logger = logging.getLogger(__name__)


def run_diagnostic_pipeline():
    """
    Menjalankan pipeline analisis diagnostik secara end-to-end (tanpa foreign flow data):
    1. Load data dari PostgreSQL (OHLC, Broker, Insider, Fundamental/Meta)
    2. Menjalankan engine analisis kuantitatif (Trend, Bandarmology, Volume Z-Score, Insider)
    3. Menggenerasi narasi AI Root Cause Analysis (Google Gemini 3.5 Flash dengan fallback deterministik)
    4. Menyimpan/update hasil diagnostik ke tabel idxsaham.diagnostic_results
    """
    start_time = time.time()
    logger.info("Starting Diagnostic Pipeline execution...")

    try:
        from .data_loader import (
            load_price_data,
            load_broker_activity_data,
            load_insider_activity_data,
            load_company_meta_data
        )
        from .diagnostic_engine import run_full_diagnostic_analysis
        from .db_writer import save_diagnostic_results
    except ImportError:
        from data_loader import (
            load_price_data,
            load_broker_activity_data,
            load_insider_activity_data,
            load_company_meta_data
        )
        from diagnostic_engine import run_full_diagnostic_analysis
        from db_writer import save_diagnostic_results

    price_df = load_price_data()
    broker_df = load_broker_activity_data()
    insider_df = load_insider_activity_data()
    meta_df = load_company_meta_data()

    if price_df.empty:
        logger.warning("Data OHLC kosong. Pipeline diagnostik dihentikan.")
        return {
            "status": "warning",
            "message": "Data OHLC kosong",
            "processed_count": 0,
            "elapsed_seconds": round(time.time() - start_time, 2)
        }

    diag_df = run_full_diagnostic_analysis(price_df, broker_df, insider_df, meta_df)
    saved_count = save_diagnostic_results(diag_df)

    elapsed = round(time.time() - start_time, 2)
    logger.info(f"Diagnostic Pipeline completed successfully: {saved_count} records updated in {elapsed}s")

    return {
        "status": "success",
        "message": f"Berhasil menganalisis dan menyimpan {saved_count} emiten",
        "processed_count": saved_count,
        "elapsed_seconds": elapsed
    }
