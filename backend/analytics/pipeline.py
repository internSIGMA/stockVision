import time
import logging
from .data_loader import (
    load_ohlc_data,
    load_broker_activity,
    load_insider_activity,
    load_stock_info
)
from .analytics_engine import (
    run_single_symbol_analytics,
    calculate_composite_market_analytics
)
from .db_writer import save_analytics_results

logger = logging.getLogger(__name__)

SUPPORTED_SYMBOLS = ["BBCA", "BBNI", "BBRI", "BMRI", "BJBR"]

def run_analytics_pipeline(symbols=None):
    """
    Eksekusi pipeline Analytics Processing Layer secara end-to-end:
    1. Memuat data dari database PostgreSQL.
    2. Menghitung indikator teknikal, metrik risiko & performa, bandarmology, dan sentimen insider per emiten.
    3. Menghitung skor ringkasan agregat pasar (Market Breadth & Composite Sentiment).
    4. Menyimpan/memperbarui hasil ke tabel idxsaham.analytics_results.
    """
    start_time = time.time()
    logger.info("========== Starting Analytics Processing Pipeline ==========")

    target_symbols = symbols or SUPPORTED_SYMBOLS

    try:
        ohlc_df = load_ohlc_data()
        broker_df = load_broker_activity()
        insider_df = load_insider_activity()
        stock_info_df = load_stock_info()

        symbol_results = []
        for sym in target_symbols:
            try:
                res = run_single_symbol_analytics(
                    symbol=sym,
                    ohlc_df=ohlc_df,
                    broker_df=broker_df,
                    insider_df=insider_df,
                    stock_info_df=stock_info_df
                )
                symbol_results.append(res)
            except Exception as e:
                logger.error(f"Gagal memproses analitik untuk {sym}: {e}")

        # Compute market-wide composite scores
        market_meta = calculate_composite_market_analytics(symbol_results)

        for res in symbol_results:
            res["market_breadth_score"] = market_meta["market_breadth_score"]
            res["composite_sentiment_score"] = market_meta["composite_sentiment_score"]
            res["composite_sentiment_label"] = market_meta["composite_sentiment_label"]

        saved_count = save_analytics_results(symbol_results)

        elapsed = round(time.time() - start_time, 2)
        logger.info(f"Analytics Pipeline completed successfully: {saved_count} records processed in {elapsed}s")

        return {
            "status": "success",
            "message": f"Berhasil memproses dan menyimpan analitik {saved_count} emiten.",
            "processed_count": saved_count,
            "elapsed_seconds": elapsed,
            "market_summary": market_meta,
            "results": symbol_results
        }
    except Exception as e:
        logger.exception("Terjadi kesalahan pada Analytics Pipeline")
        elapsed = round(time.time() - start_time, 2)
        return {
            "status": "error",
            "message": f"Gagal menjalankan Analytics Pipeline: {str(e)}",
            "processed_count": 0,
            "elapsed_seconds": elapsed
        }

if __name__ == "__main__":
    run_analytics_pipeline()
