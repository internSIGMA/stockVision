"""
Comprehensive test suite for StockVision Clustering-Based LGBM Forecasting
and Accuracy Tracking module.
"""

import os
import sys
import unittest
from dotenv import load_dotenv, find_dotenv

# Ensure backend root is in sys.path and load environment variables
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

load_dotenv(find_dotenv(), override=True)

from forecasting.database import (
    ensure_forecast_tables,
    engine,
    load_stock_data,
    load_cluster_metadata,
    load_cluster_assignments_full,
    load_accuracy_summary,
    load_accuracy_dashboard,
    load_accuracy_by_symbol
)
from forecasting.clustering import run_clustering, assign_new_stock
from forecasting.cluster_trainer import train_all_cluster_models, forecast_with_cluster_models
from forecasting.pipeline import run_pipeline
from app import app
from sqlalchemy import text


class TestForecastingSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n=======================================================")
        print("=== RUNNING STOCKVISION FORECASTING TEST SUITE      ===")
        print("=======================================================")
        ensure_forecast_tables()
        cls.client = app.test_client()

    def test_01_database_tables_exist(self):
        """Verify all new tables exist in idxsaham schema."""
        print("\n[Test 1] Verifying database tables in idxsaham schema...")
        tables = ['stock_clusters', 'cluster_metadata', 'cluster_hyperparams', 'forecast_accuracy', 'stock_forecasting']
        with engine.connect() as conn:
            for t in tables:
                res = conn.execute(text(f"SELECT count(*) FROM idxsaham.{t}")).scalar()
                self.assertIsNotNone(res)
                print(f"  [PASS] Table idxsaham.{t} exists ({res} rows)")

    def test_02_clustering_pipeline(self):
        """Verify stock movement clustering and cluster labeling."""
        print("\n[Test 2] Testing K-Means clustering on stock movements...")
        df = load_stock_data()
        self.assertFalse(df.empty, "Stock data should not be empty")
        
        assignments, metadata, features_df = run_clustering(df, n_clusters='auto')
        self.assertTrue(len(assignments) > 0, "Should assign stocks to clusters")
        self.assertTrue(len(metadata) >= 2, "Should create at least 2 clusters")
        
        print(f"  [PASS] Created {len(metadata)} clusters for {len(assignments)} stocks")
        for m in metadata:
            print(f"    - Cluster {m['cluster_id']}: '{m.get('cluster_label')}' ({m.get('n_members')} stocks, Silhouette: {m.get('silhouette_score'):.4f})")

    def test_03_assign_new_stock(self):
        """Verify assigning an unseen / single stock into nearest cluster."""
        print("\n[Test 3] Testing assignment of individual stock to cluster...")
        df = load_stock_data()
        sample_sym = 'BBCA' if 'BBCA' in df['symbol'].values else df['symbol'].iloc[0]
        stock_df = df[df['symbol'] == sample_sym]
        
        cid = assign_new_stock(sample_sym, stock_df)
        self.assertIsInstance(cid, int)
        print(f"  [PASS] Successfully assigned {sample_sym} to Cluster {cid}")

    def test_04_full_pipeline_execution(self):
        """Verify end-to-end training, accuracy calculation, and forecasting."""
        print("\n[Test 4] Testing end-to-end training, accuracy metrics & 7-day forecast...")
        success = run_pipeline(force_recluster=False, run_tuning=False)
        self.assertTrue(success, "Pipeline execution should succeed")
        
        # Verify accuracy records exist
        dash = load_accuracy_dashboard()
        self.assertTrue(len(dash) > 0, "Accuracy dashboard records should exist")
        print(f"  [PASS] Generated {len(dash)} accuracy records across targets")
        
        # Print sample metric
        sample = dash[0]
        print(f"  [PASS] Sample metric for {sample['symbol']} ({sample['target_col']}):")
        print(f"      Accuracy: {sample['accuracy_pct']}% | Confidence: {sample['confidence_level']} | R2: {sample['r2_score']} | MAPE: {sample['mape']}%")

    def test_05_flask_api_endpoints(self):
        """Verify all REST API endpoints return HTTP 200 and valid JSON."""
        print("\n[Test 5] Testing Flask REST API endpoints...")
        
        endpoints = [
            ('/api/forecast/clusters', 'GET', None),
            ('/api/forecast/cluster/BBCA', 'GET', None),
            ('/api/forecast/accuracy', 'GET', None),
            ('/api/forecast/accuracy?symbol=BBCA', 'GET', None),
            ('/api/forecast/accuracy/summary', 'GET', None),
            ('/api/forecast/accuracy/dashboard', 'GET', None),
            ('/api/forecast/hyperparams', 'GET', None),
            ('/api/forecast/pipeline-status', 'GET', None),
            ('/api/forecast/assign-stock', 'POST', {'symbol': 'BBCA'}),
        ]

        for path, method, payload in endpoints:
            if method == 'GET':
                res = self.client.get(path)
            else:
                res = self.client.post(path, json=payload)
            
            self.assertEqual(res.status_code, 200, f"Endpoint {path} failed with {res.status_code}")
            data = res.get_json()
            self.assertIn("status", data)
            print(f"  [PASS] [{method}] {path:<40} -> HTTP 200 OK")


if __name__ == "__main__":
    unittest.main()
