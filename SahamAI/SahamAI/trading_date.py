import psycopg2

conn = psycopg2.connect(
    host= "localhost",
    database= "postgres",
    user= "postgres",
    password= "Sigma#2026"
)

cur = conn.cursor()

year = 2026

query = f"""
INSERT INTO idxsaham.trading_calendar (trading_date, is_trading_day)
SELECT d::date,
       CASE 
           WHEN EXTRACT(DOW FROM d) IN (0,6) THEN FALSE
           WHEN d IN (SELECT holiday_date FROM idxsaham.holidays) THEN FALSE
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