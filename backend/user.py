import os
import json
import psycopg2
import string
import random
import time
import uuid
import smtplib
import requests
import secrets
from email.mime.text import MIMEText
from flask import Blueprint, jsonify, request, render_template
from dotenv import load_dotenv, find_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from admin_routes import log_activity

load_dotenv(find_dotenv(), override=True)

# In-memory stores for password reset mechanism
_reset_codes = {}   # email -> { "code": code, "expires_at": timestamp }
_reset_tokens = {}  # temp_token -> email

user_bp = Blueprint("user_bp", __name__)


def _normalize_access_role(value):
    if value is None:
        return "user"

    normalized = str(value).strip().lower()
    return "admin" if normalized == "admin" else "user"


def get_connection():
    db_host = os.getenv("DB_HOST") or "db"
    db_port = int(os.getenv("DB_PORT") or 5432)
    db_name = os.getenv("DB_NAME") or "stockVision"
    db_user = os.getenv("DB_USER") or "stockvision"
    db_pass = os.getenv("DB_PASSWORD") or "stockvision_pass"
    try:
        return psycopg2.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_pass,
            port=db_port,
        )
    except psycopg2.OperationalError:
        # Fallback 1: Coba hostname 'db' (Docker container)
        try:
            return psycopg2.connect(
                host="db",
                database=db_name,
                user=db_user,
                password=db_pass,
                port=5432,
            )
        except psycopg2.OperationalError:
            # Fallback 2: Coba 'localhost'
            return psycopg2.connect(
                host="localhost",
                database=db_name,
                user=db_user,
                password=db_pass,
                port=5433,
            )


def _ensure_users_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("CREATE SCHEMA IF NOT EXISTS idxsaham;")
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS idxsaham.users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            username VARCHAR(100) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            name VARCHAR(255),
            access_role VARCHAR(20) NOT NULL DEFAULT 'user',
            default_ticker VARCHAR(20),
            phone_number VARCHAR(50),
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    cur.execute(
        """
        ALTER TABLE idxsaham.users
        ADD COLUMN IF NOT EXISTS access_role VARCHAR(20) NOT NULL DEFAULT 'user';
        """
    )
    cur.execute(
        """
        ALTER TABLE idxsaham.users
        ADD COLUMN IF NOT EXISTS phone_number VARCHAR(50);
        """
    )
    cur.execute(
        """
        UPDATE idxsaham.users
        SET access_role = CASE
            WHEN LOWER(COALESCE(access_role, '')) = 'admin' THEN 'admin'
            ELSE 'user'
        END
        WHERE access_role IS NULL OR LOWER(access_role) NOT IN ('user', 'admin');
        """
    )
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM idxsaham.users;")
    count = cur.fetchone()[0]
    if count == 0:
        users_to_seed = [
            {
                "email": "dewi@sahamscope.id",
                "username": "dewi",
                "password": generate_password_hash("password123"),
                "name": "Dewi",
                "access_role": "user",
                "default_ticker": "BBNI"
            },
            {
                "email": "admin@sahamscope.id",
                "username": "admin",
                "password": generate_password_hash("admin123"),
                "name": "Admin",
                "access_role": "admin",
                "default_ticker": "BBCA"
            }
        ]
        for u in users_to_seed:
            cur.execute(
                """
                INSERT INTO idxsaham.users (email, username, password, name, access_role, default_ticker)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (email) DO UPDATE SET
                    password = EXCLUDED.password,
                    name = EXCLUDED.name,
                    access_role = EXCLUDED.access_role;
                """,
                (u["email"], u["username"], u["password"], u["name"], u["access_role"], u["default_ticker"])
            )
        conn.commit()

    cur.execute(
        """
        INSERT INTO idxsaham.users (email, username, password, name, access_role, default_ticker)
        VALUES ('admin@sahamscope.id', 'admin', %s, 'Admin', 'admin', 'BBCA')
        ON CONFLICT (email) DO UPDATE SET
            password = EXCLUDED.password,
            name = EXCLUDED.name,
            access_role = EXCLUDED.access_role;
        """,
        (generate_password_hash("admin123"),)
    )
    conn.commit()

    cur.close()
    conn.close()


def create_user(payload):
    if not payload:
        raise ValueError("request body is required")

    required_fields = ["email", "username", "password"]
    for field in required_fields:
        if not payload.get(field):
            raise ValueError(f"{field} is required")

    password_hash = generate_password_hash(str(payload["password"]))
    access_role = _normalize_access_role(payload.get("access_role"))

    _ensure_users_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO idxsaham.users (email, username, password, name, access_role, default_ticker, phone_number)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, email, username, name, access_role, default_ticker, phone_number;
        """,
        (
            str(payload["email"]).strip().lower(),
            str(payload["username"]).strip(),
            password_hash,
            str(payload.get("name") or "").strip() or None,
            access_role,
            str(payload.get("default_ticker") or "").strip().upper() or None,
            str(payload.get("phone_number") or "").strip() or None,
        ),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": row[0],
        "email": row[1],
        "username": row[2],
        "name": row[3],
        "access_role": row[4],
        "default_ticker": row[5],
        "phone_number": row[6],
    }


def get_user(user_id):
    if not user_id:
        raise ValueError("user_id is required")

    _ensure_users_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, email, username, name, access_role, default_ticker, phone_number FROM idxsaham.users WHERE id = %s;",
        (user_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "email": row[1],
        "username": row[2],
        "name": row[3],
        "access_role": row[4],
        "default_ticker": row[5],
        "phone_number": row[6],
    }


def get_users():
    _ensure_users_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, email, username, name, access_role, default_ticker, phone_number FROM idxsaham.users ORDER BY id ASC;"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return [
        {
            "id": row[0],
            "email": row[1],
            "username": row[2],
            "name": row[3],
            "access_role": row[4],
            "default_ticker": row[5],
            "phone_number": row[6],
        }
        for row in rows
    ]


def _ensure_watchlists_table():
    """Pastikan tabel idxsaham.watchlists ada di PostgreSQL dan memiliki kolom name dan symbols."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("CREATE SCHEMA IF NOT EXISTS idxsaham;")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS idxsaham.watchlists (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name VARCHAR(255) NOT NULL DEFAULT 'Daftar Utama',
                symbols JSONB NOT NULL DEFAULT '[]',
                created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        cur.execute("ALTER TABLE idxsaham.watchlists ADD COLUMN IF NOT EXISTS name VARCHAR(255) NOT NULL DEFAULT 'Daftar Utama';")
        cur.execute("ALTER TABLE idxsaham.watchlists ADD COLUMN IF NOT EXISTS symbols JSONB NOT NULL DEFAULT '[]'::jsonb;")
        cur.execute("""
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'idxsaham' AND table_name = 'watchlists' AND column_name = 'stock_code';
        """)
        if cur.fetchone():
            cur.execute("ALTER TABLE idxsaham.watchlists ALTER COLUMN stock_code DROP NOT NULL;")

        cur.execute("CREATE INDEX IF NOT EXISTS idx_watchlists_user_id ON idxsaham.watchlists (user_id);")
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Warning: _ensure_watchlists_table skipped due to DB connection: {e}")



def get_user_unique_symbols(user_id, exclude_watchlist_id=None):
    _ensure_watchlists_table()
    conn = get_connection()
    cur = conn.cursor()
    if exclude_watchlist_id:
        cur.execute("SELECT symbols FROM idxsaham.watchlists WHERE user_id = %s AND id != %s;", (user_id, exclude_watchlist_id))
    else:
        cur.execute("SELECT symbols FROM idxsaham.watchlists WHERE user_id = %s;", (user_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    unique_symbols = set()
    for row in rows:
        syms = row[0]  # JSONB langsung menjadi list Python
        if isinstance(syms, str):
            syms = json.loads(syms)
        if isinstance(syms, list):
            for s in syms:
                if str(s).strip():
                    unique_symbols.add(str(s).strip().upper())
    return unique_symbols


def create_watchlist(user_id, payload):
    if not payload:
        raise ValueError("request body is required")
    name = str(payload.get("name") or "").strip()
    if not name:
        raise ValueError("name is required")
    symbols = payload.get("symbols") or []
    if not isinstance(symbols, list):
        raise ValueError("symbols must be a list")

    normalized_symbols = [str(s).strip().upper() for s in symbols if str(s).strip()]

    _ensure_watchlists_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO idxsaham.watchlists (user_id, name, symbols) VALUES (%s, %s, %s) RETURNING id;",
        (user_id, name, json.dumps(normalized_symbols))
    )
    watchlist_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return {
        "id": watchlist_id,
        "user_id": user_id,
        "name": name,
        "symbols": normalized_symbols
    }


def get_watchlists(user_id):
    _ensure_watchlists_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, name, symbols, created_at FROM idxsaham.watchlists WHERE user_id = %s ORDER BY id ASC;", (user_id,))
    rows = cur.fetchall()

    if not rows:
        default_name = "Daftar Utama"
        default_symbols = ["BBCA", "BBRI", "BMRI", "TLKM", "ANTM", "PTBA"]
        cur.execute(
            "INSERT INTO idxsaham.watchlists (user_id, name, symbols) VALUES (%s, %s, %s) RETURNING id, user_id, name, symbols, created_at;",
            (user_id, default_name, json.dumps(default_symbols))
        )
        conn.commit()
        cur.execute("SELECT id, user_id, name, symbols, created_at FROM idxsaham.watchlists WHERE user_id = %s ORDER BY id ASC;", (user_id,))
        rows = cur.fetchall()

    cur.close()
    conn.close()

    result = []
    for row in rows:
        syms = row[3]  # JSONB → Python list
        if isinstance(syms, str):
            try:
                syms = json.loads(syms)
            except Exception:
                syms = []
        result.append({
            "id": row[0],
            "user_id": row[1],
            "name": row[2],
            "symbols": syms if isinstance(syms, list) else [],
            "created_at": str(row[4]) if row[4] else None
        })
    return result


def get_watchlist(user_id, watchlist_id):
    _ensure_watchlists_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, name, symbols, created_at FROM idxsaham.watchlists WHERE user_id = %s AND id = %s;", (user_id, watchlist_id))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    syms = row[3]
    if isinstance(syms, str):
        try:
            syms = json.loads(syms)
        except Exception:
            syms = []

    return {
        "id": row[0],
        "user_id": row[1],
        "name": row[2],
        "symbols": syms if isinstance(syms, list) else [],
        "created_at": str(row[4]) if row[4] else None
    }


def update_watchlist(user_id, watchlist_id, payload):
    if not payload:
        raise ValueError("request body is required")

    _ensure_watchlists_table()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM idxsaham.watchlists WHERE user_id = %s AND id = %s;", (user_id, watchlist_id))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return None

    fields = []
    values = []

    if "name" in payload:
        name = str(payload["name"]).strip()
        if not name:
            raise ValueError("name cannot be empty")
        fields.append("name = %s")
        values.append(name)

    if "symbols" in payload:
        symbols = payload["symbols"]
        if not isinstance(symbols, list):
            raise ValueError("symbols must be a list")
        normalized_symbols = [str(s).strip().upper() for s in symbols if str(s).strip()]

        fields.append("symbols = %s")
        values.append(json.dumps(normalized_symbols))

    if not fields:
        cur.close()
        conn.close()
        raise ValueError("no fields provided for update")

    values.extend([user_id, watchlist_id])
    cur.execute(
        f"UPDATE idxsaham.watchlists SET {', '.join(fields)} WHERE user_id = %s AND id = %s;",
        values
    )
    conn.commit()
    cur.close()
    conn.close()

    return get_watchlist(user_id, watchlist_id)


def delete_watchlist(user_id, watchlist_id):
    _ensure_watchlists_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM idxsaham.watchlists WHERE user_id = %s AND id = %s;", (user_id, watchlist_id))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return None

    cur.execute("DELETE FROM idxsaham.watchlists WHERE user_id = %s AND id = %s;", (user_id, watchlist_id))
    conn.commit()
    cur.close()
    conn.close()
    return {"id": watchlist_id, "deleted": True}


def update_user(user_id, payload):
    if not user_id:
        raise ValueError("user_id is required")

    if not payload:
        raise ValueError("request body is required")

    _ensure_users_table()
    conn = get_connection()
    cur = conn.cursor()

    fields = []
    values = []

    if "email" in payload:
        fields.append("email = %s")
        values.append(str(payload["email"]).strip().lower())
    if "username" in payload:
        fields.append("username = %s")
        values.append(str(payload["username"]).strip())
    if "password" in payload:
        fields.append("password = %s")
        values.append(str(payload["password"]))
    if "name" in payload:
        fields.append("name = %s")
        values.append(str(payload.get("name") or "").strip() or None)
    if "access_role" in payload:
        fields.append("access_role = %s")
        values.append(_normalize_access_role(payload.get("access_role")))
    if "default_ticker" in payload:
        fields.append("default_ticker = %s")
        values.append(str(payload.get("default_ticker") or "").strip().upper() or None)
    if "phone_number" in payload:
        fields.append("phone_number = %s")
        values.append(str(payload.get("phone_number") or "").strip() or None)

    if not fields:
        raise ValueError("no fields provided for update")

    values.extend([user_id])
    cur.execute(
        f"UPDATE idxsaham.users SET {', '.join(fields)} WHERE id = %s RETURNING id, email, username, name, access_role, default_ticker, phone_number;",
        values,
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "email": row[1],
        "username": row[2],
        "name": row[3],
        "access_role": row[4],
        "default_ticker": row[5],
        "phone_number": row[6],
    }


def login_user(payload):
    if not payload:
        raise ValueError("request body is required")

    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")

    if not email or not password:
        raise ValueError("email and password are required")

    _ensure_users_table()

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            email,
            username,
            name,
            access_role,
            default_ticker,
            phone_number,
            password
        FROM idxsaham.users
        WHERE email = %s;
        """,
        (email,),
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return None

    (
        user_id,
        email_value,
        username,
        name,
        access_role,
        default_ticker,
        phone_number,
        stored_hash,
    ) = row

    if not check_password_hash(stored_hash, password):
        return None

    return {
        "id": user_id,
        "email": email_value,
        "username": username,
        "name": name,
        "access_role": access_role,
        "default_ticker": default_ticker,
        "phone_number": phone_number,
    }


def delete_user(user_id):
    if not user_id:
        raise ValueError("user_id is required")

    _ensure_users_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM idxsaham.users WHERE id = %s RETURNING id;", (user_id,))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return {"id": row[0], "deleted": True} if row else {"id": user_id, "deleted": False}


@user_bp.route("/users", methods=["POST"])
def create_user_route():
    payload = request.get_json(silent=True) or {}
    user = create_user(payload)
    try:
        send_registration_email(user["email"], user.get("name"), user.get("username"))
    except Exception as e:
        print(f"[SMTP] Error sending registration notification: {e}")
    return jsonify(user), 201


@user_bp.route("/users", methods=["GET"])
def list_users_route():
    return jsonify(get_users())


@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user_route(user_id):
    user = get_user(user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404
    return jsonify(user)


@user_bp.route("/users/<int:user_id>", methods=["PUT"])
def update_user_route(user_id):
    payload = request.get_json(silent=True) or {}
    user = update_user(user_id, payload)
    if not user:
        return jsonify({"error": "user not found"}), 404
    return jsonify(user)


@user_bp.route("/users/<int:user_id>/watchlists", methods=["GET"])
def list_watchlists_route(user_id):
    return jsonify(get_watchlists(user_id))


@user_bp.route("/users/<int:user_id>/watchlist-quota", methods=["GET"])
def get_watchlist_quota_route(user_id):
    symbols = get_user_unique_symbols(user_id)
    return jsonify({
        "user_id": user_id,
        "unique_symbols": sorted(list(symbols)),
        "used_quota": len(symbols),
        "max_quota": None,
        "remaining_quota": None,
        "is_unlimited": True
    })


@user_bp.route("/users/<int:user_id>/watchlists", methods=["POST"])
def create_watchlist_route(user_id):
    payload = request.get_json(silent=True) or {}
    try:
        wl = create_watchlist(user_id, payload)
        return jsonify(wl), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@user_bp.route("/users/<int:user_id>/watchlists/<int:watchlist_id>", methods=["GET"])
def get_watchlist_route(user_id, watchlist_id):
    wl = get_watchlist(user_id, watchlist_id)
    if not wl:
        return jsonify({"error": "watchlist not found"}), 404
    return jsonify(wl)


@user_bp.route("/users/<int:user_id>/watchlists/<int:watchlist_id>", methods=["PUT"])
def update_watchlist_route(user_id, watchlist_id):
    payload = request.get_json(silent=True) or {}
    try:
        wl = update_watchlist(user_id, watchlist_id, payload)
        if not wl:
            return jsonify({"error": "watchlist not found"}), 404
        return jsonify(wl)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@user_bp.route("/users/<int:user_id>/watchlists/<int:watchlist_id>", methods=["DELETE"])
def delete_watchlist_route(user_id, watchlist_id):
    result = delete_watchlist(user_id, watchlist_id)
    if not result:
        return jsonify({"error": "watchlist not found"}), 404
    return jsonify(result)


@user_bp.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user_route(user_id):
    result = delete_user(user_id)
    if not result.get("deleted"):
        return jsonify({"error": "user not found"}), 404
    return jsonify(result)


@user_bp.route("/users/login", methods=["POST"])
def login_user_route():
    payload = request.get_json(silent=True) or {}

    user = login_user(payload)

    if not user:
        return jsonify({
            "error": "invalid credentials"
        }), 401

    log_activity(
        user["id"],
        "LOGIN",
        "User berhasil login"
    )

    return jsonify(user)

@user_bp.route("/users/logout", methods=["POST"])
def logout_user_route():
    payload = request.get_json(silent=True) or {}

    user_id = payload.get("user_id")

    if user_id:
        log_activity(
            user_id,
            "LOGOUT",
            "User melakukan logout"
        )

    return jsonify({
        "message": "Logout berhasil"
    })


def send_reset_email(email, code):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)
    
    subject = "Kode Verifikasi Reset Password stockVision"
    body = f"Kode verifikasi reset password Anda adalah: {code}\nKode ini berlaku selama 5 menit."
    
    if smtp_host and smtp_port and smtp_user and smtp_pass:
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = smtp_from
            msg["To"] = email
            
            # Send via SMTP
            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, [email], msg.as_string())
            print(f"[SMTP] Reset code sent to {email} successfully.")
            return True
        except Exception as e:
            print(f"[SMTP] Error sending email via SMTP: {e}")
            return False
    else:
        # Fallback simulation
        print(f"\n==========================================")
        print(f"[SMTP SIMULATION] To: {email}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        print(f"==========================================\n")
        return False


def _make_display_name(name, username, email):
    if name and str(name).strip():
        return str(name).strip()
    if username and str(username).strip():
        return str(username).strip()
    return email.split("@")[0] if email and "@" in email else email


def send_email(subject, body, email):
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    smtp_from = os.getenv("SMTP_FROM", smtp_user)

    if smtp_host and smtp_port and smtp_user and smtp_pass:
        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = smtp_from
            msg["To"] = email

            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, [email], msg.as_string())

            print(f"[SMTP] Notification sent to {email} successfully.")
            return True
        except Exception as e:
            print(f"[SMTP] Error sending notification email to {email}: {e}")
            return False
    else:
        print(f"\n==========================================")
        print(f"[SMTP SIMULATION] To: {email}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        print(f"==========================================\n")
        return False


def send_registration_email(email, name=None, username=None):
    display_name = _make_display_name(name, username, email)
    subject = "Selamat datang di stockVision"
    body = (
        f"Halo {display_name},\n\n"
        f"Terima kasih telah mendaftar di stockVision. Akun Anda telah berhasil dibuat dengan email {email}.\n\n"
        "Selamat datang dan selamat menggunakan stockVision!"
    )
    return send_email(subject, body, email)


def send_google_login_email(email, name=None, is_new=False):
    display_name = _make_display_name(name, None, email)
    if is_new:
        subject = "Akun stockVision berhasil dibuat melalui Google"
        body = (
            f"Halo {display_name},\n\n"
            f"Akun stockVision Anda telah berhasil dibuat menggunakan akun Google {email}.\n"
            "Anda dapat masuk kembali menggunakan Google yang sama.\n\n"
            "Selamat datang di stockVision!"
        )
    else:
        subject = "Login Google berhasil di stockVision"
        body = (
            f"Halo {display_name},\n\n"
            f"Anda baru saja berhasil login ke stockVision menggunakan akun Google {email}.\n\n"
            "Jika ini bukan Anda, segera hubungi administrator."
        )
    return send_email(subject, body, email)


@user_bp.route("/users/reset-password/send-code", methods=["POST"])
def send_code_route():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "Email wajib diisi"}), 400
        
    _ensure_users_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM idxsaham.users WHERE email = %s;", (email,))
    user_exists = cur.fetchone()
    cur.close()
    conn.close()
    
    if not user_exists:
        return jsonify({"error": "Email tidak terdaftar di database"}), 404
        
    # Generate 6-char alphanumeric code (uppercase letters + numbers)
    code = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    _reset_codes[email] = {
        "code": code,
        "expires_at": time.time() + 300 # 5 minutes
    }
    
    # Send email (or simulate)
    smtp_sent = send_reset_email(email, code)
    
    resp = {
        "message": "Kode verifikasi telah dikirim ke email.",
        "simulated": not smtp_sent
    }
    if not smtp_sent:
        resp["debug_code"] = code # helper for testing in browser without console check
        
    return jsonify(resp)


@user_bp.route("/users/reset-password/verify-code", methods=["POST"])
def verify_code_route():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email") or "").strip().lower()
    code = str(payload.get("code") or "").strip().upper()
    
    if not email or not code:
        return jsonify({"error": "Email dan kode verifikasi wajib diisi"}), 400
        
    entry = _reset_codes.get(email)
    if not entry:
        return jsonify({"error": "Silakan kirim kode terlebih dahulu"}), 400
        
    if time.time() > entry["expires_at"]:
        # Expired
        _reset_codes.pop(email, None)
        return jsonify({"error": "Kode verifikasi telah kadaluwarsa (berlaku 5 menit)"}), 400
        
    if entry["code"] != code:
        return jsonify({"error": "Kode verifikasi salah"}), 400
        
    # Validation succeeded, remove code and generate temp reset token
    _reset_codes.pop(email, None)
    temp_token = str(uuid.uuid4())
    _reset_tokens[temp_token] = email
    
    return jsonify({
        "message": "Autentikasi berhasil.",
        "token": temp_token
    })


@user_bp.route("/users/reset-password/reset", methods=["POST"])
def reset_password_route():
    payload = request.get_json(silent=True) or {}
    token = str(payload.get("token") or "").strip()
    new_password = str(payload.get("password") or "")
    
    if not token or not new_password:
        return jsonify({"error": "Token dan kata sandi baru wajib diisi"}), 400
        
    if len(new_password) < 6:
        return jsonify({"error": "Kata sandi minimal 6 karakter"}), 400
        
    email = _reset_tokens.get(token)
    if not email:
        return jsonify({"error": "Token reset password tidak valid atau telah kadaluwarsa"}), 400
        
    # Update password in DB
    password_hash = generate_password_hash(new_password)
    
    _ensure_users_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE idxsaham.users SET password = %s WHERE email = %s RETURNING id;",
        (password_hash, email)
    )
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if not updated:
        return jsonify({"error": "Gagal mereset kata sandi. Pengguna tidak ditemukan."}), 404
        
    # Revoke token
    _reset_tokens.pop(token, None)
    
    return jsonify({
        "message": "Kata sandi berhasil direset. Silakan masuk kembali."
    })


@user_bp.route("/users/google-login", methods=["POST"])
def google_login_route():
    payload = request.get_json(silent=True) or {}
    id_token = payload.get("id_token")
    if not id_token:
        return jsonify({"error": "id_token is required"}), 400

    # Verify token with Google API
    try:
        res = requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}",
            timeout=5
        )
        if res.status_code != 200:
            return jsonify({"error": "Invalid Google token"}), 400
        
        token_info = res.json()
    except Exception as e:
        return jsonify({"error": f"Failed to verify token with Google: {str(e)}"}), 500

    # Check client ID/audience
    expected_client_id = "984699715154-avv957f6q8sncnjglfe00d4ksrg01ifl.apps.googleusercontent.com"
    aud = token_info.get("aud")
    if aud != expected_client_id:
        return jsonify({"error": "Token audience mismatch"}), 400

    email = token_info.get("email")
    if not email:
        return jsonify({"error": "Email not found in token"}), 400
    
    email = email.strip().lower()
    name = token_info.get("name") or token_info.get("given_name") or email.split("@")[0]

    _ensure_users_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, email, username, name, access_role, default_ticker, phone_number FROM idxsaham.users WHERE email = %s;",
        (email,),
    )
    row = cur.fetchone()

    if row:
        user_id, email_val, username, name_val, access_role, default_ticker, phone_number = row
        cur.close()
        conn.close()
        try:
            send_google_login_email(email_val, name_val, is_new=False)
        except Exception as e:
            print(f"[SMTP] Error sending Google login notification: {e}")
        return jsonify({
            "id": user_id,
            "email": email_val,
            "username": username,
            "name": name_val,
            "access_role": access_role,
            "default_ticker": default_ticker,
            "phone_number": phone_number
        })
    else:
        # Create a new user since they don't exist
        # Generate unique username
        base_username = email.split("@")[0]
        base_username = "".join(c for c in base_username if c.isalnum() or c in "._")
        if not base_username:
            base_username = "user"
        
        username = base_username
        suffix_counter = 1
        while True:
            cur.execute("SELECT id FROM idxsaham.users WHERE username = %s;", (username,))
            if not cur.fetchone():
                break
            username = f"{base_username}{suffix_counter}"
            suffix_counter += 1

        # Generate random password hash (so it's not empty/null)
        random_pass = secrets.token_hex(16)
        password_hash = generate_password_hash(random_pass)

        # Insert new user
        cur.execute(
            """
            INSERT INTO idxsaham.users (email, username, password, name, access_role, default_ticker)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, email, username, name, access_role, default_ticker, phone_number;
            """,
            (email, username, password_hash, name, "user", "BBCA")
        )
        new_row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        try:
            send_google_login_email(new_row[1], new_row[3], is_new=True)
        except Exception as e:
            print(f"[SMTP] Error sending Google welcome notification: {e}")

        return jsonify({
            "id": new_row[0],
            "email": new_row[1],
            "username": new_row[2],
            "name": new_row[3],
            "access_role": new_row[4],
            "default_ticker": new_row[5],
            "phone_number": new_row[6]
        }), 201

@user_bp.route("/test-ui")
def test_ui():
    return render_template("test_ui.html")