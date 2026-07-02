-- =============================================================
-- DDL - Schema idxsaham
-- =============================================================

CREATE SCHEMA IF NOT EXISTS idxsaham;

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