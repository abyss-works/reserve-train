"""
db.py — PostgreSQL 데이터베이스 레이어
"""
import os
import threading
from contextlib import contextmanager
from datetime import datetime

import psycopg2
import psycopg2.pool
from psycopg2.extras import RealDictCursor

_pool = None
_pool_lock = threading.Lock()


def _get_dsn():
    return (
        f"host={os.getenv('DB_HOST', 'localhost')} "
        f"port={os.getenv('DB_PORT', '5432')} "
        f"dbname={os.getenv('DB_NAME', 'reservetrain')} "
        f"user={os.getenv('DB_USER', 'postgres')} "
        f"password={os.getenv('DB_PASSWORD', 'postgres')}"
    )


def init_pool(minconn=1, maxconn=5):
    global _pool
    with _pool_lock:
        if _pool is None:
            _pool = psycopg2.pool.ThreadedConnectionPool(minconn, maxconn, _get_dsn())
            _create_tables()


def _create_tables():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS monitor_tasks (
                    task_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    korail_id TEXT NOT NULL,
                    korail_pw TEXT NOT NULL,
                    dep TEXT NOT NULL,
                    arr TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    train_type TEXT DEFAULT 'ktx',
                    train_no TEXT DEFAULT '',
                    train_label TEXT DEFAULT '',
                    seat_option TEXT DEFAULT 'general-first',
                    try_waiting BOOLEAN DEFAULT FALSE,
                    interval_sec INTEGER DEFAULT 30,
                    status TEXT DEFAULT 'monitoring',
                    check_count INTEGER DEFAULT 0,
                    error_msg TEXT DEFAULT '',
                    result JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                );
                CREATE TABLE IF NOT EXISTS monitor_logs (
                    id SERIAL PRIMARY KEY,
                    task_id TEXT NOT NULL REFERENCES monitor_tasks(task_id) ON DELETE CASCADE,
                    level TEXT NOT NULL DEFAULT 'info',
                    message TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_monitor_logs_task ON monitor_logs(task_id, created_at DESC);
            """)
            conn.commit()


@contextmanager
def get_conn():
    global _pool
    if _pool is None:
        init_pool()
    conn = _pool.getconn()
    try:
        yield conn
    finally:
        _pool.putconn(conn)


def close_pool():
    global _pool
    with _pool_lock:
        if _pool:
            _pool.closeall()
            _pool = None


# ─── Monitor Tasks ──────────────────────────────


def create_task(task: dict) -> str:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO monitor_tasks
                    (task_id, session_id, korail_id, korail_pw,
                     dep, arr, date, time, train_type, train_no, train_label,
                     seat_option, try_waiting, interval_sec)
                VALUES (%(task_id)s, %(session_id)s, %(korail_id)s, %(korail_pw)s,
                        %(dep)s, %(arr)s, %(date)s, %(time)s, %(train_type)s, %(train_no)s, %(train_label)s,
                        %(seat_option)s, %(try_waiting)s, %(interval_sec)s)
            """, task)
            conn.commit()


def get_task(task_id: str) -> dict | None:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM monitor_tasks WHERE task_id = %s", (task_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def get_tasks_by_session(session_id: str) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM monitor_tasks WHERE session_id = %s ORDER BY created_at DESC",
                (session_id,),
            )
            return [dict(r) for r in cur.fetchall()]


def get_active_tasks() -> list[dict]:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM monitor_tasks WHERE status = 'monitoring' ORDER BY created_at ASC"
            )
            return [dict(r) for r in cur.fetchall()]


def update_task_status(task_id: str, **kwargs):
    sets = ", ".join(f"{k} = %({k})s" for k in kwargs)
    kwargs["task_id"] = task_id
    kwargs["updated_at"] = datetime.utcnow()
    sets += ", updated_at = %(updated_at)s"
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE monitor_tasks SET {sets} WHERE task_id = %(task_id)s",
                kwargs,
            )
            conn.commit()


def delete_task(task_id: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM monitor_logs WHERE task_id = %s", (task_id,))
            cur.execute("DELETE FROM monitor_tasks WHERE task_id = %s", (task_id,))
            conn.commit()


# ─── Logs ───────────────────────────────────────


def add_log(task_id: str, level: str, message: str):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO monitor_logs (task_id, level, message) VALUES (%s, %s, %s)",
                (task_id, level, message),
            )
            conn.commit()


def get_logs(task_id: str, limit: int = 50) -> list[dict]:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, level, message, created_at FROM monitor_logs WHERE task_id = %s ORDER BY created_at DESC LIMIT %s",
                (task_id, limit),
            )
            return [dict(r) for r in cur.fetchall()]
