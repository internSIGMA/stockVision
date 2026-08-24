try:
    from sqlalchemy import create_engine, text
except Exception:  
    create_engine = None
    text = None

import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

from .logger import logger

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "10.1.8.108"),
    "database": os.getenv("DB_NAME", "stockVision"),
    "user":     os.getenv("DB_USER", "stockvision"),
    "password": os.getenv("DB_PASSWORD", "Sigma#2026"),
    "port":     int(os.getenv("DB_PORT", 5434)),
}

def get_raw_connection():
    """Returns a psycopg2 connection with fallback to local Docker instance if primary is unreachable."""
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            connect_timeout=10
        )
        return conn
    except psycopg2.OperationalError as e:
        logger.warning("Primary DB (%s:%s) unreachable (%s), falling back to local...",
                       DB_CONFIG['host'], DB_CONFIG['port'], e)
        # Fallback to local Docker postgres
        return psycopg2.connect(
            host="localhost",
            port=5433,
            database="stockVision",
            user="stockvision",
            password="stockvision_pass",
            connect_timeout=5
        )

def get_engine():
    if create_engine is None:
        raise ImportError("sqlalchemy is required for database operations. Install sqlalchemy and a DB driver (e.g. psycopg2).")

    try:
        test_conn = psycopg2.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            database=DB_CONFIG['database'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            connect_timeout=10
        )
        test_conn.close()
        url = (
            f"postgresql+psycopg2://"
            f"{DB_CONFIG['user']}:{DB_CONFIG['password']}"
            f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
            f"/{DB_CONFIG['database']}"
        )
    except psycopg2.OperationalError:
        url = "postgresql+psycopg2://stockvision:stockvision_pass@localhost:5433/stockVision"

    return create_engine(url)

engine = get_engine()

def load_stock_data():

    query = """

    SELECT *

    FROM idxsaham.ohlc_forecasting

    ORDER BY symbol,tanggal

    """

    return pd.read_sql(query, engine)

def load_trading_calendar():

    query = """

    SELECT *

    FROM idxsaham.trading_calendar

    ORDER BY trading_date

    """

    return pd.read_sql(query, engine)

def refresh_forecast(df):

    records = df[
        [
            "symbol",
            "tanggal",
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]
    ].to_dict("records")

    query = text("""
        INSERT INTO idxsaham.stock_forecasting
        (
            symbol,
            tanggal,
            open,
            high,
            low,
            close,
            volume
        )
        VALUES
        (
            :symbol,
            :tanggal,
            :open,
            :high,
            :low,
            :close,
            :volume
        )
    """)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE idxsaham.stock_forecasting"))
        conn.execute(query, records)

def get_symbols():

    query = """

    SELECT DISTINCT symbol

    FROM idxsaham.ohlc_forecasting

    ORDER BY symbol

    """

    return pd.read_sql(query, engine)["symbol"].tolist()


# ============================================================
# DDL: Ensure new forecasting tables exist
# ============================================================

def ensure_forecast_tables():
    """Create clustering, hyperparameter, and accuracy tables if they don't exist."""
    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS idxsaham.stock_clusters (
            symbol          VARCHAR(20) PRIMARY KEY,
            cluster_id      INTEGER NOT NULL,
            cluster_label   VARCHAR(100),
            avg_return       DOUBLE PRECISION,
            avg_volatility   DOUBLE PRECISION,
            avg_volume       DOUBLE PRECISION,
            momentum_score   DOUBLE PRECISION,
            updated_at       TIMESTAMP DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS idxsaham.cluster_metadata (
            cluster_id          INTEGER PRIMARY KEY,
            cluster_label       VARCHAR(100),
            n_members           INTEGER,
            centroid_return      DOUBLE PRECISION,
            centroid_volatility  DOUBLE PRECISION,
            centroid_volume      DOUBLE PRECISION,
            centroid_momentum    DOUBLE PRECISION,
            silhouette_score     DOUBLE PRECISION,
            updated_at           TIMESTAMP DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS idxsaham.cluster_hyperparams (
            cluster_id      INTEGER NOT NULL,
            target_col      VARCHAR(20) NOT NULL,
            params          JSONB NOT NULL,
            best_score      DOUBLE PRECISION,
            n_trials        INTEGER,
            tuning_duration_sec DOUBLE PRECISION,
            updated_at      TIMESTAMP DEFAULT NOW(),
            PRIMARY KEY (cluster_id, target_col)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS idxsaham.forecast_accuracy (
            id              BIGSERIAL PRIMARY KEY,
            symbol          VARCHAR(20) NOT NULL,
            cluster_id      INTEGER,
            target_col      VARCHAR(20) NOT NULL,
            mae             DOUBLE PRECISION,
            rmse            DOUBLE PRECISION,
            mape            DOUBLE PRECISION,
            r2_score        DOUBLE PRECISION,
            accuracy_pct    DOUBLE PRECISION,
            confidence_level VARCHAR(20),
            n_train_samples INTEGER,
            n_test_samples  INTEGER,
            forecast_horizon INTEGER,
            model_version   VARCHAR(50),
            created_at      TIMESTAMP DEFAULT NOW()
        );
        """
    ]

    conn = get_raw_connection()
    try:
        cur = conn.cursor()
        for ddl in ddl_statements:
            cur.execute(ddl)
        conn.commit()
        cur.close()
    finally:
        conn.close()


# ============================================================
# Cluster Assignments CRUD
# ============================================================

def save_cluster_assignments(records):
    """
    UPSERT cluster assignments into idxsaham.stock_clusters.
    records: list of dicts with keys: symbol, cluster_id, cluster_label,
             avg_return, avg_volatility, avg_volume, momentum_score
    """
    if not records:
        return

    conn = get_raw_connection()
    try:
        cur = conn.cursor()
        query = """
            INSERT INTO idxsaham.stock_clusters
                (symbol, cluster_id, cluster_label, avg_return, avg_volatility, avg_volume, momentum_score, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (symbol) DO UPDATE SET
                cluster_id     = EXCLUDED.cluster_id,
                cluster_label  = EXCLUDED.cluster_label,
                avg_return     = EXCLUDED.avg_return,
                avg_volatility = EXCLUDED.avg_volatility,
                avg_volume     = EXCLUDED.avg_volume,
                momentum_score = EXCLUDED.momentum_score,
                updated_at     = NOW();
        """
        from psycopg2.extras import execute_batch
        params = [
            (r['symbol'], r['cluster_id'], r['cluster_label'],
             r['avg_return'], r['avg_volatility'], r['avg_volume'], r['momentum_score'])
            for r in records
        ]
        execute_batch(cur, query, params)
        conn.commit()
        cur.close()
    finally:
        conn.close()


def save_single_cluster_assignment(symbol, cluster_id, cluster_label,
                                   avg_return, avg_volatility, avg_volume, momentum_score):
    """UPSERT a single stock's cluster assignment."""
    save_cluster_assignments([{
        'symbol': symbol,
        'cluster_id': cluster_id,
        'cluster_label': cluster_label,
        'avg_return': avg_return,
        'avg_volatility': avg_volatility,
        'avg_volume': avg_volume,
        'momentum_score': momentum_score,
    }])


def load_cluster_assignments():
    """Load all cluster assignments. Returns dict {symbol: cluster_id}."""
    query = "SELECT symbol, cluster_id FROM idxsaham.stock_clusters ORDER BY symbol"
    df = pd.read_sql(query, engine)
    return dict(zip(df['symbol'], df['cluster_id']))


def load_cluster_assignments_full():
    """Load all cluster assignments with full info. Returns list of dicts."""
    query = "SELECT * FROM idxsaham.stock_clusters ORDER BY cluster_id, symbol"
    df = pd.read_sql(query, engine)
    return df.to_dict('records')


def load_cluster_members(cluster_id):
    """Load all symbols in a specific cluster."""
    query = text("SELECT symbol FROM idxsaham.stock_clusters WHERE cluster_id = :cid ORDER BY symbol")
    with engine.connect() as conn:
        result = conn.execute(query, {"cid": cluster_id})
        return [row[0] for row in result]


# ============================================================
# Cluster Metadata CRUD
# ============================================================

def save_cluster_metadata(records):
    """UPSERT cluster metadata into idxsaham.cluster_metadata."""
    if not records:
        return

    conn = get_raw_connection()
    try:
        cur = conn.cursor()
        query = """
            INSERT INTO idxsaham.cluster_metadata
                (cluster_id, cluster_label, n_members, centroid_return,
                 centroid_volatility, centroid_volume, centroid_momentum,
                 silhouette_score, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (cluster_id) DO UPDATE SET
                cluster_label       = EXCLUDED.cluster_label,
                n_members           = EXCLUDED.n_members,
                centroid_return     = EXCLUDED.centroid_return,
                centroid_volatility = EXCLUDED.centroid_volatility,
                centroid_volume     = EXCLUDED.centroid_volume,
                centroid_momentum   = EXCLUDED.centroid_momentum,
                silhouette_score    = EXCLUDED.silhouette_score,
                updated_at          = NOW();
        """
        from psycopg2.extras import execute_batch
        params = [
            (r['cluster_id'], r['cluster_label'], r['n_members'],
             r['centroid_return'], r['centroid_volatility'],
             r['centroid_volume'], r['centroid_momentum'],
             r['silhouette_score'])
            for r in records
        ]
        execute_batch(cur, query, params)
        conn.commit()
        cur.close()
    finally:
        conn.close()


def load_cluster_metadata():
    """Load all cluster metadata. Returns list of dicts."""
    query = "SELECT * FROM idxsaham.cluster_metadata ORDER BY cluster_id"
    df = pd.read_sql(query, engine)
    return df.to_dict('records')


# ============================================================
# Cluster Hyperparameters CRUD
# ============================================================

def save_cluster_hyperparams(records):
    """
    UPSERT tuned hyperparameters into idxsaham.cluster_hyperparams.
    records: list of dicts with keys: cluster_id, target_col, params (dict),
             best_score, n_trials, tuning_duration_sec
    """
    if not records:
        return

    conn = get_raw_connection()
    try:
        cur = conn.cursor()
        query = """
            INSERT INTO idxsaham.cluster_hyperparams
                (cluster_id, target_col, params, best_score, n_trials, tuning_duration_sec, updated_at)
            VALUES (%s, %s, %s::jsonb, %s, %s, %s, NOW())
            ON CONFLICT (cluster_id, target_col) DO UPDATE SET
                params              = EXCLUDED.params,
                best_score          = EXCLUDED.best_score,
                n_trials            = EXCLUDED.n_trials,
                tuning_duration_sec = EXCLUDED.tuning_duration_sec,
                updated_at          = NOW();
        """
        from psycopg2.extras import execute_batch
        import json as _json
        params = [
            (r['cluster_id'], r['target_col'], _json.dumps(r['params']),
             r['best_score'], r['n_trials'], r['tuning_duration_sec'])
            for r in records
        ]
        execute_batch(cur, query, params)
        conn.commit()
        cur.close()
    finally:
        conn.close()


def load_cluster_hyperparams(cluster_id, target_col):
    """Load tuned hyperparameters for a specific cluster and target. Returns dict or None."""
    query = text("""
        SELECT params FROM idxsaham.cluster_hyperparams
        WHERE cluster_id = :cid AND target_col = :tc
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"cid": cluster_id, "tc": target_col})
        row = result.fetchone()
        if row:
            import json as _json
            p = row[0]
            return _json.loads(p) if isinstance(p, str) else p
    return None


def load_all_hyperparams():
    """Load all hyperparameters. Returns list of dicts."""
    query = "SELECT * FROM idxsaham.cluster_hyperparams ORDER BY cluster_id, target_col"
    df = pd.read_sql(query, engine)
    return df.to_dict('records')


# ============================================================
# Forecast Accuracy CRUD
# ============================================================

def save_accuracy_records(records):
    """
    INSERT accuracy metrics into idxsaham.forecast_accuracy.
    records: list of dicts with keys: symbol, cluster_id, target_col, mae, rmse,
             mape, r2_score, accuracy_pct, confidence_level, n_train_samples,
             n_test_samples, forecast_horizon, model_version
    """
    if not records:
        return

    conn = get_raw_connection()
    try:
        cur = conn.cursor()
        query = """
            INSERT INTO idxsaham.forecast_accuracy
                (symbol, cluster_id, target_col, mae, rmse, mape, r2_score,
                 accuracy_pct, confidence_level, n_train_samples, n_test_samples,
                 forecast_horizon, model_version, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        from psycopg2.extras import execute_batch
        params = [
            (r['symbol'], r['cluster_id'], r['target_col'],
             r['mae'], r['rmse'], r['mape'], r['r2_score'],
             r['accuracy_pct'], r['confidence_level'],
             r['n_train_samples'], r['n_test_samples'],
             r['forecast_horizon'], r['model_version'])
            for r in records
        ]
        execute_batch(cur, query, params)
        conn.commit()
        cur.close()
    finally:
        conn.close()


def load_accuracy_by_symbol(symbol):
    """Load latest accuracy metrics for a symbol. Returns list of dicts (one per target)."""
    query = text("""
        SELECT DISTINCT ON (target_col)
            symbol, cluster_id, target_col, mae, rmse, mape, r2_score,
            accuracy_pct, confidence_level, n_train_samples, n_test_samples,
            forecast_horizon, model_version, created_at
        FROM idxsaham.forecast_accuracy
        WHERE symbol = :sym
        ORDER BY target_col, created_at DESC
    """)
    df = pd.read_sql(query, engine, params={"sym": symbol})
    return df.to_dict('records')


def load_accuracy_summary():
    """Load average accuracy per cluster. Returns list of dicts."""
    query = """
        WITH latest AS (
            SELECT DISTINCT ON (symbol, target_col)
                symbol, cluster_id, target_col, accuracy_pct, confidence_level,
                mape, r2_score, created_at
            FROM idxsaham.forecast_accuracy
            ORDER BY symbol, target_col, created_at DESC
        )
        SELECT
            cluster_id,
            target_col,
            COUNT(DISTINCT symbol) AS n_symbols,
            ROUND(AVG(accuracy_pct)::numeric, 2) AS avg_accuracy_pct,
            ROUND(AVG(mape)::numeric, 4) AS avg_mape,
            ROUND(AVG(r2_score)::numeric, 4) AS avg_r2
        FROM latest
        GROUP BY cluster_id, target_col
        ORDER BY cluster_id, target_col
    """
    df = pd.read_sql(query, engine)
    return df.to_dict('records')


def load_accuracy_dashboard():
    """
    Load full accuracy dashboard data: every symbol's latest accuracy + cluster info.
    Designed for UI/UX team consumption.
    """
    query = """
        WITH latest_acc AS (
            SELECT DISTINCT ON (fa.symbol, fa.target_col)
                fa.symbol,
                fa.cluster_id,
                fa.target_col,
                fa.mae,
                fa.rmse,
                fa.mape,
                fa.r2_score,
                fa.accuracy_pct,
                fa.confidence_level,
                fa.n_train_samples,
                fa.n_test_samples,
                fa.forecast_horizon,
                fa.model_version,
                fa.created_at
            FROM idxsaham.forecast_accuracy fa
            ORDER BY fa.symbol, fa.target_col, fa.created_at DESC
        )
        SELECT
            la.*,
            sc.cluster_label,
            cm.n_members AS cluster_size,
            cm.silhouette_score AS cluster_quality
        FROM latest_acc la
        LEFT JOIN idxsaham.stock_clusters sc ON la.symbol = sc.symbol
        LEFT JOIN idxsaham.cluster_metadata cm ON la.cluster_id = cm.cluster_id
        ORDER BY la.symbol, la.target_col
    """
    df = pd.read_sql(query, engine)
    return df.to_dict('records')