import os
import psycopg2
from psycopg2.extras import execute_batch
import logging
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

logger = logging.getLogger(__name__)

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS idxsaham.analytics_results (
    symbol VARCHAR(10) NOT NULL,
    tanggal_analisis DATE NOT NULL,
    last_close NUMERIC(15,2),
    change_pct_1d NUMERIC(8,4),
    change_pct_7d NUMERIC(8,4),
    change_pct_30d NUMERIC(8,4),
    rsi_14 NUMERIC(8,4),
    rsi_signal VARCHAR(20),
    macd_line NUMERIC(15,4),
    macd_signal NUMERIC(15,4),
    macd_hist NUMERIC(15,4),
    macd_trend VARCHAR(20),
    sma_5 NUMERIC(15,2),
    sma_20 NUMERIC(15,2),
    sma_50 NUMERIC(15,2),
    sma_200 NUMERIC(15,2),
    ema_12 NUMERIC(15,2),
    ema_26 NUMERIC(15,2),
    bb_upper NUMERIC(15,2),
    bb_middle NUMERIC(15,2),
    bb_lower NUMERIC(15,2),
    atr_14 NUMERIC(15,2),
    pivot_point NUMERIC(15,2),
    support_1 NUMERIC(15,2),
    support_2 NUMERIC(15,2),
    resistance_1 NUMERIC(15,2),
    resistance_2 NUMERIC(15,2),
    volatility_ann NUMERIC(8,4),
    sharpe_ratio NUMERIC(8,4),
    sortino_ratio NUMERIC(8,4),
    max_drawdown NUMERIC(8,4),
    beta NUMERIC(8,4),
    cagr NUMERIC(8,4),
    net_foreign_flow_1d NUMERIC(20,2),
    net_foreign_flow_5d NUMERIC(20,2),
    net_foreign_flow_20d NUMERIC(20,2),
    big_money_status VARCHAR(50),
    broker_hhi NUMERIC(8,4),
    insider_net_vol_30d NUMERIC(20,2),
    insider_sentiment_score NUMERIC(8,4),
    insider_trx_count INT,
    market_breadth_score NUMERIC(8,4),
    composite_sentiment_score NUMERIC(8,4),
    composite_sentiment_label VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (symbol, tanggal_analisis)
);

CREATE INDEX IF NOT EXISTS idx_analytics_results_symbol ON idxsaham.analytics_results (symbol);
CREATE INDEX IF NOT EXISTS idx_analytics_results_tanggal ON idxsaham.analytics_results (tanggal_analisis);
"""

UPSERT_SQL = """
INSERT INTO idxsaham.analytics_results (
    symbol, tanggal_analisis, last_close, change_pct_1d, change_pct_7d, change_pct_30d,
    rsi_14, rsi_signal, macd_line, macd_signal, macd_hist, macd_trend,
    sma_5, sma_20, sma_50, sma_200, ema_12, ema_26,
    bb_upper, bb_middle, bb_lower, atr_14,
    pivot_point, support_1, support_2, resistance_1, resistance_2,
    volatility_ann, sharpe_ratio, sortino_ratio, max_drawdown, beta, cagr,
    net_foreign_flow_1d, net_foreign_flow_5d, net_foreign_flow_20d, big_money_status, broker_hhi,
    insider_net_vol_30d, insider_sentiment_score, insider_trx_count,
    market_breadth_score, composite_sentiment_score, composite_sentiment_label
) VALUES (
    %(symbol)s, %(tanggal_analisis)s, %(last_close)s, %(change_pct_1d)s, %(change_pct_7d)s, %(change_pct_30d)s,
    %(rsi_14)s, %(rsi_signal)s, %(macd_line)s, %(macd_signal)s, %(macd_hist)s, %(macd_trend)s,
    %(sma_5)s, %(sma_20)s, %(sma_50)s, %(sma_200)s, %(ema_12)s, %(ema_26)s,
    %(bb_upper)s, %(bb_middle)s, %(bb_lower)s, %(atr_14)s,
    %(pivot_point)s, %(support_1)s, %(support_2)s, %(resistance_1)s, %(resistance_2)s,
    %(volatility_ann)s, %(sharpe_ratio)s, %(sortino_ratio)s, %(max_drawdown)s, %(beta)s, %(cagr)s,
    %(net_foreign_flow_1d)s, %(net_foreign_flow_5d)s, %(net_foreign_flow_20d)s, %(big_money_status)s, %(broker_hhi)s,
    %(insider_net_vol_30d)s, %(insider_sentiment_score)s, %(insider_trx_count)s,
    %(market_breadth_score)s, %(composite_sentiment_score)s, %(composite_sentiment_label)s
) ON CONFLICT (symbol, tanggal_analisis) DO UPDATE SET
    last_close = EXCLUDED.last_close,
    change_pct_1d = EXCLUDED.change_pct_1d,
    change_pct_7d = EXCLUDED.change_pct_7d,
    change_pct_30d = EXCLUDED.change_pct_30d,
    rsi_14 = EXCLUDED.rsi_14,
    rsi_signal = EXCLUDED.rsi_signal,
    macd_line = EXCLUDED.macd_line,
    macd_signal = EXCLUDED.macd_signal,
    macd_hist = EXCLUDED.macd_hist,
    macd_trend = EXCLUDED.macd_trend,
    sma_5 = EXCLUDED.sma_5,
    sma_20 = EXCLUDED.sma_20,
    sma_50 = EXCLUDED.sma_50,
    sma_200 = EXCLUDED.sma_200,
    ema_12 = EXCLUDED.ema_12,
    ema_26 = EXCLUDED.ema_26,
    bb_upper = EXCLUDED.bb_upper,
    bb_middle = EXCLUDED.bb_middle,
    bb_lower = EXCLUDED.bb_lower,
    atr_14 = EXCLUDED.atr_14,
    pivot_point = EXCLUDED.pivot_point,
    support_1 = EXCLUDED.support_1,
    support_2 = EXCLUDED.support_2,
    resistance_1 = EXCLUDED.resistance_1,
    resistance_2 = EXCLUDED.resistance_2,
    volatility_ann = EXCLUDED.volatility_ann,
    sharpe_ratio = EXCLUDED.sharpe_ratio,
    sortino_ratio = EXCLUDED.sortino_ratio,
    max_drawdown = EXCLUDED.max_drawdown,
    beta = EXCLUDED.beta,
    cagr = EXCLUDED.cagr,
    net_foreign_flow_1d = EXCLUDED.net_foreign_flow_1d,
    net_foreign_flow_5d = EXCLUDED.net_foreign_flow_5d,
    net_foreign_flow_20d = EXCLUDED.net_foreign_flow_20d,
    big_money_status = EXCLUDED.big_money_status,
    broker_hhi = EXCLUDED.broker_hhi,
    insider_net_vol_30d = EXCLUDED.insider_net_vol_30d,
    insider_sentiment_score = EXCLUDED.insider_sentiment_score,
    insider_trx_count = EXCLUDED.insider_trx_count,
    market_breadth_score = EXCLUDED.market_breadth_score,
    composite_sentiment_score = EXCLUDED.composite_sentiment_score,
    composite_sentiment_label = EXCLUDED.composite_sentiment_label,
    created_at = NOW();
"""

def _get_connection():
    h = os.getenv("DB_HOST", "localhost")
    db = os.getenv("DB_NAME", "stockVision")
    u = os.getenv("DB_USER", "stockvision")
    p = os.getenv("DB_PASSWORD", "stockvision_pass")
    port = int(os.getenv("DB_PORT", 5433))
    try:
        return psycopg2.connect(host=h, database=db, user=u, password=p, port=port)
    except psycopg2.OperationalError:
        targets = [("db", 5432), ("localhost", 5433), ("localhost", 5434), ("127.0.0.1", 5433)]
        for host_cand, port_cand in targets:
            try:
                return psycopg2.connect(host=host_cand, database=db, user=u, password=p, port=port_cand)
            except psycopg2.OperationalError:
                continue
        raise


def save_analytics_results(results_list: list) -> int:
    """Simpan atau perbarui list hasil analisis ke database."""
    if not results_list:
        return 0

    conn = None
    try:
        conn = _get_connection()
        cur = conn.cursor()
        cur.execute(CREATE_TABLE_SQL)

        execute_batch(cur, UPSERT_SQL, results_list)
        conn.commit()
        count = len(results_list)
        cur.close()
        logger.info(f"Berhasil menyimpan {count} record analitik ke idxsaham.analytics_results")
        return count
    except Exception as e:
        logger.error(f"Error menyimpan analytics results: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()
