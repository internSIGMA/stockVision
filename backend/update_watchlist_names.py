import psycopg2
import os
from user import get_connection

try:
    conn = get_connection()
    cur = conn.cursor()
    
    # 1. Ubah "Daftar Pantau Utama" jadi "Daftar Utama"
    cur.execute("UPDATE idxsaham.watchlists SET name = 'Daftar Utama' WHERE name = 'Daftar Pantau Utama';")
    
    # 2. Ubah "Daftar Pantau 2", "Daftar Pantau 3", dsb. jadi "Daftar 2", "Daftar 3", dst.
    cur.execute("UPDATE idxsaham.watchlists SET name = REPLACE(name, 'Daftar Pantau ', 'Daftar ') WHERE name LIKE 'Daftar Pantau %';")
    
    conn.commit()
    cur.close()
    conn.close()
    print("Berhasil mengupdate nama watchlist di database.")
except Exception as e:
    print(f"Error: {e}")
