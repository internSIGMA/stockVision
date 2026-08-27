"""
Forecasting module for chart pattern-based price projections and trade setups.
Generates price targets, Fibonacci extensions/retracements, stop losses,
risk/reward calculations, calendar-aware forward projection paths, and accuracy metrics.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta

from .patterns import DetectedPattern
from .fibonacci import calculate_fibonacci_levels


@dataclass
class PatternSignal:
    pattern: DetectedPattern
    symbol: str
    timeframe: str
    current_price: float
    breakout_level: float
    target_price: float
    stop_loss: float
    expected_return_pct: float
    potential_risk_pct: float
    risk_reward_ratio: float
    bias: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    status_label: str
    rules_checklist: List[Dict] = field(default_factory=list)
    forecast_trajectory: Dict = field(default_factory=dict)
    fibo_data: Dict = field(default_factory=dict)
    tp1: float = 0.0
    tp2: float = 0.0
    tp3: float = 0.0
    fibo_support: Optional[float] = None
    fibo_resistance: Optional[float] = None
    buy_area: Dict = field(default_factory=dict)
    sell_area: Dict = field(default_factory=dict)
    detection_reasons: List[str] = field(default_factory=list)


def generate_detection_reasons(pattern: DetectedPattern) -> List[str]:
    """
    Generate human-readable reasons explaining why a specific pattern was detected.
    """
    reasons = []

    # Key point analysis
    kp_names = [kp['name'] for kp in pattern.key_points] if pattern.key_points else []
    n_points = len(pattern.key_points) if pattern.key_points else 0
    if n_points >= 2:
        reasons.append(
            f"Ditemukan {n_points} titik referensi utama: {', '.join(kp_names)}"
        )

    # Price levels
    if n_points >= 2:
        prices = [kp['price'] for kp in pattern.key_points]
        price_range_pct = ((max(prices) - min(prices)) / (min(prices) + 1e-9)) * 100
        reasons.append(
            f"Rentang harga formasi: {min(prices):,.2f} – {max(prices):,.2f} "
            f"(spread {price_range_pct:.1f}%)"
        )

    # Duration
    if pattern.start_date and pattern.end_date:
        start_str = pattern.start_date.strftime('%d %b %Y') if hasattr(pattern.start_date, 'strftime') else str(pattern.start_date)
        end_str = pattern.end_date.strftime('%d %b %Y') if hasattr(pattern.end_date, 'strftime') else str(pattern.end_date)
        bar_count = pattern.end_index - pattern.start_index
        reasons.append(
            f"Formasi terbentuk dari {start_str} hingga {end_str} ({bar_count} bar)"
        )

    # Breakout level
    reasons.append(f"Level breakout teridentifikasi di harga {pattern.breakout_level:,.2f}")

    # Target price
    if "Bullish" in pattern.directional_bias:
        reasons.append(
            f"Target harga kenaikan (TP): {pattern.target_price:,.2f} — proyeksi naik"
        )
    else:
        reasons.append(
            f"Target penurunan (support bawah): {pattern.target_price:,.2f} — proyeksi koreksi jika breakdown neckline {pattern.breakout_level:,.2f}"
        )

    # Breakout status
    status_map = {
        "PENDING_BREAKOUT": "⏳ Pola terbentuk, menunggu konfirmasi breakout",
        "CONFIRMED_BREAKOUT": "✅ Breakout terkonfirmasi",
        "TARGET_REACHED": "🎯 Target harga sudah tercapai",
        "INVALIDATED": "❌ Pola gagal / tertembus invalidation level",
    }
    reasons.append(f"Status: {status_map.get(pattern.status, pattern.status)}")

    # Volume confirmation
    if pattern.volume_confirmed:
        reasons.append("✅ Volume saat breakout melebihi rata-rata 20-MA (terkonfirmasi)")
    else:
        reasons.append("⚠️ Volume saat breakout belum melampaui rata-rata 20-MA")

    return reasons


def generate_future_trajectory(df: pd.DataFrame, pattern: DetectedPattern, is_bullish: bool, 
                               target_price: float, stop_loss: float, timeframe: str) -> Dict:
    """
    Memproyeksikan lintasan harga masa depan dan batas ketidakpastian (confidence cone)
    dengan menggunakan hari-hari bursa aktif dari database trading_calendar (melewati hari libur & akhir pekan).
    """
    last_date = df.index[-1]
    last_price = float(df['Close'].iloc[-1])
    
    # Tentukan jumlah langkah proyeksi
    if "1h" in timeframe:
        n_steps = 15
        future_dates = [last_date + timedelta(hours=i) for i in range(1, n_steps + 1)]
    elif "1wk" in timeframe:
        n_steps = 10
        future_dates = [last_date + timedelta(weeks=i) for i in range(1, n_steps + 1)]
    elif "1mo" in timeframe:
        n_steps = 8
        future_dates = [last_date + timedelta(days=30 * i) for i in range(1, n_steps + 1)]
    else:  # Daily (1d) - Gunakan database trading_calendar
        n_steps = 15
        try:
            from ..trading_calendar import get_next_trading_days
            trading_dates = get_next_trading_days(last_date, n_days=n_steps)
            future_dates = [pd.to_datetime(d) for d in trading_dates]
        except Exception:
            # Fallback jika query calendar gagal
            future_dates = []
            step_d = pd.to_datetime(last_date).date()
            while len(future_dates) < n_steps:
                step_d += timedelta(days=1)
                if step_d.weekday() < 5:
                    future_dates.append(pd.to_datetime(step_d))
        
    all_dates = [last_date] + future_dates
    
    # Proyeksi linier ke target harga
    pathway = np.linspace(last_price, target_price, len(all_dates))
    
    # Confidence cone berdasarkan ATR
    atr = df['ATR'].iloc[-1] if 'ATR' in df.columns and not pd.isna(df['ATR'].iloc[-1]) else (last_price * 0.02)
    upper_bounds = []
    lower_bounds = []
    
    for i, p in enumerate(pathway):
        cone = atr * np.sqrt(i + 1) * 0.6
        upper_bounds.append(round(float(p + cone), 2))
        lower_bounds.append(round(float(max(0.01, p - cone)), 2))
        
    date_strs = []
    for d in all_dates:
        if isinstance(d, (datetime, pd.Timestamp)):
            date_strs.append(d.strftime('%Y-%m-%d %H:%M') if '1h' in timeframe else d.strftime('%Y-%m-%d'))
        elif isinstance(d, date):
            date_strs.append(d.strftime('%Y-%m-%d'))
        else:
            date_strs.append(str(d)[:10])

    return {
        'dates': date_strs,
        'pathway': [round(float(x), 2) for x in pathway],
        'upper_bound': upper_bounds,
        'lower_bound': lower_bounds,
        'target_date': date_strs[-1] if date_strs else None
    }


def generate_forecast(df: pd.DataFrame, pattern: DetectedPattern, symbol: str, timeframe: str) -> PatternSignal:
    """
    Generate forecasting metrics, rules checklist, Fibonacci multi-targets, and forward trajectory for a given pattern.
    """
    current_price = float(df['Close'].iloc[-1])
    breakout_level = float(pattern.breakout_level)
    target_price = float(pattern.target_price)
    stop_loss = float(pattern.stop_loss)
    
    is_bullish = "Bullish" in pattern.directional_bias
    
    # Ekstraksi swing high dan low untuk kalkulasi Fibonacci
    pattern_prices = [kp['price'] for kp in pattern.key_points] if pattern.key_points else [breakout_level, stop_loss]
    swing_high = max(pattern_prices + [breakout_level, target_price if not is_bullish else stop_loss])
    swing_low = min(pattern_prices + [breakout_level, stop_loss if not is_bullish else target_price])
    
    # Fibonacci Levels
    fibo_data = calculate_fibonacci_levels(
        swing_high=swing_high,
        swing_low=swing_low,
        is_bullish=is_bullish,
        current_price=current_price
    )
    
    tp1 = fibo_data["tp1"]  # 100% Measured Move
    tp2 = fibo_data["tp2"]  # 127.2% Fibo Extension
    tp3 = fibo_data["tp3"]  # 161.8% Fibo Golden Extension
    buy_area = fibo_data.get("buy_area", {})
    sell_area = fibo_data.get("sell_area", {})
    
    # Expected Return & Potential Risk %
    if is_bullish:
        expected_return_pct = ((target_price - current_price) / (current_price + 1e-9)) * 100.0
        potential_risk_pct = ((current_price - stop_loss) / (current_price + 1e-9)) * 100.0
        bias = "BULLISH"
    else:
        expected_return_pct = ((current_price - target_price) / (current_price + 1e-9)) * 100.0
        potential_risk_pct = ((stop_loss - current_price) / (current_price + 1e-9)) * 100.0
        bias = "BEARISH"
        
    expected_return_pct = max(-9999.99, min(99999.99, expected_return_pct))
    potential_risk_pct = max(0.01, min(99999.99, potential_risk_pct))
    risk_reward_ratio = max(0.0, min(99999.99, expected_return_pct / potential_risk_pct)) if potential_risk_pct > 0 else 0.0
    
    # Status label
    if pattern.status == "CONFIRMED_BREAKOUT":
        status_label = "🟢 BREAKOUT AKTIF (TERKONFIRMASI)"
    elif pattern.status == "PENDING_BREAKOUT":
        status_label = "🟡 FORMASI TERBENTUK (MENUNGGU BREAKOUT)"
    elif pattern.status == "TARGET_REACHED":
        status_label = "🎯 TARGET HARGA TERCAPAI"
    else:
        status_label = "🔴 TERTEMBUS / TIDAK VALID"
        
    # Bulkowski Rules Checklist
    checklist = [
        {
            "rule": "Identifikasi Formasi Geometri",
            "description": pattern.description,
            "passed": True
        },
        {
            "rule": "Level Breakout / Trigger",
            "description": f"Konfirmasi penutupan candle di atas/bawah level {breakout_level:,.2f}",
            "passed": pattern.status in ["CONFIRMED_BREAKOUT", "TARGET_REACHED"]
        },
        {
            "rule": "Konfirmasi Volume (Above 20-SMA)",
            "description": "Volume saat breakout melebihi rata-rata 20-MA",
            "passed": bool(pattern.volume_confirmed)
        },
        {
            "rule": "Teknik Pengukuran (Measured Move & Fibo 100%)",
            "description": f"Target harga diproyeksikan pada level {target_price:,.2f}",
            "passed": True
        },
        {
            "rule": "Golden Ratio Fibo (161.8%) Confluence",
            "description": f"Target ekstensi lanjutan TP3 pada level {tp3:,.2f}",
            "passed": tp3 > 0
        },
        {
            "rule": "Manajemen Risiko (Stop Loss & RRR)",
            "description": f"Level proteksi Stop Loss di {stop_loss:,.2f} dengan RRR {risk_reward_ratio:.2f}:1",
            "passed": risk_reward_ratio >= 1.0
        }
    ]
    
    # Lintasan Trajectory Masa Depan (Memanfaatkan kalender bursa)
    forecast_trajectory = generate_future_trajectory(df, pattern, is_bullish, target_price, stop_loss, timeframe)
    
    # Narasi Alasan Deteksi
    detection_reasons = generate_detection_reasons(pattern)

    return PatternSignal(
        pattern=pattern,
        symbol=symbol,
        timeframe=timeframe,
        current_price=round(current_price, 2),
        breakout_level=round(breakout_level, 2),
        target_price=round(target_price, 2),
        stop_loss=round(stop_loss, 2),
        expected_return_pct=round(expected_return_pct, 2),
        potential_risk_pct=round(potential_risk_pct, 2),
        risk_reward_ratio=round(risk_reward_ratio, 2),
        bias=bias,
        status_label=status_label,
        rules_checklist=checklist,
        forecast_trajectory=forecast_trajectory,
        fibo_data=fibo_data,
        tp1=round(tp1, 2),
        tp2=round(tp2, 2),
        tp3=round(tp3, 2),
        fibo_support=round(fibo_data["nearest_support"], 2) if fibo_data.get("nearest_support") is not None else None,
        fibo_resistance=round(fibo_data["nearest_resistance"], 2) if fibo_data.get("nearest_resistance") is not None else None,
        buy_area=buy_area,
        sell_area=sell_area,
        detection_reasons=detection_reasons
    )


def evaluate_all_pattern_forecasts(df: pd.DataFrame, patterns: List[DetectedPattern], timeframe: str) -> Dict[str, Any]:
    """
    Evaluasi akurasi historis peramalan (MAE, RMSE, MAPE, Directional Accuracy, Win Rate)
    pada seluruh pola historis yang terdeteksi dengan rincian per pola.
    """
    if "1h" in timeframe:
        n_steps = 15
    elif "1wk" in timeframe:
        n_steps = 10
    elif "1mo" in timeframe:
        n_steps = 8
    else:  # Daily (1d)
        n_steps = 15

    eval_records = []
    
    for p in patterns:
        if p.end_index >= len(df) - 2:
            continue
            
        horizon_idx = min(len(df), p.end_index + n_steps + 1)
        actual_sub_df = df.iloc[p.end_index : horizon_idx]
        if len(actual_sub_df) < 3:
            continue
            
        actual_close = actual_sub_df['Close'].values
        dates = actual_sub_df.index
        start_price = float(actual_close[0])
        pred_pathway = np.linspace(start_price, p.target_price, len(actual_close))
        
        abs_err = np.abs(actual_close - pred_pathway)
        sq_err = (actual_close - pred_pathway) ** 2
        pct_err = np.abs((actual_close - pred_pathway) / (actual_close + 1e-9)) * 100.0
        
        mae = float(np.mean(abs_err))
        rmse = float(np.sqrt(np.mean(sq_err)))
        mape = float(np.mean(pct_err))
        
        is_bullish = "Bullish" in p.directional_bias
        if is_bullish:
            best_realized = float(actual_sub_df['High'].max())
            dir_correct = bool(actual_close[-1] > start_price or best_realized >= p.breakout_level)
        else:
            best_realized = float(actual_sub_df['Low'].min())
            dir_correct = bool(actual_close[-1] < start_price or best_realized <= p.breakout_level)
            
        target_error = abs(best_realized - p.target_price)
        target_reached = (p.status == "TARGET_REACHED")
        
        start_date_str = p.start_date.strftime('%Y-%m-%d') if hasattr(p.start_date, 'strftime') else str(p.start_date)
        end_date_str = p.end_date.strftime('%Y-%m-%d') if hasattr(p.end_date, 'strftime') else str(p.end_date)
        
        eval_records.append({
            "pattern_id": p.id,
            "pattern_name": p.name,
            "directional_bias": p.directional_bias,
            "pattern_type": p.pattern_type,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "breakout_level": float(p.breakout_level),
            "target_price": float(p.target_price),
            "stop_loss": float(p.stop_loss),
            "status": p.status,
            "best_realized": best_realized,
            "target_error": float(target_error),
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "mape": round(mape, 2),
            "dir_correct": dir_correct,
            "target_reached": target_reached,
            "eval_dates": [d.strftime('%Y-%m-%d %H:%M') if '1h' in timeframe else d.strftime('%Y-%m-%d') for d in dates],
            "actual_close": [round(float(x), 2) for x in actual_close],
            "pred_pathway": [round(float(x), 2) for x in pred_pathway],
            "bars_count": len(actual_close)
        })
        
    if not eval_records:
        return {
            "has_data": False,
            "total_evaluated": 0,
            "avg_mae": 0.0,
            "avg_rmse": 0.0,
            "avg_mape": 0.0,
            "win_rate": 0.0,
            "dir_accuracy": 0.0,
            "eval_records": [],
            "by_pattern": []
        }
        
    df_eval = pd.DataFrame(eval_records)
    avg_mae = round(float(df_eval['mae'].mean()), 2)
    avg_rmse = round(float(df_eval['rmse'].mean()), 2)
    avg_mape = round(float(df_eval['mape'].mean()), 2)
    win_rate = round(float(df_eval['target_reached'].mean() * 100.0), 2)
    dir_accuracy = round(float(df_eval['dir_correct'].mean() * 100.0), 2)
    
    # Aggregated by pattern name
    by_pattern_df = df_eval.groupby('pattern_name').agg(
        total_count=('pattern_id', 'count'),
        avg_mae=('mae', 'mean'),
        avg_rmse=('rmse', 'mean'),
        avg_mape=('mape', 'mean'),
        win_rate=('target_reached', lambda x: round(float(x.mean() * 100.0), 2))
    ).reset_index().sort_values('total_count', ascending=False)
    
    by_pattern_list = by_pattern_df.to_dict(orient='records')
    
    return {
        "has_data": True,
        "total_evaluated": len(eval_records),
        "avg_mae": avg_mae,
        "avg_rmse": avg_rmse,
        "avg_mape": avg_mape,
        "win_rate": win_rate,
        "dir_accuracy": dir_accuracy,
        "eval_records": eval_records,
        "by_pattern": by_pattern_list
    }
