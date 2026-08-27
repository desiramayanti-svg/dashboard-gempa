"""
Lapisan data untuk aplikasi Raya Houses.
Menggunakan SQLite (stdlib sqlite3) - tanpa dependensi eksternal tambahan.
Database dibuat & di-seed otomatis saat pertama kali dijalankan.
"""
import sqlite3
import os
import random
import hashlib
import hmac
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "raya_houses.db")

PROPERTY_TYPES = ["Rumah", "Apartemen", "Tanah", "Ruko", "Villa"]
LISTING_STATUSES = ["Tersedia", "Pending", "Terjual", "Disewa"]
CITIES = [
    ("Jakarta Selatan", "DKI Jakarta"),
    ("Jakarta Barat", "DKI Jakarta"),
    ("Jakarta Timur", "DKI Jakarta"),
    ("Bandung", "Jawa Barat"),
    ("Bekasi", "Jawa Barat"),
    ("Depok", "Jawa Barat"),
    ("Bogor", "Jawa Barat"),
    ("Tangerang Selatan", "Banten"),
    ("Surabaya", "Jawa Timur"),
    ("Denpasar", "Bali"),
]
STAFF_ROLES = ["Admin", "Manager", "Agent", "Finance", "Marketing"]
TRANSACTION_TYPES = ["Penjualan", "Sewa", "Komisi Agent", "Pengeluaran Operasional", "Lainnya"]

# NOTE: hashing berbasis PBKDF2-HMAC-SHA256 dengan salt unik per-user (stdlib saja,
# tanpa dependensi tambahan). Cukup untuk kebutuhan MVP internal; untuk produksi
# skala besar pertimbangkan bcrypt/argon2.
_PBKDF2_ITERATIONS = 200_000


def _pbkdf2(raw_password: str, salt_hex: str) -> str:
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", raw_password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return dk.hex()


def hash_password(raw_password: str, salt_hex: str = None):
    """Menghasilkan (hash, salt) baru jika salt tidak diberikan, atau hash untuk salt yang ada."""
    if salt_hex is None:
        salt_hex = os.urandom(16).hex()
        return _pbkdf2(raw_password, salt_hex), salt_hex
    return _pbkdf2(raw_password, salt_hex)


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS staff (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    photo_emoji TEXT DEFAULT '🧑‍💼',
    join_date TEXT,
    status TEXT DEFAULT 'Aktif',
    notes TEXT
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    staff_id INTEGER,
    role TEXT NOT NULL,
    FOREIGN KEY(staff_id) REFERENCES staff(id)
);

CREATE TABLE IF NOT EXISTS listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Tersedia',
    price REAL NOT NULL,
    price_unit TEXT DEFAULT 'Jual',
    address TEXT,
    city TEXT NOT NULL,
    province TEXT,
    bedrooms INTEGER DEFAULT 0,
    bathrooms INTEGER DEFAULT 0,
    land_area REAL DEFAULT 0,
    building_area REAL DEFAULT 0,
    description TEXT,
    agent_id INTEGER,
    views INTEGER DEFAULT 0,
    created_date TEXT,
    sold_date TEXT,
    FOREIGN KEY(agent_id) REFERENCES staff(id)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id INTEGER,
    agent_id INTEGER,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    date TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY(listing_id) REFERENCES listings(id),
    FOREIGN KEY(agent_id) REFERENCES staff(id)
);
"""


def init_db(seed: bool = True):
    conn = get_conn()
    conn.executescript(SCHEMA)
    conn.commit()
    if seed:
        cur = conn.execute("SELECT COUNT(*) AS c FROM staff")
        if cur.fetchone()["c"] == 0:
            _seed_data(conn)
    conn.close()


def _seed_data(conn: sqlite3.Connection):
    rnd = random.Random(42)
    today = datetime.now()

    staff_rows = [
        ("Budi Santoso", "Admin", "0812-1000-0001", "budi.admin@rayahouses.co.id"),
        ("Siti Rahma", "Manager", "0812-1000-0002", "siti.manager@rayahouses.co.id"),
        ("Dewi Anjani", "Finance", "0812-1000-0003", "dewi.finance@rayahouses.co.id"),
        ("Rina Marlina", "Marketing", "0812-1000-0004", "rina.marketing@rayahouses.co.id"),
        ("Andi Wijaya", "Agent", "0813-2000-0001", "andi.wijaya@rayahouses.co.id"),
        ("Maya Kusuma", "Agent", "0813-2000-0002", "maya.kusuma@rayahouses.co.id"),
        ("Rizky Pratama", "Agent", "0813-2000-0003", "rizky.pratama@rayahouses.co.id"),
        ("Putri Lestari", "Agent", "0813-2000-0004", "putri.lestari@rayahouses.co.id"),
        ("Fajar Nugroho", "Agent", "0813-2000-0005", "fajar.nugroho@rayahouses.co.id"),
    ]
    staff_ids = {}
    for name, role, phone, email in staff_rows:
        join_date = (today - timedelta(days=rnd.randint(120, 1200))).strftime("%Y-%m-%d")
        cur = conn.execute(
            "INSERT INTO staff (name, role, phone, email, join_date, status) VALUES (?,?,?,?,?,?)",
            (name, role, phone, email, join_date, "Aktif"),
        )
        staff_ids[name] = cur.lastrowid

    # Default login users
    default_users = [
        ("admin", "admin123", staff_ids["Budi Santoso"], "Admin"),
        ("manager", "manager123", staff_ids["Siti Rahma"], "Manager"),
        ("finance", "finance123", staff_ids["Dewi Anjani"], "Finance"),
        ("agent.andi", "agent123", staff_ids["Andi Wijaya"], "Agent"),
    ]
    for username, pwd, sid, role in default_users:
        pwd_hash, pwd_salt = hash_password(pwd)
        conn.execute(
            "INSERT INTO users (username, password_hash, password_salt, staff_id, role) VALUES (?,?,?,?,?)",
            (username, pwd_hash, pwd_salt, sid, role),
        )

    agent_ids = [staff_ids[n] for n, r, *_ in staff_rows if r == "Agent"]

    title_templates = {
        "Rumah": "Rumah {bed}KT Nyaman di {city}",
        "Apartemen": "Apartemen {bed}BR Strategis di {city}",
        "Tanah": "Tanah Kavling Prospektif di {city}",
        "Ruko": "Ruko 3 Lantai Lokasi Ramai {city}",
        "Villa": "Villa Mewah View Alam di {city}",
    }
    base_price = {"Rumah": 1.5e9, "Apartemen": 900e6, "Tanah": 700e6, "Ruko": 2.2e9, "Villa": 3.5e9}

    n_listings = 60
    listing_ids_by_status = {"Terjual": [], "Tersedia": [], "Pending": [], "Disewa": []}
    for i in range(n_listings):
        ptype = rnd.choice(PROPERTY_TYPES)
        city, province = rnd.choice(CITIES)
        bed = rnd.randint(2, 5)
        bath = max(1, bed - rnd.randint(0, 2))
        land = round(rnd.uniform(80, 500), 0) if ptype != "Apartemen" else 0
        building = round(rnd.uniform(60, 350), 0)
        price = round(base_price[ptype] * rnd.uniform(0.6, 2.4) / 1e6) * 1e6
        price_unit = "Sewa/Tahun" if ptype in ("Apartemen", "Rumah") and rnd.random() < 0.15 else "Jual"
        status = rnd.choices(LISTING_STATUSES, weights=[45, 15, 30, 10])[0]
        agent_id = rnd.choice(agent_ids)
        created_date = today - timedelta(days=rnd.randint(5, 400))
        sold_date = None
        if status == "Terjual":
            sold_date = created_date + timedelta(days=rnd.randint(5, 90))
            if sold_date > today:
                sold_date = today
        title = title_templates[ptype].format(bed=bed, city=city)
        views = rnd.randint(5, 400)

        cur = conn.execute(
            """INSERT INTO listings
            (title, type, status, price, price_unit, address, city, province, bedrooms, bathrooms,
             land_area, building_area, description, agent_id, views, created_date, sold_date)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                title, ptype, status, price, price_unit,
                f"Jl. {rnd.choice(['Mawar','Melati','Anggrek','Kenanga','Kemuning','Cendana'])} No. {rnd.randint(1,150)}",
                city, province, bed if ptype != "Tanah" else 0, bath if ptype != "Tanah" else 0,
                land, building if ptype != "Tanah" else 0,
                f"{ptype} berkualitas di kawasan {city}, akses mudah ke fasilitas umum, cocok untuk investasi maupun hunian.",
                agent_id, views,
                created_date.strftime("%Y-%m-%d"),
                sold_date.strftime("%Y-%m-%d") if sold_date else None,
            ),
        )
        listing_ids_by_status[status].append((cur.lastrowid, price, agent_id, sold_date))

    # Transaksi keuangan dari listing terjual: Penjualan + Komisi Agent
    for lid, price, agent_id, sold_date in listing_ids_by_status["Terjual"]:
        d = sold_date.strftime("%Y-%m-%d")
        conn.execute(
            "INSERT INTO transactions (listing_id, agent_id, type, amount, date, description) VALUES (?,?,?,?,?,?)",
            (lid, agent_id, "Penjualan", price, d, f"Penjualan listing #{lid}"),
        )
        komisi = round(price * 0.025)
        conn.execute(
            "INSERT INTO transactions (listing_id, agent_id, type, amount, date, description) VALUES (?,?,?,?,?,?)",
            (lid, agent_id, "Komisi Agent", -komisi, d, f"Komisi agent untuk listing #{lid}"),
        )

    # Sewa untuk listing berstatus Disewa
    for lid, price, agent_id, _ in listing_ids_by_status["Disewa"]:
        d = (today - timedelta(days=rnd.randint(1, 200))).strftime("%Y-%m-%d")
        conn.execute(
            "INSERT INTO transactions (listing_id, agent_id, type, amount, date, description) VALUES (?,?,?,?,?,?)",
            (lid, agent_id, "Sewa", round(price * 0.08), d, f"Sewa listing #{lid}"),
        )

    # Pengeluaran operasional bulanan selama 12 bulan terakhir
    for m in range(12, 0, -1):
        d = (today - timedelta(days=30 * m)).strftime("%Y-%m-%d")
        conn.execute(
            "INSERT INTO transactions (listing_id, agent_id, type, amount, date, description) VALUES (?,?,?,?,?,?)",
            (None, None, "Pengeluaran Operasional", -round(rnd.uniform(15e6, 35e6)), d, "Sewa kantor, iklan, dan operasional bulanan"),
        )

    conn.commit()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def authenticate(username: str, password: str):
    conn = get_conn()
    row = conn.execute(
        """SELECT u.id as user_id, u.username, u.role, u.staff_id, u.password_hash, u.password_salt,
                  s.name as staff_name, s.status as staff_status
           FROM users u LEFT JOIN staff s ON s.id = u.staff_id
           WHERE u.username = ?""",
        (username,),
    ).fetchone()
    conn.close()
    if not row:
        return None
    computed = hash_password(password, row["password_salt"])
    if not hmac.compare_digest(computed, row["password_hash"]):
        return None
    if row["staff_status"] is not None and row["staff_status"] != "Aktif":
        return None
    result = dict(row)
    result.pop("password_hash", None)
    result.pop("password_salt", None)
    return result


def create_user(username: str, password: str, staff_id: int, role: str):
    pwd_hash, pwd_salt = hash_password(password)
    conn = get_conn()
    conn.execute(
        "INSERT INTO users (username, password_hash, password_salt, staff_id, role) VALUES (?,?,?,?,?)",
        (username, pwd_hash, pwd_salt, staff_id, role),
    )
    conn.commit()
    conn.close()


def username_exists(username: str) -> bool:
    conn = get_conn()
    row = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return row is not None


# ---------------------------------------------------------------------------
# Staff / Agent
# ---------------------------------------------------------------------------

def list_staff(role: str = None, status: str = None):
    conn = get_conn()
    q = "SELECT * FROM staff WHERE 1=1"
    params = []
    if role:
        q += " AND role = ?"
        params.append(role)
    if status:
        q += " AND status = ?"
        params.append(status)
    q += " ORDER BY name"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_staff(staff_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM staff WHERE id = ?", (staff_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_staff(name, role, phone, email, join_date, notes=""):
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO staff (name, role, phone, email, join_date, status, notes) VALUES (?,?,?,?,?,?,?)",
        (name, role, phone, email, join_date, "Aktif", notes),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_staff(staff_id, **fields):
    if not fields:
        return
    conn = get_conn()
    cols = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(f"UPDATE staff SET {cols} WHERE id = ?", (*fields.values(), staff_id))
    conn.commit()
    conn.close()


def set_staff_status(staff_id, status):
    update_staff(staff_id, status=status)


# ---------------------------------------------------------------------------
# Listings
# ---------------------------------------------------------------------------

def list_listings(filters: dict = None, order_by: str = "created_date DESC"):
    filters = filters or {}
    conn = get_conn()
    q = """SELECT l.*, s.name as agent_name, s.phone as agent_phone, s.email as agent_email
           FROM listings l LEFT JOIN staff s ON s.id = l.agent_id WHERE 1=1"""
    params = []
    if filters.get("type"):
        q += " AND l.type = ?"
        params.append(filters["type"])
    if filters.get("status"):
        q += " AND l.status = ?"
        params.append(filters["status"])
    if filters.get("city"):
        q += " AND l.city = ?"
        params.append(filters["city"])
    if filters.get("agent_id"):
        q += " AND l.agent_id = ?"
        params.append(filters["agent_id"])
    if filters.get("min_price") is not None:
        q += " AND l.price >= ?"
        params.append(filters["min_price"])
    if filters.get("max_price") is not None:
        q += " AND l.price <= ?"
        params.append(filters["max_price"])
    if filters.get("min_bedrooms") is not None:
        q += " AND l.bedrooms >= ?"
        params.append(filters["min_bedrooms"])
    if filters.get("keyword"):
        q += " AND (l.title LIKE ? OR l.address LIKE ? OR l.city LIKE ?)"
        kw = f"%{filters['keyword']}%"
        params += [kw, kw, kw]
    q += f" ORDER BY {order_by}"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_listing(listing_id: int):
    conn = get_conn()
    row = conn.execute(
        """SELECT l.*, s.name as agent_name, s.phone as agent_phone, s.email as agent_email
           FROM listings l LEFT JOIN staff s ON s.id = l.agent_id WHERE l.id = ?""",
        (listing_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def add_listing(data: dict):
    conn = get_conn()
    cols = [
        "title", "type", "status", "price", "price_unit", "address", "city", "province",
        "bedrooms", "bathrooms", "land_area", "building_area", "description", "agent_id",
        "created_date",
    ]
    values = [data.get(c) for c in cols]
    placeholders = ",".join(["?"] * len(cols))
    cur = conn.execute(f"INSERT INTO listings ({','.join(cols)}) VALUES ({placeholders})", values)
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_listing(listing_id: int, **fields):
    if not fields:
        return
    conn = get_conn()
    cols = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(f"UPDATE listings SET {cols} WHERE id = ?", (*fields.values(), listing_id))
    conn.commit()
    conn.close()


def delete_listing(listing_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM transactions WHERE listing_id = ?", (listing_id,))
    conn.execute("DELETE FROM listings WHERE id = ?", (listing_id,))
    conn.commit()
    conn.close()


def increment_view(listing_id: int):
    conn = get_conn()
    conn.execute("UPDATE listings SET views = views + 1 WHERE id = ?", (listing_id,))
    conn.commit()
    conn.close()


def distinct_cities():
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT city FROM listings ORDER BY city").fetchall()
    conn.close()
    return [r["city"] for r in rows]


# ---------------------------------------------------------------------------
# Transactions / Keuangan
# ---------------------------------------------------------------------------

def add_transaction(listing_id, agent_id, ttype, amount, date, description=""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO transactions (listing_id, agent_id, type, amount, date, description) VALUES (?,?,?,?,?,?)",
        (listing_id, agent_id, ttype, amount, date, description),
    )
    conn.commit()
    conn.close()


def list_transactions(filters: dict = None):
    filters = filters or {}
    conn = get_conn()
    q = """SELECT t.*, l.title as listing_title, s.name as agent_name
           FROM transactions t
           LEFT JOIN listings l ON l.id = t.listing_id
           LEFT JOIN staff s ON s.id = t.agent_id WHERE 1=1"""
    params = []
    if filters.get("type"):
        q += " AND t.type = ?"
        params.append(filters["type"])
    if filters.get("start_date"):
        q += " AND t.date >= ?"
        params.append(filters["start_date"])
    if filters.get("end_date"):
        q += " AND t.date <= ?"
        params.append(filters["end_date"])
    q += " ORDER BY t.date DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_transaction(tx_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()
