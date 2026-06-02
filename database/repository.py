import os
import sqlite3

from config import DB_PATH


def _ensure_db_dir():
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)


def _get_connection():
    _ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            cpu_temp    REAL,
            ram_total   INTEGER,
            ram_used    INTEGER,
            ram_percent REAL,
            gpu_name    TEXT,
            gpu_temp    REAL,
            vram_total  INTEGER,
            vram_used   INTEGER,
            vram_percent REAL,
            gpu_util    REAL
        )
    """)
    conn.commit()
    conn.close()


def insert_telemetry(system, gpu):
    conn = _get_connection()
    conn.execute("""
        INSERT INTO telemetry
            (cpu_temp, ram_total, ram_used, ram_percent,
             gpu_name, gpu_temp, vram_total, vram_used, vram_percent, gpu_util)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
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
    ))
    conn.commit()
    conn.close()


def get_recent_entries(limit=5):
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM telemetry ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
