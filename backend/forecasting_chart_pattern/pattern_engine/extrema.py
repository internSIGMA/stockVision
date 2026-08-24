"""
Extrema detection and geometric utilities for chart pattern recognition.
Detects swing highs (peaks), swing lows (valleys), trendlines, and curve shapes (Adam vs Eve).
Supports pure NumPy execution with seamless SciPy fallback.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional

try:
    from scipy.signal import argrelextrema
    from scipy.stats import linregress
    HAS_SCIPY = True
except Exception:
    HAS_SCIPY = False


def _find_peaks_numpy(arr: np.ndarray, order: int = 5) -> np.ndarray:
    """Deteksi puncak lokal menggunakan pure NumPy tanpa dependensi luar."""
    n = len(arr)
    peaks = []
    for i in range(order, n - order):
        val = arr[i]
        is_peak = True
        for k in range(1, order + 1):
            if val <= arr[i - k] or val < arr[i + k]:
                is_peak = False
                break
        if is_peak:
            peaks.append(i)
    return np.array(peaks, dtype=int)


def _find_valleys_numpy(arr: np.ndarray, order: int = 5) -> np.ndarray:
    """Deteksi lembah lokal menggunakan pure NumPy tanpa dependensi luar."""
    n = len(arr)
    valleys = []
    for i in range(order, n - order):
        val = arr[i]
        is_valley = True
        for k in range(1, order + 1):
            if val >= arr[i - k] or val > arr[i + k]:
                is_valley = False
                break
        if is_valley:
            valleys.append(i)
    return np.array(valleys, dtype=int)


def find_extrema(df: pd.DataFrame, order: int = 5) -> Tuple[List[Dict], List[Dict]]:
    """
    Find local peaks (swing highs) and valleys (swing lows).
    Returns list of dicts with:
    {'index': int, 'date': Timestamp, 'price': float, 'volume': float, 'vol_ratio': float, 'type': str}
    """
    highs = df['High'].values
    lows = df['Low'].values
    dates = df.index
    volumes = df['Volume'].values if 'Volume' in df.columns else np.zeros(len(df))
    vol_ratios = df['Vol_Ratio'].values if 'Vol_Ratio' in df.columns else np.ones(len(df))
    
    # Calculate local maxima and minima indices
    if HAS_SCIPY:
        try:
            peak_idx = argrelextrema(highs, np.greater, order=order)[0]
            valley_idx = argrelextrema(lows, np.less, order=order)[0]
        except Exception:
            peak_idx = _find_peaks_numpy(highs, order=order)
            valley_idx = _find_valleys_numpy(lows, order=order)
    else:
        peak_idx = _find_peaks_numpy(highs, order=order)
        valley_idx = _find_valleys_numpy(lows, order=order)
    
    peaks = []
    for idx in peak_idx:
        peaks.append({
            'index': int(idx),
            'date': dates[idx],
            'price': float(highs[idx]),
            'volume': float(volumes[idx]),
            'vol_ratio': float(vol_ratios[idx]),
            'type': 'PEAK'
        })
        
    valleys = []
    for idx in valley_idx:
        valleys.append({
            'index': int(idx),
            'date': dates[idx],
            'price': float(lows[idx]),
            'volume': float(volumes[idx]),
            'vol_ratio': float(vol_ratios[idx]),
            'type': 'VALLEY'
        })
        
    return peaks, valleys


def fit_trendline(indices: List[int], prices: List[float]) -> Dict:
    """
    Fit a linear trendline using linear regression.
    """
    if len(indices) < 2:
        return {'slope': 0.0, 'intercept': prices[0] if prices else 0.0, 'r_squared': 0.0}
        
    x = np.array(indices, dtype=float)
    y = np.array(prices, dtype=float)
    
    if HAS_SCIPY:
        try:
            reg = linregress(x, y)
            r_sq = float(reg.rvalue ** 2) if not np.isnan(reg.rvalue) else 0.0
            return {
                'slope': float(reg.slope),
                'intercept': float(reg.intercept),
                'r_squared': r_sq
            }
        except Exception:
            pass

    # Pure NumPy implementation
    try:
        slope, intercept = np.polyfit(x, y, 1)
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_sq = float(1 - (ss_res / (ss_tot + 1e-9)))
        return {
            'slope': float(slope),
            'intercept': float(intercept),
            'r_squared': max(0.0, min(1.0, r_sq))
        }
    except Exception:
        return {'slope': 0.0, 'intercept': float(prices[0]), 'r_squared': 0.0}


def determine_prior_trend(df: pd.DataFrame, start_idx: int, lookback: int = 30) -> str:
    """
    Determine if the price prior to start_idx was in an 'UPTREND', 'DOWNTREND', or 'SIDEWAYS'.
    """
    prior_start = max(0, start_idx - lookback)
    if start_idx <= prior_start:
        return 'SIDEWAYS'
        
    prior_df = df.iloc[prior_start:start_idx]
    if len(prior_df) < 5:
        return 'SIDEWAYS'
        
    p_start = prior_df['Close'].iloc[0]
    p_end = prior_df['Close'].iloc[-1]
    pct_change = (p_end - p_start) / (p_start + 1e-9)
    
    if pct_change >= 0.04:
        return 'UPTREND'
    elif pct_change <= -0.04:
        return 'DOWNTREND'
    else:
        return 'SIDEWAYS'


def evaluate_shape_adam_eve(df: pd.DataFrame, center_idx: int, is_peak: bool = False, window: int = 4) -> str:
    """
    Classify a peak/valley as 'Adam' (sharp V-shape) or 'Eve' (wider, rounded shape).
    Bulkowski definition:
    - Adam: narrow, sharp spike, often 1-3 bars wide at the extreme.
    - Eve: wider, rounded bottom/top with multiple bars consolidating near the extreme.
    """
    start_w = max(0, center_idx - window)
    end_w = min(len(df), center_idx + window + 1)
    
    sub_df = df.iloc[start_w:end_w]
    if len(sub_df) < 3:
        return 'Adam'
        
    if is_peak:
        extreme_val = sub_df['High'].max()
        threshold = extreme_val * 0.985  # Within 1.5% of peak
        bars_near_extreme = (sub_df['High'] >= threshold).sum()
    else:
        extreme_val = sub_df['Low'].min()
        threshold = extreme_val * 1.015  # Within 1.5% of bottom
        bars_near_extreme = (sub_df['Low'] <= threshold).sum()
        
    # If 3 or more bars dwell near the extreme => rounded 'Eve', otherwise sharp 'Adam'
    if bars_near_extreme >= 3:
        return 'Eve'
    else:
        return 'Adam'
