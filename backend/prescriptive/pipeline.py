import logging
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv, find_dotenv

from prescriptive.data_loader import (
    load_ohlc, load_broker_activity, load_insider_activity,
    load_fundamental, load_company_info, load_forecast_data
)
from prescriptive.features import (
    process_additional_features, generate_technical_features, generate_decision_scores
)
from prescriptive.db_writer import save_results, ensure_table_exists

load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)


def _get_engine():
    """Membuat SQLAlchemy engine menggunakan env vars StockVision."""
    db_url = (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(db_url)


def run_prescriptive_pipeline():
    """
    Menjalankan pipeline prescriptive secara end-to-end:
    1. Menarik data dari PostgreSQL (OHLC, broker, insider, fundamental, company info, forecast)
    2. Menghitung fitur teknikal (SMA, EMA, RSI, MACD)
    3. Menghitung skor gabungan tekno-fundamental (maks 100 poin)
    4. Menyimpan hasil rekomendasi ke tabel idxsaham.prescriptive_results
    
    Returns:
        dict: Ringkasan hasil pipeline (jumlah record, daftar rekomendasi)
    """
    logger.info("=== MEMULAI PIPELINE PRESCRIPTIVE ===")

    # Pastikan tabel output sudah ada
    ensure_table_exists()

    # Buat koneksi SQLAlchemy
    engine = _get_engine()

    # 1. Menarik Seluruh Data dari Database
    logger.info("Langkah 1/4: Menarik data dari database...")
    ohlc_df = load_ohlc(engine)
    broker_df = load_broker_activity(engine)
    insider_df = load_insider_activity(engine)
    fund_df = load_fundamental(engine)
    info_df = load_company_info(engine)
    forecast_df = load_forecast_data(engine)  # Dari tabel stock_forecasting, bukan CSV

    # 2. Proses Fitur Teknikal dan Aktivitas Broker/Insider
    logger.info("Langkah 2/4: Menghitung fitur teknikal & aktivitas pasar...")
    broker_score, insider_score = process_additional_features(broker_df, insider_df)
    feature_df = generate_technical_features(ohlc_df)

    # 3. Hitung Skor Gabungan (Teknikal + Fundamental + Prediksi ML)
    logger.info("Langkah 3/4: Menghitung skor keputusan...")
    score_df = generate_decision_scores(
        feature_df, forecast_df, broker_score, insider_score, fund_df, info_df
    )

    # 4. Simpan Hasil ke Database
    logger.info("Langkah 4/4: Menyimpan hasil ke database...")
    saved_count = save_results(score_df)

    # Siapkan ringkasan hasil
    results_summary = []
    display_cols = ["symbol", "sector", "TOTAL_SCORE", "RECOMMENDATION", "expected_return", "current_close"]
    
    for _, row in score_df.iterrows():
        results_summary.append({
            "symbol": row.get("symbol"),
            "company_name": row.get("company_name"),
            "sector": row.get("sector"),
            "total_score": int(row.get("TOTAL_SCORE", 0)),
            "recommendation": row.get("RECOMMENDATION"),
            "insight_summary": row.get("insight_summary"),
            "llm_summary": row.get("llm_summary"),
            "new_buyer_strategy": {
                "recommendation": row.get("rec_new_buyer"),
                "reason": row.get("reason_buyer"),
                "ideal_entry_price": float(row.get("entry_price", 0)),
            },
            "holding_strategy": {
                "recommendation": row.get("rec_holding"),
                "reason": row.get("reason_holding"),
            },
            "trade_setup": {
                "current_close": float(row.get("current_close", 0)),
                "entry_price": float(row.get("entry_price", 0)),
                "support_price": float(row.get("support_price", 0)),
                "resistance_price": float(row.get("resistance_price", 0)),
                "target_price": float(row.get("target_price", 0)),
                "stop_loss": float(row.get("stop_loss", 0)),
                "risk_reward_ratio": float(row.get("risk_reward_ratio", 0)),
                "expected_return": round(float(row.get("expected_return", 0)), 2),
            },
            "scores": {
                "technical": {
                    "trend": int(row.get("score_trend", 0)),
                    "rsi": int(row.get("score_rsi", 0)),
                    "macd": int(row.get("score_macd", 0)),
                },
                "ml_forecast": int(row.get("score_forecast", 0)),
                "fundamental": {
                    "valuation": int(row.get("score_valuation", 0)),
                    "profitability": int(row.get("score_profitability", 0)),
                    "growth": int(row.get("score_growth", 0)),
                },
            },
            "signals": {
                "trend": row.get("TREND"),
                "rsi": row.get("RSI_SIGNAL"),
                "macd": row.get("MACD_SIGNAL2"),
                "volume": row.get("VOLUME_SIGNAL"),
            }
        })



    logger.info(f"=== PIPELINE SELESAI: {saved_count} emiten diproses ===")

    return {
        "status": "success",
        "message": f"Pipeline prescriptive selesai. {saved_count} emiten diproses dan disimpan ke database.",
        "total_processed": saved_count,
        "results": results_summary
    }
