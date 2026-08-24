"""
Chart Pattern Forecasting Pipeline
==================================
Orkestrasi end-to-end proses pengenalan pola chart, peramalan multi-target Fibonacci,
pengecekan kalender libur bursa, evaluasi akurasi, dan penyimpanan ke database PostgreSQL.
"""

import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Any
import pandas as pd

from .trading_calendar import get_calendar_status
from .database import save_chart_pattern_results, get_available_symbols, init_db
from .pattern_engine.data_loader import load_stock_data, TIMEFRAME_CONFIG
from .pattern_engine.patterns import detect_all_patterns
from .pattern_engine.forecasting import generate_forecast, evaluate_all_pattern_forecasts

logger = logging.getLogger(__name__)


def run_chart_pattern_pipeline(
    symbols: Optional[List[str]] = None,
    timeframes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Menjalankan pipeline deteksi chart pattern dan forecasting untuk list simbol & timeframe.
    Hasilnya disimpan ke tabel PostgreSQL idxsaham.chart_pattern_forecasting.
    """
    init_db()

    if not symbols:
        symbols = get_available_symbols()
        if not symbols:
            symbols = ["BBCA", "BBRI", "TLKM", "ASII", "BMRI"]

    if not timeframes:
        timeframes = ["1d"]

    today_str = date.today().strftime("%Y-%m-%d")
    cal_status = get_calendar_status(date.today())

    all_records = []
    processed_count = 0
    patterns_by_symbol = {}

    for sym in symbols:
        sym_clean = sym.strip().upper()
        patterns_by_symbol[sym_clean] = 0

        for tf in timeframes:
            # Cari konfigurasi timeframe
            window_order = 5
            for tf_k, cfg in TIMEFRAME_CONFIG.items():
                if cfg.get("interval") == tf or cfg.get("timeframe_code") == tf:
                    window_order = cfg.get("window_order", 5)
                    break

            try:
                # 1. Load Data OHLC
                df = load_stock_data(sym_clean, interval=tf, period="1y")
                if df.empty or len(df) < 15:
                    continue

                # 2. Deteksi Semua 50 Pola
                patterns = detect_all_patterns(df, window_order=window_order)
                if not patterns:
                    continue

                # 3. Evaluasi Akurasi Historis
                eval_metrics = evaluate_all_pattern_forecasts(df, patterns, timeframe=tf)

                # 4. Generate Signal & Metrik Peramalan per Pola
                for p in patterns:
                    signal = generate_forecast(df, p, sym_clean, tf)

                    # Siapkan key points & geometry serializable
                    kps = []
                    if p.key_points:
                        for kp in p.key_points:
                            kp_copy = dict(kp)
                            if isinstance(kp_copy.get("date"), (datetime, date, pd.Timestamp)):
                                kp_copy["date"] = str(kp_copy["date"])[:10]
                            kps.append(kp_copy)

                    geom_lines = []
                    if p.geometry_lines:
                        for gl in p.geometry_lines:
                            gl_copy = dict(gl)
                            if isinstance(gl_copy.get("date1"), (datetime, date, pd.Timestamp)):
                                gl_copy["date1"] = str(gl_copy["date1"])[:10]
                            if isinstance(gl_copy.get("date2"), (datetime, date, pd.Timestamp)):
                                gl_copy["date2"] = str(gl_copy["date2"])[:10]
                            geom_lines.append(gl_copy)

                    s_date_str = str(p.start_date)[:10] if p.start_date else None
                    e_date_str = str(p.end_date)[:10] if p.end_date else None
                    b_date_str = str(p.breakout_date)[:10] if p.breakout_date else None
                    t_date_str = signal.forecast_trajectory.get("target_date")

                    rec = {
                        "symbol": sym_clean,
                        "timeframe": tf,
                        "analysis_date": today_str,
                        "pattern_name": p.name,
                        "pattern_type": p.pattern_type,
                        "directional_bias": p.directional_bias,
                        "pattern_status": p.status,
                        "quality_score": p.quality_score,
                        "current_price": signal.current_price,
                        "breakout_level": signal.breakout_level,
                        "target_price": signal.target_price,
                        "stop_loss": signal.stop_loss,
                        "expected_return_pct": signal.expected_return_pct,
                        "potential_risk_pct": signal.potential_risk_pct,
                        "risk_reward_ratio": signal.risk_reward_ratio,
                        "tp1": signal.tp1,
                        "tp2": signal.tp2,
                        "tp3": signal.tp3,
                        "fibo_support": signal.fibo_support,
                        "fibo_resistance": signal.fibo_resistance,
                        "volume_confirmed": bool(p.volume_confirmed),
                        "start_date": s_date_str,
                        "end_date": e_date_str,
                        "breakout_date": b_date_str,
                        "target_date": t_date_str,
                        "is_today_holiday": cal_status.get("is_holiday", False),
                        "holiday_description": cal_status.get("keterangan"),
                        "next_trading_day": cal_status.get("next_trading_day"),
                        "key_points": kps,
                        "geometry_lines": geom_lines,
                        "forecast_trajectory": signal.forecast_trajectory,
                        "rules_checklist": signal.rules_checklist,
                        "detection_reasons": signal.detection_reasons,
                        "statistical_notes": p.statistical_notes,
                        "description": p.description,
                        "evaluation_metrics": eval_metrics
                    }
                    all_records.append(rec)
                    patterns_by_symbol[sym_clean] += 1

                processed_count += 1
            except Exception as e:
                logger.error(f"[ChartPatternPipeline] Error memproses {sym_clean} ({tf}): {e}")

    # 5. Simpan seluruh hasil ke Database PostgreSQL
    saved_count = save_chart_pattern_results(all_records)

    return {
        "status": "success",
        "analysis_date": today_str,
        "calendar_status": cal_status,
        "symbols_processed": processed_count,
        "total_patterns_detected": len(all_records),
        "total_records_saved": saved_count,
        "patterns_by_symbol": patterns_by_symbol
    }
