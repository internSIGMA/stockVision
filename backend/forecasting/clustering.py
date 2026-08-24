"""
Clustering module for StockVision.
Groups emitens (IDX stocks) based on movement patterns using K-Means clustering
with automatic detection of optimal k via Silhouette Score.

Features used for clustering:
- avg_daily_return: Average daily return
- volatility_30d: 30-day rolling standard deviation of returns
- avg_volume_normalized: Average volume (Z-score normalized by StandardScaler)
- momentum_20d: 20-day price momentum (return)
- rsi_mean: Mean RSI-14
- beta_proxy: Correlation of stock returns with market median returns
"""

import numpy as np
import pandas as pd
import pickle
from datetime import datetime
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score

from .config import MIN_DATA_POINTS, MAX_CLUSTERS, MIN_CLUSTER_SIZE, MODELS_DIR
from .database import (
    save_cluster_assignments,
    save_cluster_metadata,
    save_single_cluster_assignment,
    load_cluster_assignments,
    load_cluster_metadata,
)
from .logger import logger


# Feature columns used for clustering (standardized before KMeans)
CLUSTER_FEATURE_COLS = [
    'avg_daily_return',
    'volatility_30d',
    'avg_volume',
    'momentum_20d',
    'rsi_mean',
    'beta_proxy',
]


def compute_stock_features(df):
    """
    Compute clustering features per symbol from OHLCV data.

    Args:
        df: DataFrame with columns [symbol, tanggal, open, high, low, close, volume]

    Returns:
        DataFrame with one row per symbol and columns:
        [symbol, avg_daily_return, volatility_30d, avg_volume, momentum_20d, rsi_mean, beta_proxy]
    """
    features = []
    symbols = df['symbol'].unique()

    # --- Pre-compute market median return per date for beta proxy ---
    market_returns_series = {}
    for symbol in symbols:
        stock = df[df['symbol'] == symbol].copy()
        stock = stock.sort_values('tanggal').reset_index(drop=True)
        if len(stock) < MIN_DATA_POINTS:
            continue
        stock['return'] = stock['close'].astype(float).pct_change()
        market_returns_series[symbol] = stock.set_index('tanggal')['return']

    if not market_returns_series:
        logger.warning("No stocks with sufficient data for feature computation.")
        return pd.DataFrame()

    # Align all returns on a common date index and compute median
    market_df = pd.DataFrame(market_returns_series)
    market_median = market_df.median(axis=1)

    # --- Compute per-symbol features ---
    for symbol in symbols:
        stock = df[df['symbol'] == symbol].copy()
        stock = stock.sort_values('tanggal').reset_index(drop=True)

        if len(stock) < MIN_DATA_POINTS:
            continue

        stock['close'] = stock['close'].astype(float)
        stock['volume'] = stock['volume'].astype(float)
        stock['return'] = stock['close'].pct_change()
        recent = stock.tail(60)  # Last ~60 trading days

        # 1. Average daily return
        avg_return = recent['return'].mean()

        # 2. Volatility (30-day std of daily returns)
        volatility = recent['return'].tail(30).std()

        # 3. Average volume (raw; StandardScaler will normalize later)
        avg_volume = recent['volume'].mean()

        # 4. Momentum 20d (price change ratio over last 20 trading days)
        if len(recent) >= 20:
            momentum = (recent['close'].iloc[-1] / recent['close'].iloc[-20]) - 1
        else:
            momentum = 0.0

        # 5. RSI-14 mean (simplified Wilder-style)
        delta = recent['close'].diff()
        gain = delta.where(delta > 0, 0.0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi_mean = rsi.dropna().mean()

        # 6. Beta proxy (correlation with market median return)
        stock_returns = stock.set_index('tanggal')['return']
        common_idx = stock_returns.index.intersection(market_median.index)
        if len(common_idx) > 20:
            beta = stock_returns.loc[common_idx].corr(market_median.loc[common_idx])
        else:
            beta = 0.0

        features.append({
            'symbol': symbol,
            'avg_daily_return': avg_return if pd.notna(avg_return) else 0.0,
            'volatility_30d': volatility if pd.notna(volatility) else 0.0,
            'avg_volume': avg_volume if pd.notna(avg_volume) else 0.0,
            'momentum_20d': momentum if pd.notna(momentum) else 0.0,
            'rsi_mean': rsi_mean if pd.notna(rsi_mean) else 50.0,
            'beta_proxy': beta if pd.notna(beta) else 0.0,
        })

    result = pd.DataFrame(features)
    logger.info("Computed features for %d / %d symbols (min %d data points required).",
                len(result), len(symbols), MIN_DATA_POINTS)
    return result


def _find_optimal_k(X_scaled, k_range):
    """Find optimal number of clusters using Silhouette Score."""
    best_k = k_range[0]
    best_score = -1
    scores = {}

    for k in k_range:
        if k >= len(X_scaled):
            break
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)

        if len(set(labels)) < 2:
            continue

        score = silhouette_score(X_scaled, labels)
        scores[k] = score
        logger.info("  k=%d: silhouette=%.4f", k, score)

        if score > best_score:
            best_score = score
            best_k = k

    logger.info("  Optimal k=%d (silhouette=%.4f)", best_k, best_score)
    return best_k, best_score


def label_clusters(centroids_df):
    """
    Assign descriptive labels based on centroid characteristics (in standardized space).

    Args:
        centroids_df: DataFrame with columns [cluster_id, centroid_return,
                      centroid_volatility, centroid_volume, centroid_momentum]

    Returns:
        dict {cluster_id: label_string}
    """
    labels = {}
    for _, row in centroids_df.iterrows():
        cid = int(row['cluster_id'])
        parts = []

        # Volatility label
        vol = row.get('centroid_volatility', 0)
        if vol > 0.5:
            parts.append("High Volatility")
        elif vol < -0.5:
            parts.append("Low Volatility")
        else:
            parts.append("Mid Volatility")

        # Return / Momentum label
        ret = row.get('centroid_return', 0)
        mom = row.get('centroid_momentum', 0)
        if ret > 0.3 or mom > 0.3:
            parts.append("Growth")
        elif ret < -0.3 or mom < -0.3:
            parts.append("Declining")
        else:
            parts.append("Stable")

        # Volume / Liquidity label
        v = row.get('centroid_volume', 0)
        if v > 0.5:
            parts.append("High Liquidity")
        elif v < -0.5:
            parts.append("Low Liquidity")

        labels[cid] = " - ".join(parts)

    return labels


def _save_models(scaler, kmeans):
    """Persist scaler and KMeans model to disk."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODELS_DIR / 'clustering_scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    with open(MODELS_DIR / 'clustering_kmeans.pkl', 'wb') as f:
        pickle.dump(kmeans, f)
    logger.info("Saved clustering scaler & KMeans model to %s", MODELS_DIR)


def _load_models():
    """Load persisted scaler and KMeans model."""
    scaler_path = MODELS_DIR / 'clustering_scaler.pkl'
    kmeans_path = MODELS_DIR / 'clustering_kmeans.pkl'

    if not scaler_path.exists() or not kmeans_path.exists():
        raise FileNotFoundError(
            f"Clustering models not found at {MODELS_DIR}. Run clustering first."
        )

    with open(scaler_path, 'rb') as f:
        scaler = pickle.load(f)
    with open(kmeans_path, 'rb') as f:
        kmeans = pickle.load(f)
    return scaler, kmeans


def run_clustering(df, n_clusters='auto'):
    """
    Run full clustering pipeline: compute features → K-Means → label → persist.

    Args:
        df: Full OHLCV DataFrame with 'symbol' column (from load_stock_data)
        n_clusters: int or 'auto' for Silhouette-based detection (range 3-MAX_CLUSTERS)

    Returns:
        cluster_assignments: dict {symbol: cluster_id}
        metadata_records: list of dicts (one per cluster)
        features_df: DataFrame with per-symbol features + cluster assignment
    """
    logger.info("========== Clustering Pipeline Started ==========")

    # 1. Compute per-symbol features
    features_df = compute_stock_features(df)

    if features_df.empty or len(features_df) < 6:
        logger.warning("Not enough stocks with sufficient data for clustering (%d found).",
                       len(features_df))
        return {}, [], features_df

    # 2. Standardize feature matrix
    X = features_df[CLUSTER_FEATURE_COLS].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # 3. Determine k
    if n_clusters == 'auto':
        max_k = min(MAX_CLUSTERS + 1, len(features_df))
        k_range = range(3, max_k)
        logger.info("Auto-detecting optimal k (range %d-%d)...", k_range.start, k_range.stop - 1)
        optimal_k, sil_score = _find_optimal_k(X_scaled, k_range)
    else:
        optimal_k = int(n_clusters)
        sil_score = None

    # 4. Fit final KMeans
    logger.info("Fitting KMeans with k=%d...", optimal_k)
    kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)

    if sil_score is None and len(set(labels)) > 1:
        sil_score = silhouette_score(X_scaled, labels)

    features_df['cluster_id'] = labels

    # 5. Persist models for assign_new_stock()
    _save_models(scaler, kmeans)

    # 6. Build cluster_assignments dict
    cluster_assignments = {}
    for _, row in features_df.iterrows():
        cluster_assignments[row['symbol']] = int(row['cluster_id'])

    # 7. Build metadata from centroids (in *standardized* space for labeling)
    centroids_scaled = kmeans.cluster_centers_

    metadata_records = []
    for i in range(optimal_k):
        members = features_df[features_df['cluster_id'] == i]
        metadata_records.append({
            'cluster_id': i,
            'n_members': len(members),
            'centroid_return': float(centroids_scaled[i][0]),
            'centroid_volatility': float(centroids_scaled[i][1]),
            'centroid_volume': float(centroids_scaled[i][2]),
            'centroid_momentum': float(centroids_scaled[i][3]),
            'silhouette_score': float(sil_score) if sil_score is not None else 0.0,
        })

    # 8. Label clusters
    meta_df = pd.DataFrame(metadata_records)
    cluster_labels = label_clusters(meta_df)
    for rec in metadata_records:
        rec['cluster_label'] = cluster_labels.get(rec['cluster_id'], f"Cluster {rec['cluster_id']}")

    features_df['cluster_label'] = features_df['cluster_id'].map(cluster_labels)

    # 9. Persist to database
    logger.info("Saving cluster assignments & metadata to database...")

    assignment_records = []
    for _, row in features_df.iterrows():
        assignment_records.append({
            'symbol': row['symbol'],
            'cluster_id': int(row['cluster_id']),
            'cluster_label': row['cluster_label'],
            'avg_return': float(row['avg_daily_return']),
            'avg_volatility': float(row['volatility_30d']),
            'avg_volume': float(row['avg_volume']),
            'momentum_score': float(row['momentum_20d']),
        })
    save_cluster_assignments(assignment_records)
    save_cluster_metadata(metadata_records)

    for rec in metadata_records:
        logger.info("  Cluster %d (%s): %d members",
                    rec['cluster_id'], rec['cluster_label'], rec['n_members'])

    logger.info("========== Clustering Complete: %d clusters, silhouette=%.4f ==========",
                optimal_k, sil_score if sil_score else 0.0)

    return cluster_assignments, metadata_records, features_df


def assign_new_stock(symbol, df):
    """
    Assign a new / unseen stock to the nearest existing cluster using
    persisted scaler and KMeans centroids.

    Args:
        symbol: stock ticker (e.g. "GOTO")
        df: OHLCV DataFrame for this symbol (must include 'symbol' column or will be added)

    Returns:
        cluster_id (int)
    """
    scaler, kmeans = _load_models()

    single_df = df.copy()
    if 'symbol' not in single_df.columns:
        single_df['symbol'] = symbol.upper()

    features = compute_stock_features(single_df)

    if features.empty:
        raise ValueError(
            f"Insufficient data for {symbol} (need >= {MIN_DATA_POINTS} data points)"
        )

    X = features[CLUSTER_FEATURE_COLS].values
    X_scaled = scaler.transform(X)
    cluster_id = int(kmeans.predict(X_scaled)[0])

    # Look up cluster label from DB
    metadata = load_cluster_metadata()
    label = f"Cluster {cluster_id}"
    for m in metadata:
        if m['cluster_id'] == cluster_id:
            label = m.get('cluster_label', label)
            break

    # Persist single assignment
    save_single_cluster_assignment(
        symbol=symbol.upper(),
        cluster_id=cluster_id,
        cluster_label=label,
        avg_return=float(features.iloc[0]['avg_daily_return']),
        avg_volatility=float(features.iloc[0]['volatility_30d']),
        avg_volume=float(features.iloc[0]['avg_volume']),
        momentum_score=float(features.iloc[0]['momentum_20d']),
    )

    logger.info("Assigned %s -> cluster %d (%s)", symbol, cluster_id, label)
    return cluster_id
