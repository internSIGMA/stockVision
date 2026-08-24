"""
Fibonacci Retracement and Extension calculation module.
Computes standard and golden ratio levels for support, resistance, and multi-target forecasting.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd


FIBO_RETRACEMENT_RATIOS = [
    (0.0, "0.0% (Swing End)", "#9E9E9E"),
    (0.236, "23.6% Retracement", "#EF5350"),
    (0.382, "38.2% Retracement", "#FFA726"),
    (0.500, "50.0% Equilibrium", "#FFEE58"),
    (0.618, "61.8% Golden Pocket", "#66BB6A"),
    (0.786, "78.6% Deep Pullback", "#42A5F5"),
    (1.0, "100.0% (Swing Start)", "#AB47BC")
]

FIBO_EXTENSION_RATIOS = [
    (1.000, "100.0% (TP 1 - Measured Move)", "#26A69A"),
    (1.272, "127.2% (TP 2 - Extension)", "#29B6F6"),
    (1.618, "161.8% (TP 3 - Golden Extension)", "#00E676"),
    (2.000, "200.0% (TP 4 - Double Expansion)", "#FFD600"),
    (2.618, "261.8% (TP 5 - Max Expansion)", "#E040FB")
]


def calculate_fibonacci_levels(
    swing_high: float,
    swing_low: float,
    is_bullish: bool = True,
    current_price: Optional[float] = None
) -> Dict:
    """
    Calculate Fibonacci Retracement & Extension levels given swing high and low.
    
    For Bullish continuation/reversal:
    - Retracement is measured from swing_low to swing_high.
    - Extension targets project ABOVE swing_high.
    
    For Bearish continuation/reversal:
    - Retracement is measured from swing_high to swing_low.
    - Extension targets project BELOW swing_low.
    """
    diff = swing_high - swing_low
    if diff <= 0:
        diff = max(1e-5, swing_high * 0.01)
        
    retracements = []
    for ratio, label, color in FIBO_RETRACEMENT_RATIOS:
        if is_bullish:
            level_price = swing_high - (diff * ratio)
        else:
            level_price = swing_low + (diff * ratio)
            
        retracements.append({
            "ratio": ratio,
            "label": label,
            "price": float(level_price),
            "color": color
        })
        
    extensions = []
    for ratio, label, color in FIBO_EXTENSION_RATIOS:
        if is_bullish:
            level_price = swing_low + (diff * ratio)
        else:
            level_price = max(0.01, swing_high - (diff * ratio))
            
        extensions.append({
            "ratio": ratio,
            "label": label,
            "price": float(level_price),
            "color": color
        })
        
    nearest_support = None
    nearest_resistance = None
    
    if current_price is not None:
        all_levels = [r["price"] for r in retracements] + [e["price"] for e in extensions]
        supports = [p for p in all_levels if p < current_price]
        resistances = [p for p in all_levels if p > current_price]
        
        if supports:
            nearest_support = max(supports)
        if resistances:
            nearest_resistance = min(resistances)
            
    return {
        "swing_high": float(swing_high),
        "swing_low": float(swing_low),
        "height": float(diff),
        "is_bullish": is_bullish,
        "retracements": retracements,
        "extensions": extensions,
        "nearest_support": nearest_support,
        "nearest_resistance": nearest_resistance,
        "tp1": extensions[0]["price"],  # 100% Measured Move
        "tp2": extensions[1]["price"],  # 127.2% Fibo Extension
        "tp3": extensions[2]["price"],  # 161.8% Golden Extension
    }


def find_major_trend_swing(df: pd.DataFrame, lookback: int = 100) -> Tuple[float, float, bool]:
    """
    Find major swing high and swing low from lookback window to compute macro Fibonacci levels.
    """
    subset = df.iloc[-lookback:] if len(df) >= lookback else df
    swing_high = float(subset['High'].max())
    swing_low = float(subset['Low'].min())
    
    high_idx = subset['High'].idxmax()
    low_idx = subset['Low'].idxmin()
    
    is_bullish = subset.index.get_loc(low_idx) <= subset.index.get_loc(high_idx)
    
    return swing_high, swing_low, is_bullish
