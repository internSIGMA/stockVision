"""
Comprehensive rule-based pattern detection engine.
Implements the 50 chart patterns from Bulkowski / Big Book of Chart Patterns.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
import numpy as np
import pandas as pd

from .extrema import find_extrema, fit_trendline, determine_prior_trend, evaluate_shape_adam_eve


@dataclass
class DetectedPattern:
    id: int
    name: str
    directional_bias: str  # 'Bullish', 'Bearish', 'Bullish or Bearish', 'Non-Directional'
    pattern_type: str      # 'Reversal', 'Continuation', 'Reversal or Continuation', 'Non-Directional'
    start_index: int
    end_index: int
    start_date: Any
    end_date: Any
    breakout_level: float
    target_price: float
    stop_loss: float
    description: str
    measuring_technique: str
    statistical_notes: str
    key_points: List[Dict] = field(default_factory=list)
    geometry_lines: List[Dict] = field(default_factory=list)
    status: str = "PENDING_BREAKOUT"  # PENDING_BREAKOUT, CONFIRMED_BREAKOUT, TARGET_REACHED, INVALIDATED
    breakout_date: Optional[Any] = None
    breakout_price: Optional[float] = None
    volume_confirmed: bool = False
    quality_score: int = 4  # 1 to 5 stars


def check_breakout_status(df: pd.DataFrame, pattern_end_idx: int, breakout_level: float, 
                          target_price: float, stop_loss: float, is_bullish: bool) -> Tuple[str, Optional[Any], Optional[float], bool]:
    """
    Evaluate price action after pattern completion to assess breakout confirmation and target fulfillment.
    """
    after_df = df.iloc[pattern_end_idx:]
    if len(after_df) <= 1:
        return "PENDING_BREAKOUT", None, None, False
        
    status = "PENDING_BREAKOUT"
    breakout_date = None
    breakout_price = None
    volume_confirmed = False
    
    for i in range(len(after_df)):
        bar = after_df.iloc[i]
        date = after_df.index[i]
        close = bar['Close']
        vol_ratio = bar.get('Vol_Ratio', 1.0)
        
        if is_bullish:
            if status == "PENDING_BREAKOUT":
                if close > breakout_level:
                    status = "CONFIRMED_BREAKOUT"
                    breakout_date = date
                    breakout_price = close
                    volume_confirmed = bool(vol_ratio >= 1.05)
            elif status == "CONFIRMED_BREAKOUT":
                if bar['High'] >= target_price:
                    status = "TARGET_REACHED"
                    break
                elif bar['Low'] <= stop_loss:
                    status = "INVALIDATED"
                    break
        else:  # Bearish
            if status == "PENDING_BREAKOUT":
                if close < breakout_level:
                    status = "CONFIRMED_BREAKOUT"
                    breakout_date = date
                    breakout_price = close
                    volume_confirmed = bool(vol_ratio >= 1.05)
            elif status == "CONFIRMED_BREAKOUT":
                if bar['Low'] <= target_price:
                    status = "TARGET_REACHED"
                    break
                elif bar['High'] >= stop_loss:
                    status = "INVALIDATED"
                    break
                    
    return status, breakout_date, breakout_price, volume_confirmed


# -------------------------------------------------------------------------
# 1. DOUBLE BOTTOMS (#9 Adam & Adam, #10 Adam & Eve, #11 Eve & Eve)
# -------------------------------------------------------------------------
def detect_double_bottoms(df: pd.DataFrame, peaks: List[Dict], valleys: List[Dict]) -> List[DetectedPattern]:
    patterns = []
    if len(valleys) < 2 or len(peaks) < 1:
        return patterns

    for i in range(len(valleys) - 1):
        v1 = valleys[i]
        v2 = valleys[i + 1]
        
        # Check distance between valleys (5 to 60 bars)
        dist = v2['index'] - v1['index']
        if dist < 4 or dist > 65:
            continue
            
        # Check price similarity between two lows (within 3%)
        avg_low = (v1['price'] + v2['price']) / 2.0
        if abs(v1['price'] - v2['price']) / avg_low > 0.035:
            continue
            
        # Find intervening peak between v1 and v2
        inter_peaks = [p for p in peaks if v1['index'] < p['index'] < v2['index']]
        if not inter_peaks:
            continue
        peak = max(inter_peaks, key=lambda x: x['price'])
        
        # Check valley depth relative to peak (at least 3% height)
        height = peak['price'] - min(v1['price'], v2['price'])
        if height / peak['price'] < 0.03:
            continue
            
        # Prior trend check
        prior_trend = determine_prior_trend(df, v1['index'])
        
        # Classify Adam vs Eve
        shape1 = evaluate_shape_adam_eve(df, v1['index'], is_peak=False)
        shape2 = evaluate_shape_adam_eve(df, v2['index'], is_peak=False)
        
        if shape1 == 'Adam' and shape2 == 'Adam':
            pid, name = 9, "Double Bottom (Adam & Adam)"
        elif shape1 == 'Eve' and shape2 == 'Eve':
            pid, name = 11, "Double Bottom (Eve & Eve)"
        else:
            pid, name = 10, f"Double Bottom ({shape1} & {shape2})"
            
        breakout_level = peak['price']
        target_price = breakout_level + height
        stop_loss = min(v1['price'], v2['price']) * 0.99
        
        status, b_date, b_price, vol_conf = check_breakout_status(
            df, v2['index'], breakout_level, target_price, stop_loss, is_bullish=True
        )
        
        patterns.append(DetectedPattern(
            id=pid,
            name=name,
            directional_bias="Bullish",
            pattern_type="Reversal",
            start_index=v1['index'],
            end_index=v2['index'],
            start_date=v1['date'],
            end_date=v2['date'],
            breakout_level=breakout_level,
            target_price=target_price,
            stop_loss=stop_loss,
            description="Pola pembalikan arah bullish dengan dua dasar lembah serupa dan puncak pembatas (neckline).",
            measuring_technique="Ukur jarak antara intervening peak dan dua lembah, lalu tambahkan ke level breakout.",
            statistical_notes="Formasi dengan rentang lebih lebar dan volume tinggi di dasar kiri memiliki performa lebih tinggi.",
            key_points=[
                {'name': f'Bottom 1 ({shape1})', 'index': v1['index'], 'date': v1['date'], 'price': v1['price']},
                {'name': 'Neckline Peak', 'index': peak['index'], 'date': peak['date'], 'price': peak['price']},
                {'name': f'Bottom 2 ({shape2})', 'index': v2['index'], 'date': v2['date'], 'price': v2['price']}
            ],
            geometry_lines=[
                {'x': [v1['date'], df.index[min(len(df)-1, v2['index'] + 15)]], 'y': [breakout_level, breakout_level], 'name': 'Neckline (Breakout)', 'color': '#2962FF', 'style': 'dash'},
                {'x': [v1['date'], v2['date']], 'y': [v1['price'], v2['price']], 'name': 'Support Level', 'color': '#00E676', 'style': 'solid'}
            ],
            status=status,
            breakout_date=b_date,
            breakout_price=b_price,
            volume_confirmed=vol_conf,
            quality_score=4
        ))
    return patterns


# -------------------------------------------------------------------------
# 2. DOUBLE TOPS (#12 Adam & Adam, #13 Adam & Eve, #14 Eve & Eve)
# -------------------------------------------------------------------------
def detect_double_tops(df: pd.DataFrame, peaks: List[Dict], valleys: List[Dict]) -> List[DetectedPattern]:
    patterns = []
    if len(peaks) < 2 or len(valleys) < 1:
        return patterns

    for i in range(len(peaks) - 1):
        p1 = peaks[i]
        p2 = peaks[i + 1]
        
        dist = p2['index'] - p1['index']
        if dist < 4 or dist > 65:
            continue
            
        avg_high = (p1['price'] + p2['price']) / 2.0
        if abs(p1['price'] - p2['price']) / avg_high > 0.035:
            continue
            
        inter_valleys = [v for v in valleys if p1['index'] < v['index'] < p2['index']]
        if not inter_valleys:
            continue
        valley = min(inter_valleys, key=lambda x: x['price'])
        
        height = max(p1['price'], p2['price']) - valley['price']
        if height / valley['price'] < 0.03:
            continue
            
        shape1 = evaluate_shape_adam_eve(df, p1['index'], is_peak=True)
        shape2 = evaluate_shape_adam_eve(df, p2['index'], is_peak=True)
        
        if shape1 == 'Adam' and shape2 == 'Adam':
            pid, name = 12, "Double Tops (Adam & Adam)"
        elif shape1 == 'Eve' and shape2 == 'Eve':
            pid, name = 14, "Double Tops (Eve & Eve)"
        else:
            pid, name = 13, f"Double Tops ({shape1} & {shape2})"
            
        breakout_level = valley['price']
        target_price = max(0.01, breakout_level - height)
        stop_loss = max(p1['price'], p2['price']) * 1.01
        
        status, b_date, b_price, vol_conf = check_breakout_status(
            df, p2['index'], breakout_level, target_price, stop_loss, is_bullish=False
        )
        
        patterns.append(DetectedPattern(
            id=pid,
            name=name,
            directional_bias="Bearish",
            pattern_type="Reversal",
            start_index=p1['index'],
            end_index=p2['index'],
            start_date=p1['date'],
            end_date=p2['date'],
            breakout_level=breakout_level,
            target_price=target_price,
            stop_loss=stop_loss,
            description="Pola pembalikan arah bearish dengan dua puncak serupa dan lembah pembatas (neckline).",
            measuring_technique="Ukur jarak antara puncak dan lembah, lalu kurangkan dari level breakout.",
            statistical_notes="Formasi dengan rentang lebih tinggi dan volume tinggi di puncak kiri cenderung berperforma terbaik.",
            key_points=[
                {'name': f'Top 1 ({shape1})', 'index': p1['index'], 'date': p1['date'], 'price': p1['price']},
                {'name': 'Neckline Valley', 'index': valley['index'], 'date': valley['date'], 'price': valley['price']},
                {'name': f'Top 2 ({shape2})', 'index': p2['index'], 'date': p2['date'], 'price': p2['price']}
            ],
            geometry_lines=[
                {'x': [p1['date'], df.index[min(len(df)-1, p2['index'] + 15)]], 'y': [breakout_level, breakout_level], 'name': 'Neckline (Breakdown)', 'color': '#FF1744', 'style': 'dash'},
                {'x': [p1['date'], p2['date']], 'y': [p1['price'], p2['price']], 'name': 'Resistance Level', 'color': '#FF5252', 'style': 'solid'}
            ],
            status=status,
            breakout_date=b_date,
            breakout_price=b_price,
            volume_confirmed=vol_conf,
            quality_score=4
        ))
    return patterns


# -------------------------------------------------------------------------
# 3. HEAD & SHOULDERS (#22 Inverted, #24 Inverted Continuation, #25 Standard)
# -------------------------------------------------------------------------
def detect_head_and_shoulders(df: pd.DataFrame, peaks: List[Dict], valleys: List[Dict]) -> List[DetectedPattern]:
    patterns = []
    
    # 1. Standard Head & Shoulders (#25)
    if len(peaks) >= 3 and len(valleys) >= 2:
        for i in range(len(peaks) - 2):
            ls = peaks[i]      # Left shoulder
            head = peaks[i+1]  # Head
            rs = peaks[i+2]    # Right shoulder
            
            # Head must be higher than both shoulders
            if not (head['price'] > ls['price'] * 1.015 and head['price'] > rs['price'] * 1.015):
                continue
                
            # Left and right shoulders should be roughly comparable (within 6%)
            if abs(ls['price'] - rs['price']) / ((ls['price'] + rs['price'])/2.0) > 0.07:
                continue
                
            # Intervening valleys (neckline)
            v1_candidates = [v for v in valleys if ls['index'] < v['index'] < head['index']]
            v2_candidates = [v for v in valleys if head['index'] < v['index'] < rs['index']]
            if not v1_candidates or not v2_candidates:
                continue
                
            v1 = min(v1_candidates, key=lambda x: x['price'])
            v2 = min(v2_candidates, key=lambda x: x['price'])
            
            # Fit neckline
            neck_reg = fit_trendline([v1['index'], v2['index']], [v1['price'], v2['price']])
            neckline_at_rs = neck_reg['slope'] * rs['index'] + neck_reg['intercept']
            
            height = head['price'] - ((v1['price'] + v2['price'])/2.0)
            breakout_level = neckline_at_rs
            target_price = max(0.01, breakout_level - height)
            stop_loss = rs['price'] * 1.015
            
            status, b_date, b_price, vol_conf = check_breakout_status(
                df, rs['index'], breakout_level, target_price, stop_loss, is_bullish=False
            )
            
            patterns.append(DetectedPattern(
                id=25,
                name="Head & Shoulders (Standard)",
                directional_bias="Bearish",
                pattern_type="Reversal",
                start_index=ls['index'],
                end_index=rs['index'],
                start_date=ls['date'],
                end_date=rs['date'],
                breakout_level=breakout_level,
                target_price=target_price,
                stop_loss=stop_loss,
                description="Pola pembalikan arah bearish klasik dengan 3 puncak: Left Shoulder, Head (puncak tertinggi), dan Right Shoulder.",
                measuring_technique="Ukur jarak dari puncak Head ke Neckline, lalu kurangkan dari level Neckline saat breakout.",
                statistical_notes="Pola ramping & tinggi serta adanya gap pada hari breakout meningkatkan potensi kesuksesan target.",
                key_points=[
                    {'name': 'Left Shoulder', 'index': ls['index'], 'date': ls['date'], 'price': ls['price']},
                    {'name': 'Neckline V1', 'index': v1['index'], 'date': v1['date'], 'price': v1['price']},
                    {'name': 'Head', 'index': head['index'], 'date': head['date'], 'price': head['price']},
                    {'name': 'Neckline V2', 'index': v2['index'], 'date': v2['date'], 'price': v2['price']},
                    {'name': 'Right Shoulder', 'index': rs['index'], 'date': rs['date'], 'price': rs['price']}
                ],
                geometry_lines=[
                    {'x': [v1['date'], df.index[min(len(df)-1, rs['index'] + 20)]], 
                     'y': [v1['price'], neck_reg['slope'] * min(len(df)-1, rs['index'] + 20) + neck_reg['intercept']], 
                     'name': 'Neckline', 'color': '#FF1744', 'style': 'solid'}
                ],
                status=status,
                breakout_date=b_date,
                breakout_price=b_price,
                volume_confirmed=vol_conf,
                quality_score=5
            ))

    # 2. Inverted Head & Shoulders (#22 & #24)
    if len(valleys) >= 3 and len(peaks) >= 2:
        for i in range(len(valleys) - 2):
            ls = valleys[i]
            head = valleys[i+1]
            rs = valleys[i+2]
            
            if not (head['price'] < ls['price'] * 0.985 and head['price'] < rs['price'] * 0.985):
                continue
                
            if abs(ls['price'] - rs['price']) / ((ls['price'] + rs['price'])/2.0) > 0.07:
                continue
                
            p1_candidates = [p for p in peaks if ls['index'] < p['index'] < head['index']]
            p2_candidates = [p for p in peaks if head['index'] < p['index'] < rs['index']]
            if not p1_candidates or not p2_candidates:
                continue
                
            p1 = max(p1_candidates, key=lambda x: x['price'])
            p2 = max(p2_candidates, key=lambda x: x['price'])
            
            neck_reg = fit_trendline([p1['index'], p2['index']], [p1['price'], p2['price']])
            neckline_at_rs = neck_reg['slope'] * rs['index'] + neck_reg['intercept']
            
            height = ((p1['price'] + p2['price'])/2.0) - head['price']
            breakout_level = neckline_at_rs
            target_price = breakout_level + height
            stop_loss = rs['price'] * 0.985
            
            prior_trend = determine_prior_trend(df, ls['index'])
            is_cont = (prior_trend == 'UPTREND')
            pid = 24 if is_cont else 22
            pname = "Head & Shoulders (Inverted Continuation)" if is_cont else "Head & Shoulders (Inverted)"
            ptype = "Continuation" if is_cont else "Reversal"
            
            status, b_date, b_price, vol_conf = check_breakout_status(
                df, rs['index'], breakout_level, target_price, stop_loss, is_bullish=True
            )
            
            patterns.append(DetectedPattern(
                id=pid,
                name=pname,
                directional_bias="Bullish",
                pattern_type=ptype,
                start_index=ls['index'],
                end_index=rs['index'],
                start_date=ls['date'],
                end_date=rs['date'],
                breakout_level=breakout_level,
                target_price=target_price,
                stop_loss=stop_loss,
                description="Pola dasar bullish dengan 3 lembah: Left Shoulder, Head (lembah terdalam), dan Right Shoulder.",
                measuring_technique="Ukur jarak dari lembah Head ke garis Neckline, lalu tambahkan ke level Neckline saat breakout.",
                statistical_notes="Breakout dengan gap volume tinggi serta neckline miring ke bawah memiliki performa sangat kuat.",
                key_points=[
                    {'name': 'Left Shoulder', 'index': ls['index'], 'date': ls['date'], 'price': ls['price']},
                    {'name': 'Neckline P1', 'index': p1['index'], 'date': p1['date'], 'price': p1['price']},
                    {'name': 'Inverted Head', 'index': head['index'], 'date': head['date'], 'price': head['price']},
                    {'name': 'Neckline P2', 'index': p2['index'], 'date': p2['date'], 'price': p2['price']},
                    {'name': 'Right Shoulder', 'index': rs['index'], 'date': rs['date'], 'price': rs['price']}
                ],
                geometry_lines=[
                    {'x': [p1['date'], df.index[min(len(df)-1, rs['index'] + 20)]], 
                     'y': [p1['price'], neck_reg['slope'] * min(len(df)-1, rs['index'] + 20) + neck_reg['intercept']], 
                     'name': 'Neckline', 'color': '#00E676', 'style': 'solid'}
                ],
                status=status,
                breakout_date=b_date,
                breakout_price=b_price,
                volume_confirmed=vol_conf,
                quality_score=5
            ))
            
    return patterns


# -------------------------------------------------------------------------
# 4. TRIANGLES (#44 Ascending, #45 Descending, #46 Symmetrical)
# -------------------------------------------------------------------------
def detect_triangles(df: pd.DataFrame, peaks: List[Dict], valleys: List[Dict]) -> List[DetectedPattern]:
    patterns = []
    if len(peaks) < 2 or len(valleys) < 2:
        return patterns

    # Sliding window of 2 peaks + 2 valleys
    for i in range(len(peaks) - 1):
        p1, p2 = peaks[i], peaks[i+1]
        matching_valleys = [v for v in valleys if p1['index'] <= v['index'] <= min(len(df)-1, p2['index'] + 15) or (v['index'] >= p1['index'] - 10 and v['index'] <= p2['index'])]
        if len(matching_valleys) < 2:
            continue
            
        v1, v2 = matching_valleys[-2], matching_valleys[-1]
        if v1['index'] >= v2['index']:
            continue
            
        start_idx = min(p1['index'], v1['index'])
        end_idx = max(p2['index'], v2['index'])
        if end_idx - start_idx < 6 or end_idx - start_idx > 80:
            continue
            
        top_reg = fit_trendline([p1['index'], p2['index']], [p1['price'], p2['price']])
        bot_reg = fit_trendline([v1['index'], v2['index']], [v1['price'], v2['price']])
        
        top_slope = top_reg['slope']
        bot_slope = bot_reg['slope']
        
        # Triangles must converge (top slope < bot slope)
        if top_slope >= bot_slope:
            continue
            
        height = p1['price'] - v1['price']
        if height <= 0:
            continue
            
        # Classify triangle type
        # 1. Ascending Triangle (#44): flat top (abs slope < 0.05*ATR), rising bottom (bot_slope > 0)
        atr = df['ATR'].iloc[end_idx] if 'ATR' in df.columns else 1.0
        is_flat_top = abs(p1['price'] - p2['price']) / ((p1['price'] + p2['price'])/2.0) < 0.02
        is_flat_bot = abs(v1['price'] - v2['price']) / ((v1['price'] + v2['price'])/2.0) < 0.02
        
        if is_flat_top and bot_slope > 0:
            pid = 44
            name = "Triangles (Ascending)"
            bias = "Bullish"
            ptype = "Continuation"
            breakout_level = max(p1['price'], p2['price'])
            target_price = breakout_level + height
            stop_loss = v2['price'] * 0.985
            is_bull = True
        elif is_flat_bot and top_slope < 0:
            pid = 45
            name = "Triangles (Descending)"
            bias = "Bearish"
            ptype = "Continuation"
            breakout_level = min(v1['price'], v2['price'])
            target_price = max(0.01, breakout_level - height)
            stop_loss = p2['price'] * 1.015
            is_bull = False
        else:
            pid = 46
            name = "Triangles (Symmetrical)"
            # Determine direction from breakout or prior trend
            prior_t = determine_prior_trend(df, start_idx)
            is_bull = (prior_t != 'DOWNTREND')
            bias = "Bullish" if is_bull else "Bearish"
            ptype = "Continuation or Reversal"
            breakout_level = top_reg['slope'] * end_idx + top_reg['intercept'] if is_bull else bot_reg['slope'] * end_idx + bot_reg['intercept']
            target_price = (breakout_level + height) if is_bull else max(0.01, breakout_level - height)
            stop_loss = (bot_reg['slope'] * end_idx + bot_reg['intercept']) if is_bull else (top_reg['slope'] * end_idx + top_reg['intercept'])
            
        status, b_date, b_price, vol_conf = check_breakout_status(
            df, end_idx, breakout_level, target_price, stop_loss, is_bullish=is_bull
        )
        
        patterns.append(DetectedPattern(
            id=pid,
            name=name,
            directional_bias=bias,
            pattern_type=ptype,
            start_index=start_idx,
            end_index=end_idx,
            start_date=df.index[start_idx],
            end_date=df.index[end_idx],
            breakout_level=breakout_level,
            target_price=target_price,
            stop_loss=stop_loss,
            description=f"Pola formasi {name} dengan garis batas konvergen. Breakout optimal terjadi pada 2/3 s.d. 3/4 formasi.",
            measuring_technique="Ukur tinggi dasar segitiga (base height) dan proyeksikan ke arah breakout.",
            statistical_notes="Volume yang mengering selama formasi dan melonjak saat breakout menghasilkan reli paling solid.",
            key_points=[
                {'name': 'Peak 1', 'index': p1['index'], 'date': p1['date'], 'price': p1['price']},
                {'name': 'Valley 1', 'index': v1['index'], 'date': v1['date'], 'price': v1['price']},
                {'name': 'Peak 2', 'index': p2['index'], 'date': p2['date'], 'price': p2['price']},
                {'name': 'Valley 2', 'index': v2['index'], 'date': v2['date'], 'price': v2['price']}
            ],
            geometry_lines=[
                {'x': [p1['date'], df.index[min(len(df)-1, end_idx + 15)]], 
                 'y': [p1['price'], top_reg['slope'] * min(len(df)-1, end_idx + 15) + top_reg['intercept']], 
                 'name': 'Upper Resistance Line', 'color': '#FF5252', 'style': 'solid'},
                {'x': [v1['date'], df.index[min(len(df)-1, end_idx + 15)]], 
                 'y': [v1['price'], bot_reg['slope'] * min(len(df)-1, end_idx + 15) + bot_reg['intercept']], 
                 'name': 'Lower Support Line', 'color': '#00E676', 'style': 'solid'}
            ],
            status=status,
            breakout_date=b_date,
            breakout_price=b_price,
            volume_confirmed=vol_conf,
            quality_score=4
        ))
    return patterns


# -------------------------------------------------------------------------
# 5. WEDGES (#49 Falling, #50 Rising)
# -------------------------------------------------------------------------
def detect_wedges(df: pd.DataFrame, peaks: List[Dict], valleys: List[Dict]) -> List[DetectedPattern]:
    patterns = []
    if len(peaks) < 2 or len(valleys) < 2:
        return patterns

    for i in range(len(peaks) - 1):
        p1, p2 = peaks[i], peaks[i+1]
        cand_valleys = [v for v in valleys if p1['index'] - 5 <= v['index'] <= p2['index'] + 15]
        if len(cand_valleys) < 2:
            continue
        v1, v2 = cand_valleys[-2], cand_valleys[-1]
        
        top_reg = fit_trendline([p1['index'], p2['index']], [p1['price'], p2['price']])
        bot_reg = fit_trendline([v1['index'], v2['index']], [v1['price'], v2['price']])
        
        top_s, bot_s = top_reg['slope'], bot_reg['slope']
        start_idx = min(p1['index'], v1['index'])
        end_idx = max(p2['index'], v2['index'])
        
        # Falling Wedge (#49): both slopes negative, top steeper than bot (converging down)
        if top_s < 0 and bot_s < 0 and top_s < bot_s:
            breakout_level = top_reg['slope'] * end_idx + top_reg['intercept']
            target_price = max(p1['price'], p2['price'])  # PDF: Target is highest high of formation
            stop_loss = min(v1['price'], v2['price']) * 0.985
            
            status, b_date, b_price, vol_conf = check_breakout_status(
                df, end_idx, breakout_level, target_price, stop_loss, is_bullish=True
            )
            
            patterns.append(DetectedPattern(
                id=49,
                name="Wedges (Falling)",
                directional_bias="Bullish",
                pattern_type="Continuation",
                start_index=start_idx,
                end_index=end_idx,
                start_date=df.index[start_idx],
                end_date=df.index[end_idx],
                breakout_level=breakout_level,
                target_price=target_price,
                stop_loss=stop_loss,
                description="Pola Falling Wedge dengan dua garis tren menurun yang konvergen. Mengindikasikan akumulasi dan breakout bullish.",
                measuring_technique="Target harga yang diproyeksikan adalah titik tertinggi (highest high) dari awal formasi.",
                statistical_notes="Volume yang meningkat saat breakout memberikan akselerasi target terbaik.",
                key_points=[
                    {'name': 'Upper High 1', 'index': p1['index'], 'date': p1['date'], 'price': p1['price']},
                    {'name': 'Lower Low 1', 'index': v1['index'], 'date': v1['date'], 'price': v1['price']},
                    {'name': 'Upper High 2', 'index': p2['index'], 'date': p2['date'], 'price': p2['price']},
                    {'name': 'Lower Low 2', 'index': v2['index'], 'date': v2['date'], 'price': v2['price']}
                ],
                geometry_lines=[
                    {'x': [p1['date'], df.index[min(len(df)-1, end_idx + 15)]], 
                     'y': [p1['price'], top_reg['slope'] * min(len(df)-1, end_idx + 15) + top_reg['intercept']], 
                     'name': 'Upper Wedge Line', 'color': '#00E676', 'style': 'solid'},
                    {'x': [v1['date'], df.index[min(len(df)-1, end_idx + 15)]], 
                     'y': [v1['price'], bot_reg['slope'] * min(len(df)-1, end_idx + 15) + bot_reg['intercept']], 
                     'name': 'Lower Wedge Line', 'color': '#69F0AE', 'style': 'solid'}
                ],
                status=status,
                breakout_date=b_date,
                breakout_price=b_price,
                volume_confirmed=vol_conf,
                quality_score=4
            ))

        # Rising Wedge (#50): both slopes positive, bot steeper than top (converging up)
        elif top_s > 0 and bot_s > 0 and bot_s > top_s:
            breakout_level = bot_reg['slope'] * end_idx + bot_reg['intercept']
            target_price = min(v1['price'], v2['price'])  # PDF: Target is lowest low of formation
            stop_loss = max(p1['price'], p2['price']) * 1.015
            
            status, b_date, b_price, vol_conf = check_breakout_status(
                df, end_idx, breakout_level, target_price, stop_loss, is_bullish=False
            )
            
            patterns.append(DetectedPattern(
                id=50,
                name="Wedges (Rising)",
                directional_bias="Bearish",
                pattern_type="Continuation",
                start_index=start_idx,
                end_index=end_idx,
                start_date=df.index[start_idx],
                end_date=df.index[end_idx],
                breakout_level=breakout_level,
                target_price=target_price,
                stop_loss=stop_loss,
                description="Pola Rising Wedge dengan dua garis tren menanjak yang konvergen. Mengindikasikan kehilangan momentum dan breakdown bearish.",
                measuring_technique="Target harga yang diproyeksikan adalah titik terendah (lowest low) dari formasi wedge.",
                statistical_notes="Penurunan volume saat pembentukan pola dan lonjakan saat breakdown memvalidasi pola ini.",
                key_points=[
                    {'name': 'Lower Low 1', 'index': v1['index'], 'date': v1['date'], 'price': v1['price']},
                    {'name': 'Upper High 1', 'index': p1['index'], 'date': p1['date'], 'price': p1['price']},
                    {'name': 'Lower Low 2', 'index': v2['index'], 'date': v2['date'], 'price': v2['price']},
                    {'name': 'Upper High 2', 'index': p2['index'], 'date': p2['date'], 'price': p2['price']}
                ],
                geometry_lines=[
                    {'x': [p1['date'], df.index[min(len(df)-1, end_idx + 15)]], 
                     'y': [p1['price'], top_reg['slope'] * min(len(df)-1, end_idx + 15) + top_reg['intercept']], 
                     'name': 'Upper Wedge Line', 'color': '#FF8A80', 'style': 'solid'},
                    {'x': [v1['date'], df.index[min(len(df)-1, end_idx + 15)]], 
                     'y': [v1['price'], bot_reg['slope'] * min(len(df)-1, end_idx + 15) + bot_reg['intercept']], 
                     'name': 'Lower Wedge Line', 'color': '#FF1744', 'style': 'solid'}
                ],
                status=status,
                breakout_date=b_date,
                breakout_price=b_price,
                volume_confirmed=vol_conf,
                quality_score=4
            ))
    return patterns


# -------------------------------------------------------------------------
# 6. CUP AND HANDLE (#5 Normal, #6 Inverted)
# -------------------------------------------------------------------------
def detect_cup_and_handle(df: pd.DataFrame, peaks: List[Dict], valleys: List[Dict]) -> List[DetectedPattern]:
    patterns = []
    if len(peaks) < 2 or len(valleys) < 1:
        return patterns

    for i in range(len(peaks) - 1):
        left_lip = peaks[i]
        right_lip = peaks[i+1]
        
        # Duration: at least 15 bars (on weekly/daily corresponds to multi-week formation)
        span = right_lip['index'] - left_lip['index']
        if span < 12 or span > 120:
            continue
            
        # Lips should be reasonably aligned (within 5%)
        if abs(left_lip['price'] - right_lip['price']) / left_lip['price'] > 0.06:
            continue
            
        # Intermediate valleys forming the rounded cup bottom
        inter_valleys = [v for v in valleys if left_lip['index'] < v['index'] < right_lip['index']]
        if not inter_valleys:
            continue
        cup_bottom = min(inter_valleys, key=lambda x: x['price'])
        
        depth = min(left_lip['price'], right_lip['price']) - cup_bottom['price']
        if depth / left_lip['price'] < 0.05:
            continue
            
        # Handle formation on the right of right_lip
        handle_end = min(len(df) - 1, right_lip['index'] + int(span * 0.4))
        if handle_end <= right_lip['index']:
            handle_end = right_lip['index']
            
        breakout_level = right_lip['price']
        target_price = right_lip['price'] + depth
        stop_loss = cup_bottom['price'] + (depth * 0.5)
        
        status, b_date, b_price, vol_conf = check_breakout_status(
            df, right_lip['index'], breakout_level, target_price, stop_loss, is_bullish=True
        )
        
        patterns.append(DetectedPattern(
            id=5,
            name="Cup and Handle",
            directional_bias="Bullish",
            pattern_type="Continuation",
            start_index=left_lip['index'],
            end_index=right_lip['index'],
            start_date=left_lip['date'],
            end_date=right_lip['date'],
            breakout_level=breakout_level,
            target_price=target_price,
            stop_loss=stop_loss,
            description="Pola Cup and Handle klasik berbentuk 'U' dengan handle konsolidasi di sebelah kanan.",
            measuring_technique="Ukur kedalaman dari bibir kanan ke dasar cup, lalu tambahkan ke level harga bibir kanan.",
            statistical_notes="Pola dengan handle pendek dan bibir kiri sedikit lebih tinggi daripada bibir kanan memberikan hasil optimal.",
            key_points=[
                {'name': 'Left Lip', 'index': left_lip['index'], 'date': left_lip['date'], 'price': left_lip['price']},
                {'name': 'Cup Bottom', 'index': cup_bottom['index'], 'date': cup_bottom['date'], 'price': cup_bottom['price']},
                {'name': 'Right Lip', 'index': right_lip['index'], 'date': right_lip['date'], 'price': right_lip['price']}
            ],
            geometry_lines=[
                {'x': [left_lip['date'], df.index[min(len(df)-1, right_lip['index'] + 20)]], 
                 'y': [right_lip['price'], right_lip['price']], 'name': 'Cup Lip (Breakout)', 'color': '#2962FF', 'style': 'dash'}
            ],
            status=status,
            breakout_date=b_date,
            breakout_price=b_price,
            volume_confirmed=vol_conf,
            quality_score=4
        ))
    return patterns


# -------------------------------------------------------------------------
# 7. FLAGS & PENNANTS (#15 Bullish Flag, #16 Bearish Flag, #17 High & Tight, #30/#31 Pennants)
# -------------------------------------------------------------------------
def detect_flags_and_pennants(df: pd.DataFrame, peaks: List[Dict], valleys: List[Dict]) -> List[DetectedPattern]:
    patterns = []
    n = len(df)
    if n < 20:
        return patterns

    # Detect steep pole followed by 5 to 25 bars consolidation
    for i in range(15, n - 5, 5):
        # 1. Bullish Flag / Pennant Check
        pole_start = max(0, i - 15)
        p_low = df['Low'].iloc[pole_start:i-5].min()
        p_low_idx = df['Low'].iloc[pole_start:i-5].idxmin()
        p_low_pos = df.index.get_loc(p_low_idx)
        
        p_high = df['High'].iloc[p_low_pos:i].max()
        p_high_idx = df['High'].iloc[p_low_pos:i].idxmax()
        p_high_pos = df.index.get_loc(p_high_idx)
        
        pole_height = p_high - p_low
        pole_pct = pole_height / (p_low + 1e-9)
        
        if pole_pct >= 0.08 and p_high_pos > p_low_pos:
            # Consolidation area after pole: stops when breakout occurs or up to 20 bars
            flag_end_pos = p_high_pos + 1
            while flag_end_pos < n and (flag_end_pos - p_high_pos) < 20:
                if df['Close'].iloc[flag_end_pos] > p_high * 1.01:
                    break
                flag_end_pos += 1

            flag_df = df.iloc[p_high_pos:flag_end_pos]
            if len(flag_df) >= 3:
                flag_low = flag_df['Low'].min()
                # Retracement should not exceed 55% of pole
                if (p_high - flag_low) <= (pole_height * 0.55):
                    # Check High & Tight Flag (#17): pole doubles (>90%)
                    if pole_pct >= 0.85:
                        pid = 17
                        name = "Flags (High & Tight)"
                        target = p_high + (pole_height * 0.5)  # PDF rule: add one-half pole height
                    else:
                        pid = 15
                        name = "Flags (Bullish)"
                        target = p_high + pole_height
                        
                    breakout_level = p_high
                    stop_loss = flag_low * 0.985
                    
                    status, b_date, b_price, vol_conf = check_breakout_status(
                        df, p_high_pos + len(flag_df) - 1,
                        breakout_level, target, stop_loss, is_bullish=True
                    )
                    
                    patterns.append(DetectedPattern(
                        id=pid,
                        name=name,
                        directional_bias="Bullish",
                        pattern_type="Continuation",
                        start_index=p_low_pos,
                        end_index=p_high_pos + len(flag_df) - 1,
                        start_date=p_low_idx,
                        end_date=flag_df.index[-1],
                        breakout_level=breakout_level,
                        target_price=target,
                        stop_loss=stop_loss,
                        description="Pola kelanjutan bullish dengan tiang tajam (pole) diikuti konsolidasi bendera kompak.",
                        measuring_technique="Ukur panjang tiang sebelumnya, lalu tambahkan ke level breakout.",
                        statistical_notes="Pola tanpa gap saat konsolidasi dan volume menurun saat pembentukan bendera cenderung memberikan hasil terbaik.",
                        key_points=[
                            {'name': 'Pole Low', 'index': p_low_pos, 'date': p_low_idx, 'price': p_low},
                            {'name': 'Pole High', 'index': p_high_pos, 'date': p_high_idx, 'price': p_high},
                            {'name': 'Flag Low', 'index': p_high_pos + len(flag_df) - 1, 'date': flag_df.index[-1], 'price': flag_low}
                        ],
                        geometry_lines=[
                            {'x': [p_low_idx, p_high_idx], 'y': [p_low, p_high], 'name': 'Pole', 'color': '#00E676', 'style': 'solid'},
                            {'x': [p_high_idx, flag_df.index[-1]], 'y': [p_high, p_high], 'name': 'Flag Resistance', 'color': '#2962FF', 'style': 'dash'}
                        ],
                        status=status,
                        breakout_date=b_date,
                        breakout_price=b_price,
                        volume_confirmed=vol_conf,
                        quality_score=4
                    ))
    return patterns


# -------------------------------------------------------------------------
# 8. WEEKLY SPECIALTIES: HORNS & PIPES (#27, #28, #32, #33)
# -------------------------------------------------------------------------
def detect_horns_and_pipes(df: pd.DataFrame) -> List[DetectedPattern]:
    patterns = []
    n = len(df)
    if n < 6:
        return patterns

    # Pipe Bottoms (#32) & Tops (#33): 2 consecutive bars with long spikes
    for i in range(2, n - 1):
        b1 = df.iloc[i-1]
        b2 = df.iloc[i]
        
        # Check Pipe Bottom (#32): two downward spikes touching low range
        range1 = b1['High'] - b1['Low']
        range2 = b2['High'] - b2['Low']
        atr = df['ATR'].iloc[i] if 'ATR' in df.columns else 1.0
        
        if range1 > atr * 1.3 and range2 > atr * 1.3:
            # Overlapping lows
            min_low = min(b1['Low'], b2['Low'])
            max_high = max(b1['High'], b2['High'])
            if abs(b1['Low'] - b2['Low']) / min_low < 0.025:
                breakout_level = max_high
                pipe_height = max_high - min_low
                target_price = max_high + pipe_height
                stop_loss = min_low * 0.985
                
                status, b_date, b_price, vol_conf = check_breakout_status(
                    df, i, breakout_level, target_price, stop_loss, is_bullish=True
                )
                
                patterns.append(DetectedPattern(
                    id=32,
                    name="Pipe Bottoms",
                    directional_bias="Bullish",
                    pattern_type="Reversal",
                    start_index=i-1,
                    end_index=i,
                    start_date=df.index[i-1],
                    end_date=df.index[i],
                    breakout_level=breakout_level,
                    target_price=target_price,
                    stop_loss=stop_loss,
                    description="Pola Pipe Bottoms dengan dua bar/minggu berurutan yang membentuk downward price spikes panjang.",
                    measuring_technique="Hitung selisih titik tertinggi dan terendah dari kedua pipa, lalu tambahkan ke titik tertinggi.",
                    statistical_notes="Formasi dengan rentang lebih lebar dan volume lebih tinggi pada spike kiri bekerja paling efektif.",
                    key_points=[
                        {'name': 'Pipe 1', 'index': i-1, 'date': df.index[i-1], 'price': b1['Low']},
                        {'name': 'Pipe 2', 'index': i, 'date': df.index[i], 'price': b2['Low']}
                    ],
                    geometry_lines=[
                        {'x': [df.index[i-1], df.index[min(n-1, i+10)]], 'y': [breakout_level, breakout_level], 'name': 'Pipe High (Breakout)', 'color': '#00E676', 'style': 'dash'}
                    ],
                    status=status,
                    breakout_date=b_date,
                    breakout_price=b_price,
                    volume_confirmed=vol_conf,
                    quality_score=4
                ))

        # Horn Bottoms (#27): 3-bar formation where center week has higher low
        if i >= 3:
            w1, w2, w3 = df.iloc[i-2], df.iloc[i-1], df.iloc[i]
            if w2['Low'] > w1['Low'] * 1.02 and w2['Low'] > w3['Low'] * 1.02:
                if abs(w1['Low'] - w3['Low']) / min(w1['Low'], w3['Low']) < 0.03:
                    h_high = max(w1['High'], w2['High'], w3['High'])
                    l_low = min(w1['Low'], w3['Low'])
                    height = h_high - l_low
                    breakout_level = h_high
                    target_price = h_high + height
                    stop_loss = l_low * 0.985
                    
                    status, b_date, b_price, vol_conf = check_breakout_status(
                        df, i, breakout_level, target_price, stop_loss, is_bullish=True
                    )
                    
                    patterns.append(DetectedPattern(
                        id=27,
                        name="Horn Bottoms",
                        directional_bias="Bullish",
                        pattern_type="Reversal",
                        start_index=i-2,
                        end_index=i,
                        start_date=df.index[i-2],
                        end_date=df.index[i],
                        breakout_level=breakout_level,
                        target_price=target_price,
                        stop_loss=stop_loss,
                        description="Pola Horn Bottoms pada grafik mingguan dengan 2 spike tajam ke bawah yang dipisahkan oleh 1 minggu dengan low lebih tinggi.",
                        measuring_technique="Hitung selisih harga tertinggi dan terendah dalam periode 3 minggu, lalu tambahkan ke titik tertinggi.",
                        statistical_notes="Pola dengan rentang lebar antara high dan low memberikan probabilitas terbaik.",
                        key_points=[
                            {'name': 'Left Spike', 'index': i-2, 'date': df.index[i-2], 'price': w1['Low']},
                            {'name': 'Center Week', 'index': i-1, 'date': df.index[i-1], 'price': w2['Low']},
                            {'name': 'Right Spike', 'index': i, 'date': df.index[i], 'price': w3['Low']}
                        ],
                        geometry_lines=[
                            {'x': [df.index[i-2], df.index[min(n-1, i+10)]], 'y': [breakout_level, breakout_level], 'name': 'Horn High (Breakout)', 'color': '#2962FF', 'style': 'dash'}
                        ],
                        status=status,
                        breakout_date=b_date,
                        breakout_price=b_price,
                        volume_confirmed=vol_conf,
                        quality_score=4
                    ))
                    
    return patterns


# -------------------------------------------------------------------------
# 9. GAPS (#18 Area, #19 Breakaway, #20 Continuation, #21 Exhaustion)
# -------------------------------------------------------------------------
def detect_gaps(df: pd.DataFrame) -> List[DetectedPattern]:
    patterns = []
    n = len(df)
    if n < 10:
        return patterns

    for i in range(5, n):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        
        # Gap Up
        if curr['Low'] > prev['High'] * 1.01:
            gap_size = curr['Low'] - prev['High']
            vol_ratio = curr.get('Vol_Ratio', 1.0)
            
            # Check Breakaway Gap vs Area Gap vs Continuation Gap
            if vol_ratio >= 1.4:
                pid = 19
                name = "Gaps (Breakaway)"
                bias = "Bullish"
                ptype = "Continuation"
                target_price = curr['High'] + (gap_size * 2.0)
                desc = "Breakaway Gap terjadi saat harga melompat keluar dari konsolidasi dengan volume lonjakan masif."
            else:
                pid = 18
                name = "Gaps (Area)"
                bias = "Non-Directional"
                ptype = "Reversal"
                target_price = prev['High']  # Fills the gap
                desc = "Area Gap umum terjadi dalam konsolidasi, memiliki kecenderungan tertutup kembali (filled) ~90%."
                
            breakout_level = curr['Close']
            stop_loss = prev['Low'] * 0.99
            
            status, b_date, b_price, vol_conf = check_breakout_status(
                df, i, breakout_level, target_price, stop_loss, is_bullish=True
            )
            
            patterns.append(DetectedPattern(
                id=pid,
                name=name,
                directional_bias=bias,
                pattern_type=ptype,
                start_index=i-1,
                end_index=i,
                start_date=df.index[i-1],
                end_date=df.index[i],
                breakout_level=breakout_level,
                target_price=target_price,
                stop_loss=stop_loss,
                description=desc,
                measuring_technique="Proyeksikan 2x ukuran lompatan (Breakaway) atau target penutupan gap (Area Gap).",
                statistical_notes="Breakaway gaps yang terjadi dekat 12-month low/high cenderung bertahan tanpa tertutup cepat.",
                key_points=[
                    {'name': 'Pre-gap Day', 'index': i-1, 'date': df.index[i-1], 'price': prev['High']},
                    {'name': 'Gap Day', 'index': i, 'date': df.index[i], 'price': curr['Low']}
                ],
                geometry_lines=[
                    {'x': [df.index[i-1], df.index[min(n-1, i+8)]], 'y': [prev['High'], prev['High']], 'name': 'Gap Bottom', 'color': '#FFD600', 'style': 'dot'},
                    {'x': [df.index[i], df.index[min(n-1, i+8)]], 'y': [curr['Low'], curr['Low']], 'name': 'Gap Top', 'color': '#FFD600', 'style': 'dot'}
                ],
                status=status,
                breakout_date=b_date,
                breakout_price=b_price,
                volume_confirmed=bool(vol_ratio >= 1.2),
                quality_score=4
            ))
            
    return patterns


# -------------------------------------------------------------------------
# MASTER PATTERN DETECTION FUNCTION
def get_adaptive_orders(df: pd.DataFrame) -> List[int]:
    """
    Automatically calculate multi-scale optimal swing orders based on dataset length and volatility.
    """
    n = len(df)
    if n < 40:
        return [2, 3]
    elif n < 120:
        return [3, 5]
    elif n < 300:
        return [3, 5, 7]
    else:
        return [4, 6, 9]


# -------------------------------------------------------------------------
# MASTER PATTERN DETECTION FUNCTION
# -------------------------------------------------------------------------
def detect_all_patterns(df: pd.DataFrame, window_order: Optional[int] = None) -> List[DetectedPattern]:
    """
    Run all pattern detection algorithms across the time series data.
    If window_order is None, runs automatically across adaptive multi-scale orders.
    Returns deduplicated and sorted list of DetectedPattern instances.
    """
    if window_order is not None:
        scan_orders = [window_order]
    else:
        scan_orders = get_adaptive_orders(df)
        
    detected: List[DetectedPattern] = []
    
    for w_order in scan_orders:
        peaks, valleys = find_extrema(df, order=w_order)
        
        # 1. Double Bottoms & Tops
        detected.extend(detect_double_bottoms(df, peaks, valleys))
        detected.extend(detect_double_tops(df, peaks, valleys))
        
        # 2. Head and Shoulders
        detected.extend(detect_head_and_shoulders(df, peaks, valleys))
        
        # 3. Triangles
        detected.extend(detect_triangles(df, peaks, valleys))
        
        # 4. Wedges
        detected.extend(detect_wedges(df, peaks, valleys))
        
        # 5. Cup and Handle
        detected.extend(detect_cup_and_handle(df, peaks, valleys))
        
    # Flags and Pennants
    detected.extend(detect_flags_and_pennants(df, [], []))
    
    # Horns and Pipes
    detected.extend(detect_horns_and_pipes(df))
    
    # Gaps
    detected.extend(detect_gaps(df))
    
    # Deduplicate by pattern id and proximity of end_index
    unique_patterns = {}
    for p in detected:
        # Group patterns of same type that end within 3 bars of each other
        bucket_end = round(p.end_index / 3) * 3
        key = (p.id, bucket_end)
        if key not in unique_patterns:
            unique_patterns[key] = p
        else:
            if p.quality_score > unique_patterns[key].quality_score:
                unique_patterns[key] = p
                
    result = list(unique_patterns.values())
    # Sort by end_index descending (most recent first)
    result.sort(key=lambda x: x.end_index, reverse=True)
    return result

