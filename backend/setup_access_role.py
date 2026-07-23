from user import get_connection


def setup_access_roles():
    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        # Tambahkan kolom access_role apabila belum tersedia.
        cur.execute(
            """
            ALTER TABLE idxsaham.users
            ADD COLUMN IF NOT EXISTS access_role VARCHAR(20)
            NOT NULL DEFAULT 'user';
            """
        )

        # Fariz dijadikan admin untuk pengujian.
        cur.execute(
            """
            UPDATE idxsaham.users
            SET access_role = 'admin'
            WHERE email = 'fariz@sahamscope.id';
            """
        )

        # Dewi tetap menjadi user biasa.
        cur.execute(
            """
            UPDATE idxsaham.users
            SET access_role = 'user'
            WHERE email = 'dewi@sahamscope.id';
            """
        )

        conn.commit()

        # Tampilkan hasilnya.
        cur.execute(
            """
            SELECT
                id,
                email,
                username,
                name,
                role,
                access_role,
                default_ticker
            FROM idxsaham.users
            ORDER BY id ASC;
            """
        )

        users = cur.fetchall()

        print("\nAccess role berhasil disiapkan.\n")

        for user in users:
            print(
                f"ID: {user[0]} | "
                f"Email: {user[1]} | "
                f"Nama: {user[3]} | "
                f"Profil: {user[4]} | "
                f"Access Role: {user[5]}"
            )

    except Exception as error:
        if conn:
            conn.rollback()

        print(f"Gagal menyiapkan access role: {error}")

    finally:
        if cur:
            cur.close()

        if conn:
            conn.close()


if __name__ == "__main__":
    setup_access_roles()