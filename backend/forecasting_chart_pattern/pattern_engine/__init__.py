"""
Pattern Engine Package for Chart Pattern Recognition and Forecasting.
"""

from .data_loader import load_stock_data, TIMEFRAME_CONFIG
from .extrema import find_extrema, fit_trendline, determine_prior_trend, evaluate_shape_adam_eve
from .patterns import detect_all_patterns, DetectedPattern
from .forecasting import generate_forecast, PatternSignal, evaluate_all_pattern_forecasts, generate_detection_reasons
from .fibonacci import calculate_fibonacci_levels, find_major_trend_swing

__all__ = [
    'load_stock_data',
    'TIMEFRAME_CONFIG',
    'find_extrema',
    'fit_trendline',
    'determine_prior_trend',
    'evaluate_shape_adam_eve',
    'detect_all_patterns',
    'DetectedPattern',
    'generate_forecast',
    'PatternSignal',
    'evaluate_all_pattern_forecasts',
    'generate_detection_reasons',
    'calculate_fibonacci_levels',
    'find_major_trend_swing'
]
