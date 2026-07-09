import os
import psycopg2
from flask import Blueprint, jsonify, request, render_template
from dotenv import load_dotenv, find_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv(find_dotenv())

user_bp = Blueprint("user_bp", __name__)


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        port=int(os.getenv("DB_PORT", 5432)),
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
            role VARCHAR(255),
            default_ticker VARCHAR(20),
            favorites TEXT[] DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.commit()

    # Check if table is empty
    cur.execute("SELECT COUNT(*) FROM idxsaham.users;")
    count = cur.fetchone()[0]
    if count == 0:
        # Seed default users
        users_to_seed = [
            {
                "email": "fariz@sahamscope.id",
                "username": "fariz",
                "password": generate_password_hash("password123"),
                "name": "Fariz",
                "role": "Trader — Perbankan",
                "default_ticker": "BBCA",
                "favorites": ["BBCA", "BBRI", "BMRI", "TLKM", "ANTM", "PTBA", "ADRO", "INDF", "SMGR"]
            },
            {
                "email": "dewi@sahamscope.id",
                "username": "dewi",
                "password": generate_password_hash("password123"),
                "name": "Dewi",
                "role": "Trader — Properti & Energi",
                "default_ticker": "BBNI",
                "favorites": ["BBNI", "BJBR", "ASII", "GOTO", "SMRA", "ASRI", "CTRA", "INCO", "MAPI"]
            }
        ]
        for u in users_to_seed:
            cur.execute(
                """
                INSERT INTO idxsaham.users (email, username, password, name, role, default_ticker, favorites)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
                """,
                (u["email"], u["username"], u["password"], u["name"], u["role"], u["default_ticker"], u["favorites"])
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

    _ensure_users_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO idxsaham.users (email, username, password, name, role, default_ticker, favorites)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, email, username, name, role, default_ticker, favorites;
        """,
        (
            str(payload["email"]).strip().lower(),
            str(payload["username"]).strip(),
            password_hash,
            str(payload.get("name") or "").strip() or None,
            str(payload.get("role") or "").strip() or None,
            str(payload.get("default_ticker") or "").strip().upper() or None,
            [str(item).strip().upper() for item in (payload.get("favorites") or []) if str(item).strip()],
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
        "role": row[4],
        "default_ticker": row[5],
        "favorites": list(row[6]) if row[6] else [],
    }


def get_user(user_id):
    if not user_id:
        raise ValueError("user_id is required")

    _ensure_users_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, email, username, name, role, default_ticker, favorites FROM idxsaham.users WHERE id = %s;",
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
        "role": row[4],
        "default_ticker": row[5],
        "favorites": list(row[6]) if row[6] else [],
    }


def get_users():
    _ensure_users_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, email, username, name, role, default_ticker, favorites FROM idxsaham.users ORDER BY id ASC;"
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
            "role": row[4],
            "default_ticker": row[5],
            "favorites": list(row[6]) if row[6] else [],
        }
        for row in rows
    ]


def get_user_favorites(user_id):
    if not user_id:
        raise ValueError("user_id is required")

    user = get_user(user_id)
    if not user:
        return None
    return {"user_id": user_id, "favorites": user.get("favorites", [])}


def update_user_favorites(user_id, payload):
    if not user_id:
        raise ValueError("user_id is required")

    if not payload:
        raise ValueError("request body is required")

    favorites = payload.get("favorites")
    if favorites is None:
        raise ValueError("favorites is required")

    normalized_favorites = [
        str(item).strip().upper() for item in favorites if str(item).strip()
    ]

    _ensure_users_table()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE idxsaham.users SET favorites = %s WHERE id = %s RETURNING id, favorites;",
        (normalized_favorites, user_id),
    )
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not row:
        return None

    return {"user_id": row[0], "favorites": list(row[1]) if row[1] else []}


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
    if "role" in payload:
        fields.append("role = %s")
        values.append(str(payload.get("role") or "").strip() or None)
    if "default_ticker" in payload:
        fields.append("default_ticker = %s")
        values.append(str(payload.get("default_ticker") or "").strip().upper() or None)
    if "favorites" in payload:
        fields.append("favorites = %s")
        values.append([str(item).strip().upper() for item in (payload.get("favorites") or []) if str(item).strip()])

    if not fields:
        raise ValueError("no fields provided for update")

    values.extend([user_id])
    cur.execute(
        f"UPDATE idxsaham.users SET {', '.join(fields)} WHERE id = %s RETURNING id, email, username, name, role, default_ticker, favorites;",
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
        "role": row[4],
        "default_ticker": row[5],
        "favorites": list(row[6]) if row[6] else [],
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
        "SELECT id, email, username, name, role, default_ticker, favorites, password FROM idxsaham.users WHERE email = %s;",
        (email,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    user_id, email_value, username, name, role, default_ticker, favorites, stored_hash = row
    if not check_password_hash(stored_hash, password):
        return None

    return {
        "id": user_id,
        "email": email_value,
        "username": username,
        "name": name,
        "role": role,
        "default_ticker": default_ticker,
        "favorites": list(favorites) if favorites else [],
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


@user_bp.route("/users/<int:user_id>/favorites", methods=["GET", "PUT"])
def favorite_handler(user_id):
    if request.method == "GET":
        favorites = get_user_favorites(user_id)
        if not favorites:
            return jsonify({"error": "user not found"}), 404
        return jsonify(favorites)

    payload = request.get_json(silent=True) or {}
    result = update_user_favorites(user_id, payload)
    if not result:
        return jsonify({"error": "user not found"}), 404
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
        return jsonify({"error": "invalid credentials"}), 401
    return jsonify(user)


@user_bp.route("/test-ui")
def test_ui():
    return render_template("test_ui.html")
