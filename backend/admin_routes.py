import os

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Blueprint, jsonify, request
from dotenv import load_dotenv, find_dotenv
from werkzeug.security import generate_password_hash


load_dotenv(find_dotenv(), override=True)

admin_bp = Blueprint(
    "admin_bp",
    __name__,
    url_prefix="/admin"
)


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "postgres"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD"),
        port=int(os.getenv("DB_PORT", 5432)),
    )


# =========================================================
# SETUP TABLE ADMIN
# =========================================================

def ensure_admin_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("CREATE SCHEMA IF NOT EXISTS idxsaham;")

    # Tambahan kolom ke users lama
    cur.execute("""
        ALTER TABLE idxsaham.users
        ADD COLUMN IF NOT EXISTS access_role VARCHAR(30)
        DEFAULT 'user';
    """)

    cur.execute("""
        ALTER TABLE idxsaham.users
        ADD COLUMN IF NOT EXISTS is_active BOOLEAN
        DEFAULT TRUE;
    """)

    # Role / jabatan
    cur.execute("""
        CREATE TABLE IF NOT EXISTS idxsaham.roles (
            id SERIAL PRIMARY KEY,
            name VARCHAR(150) UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Ambil role lama dari users dan masukkan ke tabel roles
    cur.execute("""
        INSERT INTO idxsaham.roles (name)
        SELECT DISTINCT role
        FROM idxsaham.users
        WHERE role IS NOT NULL
          AND TRIM(role) <> ''
        ON CONFLICT (name) DO NOTHING;
    """)

    # Master menu
    cur.execute("""
        CREATE TABLE IF NOT EXISTS idxsaham.menus (
            id SERIAL PRIMARY KEY,
            menu_key VARCHAR(100) UNIQUE NOT NULL,
            name VARCHAR(150) NOT NULL,
            route VARCHAR(255) NOT NULL
        );
    """)

    menus = [
        ("stream", "Stream", "/stream"),
        ("crawl_logs", "Crawl Logs", "/crawl-logs"),
        ("auto_scheduler", "Auto Scheduler", "/auto-scheduler"),
        (
            "admin_management",
            "Admin Management",
            "/admin"
        ),
    ]

    for menu_key, name, route in menus:
        cur.execute("""
            INSERT INTO idxsaham.menus
                (menu_key, name, route)
            VALUES (%s, %s, %s)
            ON CONFLICT (menu_key) DO UPDATE
            SET
                name = EXCLUDED.name,
                route = EXCLUDED.route;
        """, (
            menu_key,
            name,
            route
        ))

    # Hak akses menu berdasarkan access_role
    cur.execute("""
        CREATE TABLE IF NOT EXISTS
        idxsaham.menu_permissions (
            id SERIAL PRIMARY KEY,
            access_role VARCHAR(30) NOT NULL,
            menu_key VARCHAR(100) NOT NULL,
            enabled BOOLEAN DEFAULT FALSE,

            UNIQUE(access_role, menu_key)
        );
    """)

    # ADMIN -> semua menu
    for menu_key, _, _ in menus:
        cur.execute("""
            INSERT INTO idxsaham.menu_permissions
                (access_role, menu_key, enabled)
            VALUES ('admin', %s, TRUE)
            ON CONFLICT (access_role, menu_key)
            DO NOTHING;
        """, (menu_key,))

    # USER -> hanya stream default
    for menu_key, _, _ in menus:
        enabled = menu_key == "stream"

        cur.execute("""
            INSERT INTO idxsaham.menu_permissions
                (access_role, menu_key, enabled)
            VALUES ('user', %s, %s)
            ON CONFLICT (access_role, menu_key)
            DO NOTHING;
        """, (
            menu_key,
            enabled
        ))

    # Activity log
    cur.execute("""
        CREATE TABLE IF NOT EXISTS
        idxsaham.user_activity (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            activity VARCHAR(100) NOT NULL,
            description TEXT,
            created_at TIMESTAMPTZ
            DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


def log_activity(user_id, activity, description=None):
    try:
        ensure_admin_tables()

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO idxsaham.user_activity
                (user_id, activity, description)
            VALUES (%s, %s, %s);
        """, (
            user_id,
            activity,
            description
        ))

        conn.commit()
        cur.close()
        conn.close()

    except Exception as error:
        print("Gagal membuat activity log:", error)


# =========================================================
# SIMPLE ADMIN CHECK
# =========================================================

def require_admin():
    """
    Cocok dengan project kamu saat ini.

    Frontend mengirim:
    X-Access-Role: admin

    NOTE:
    Untuk production sebaiknya gunakan JWT/session.
    """

    access_role = (
        request.headers
        .get("X-Access-Role", "")
        .strip()
        .lower()
    )

    return access_role == "admin"


def forbidden():
    return jsonify({
        "error": "Admin access required"
    }), 403


# =========================================================
# USER MANAGEMENT
# =========================================================

@admin_bp.route("/users", methods=["GET"])
def admin_get_users():

    if not require_admin():
        return forbidden()

    ensure_admin_tables()

    conn = get_connection()

    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    cur.execute("""
        SELECT
            id,
            email,
            username,
            name,
            role,
            access_role,
            default_ticker,
            is_active,
            created_at
        FROM idxsaham.users
        ORDER BY id ASC;
    """)

    users = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(users)


@admin_bp.route("/users", methods=["POST"])
def admin_create_user():

    if not require_admin():
        return forbidden()

    ensure_admin_tables()

    payload = request.get_json(silent=True) or {}

    email = str(
        payload.get("email") or ""
    ).strip().lower()

    username = str(
        payload.get("username") or ""
    ).strip()

    password = str(
        payload.get("password") or ""
    )

    name = str(
        payload.get("name") or ""
    ).strip()

    role = str(
        payload.get("role") or ""
    ).strip()

    access_role = str(
        payload.get("access_role") or "user"
    ).strip().lower()

    if not email:
        return jsonify({
            "error": "Email wajib diisi"
        }), 400

    if not username:
        return jsonify({
            "error": "Username wajib diisi"
        }), 400

    if len(password) < 6:
        return jsonify({
            "error":
            "Password minimal 6 karakter"
        }), 400

    if access_role not in ["admin", "user"]:
        return jsonify({
            "error": "Access role tidak valid"
        }), 400

    password_hash = generate_password_hash(
        password
    )

    conn = get_connection()

    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    try:
        cur.execute("""
            INSERT INTO idxsaham.users (
                email,
                username,
                password,
                name,
                role,
                access_role,
                is_active
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, TRUE
            )
            RETURNING
                id,
                email,
                username,
                name,
                role,
                access_role,
                is_active;
        """, (
            email,
            username,
            password_hash,
            name or None,
            role or None,
            access_role
        ))

        user = cur.fetchone()

        conn.commit()

        log_activity(
            user["id"],
            "ACCOUNT_CREATED",
            f"Akun {email} dibuat"
        )

        return jsonify(user), 201

    except psycopg2.IntegrityError:
        conn.rollback()

        return jsonify({
            "error":
            "Email atau username sudah digunakan"
        }), 409

    finally:
        cur.close()
        conn.close()


@admin_bp.route(
    "/users/<int:user_id>",
    methods=["PUT"]
)
def admin_update_user(user_id):

    if not require_admin():
        return forbidden()

    ensure_admin_tables()

    payload = request.get_json(silent=True) or {}

    fields = []
    values = []

    allowed = {
        "email",
        "username",
        "name",
        "role",
        "access_role",
        "default_ticker",
        "is_active"
    }

    for key in allowed:
        if key in payload:
            fields.append(f"{key} = %s")
            values.append(payload[key])

    # Password harus di-hash
    if payload.get("password"):
        fields.append("password = %s")

        values.append(
            generate_password_hash(
                str(payload["password"])
            )
        )

    if not fields:
        return jsonify({
            "error":
            "Tidak ada data yang diperbarui"
        }), 400

    values.append(user_id)

    conn = get_connection()

    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    cur.execute(
        f"""
        UPDATE idxsaham.users
        SET {", ".join(fields)}
        WHERE id = %s
        RETURNING
            id,
            email,
            username,
            name,
            role,
            access_role,
            is_active;
        """,
        values
    )

    user = cur.fetchone()

    if not user:
        cur.close()
        conn.close()

        return jsonify({
            "error": "User tidak ditemukan"
        }), 404

    conn.commit()

    cur.close()
    conn.close()

    log_activity(
        user_id,
        "ACCOUNT_UPDATED",
        f"Data user {user['email']} diperbarui"
    )

    return jsonify(user)


# =========================================================
# ROLE MANAGEMENT
# =========================================================

@admin_bp.route("/roles", methods=["GET"])
def admin_get_roles():

    if not require_admin():
        return forbidden()

    ensure_admin_tables()

    conn = get_connection()

    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    cur.execute("""
        SELECT
            id,
            name,
            description,
            created_at
        FROM idxsaham.roles
        ORDER BY name ASC;
    """)

    roles = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(roles)


@admin_bp.route("/roles", methods=["POST"])
def admin_create_role():

    if not require_admin():
        return forbidden()

    ensure_admin_tables()

    payload = request.get_json(silent=True) or {}

    name = str(
        payload.get("name") or ""
    ).strip()

    description = str(
        payload.get("description") or ""
    ).strip()

    if not name:
        return jsonify({
            "error": "Nama role wajib diisi"
        }), 400

    conn = get_connection()

    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    try:
        cur.execute("""
            INSERT INTO idxsaham.roles
                (name, description)
            VALUES (%s, %s)
            RETURNING
                id,
                name,
                description,
                created_at;
        """, (
            name,
            description or None
        ))

        role = cur.fetchone()

        conn.commit()

        return jsonify(role), 201

    except psycopg2.IntegrityError:
        conn.rollback()

        return jsonify({
            "error": "Role sudah tersedia"
        }), 409

    finally:
        cur.close()
        conn.close()


@admin_bp.route(
    "/roles/<int:role_id>",
    methods=["PUT"]
)
def admin_update_role(role_id):

    if not require_admin():
        return forbidden()

    ensure_admin_tables()

    payload = request.get_json(silent=True) or {}

    name = str(
        payload.get("name") or ""
    ).strip()

    description = str(
        payload.get("description") or ""
    ).strip()

    if not name:
        return jsonify({
            "error": "Nama role wajib diisi"
        }), 400

    conn = get_connection()

    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    # nama role lama
    cur.execute("""
        SELECT name
        FROM idxsaham.roles
        WHERE id = %s;
    """, (role_id,))

    old_role = cur.fetchone()

    if not old_role:
        cur.close()
        conn.close()

        return jsonify({
            "error": "Role tidak ditemukan"
        }), 404

    old_name = old_role["name"]

    cur.execute("""
        UPDATE idxsaham.roles
        SET
            name = %s,
            description = %s
        WHERE id = %s
        RETURNING
            id,
            name,
            description;
    """, (
        name,
        description or None,
        role_id
    ))

    role = cur.fetchone()

    # user yang menggunakan role lama ikut berubah
    if old_name != name:
        cur.execute("""
            UPDATE idxsaham.users
            SET role = %s
            WHERE role = %s;
        """, (
            name,
            old_name
        ))

    conn.commit()

    cur.close()
    conn.close()

    return jsonify(role)


@admin_bp.route(
    "/roles/<int:role_id>",
    methods=["DELETE"]
)
def admin_delete_role(role_id):

    if not require_admin():
        return forbidden()

    ensure_admin_tables()

    conn = get_connection()

    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    cur.execute("""
        SELECT name
        FROM idxsaham.roles
        WHERE id = %s;
    """, (role_id,))

    role = cur.fetchone()

    if not role:
        cur.close()
        conn.close()

        return jsonify({
            "error": "Role tidak ditemukan"
        }), 404

    cur.execute("""
        SELECT COUNT(*) AS total
        FROM idxsaham.users
        WHERE role = %s;
    """, (role["name"],))

    total = cur.fetchone()["total"]

    if total > 0:
        cur.close()
        conn.close()

        return jsonify({
            "error":
            "Role masih digunakan oleh user"
        }), 400

    cur.execute("""
        DELETE FROM idxsaham.roles
        WHERE id = %s;
    """, (role_id,))

    conn.commit()

    cur.close()
    conn.close()

    return jsonify({
        "deleted": True
    })


# =========================================================
# MENU MANAGEMENT
# =========================================================

@admin_bp.route(
    "/menu-permissions",
    methods=["GET"]
)
def admin_get_menu_permissions():

    if not require_admin():
        return forbidden()

    ensure_admin_tables()

    conn = get_connection()

    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    cur.execute("""
        SELECT
            m.menu_key,
            m.name,
            m.route,

            COALESCE(
                MAX(
                    CASE
                        WHEN p.access_role = 'admin'
                        THEN p.enabled::int
                    END
                ),
                0
            )::boolean AS admin_enabled,

            COALESCE(
                MAX(
                    CASE
                        WHEN p.access_role = 'user'
                        THEN p.enabled::int
                    END
                ),
                0
            )::boolean AS user_enabled

        FROM idxsaham.menus m

        LEFT JOIN idxsaham.menu_permissions p
            ON p.menu_key = m.menu_key

        GROUP BY
            m.id,
            m.menu_key,
            m.name,
            m.route

        ORDER BY m.id;
    """)

    menus = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(menus)


@admin_bp.route(
    "/menu-permissions",
    methods=["PUT"]
)
def admin_update_menu_permission():

    if not require_admin():
        return forbidden()

    ensure_admin_tables()

    payload = request.get_json(silent=True) or {}

    access_role = str(
        payload.get("access_role") or ""
    ).strip().lower()

    menu_key = str(
        payload.get("menu_key") or ""
    ).strip()

    enabled = bool(
        payload.get("enabled")
    )

    if access_role not in ["admin", "user"]:
        return jsonify({
            "error":
            "Access role tidak valid"
        }), 400

    # Admin jangan sampai mematikan akses ke admin management
    if (
        access_role == "admin"
        and menu_key == "admin_management"
        and not enabled
    ):
        return jsonify({
            "error":
            "Admin Management tidak boleh "
            "dinonaktifkan untuk admin"
        }), 400

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO idxsaham.menu_permissions (
            access_role,
            menu_key,
            enabled
        )
        VALUES (%s, %s, %s)

        ON CONFLICT (
            access_role,
            menu_key
        )

        DO UPDATE SET
            enabled = EXCLUDED.enabled;
    """, (
        access_role,
        menu_key,
        enabled
    ))

    conn.commit()

    cur.close()
    conn.close()

    return jsonify({
        "menu_key": menu_key,
        "access_role": access_role,
        "enabled": enabled
    })


# Endpoint yang boleh dibaca user biasa
@admin_bp.route(
    "/permissions/<access_role>",
    methods=["GET"]
)
def get_permissions(access_role):

    ensure_admin_tables()

    access_role = access_role.lower()

    if access_role not in ["admin", "user"]:
        return jsonify([])

    conn = get_connection()

    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    cur.execute("""
        SELECT
            m.menu_key,
            m.name,
            m.route
        FROM idxsaham.menu_permissions p

        JOIN idxsaham.menus m
            ON m.menu_key = p.menu_key

        WHERE
            p.access_role = %s
            AND p.enabled = TRUE

        ORDER BY m.id;
    """, (access_role,))

    result = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(result)


# =========================================================
# USER ACTIVITY
# =========================================================

@admin_bp.route(
    "/activity",
    methods=["GET"]
)
def admin_get_activity():

    if not require_admin():
        return forbidden()

    ensure_admin_tables()

    conn = get_connection()

    cur = conn.cursor(
        cursor_factory=RealDictCursor
    )

    cur.execute("""
        SELECT
            a.id,
            a.user_id,
            u.name,
            u.email,
            a.activity,
            a.description,
            a.created_at

        FROM idxsaham.user_activity a

        LEFT JOIN idxsaham.users u
            ON u.id = a.user_id

        ORDER BY a.created_at DESC

        LIMIT 200;
    """)

    activities = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(activities)