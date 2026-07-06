import psycopg2
import os
from dotenv import load_dotenv, find_dotenv

# Load environment variables from .env file (searching upwards if necessary)
load_dotenv(find_dotenv())

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    database=os.getenv("DB_NAME", "postgres"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD")
)

cur = conn.cursor()

year = 2026

query = f"""
INSERT INTO idxsaham.trading_calendar (trading_date, is_trading_day)
SELECT d::date,
       CASE 
           WHEN EXTRACT(DOW FROM d) IN (0,6) THEN FALSE
           ELSE TRUE
       END
FROM generate_series(
    '{year}-01-01'::date,
    '{year}-12-31'::date,
    '1 day'
) d
ON CONFLICT DO NOTHING;
"""

cur.execute(query)
conn.commit()

cur.close()
conn.close()

print("✅ Kalender berhasil dibuat!")