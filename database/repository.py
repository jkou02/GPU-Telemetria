import os

import psycopg2
import psycopg2.extras

from config import DATABASE_URL, HOSTNAME


def _get_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def _get_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def _migrate_from_sqlite():
    """Migra datos desde la antigua BD SQLite si existe."""
    sqlite_path = "data/telemetry.db"
    if not os.path.exists(sqlite_path):
        return

    import sqlite3

    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    # Verificar si la tabla existe
    table_exists = sqlite_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='telemetry'"
    ).fetchone()

    if not table_exists:
        sqlite_conn.close()
        os.rename(sqlite_path, sqlite_path + ".migrated")
        return

    rows = sqlite_conn.execute("SELECT * FROM telemetry ORDER BY id").fetchall()
    sqlite_conn.close()

    if not rows:
        os.rename(sqlite_path, sqlite_path + ".migrated")
        return

    pg_conn = _get_connection()
    cur = _get_cursor(pg_conn)
    count = 0
    for row in rows:
        cur.execute(
            """
            INSERT INTO telemetry
                (hostname, timestamp, cpu_temp, ram_total, ram_used, ram_percent,
                 gpu_name, gpu_temp, vram_total, vram_used, vram_percent, gpu_util)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                HOSTNAME,
                row["timestamp"],
                row["cpu_temp"],
                row["ram_total"],
                row["ram_used"],
                row["ram_percent"],
                row["gpu_name"],
                row["gpu_temp"],
                row["vram_total"],
                row["vram_used"],
                row["vram_percent"],
                row["gpu_util"],
            ),
        )
        count += 1

    pg_conn.commit()
    cur.close()
    pg_conn.close()
    sqlite_conn.close()

    os.rename(sqlite_path, sqlite_path + ".migrated")
    print(f"Migrados {count} registros desde SQLite como '{HOSTNAME}'")


def init_db():
    conn = _get_connection()
    cur = _get_cursor(conn)
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS telemetry (
            id            SERIAL PRIMARY KEY,
            hostname      TEXT NOT NULL,
            timestamp     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            cpu_temp      REAL,
            ram_total     BIGINT,
            ram_used      BIGINT,
            ram_percent   REAL,
            gpu_name      TEXT,
            gpu_temp      REAL,
            vram_total    BIGINT,
            vram_used     BIGINT,
            vram_percent  REAL,
            gpu_util      REAL,
            uptime_seconds BIGINT
        )
        """
    )
    conn.commit()
    cur.close()
    conn.close()

    _migrate_from_sqlite()


def insert_telemetry(system, gpu, hostname=None):
    if hostname is None:
        hostname = HOSTNAME

    conn = _get_connection()
    cur = _get_cursor(conn)
    cur.execute(
        """
        INSERT INTO telemetry
            (hostname, cpu_temp, ram_total, ram_used, ram_percent,
             gpu_name, gpu_temp, vram_total, vram_used, vram_percent, gpu_util,
             uptime_seconds)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            hostname,
            system["cpu_temp"],
            system["ram"]["total"],
            system["ram"]["used"],
            system["ram"]["percent"],
            gpu["name"] if gpu else None,
            gpu["temperature"] if gpu else None,
            gpu["memory_total"] if gpu else None,
            gpu["memory_used"] if gpu else None,
            gpu["memory_percent"] if gpu else None,
            gpu["gpu_util"] if gpu else None,
            system.get("uptime_seconds"),
        ),
    )
    conn.commit()
    cur.close()
    conn.close()


def get_recent_entries(limit=5, hostname=None):
    conn = _get_connection()
    cur = _get_cursor(conn)
    if hostname:
        cur.execute(
            "SELECT * FROM telemetry WHERE hostname = %s ORDER BY id DESC LIMIT %s",
            (hostname, limit),
        )
    else:
        cur.execute(
            "SELECT * FROM telemetry ORDER BY id DESC LIMIT %s",
            (limit,),
        )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(r) for r in rows]


def get_latest_entry(hostname=None):
    if hostname is None:
        hostname = HOSTNAME
    conn = _get_connection()
    cur = _get_cursor(conn)
    cur.execute(
        "SELECT * FROM telemetry WHERE hostname = %s ORDER BY id DESC LIMIT 1",
        (hostname,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


def get_hostnames():
    conn = _get_connection()
    cur = _get_cursor(conn)
    cur.execute(
        "SELECT DISTINCT hostname FROM telemetry ORDER BY hostname"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r["hostname"] for r in rows]


def row_to_stats(row):
    """Convierte una fila de BD en dicts system y gpu compatibles con los formatters."""
    if not row:
        return None, None

    system = {
        "cpu_temp": row.get("cpu_temp"),
        "ram": {
            "total": row.get("ram_total"),
            "used": row.get("ram_used"),
            "percent": row.get("ram_percent"),
        },
        "uptime_seconds": row.get("uptime_seconds"),
    }

    gpu = None
    if row.get("gpu_name") is not None:
        gpu = {
            "name": row["gpu_name"],
            "temperature": row["gpu_temp"],
            "memory_total": row["vram_total"],
            "memory_used": row["vram_used"],
            "memory_percent": row["vram_percent"],
            "gpu_util": row["gpu_util"],
        }

    return system, gpu
