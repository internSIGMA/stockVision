-- =============================================================
-- DDL - Schema idxsaham
-- =============================================================

CREATE SCHEMA IF NOT EXISTS idxsaham;

-- =============================================================
-- TABLE: idxsaham.watchlists
-- Daftar pantau emiten per user (menggantikan SQLite watchlist.db)
-- =============================================================
CREATE TABLE IF NOT EXISTS idxsaham.watchlists (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    symbols JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_watchlists_user_id ON idxsaham.watchlists (user_id);

-- =============================================================
-- TABLE: idxsaham.trading_calendar
-- Kalender hari trading bursa
-- =============================================================
CREATE TABLE IF NOT EXISTS idxsaham.trading_calendar (
    trading_date   DATE        NOT NULL,
    is_trading_day BOOLEAN     NOT NULL DEFAULT TRUE,
    keterangan     VARCHAR(255),
    CONSTRAINT pk_trading_calendar PRIMARY KEY (trading_date)
);

-- =============================================================
-- TABLE: idxsaham.broker
-- Master data broker
-- =============================================================
CREATE TABLE IF NOT EXISTS idxsaham.broker (
    kode           VARCHAR(10)     NOT NULL,
    namaperusahaan VARCHAR(255),
    nilai          NUMERIC(20, 2),
    CONSTRAINT pk_broker PRIMARY KEY (kode)
);

-- =============================================================
-- TABLE: idxsaham.broker_activity
-- Aktivitas transaksi broker harian (BUY / SELL)
-- =============================================================
CREATE TABLE IF NOT EXISTS  idxsaham.broker_activity (
	id bigserial NOT NULL,
	kodesaham varchar(10) NOT NULL,
	kodebroker varchar(10) NOT NULL,
	tipebroker varchar(50) NULL,
	tanggal date NOT NULL,
	nilairp numeric(20, 2) DEFAULT 0 NOT NULL,
	lot int8 DEFAULT 0 NOT NULL,
	avgprice numeric(15, 2) DEFAULT 0 NOT NULL,
	frekuensi int8 DEFAULT 0 NOT NULL,
	aksi varchar(10) NOT NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT pk_broker_activity PRIMARY KEY (id),
	CONSTRAINT uq_broker_activity UNIQUE (tanggal, kodesaham, kodebroker, aksi)
);

CREATE INDEX IF NOT EXISTS idx_broker_activity_tanggal    ON idxsaham.broker_activity (tanggal);
CREATE INDEX IF NOT EXISTS idx_broker_activity_kodesaham  ON idxsaham.broker_activity (kodesaham);
CREATE INDEX IF NOT EXISTS idx_broker_activity_kodebroker ON idxsaham.broker_activity (kodebroker);

-- =============================================================
-- TABLE: idxsaham.insider_activity
-- Aktivitas transaksi pemegang saham mayor / insider
-- =============================================================
CREATE TABLE IF NOT EXISTS idxsaham.insider_activity (
	idtrx text NOT NULL,
	nama text NULL,
	saham text NULL,
	tanggal date NULL,
	aksi varchar(50) NULL,
	sebelumnya numeric NULL,
	sebelumnyapersen numeric NULL,
	sekarang numeric NULL,
	sekarangpersen numeric NULL,
	perubahan numeric NULL,
	perubahanpersen numeric NULL,
	harga varchar NULL,
	sumber varchar(255) NULL,
	kewarganegaraan varchar(50) NULL,
	broker varchar(10) NULL,
	badge text NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT pk_insider_activity PRIMARY KEY (idtrx)
);

CREATE INDEX IF NOT EXISTS idx_insider_activity_tanggal ON idxsaham.insider_activity (tanggal);
CREATE INDEX IF NOT EXISTS idx_insider_activity_saham   ON idxsaham.insider_activity (saham);

-- =============================================================
-- TABLE: idxsaham.stock_info
-- Info lengkap saham (snapshot harian per simbol)
-- =============================================================
CREATE TABLE idxsaham.stock_info (
	symbol varchar(10) NOT NULL,
	tanggal date NOT NULL,
	nama varchar(255) NULL,
	waktu_update varchar(50) NULL,
	waktu_terakhir varchar(50) NULL,
	exchange varchar(50) NULL,
	sektor varchar(255) NULL,
	sub_sektor varchar(255) NULL,
	tipe_perusahaan varchar(100) NULL,
	status varchar(50) NULL,
	harga numeric(15, 2) NULL,
	harga_sebelumnya numeric(15, 2) NULL,
	perubahan numeric(15, 2) NULL,
	perubahan_persen text NULL,
	volume int8 NULL,
	rata_rata numeric(15, 2) NULL,
	bid_price numeric(15, 2) NULL,
	bid_volume int8 NULL,
	offer_price numeric(15, 2) NULL,
	offer_volume int8 NULL,
	followers int4 NULL,
	indeks text NULL,
	status_pasar varchar(100) NULL,
	sisa_waktu_pasar varchar(50) NULL,
	corp_action_aktif bool NULL,
	corp_action_info text NULL,
	day_trade bool NULL,
	day_trade_multiplier numeric(10, 4) NULL,
	trading_limit bool NULL,
	haircut_persen text NULL,
	margin_trading bool NULL,
	margin_persen text NULL,
	tradeable bool NULL,
	uma bool NULL,
	created_at timestamp DEFAULT now() NOT NULL,
	updated_at timestamp DEFAULT now() NOT NULL,
	CONSTRAINT pk_stock_info PRIMARY KEY (symbol, tanggal)
);

CREATE INDEX IF NOT EXISTS idx_stock_info_tanggal ON idxsaham.stock_info (tanggal);
CREATE INDEX IF NOT EXISTS idx_stock_info_symbol  ON idxsaham.stock_info (symbol);

-- =============================================================
-- TABLE: idxsaham.ohlc_forecasting
-- =============================================================
CREATE TABLE IF NOT EXISTS idxsaham.ohlc_forecasting (
    symbol VARCHAR(10),
    tanggal DATE,
    open NUMERIC(15,2),
    high NUMERIC(15,2),
    low NUMERIC(15,2),
    close NUMERIC(15,2),
    adj_close NUMERIC(15,2),
    volume BIGINT,
    CONSTRAINT pk_ohlc_forecasting PRIMARY KEY (symbol, tanggal)
);

-- =============================================================
-- TABLE: idxsaham.stock_ohlc
-- =============================================================
CREATE TABLE IF NOT EXISTS idxsaham.stock_ohlc (
    symbol VARCHAR(10),
    tanggal DATE,
    open NUMERIC(15,2),
    high NUMERIC(15,2),
    low NUMERIC(15,2),
    close NUMERIC(15,2),
    volume BIGINT,
    foreign_buy NUMERIC(20,2),
    foreign_sell NUMERIC(20,2),
    foreign_flow NUMERIC(20,2),
    PRIMARY KEY (symbol, tanggal)
);

-- =============================================================
-- TABLE: idxsaham.stock_forecasting
-- =============================================================
CREATE TABLE IF NOT EXISTS idxsaham.stock_forecasting (
    symbol VARCHAR(10),
    tanggal DATE,
    open NUMERIC(15,2),
    high NUMERIC(15,2),
    low NUMERIC(15,2),
    close NUMERIC(15,2),
    volume BIGINT,
    PRIMARY KEY (symbol, tanggal)
);

-- =============================================================
-- TABLE: idxsaham.crawl_logs
-- =============================================================
CREATE TABLE IF NOT EXISTS idxsaham.crawl_logs (
    id BIGSERIAL PRIMARY KEY,
    job_type VARCHAR(50),
    target VARCHAR(50),
    tanggal_target DATE,
    status VARCHAR(20),
    records_count INT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =============================================================
-- TABLE: idxsaham.analytics_results
-- Snapshot & cached metrics dari Analytics Processing Layer
-- =============================================================
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