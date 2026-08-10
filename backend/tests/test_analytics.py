import os
import sys
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from analytics.analytics_engine import (
    calculate_technical_indicators,
    calculate_risk_and_performance,
    calculate_flow_and_bandarmology,
    calculate_insider_metrics,
    calculate_composite_market_analytics,
    run_single_symbol_analytics
)

class AnalyticsEngineTests(unittest.TestCase):

    def setUp(self):
        # Create sample 30-day OHLC dataframe for testing
        dates = pd.date_range(start="2026-07-01", periods=30, freq="D")
        np.random.seed(42)
        closes = 6000 + np.cumsum(np.random.randn(30) * 50)
        highs = closes + np.random.rand(30) * 30
        lows = closes - np.random.rand(30) * 30
        opens = (highs + lows) / 2
        volumes = np.random.randint(1000000, 5000000, size=30)
        foreign_flows = np.random.randn(30) * 1_000_000_000

        self.sample_ohlc = pd.DataFrame({
            "symbol": "BBCA",
            "tanggal": dates,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "volume": volumes,
            "foreign_flow": foreign_flows
        })

        self.sample_broker = pd.DataFrame({
            "symbol": ["BBCA", "BBCA", "BBCA"],
            "kodebroker": ["CC", "ZP", "AK"],
            "tipebroker": ["F", "F", "D"],
            "tanggal": pd.to_datetime(["2026-07-30", "2026-07-30", "2026-07-30"]),
            "nilairp": [500_000_000, 300_000_000, 100_000_000],
            "lot": [10000, 6000, 2000],
            "avgprice": [6000, 6000, 6000],
            "frekuensi": [50, 30, 10],
            "aksi": ["BUY", "BUY", "SELL"]
        })

        self.sample_insider = pd.DataFrame({
            "symbol": ["BBCA", "BBCA"],
            "nama": ["Director A", "Commissioner B"],
            "tanggal": pd.to_datetime(["2026-07-25", "2026-07-28"]),
            "aksi": ["BUY", "SELL"],
            "perubahan": [100000, -20000],
            "perubahanpersen": [0.01, -0.002],
            "harga": ["6000", "6100"]
        })

    def test_technical_indicators_calculation(self):
        tech = calculate_technical_indicators(self.sample_ohlc)
        self.assertIsNotNone(tech["rsi_14"])
        self.assertIn(tech["rsi_signal"], ["Overbought", "Oversold", "Bullish", "Bearish", "Neutral"])
        self.assertIsNotNone(tech["macd_line"])
        self.assertIsNotNone(tech["sma_20"])
        self.assertIsNotNone(tech["bb_upper"])
        self.assertIsNotNone(tech["pivot_point"])
        self.assertGreaterEqual(tech["bb_upper"], tech["bb_lower"])

    def test_risk_and_performance_calculation(self):
        risk = calculate_risk_and_performance(self.sample_ohlc)
        self.assertIn("change_pct_1d", risk)
        self.assertIn("volatility_ann", risk)
        self.assertIn("sharpe_ratio", risk)
        self.assertIn("max_drawdown", risk)
        self.assertGreaterEqual(risk["max_drawdown"], 0)

    def test_flow_and_bandarmology_calculation(self):
        flow = calculate_flow_and_bandarmology(self.sample_ohlc, self.sample_broker, "BBCA")
        self.assertIn("net_foreign_flow_1d", flow)
        self.assertIn("big_money_status", flow)
        self.assertIn("broker_hhi", flow)
        self.assertGreaterEqual(flow["broker_hhi"], 0.0)

    def test_insider_metrics_calculation(self):
        insider = calculate_insider_metrics(self.sample_insider, "BBCA")
        self.assertEqual(insider["insider_trx_count"], 2)
        self.assertGreater(insider["insider_sentiment_score"], 50.0)

    def test_composite_market_analytics(self):
        sample_results = [
            {"rsi_14": 65, "change_pct_1d": 1.5, "insider_sentiment_score": 70},
            {"rsi_14": 45, "change_pct_1d": -0.5, "insider_sentiment_score": 40}
        ]
        composite = calculate_composite_market_analytics(sample_results)
        self.assertEqual(composite["market_breadth_score"], 50.0)
        self.assertIn(composite["composite_sentiment_label"], ["Strong Bullish", "Bullish", "Neutral", "Bearish", "Strong Bearish"])

    def test_run_single_symbol_analytics(self):
        res = run_single_symbol_analytics("BBCA", self.sample_ohlc, self.sample_broker, self.sample_insider, pd.DataFrame())
        self.assertEqual(res["symbol"], "BBCA")
        self.assertIn("rsi_14", res)
        self.assertIn("volatility_ann", res)

class AnalyticsApiRoutesTests(unittest.TestCase):

    def setUp(self):
        from app import app
        self.app = app.test_client()
        self.app.testing = True

    @patch("analytics.routes._get_connection")
    def test_get_stock_analytics_route(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "symbol": "BBCA",
                "tanggal_analisis": "2026-08-10",
                "last_close": 6050.0,
                "change_pct_1d": 0.83,
                "change_pct_7d": 1.5,
                "change_pct_30d": 3.2,
                "rsi_14": 58.4,
                "rsi_signal": "Bullish",
                "macd_line": 15.2,
                "macd_signal": 10.1,
                "macd_hist": 5.1,
                "macd_trend": "Bullish",
                "sma_5": 6020.0, "sma_20": 5980.0, "sma_50": 5900.0, "sma_200": 5700.0,
                "ema_12": 6030.0, "ema_26": 5970.0,
                "bb_upper": 6150.0, "bb_middle": 5980.0, "bb_lower": 5810.0,
                "atr_14": 85.0,
                "pivot_point": 6040.0, "support_1": 6000.0, "support_2": 5960.0,
                "resistance_1": 6080.0, "resistance_2": 6120.0,
                "volatility_ann": 18.5, "sharpe_ratio": 1.2, "sortino_ratio": 1.5,
                "max_drawdown": 4.2, "beta": 1.05, "cagr": 12.5,
                "net_foreign_flow_1d": 50000000000.0,
                "net_foreign_flow_5d": 150000000000.0,
                "net_foreign_flow_20d": 300000000000.0,
                "big_money_status": "Big Accumulation",
                "broker_hhi": 0.25,
                "insider_net_vol_30d": 500000.0,
                "insider_sentiment_score": 80.0,
                "insider_trx_count": 5,
                "market_breadth_score": 60.0,
                "composite_sentiment_score": 65.0,
                "composite_sentiment_label": "Bullish"
            }
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor

        response = self.app.get("/api/analytics/stock?symbol=BBCA")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["data"]["symbol"], "BBCA")

    @patch("analytics.routes._get_connection")
    def test_get_summary_analytics_route(self, mock_conn):
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                "symbol": "BBCA",
                "tanggal_analisis": "2026-08-10",
                "last_close": 6050.0,
                "change_pct_1d": 0.83,
                "rsi_14": 58.4,
                "macd_trend": "Bullish",
                "big_money_status": "Big Accumulation",
                "market_breadth_score": 60.0,
                "composite_sentiment_score": 65.0,
                "composite_sentiment_label": "Bullish"
            }
        ]
        mock_conn.return_value.cursor.return_value = mock_cursor

        response = self.app.get("/api/analytics/summary")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertIn("summary", data)

if __name__ == "__main__":
    unittest.main()
