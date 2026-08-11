"""
db.py — SQLite database layer
Designed for zero-friction migration to PostgreSQL:
  - All queries use ? placeholders (swap for %s in Postgres)
  - No SQLite-specific types used in application logic
  - Connection factory is the only thing that changes on migration
"""

import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "governance.db")


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Run on app startup — idempotent."""
    import bcrypt
    conn = get_conn()

    schema = """
    CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        email         TEXT NOT NULL UNIQUE,
        display_name  TEXT NOT NULL,
        role          TEXT NOT NULL DEFAULT 'user',
        password_hash TEXT NOT NULL,
        is_active     INTEGER NOT NULL DEFAULT 1,
        created_at    TEXT NOT NULL DEFAULT (datetime('now')),
        last_login    TEXT
    );

    CREATE TABLE IF NOT EXISTS audit_sessions (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id           INTEGER NOT NULL REFERENCES users(id),
        title             TEXT NOT NULL,
        use_case_raw      TEXT NOT NULL,
        use_case_enriched TEXT,
        overall_pct       REAL,
        maturity_label    TEXT,
        maturity_color    TEXT,
        maturity_desc     TEXT,
        status            TEXT NOT NULL DEFAULT 'intake',
        vendor_name       TEXT,
        created_at        TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS audit_results (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id     INTEGER NOT NULL REFERENCES audit_sessions(id) ON DELETE CASCADE,
        criterion_id   TEXT NOT NULL,
        criterion_name TEXT NOT NULL,
        function       TEXT NOT NULL,
        score          INTEGER NOT NULL,
        rationale      TEXT,
        critical_flag  INTEGER NOT NULL DEFAULT 0,
        remediation    TEXT,
        weighted_score REAL,
        weight         REAL
    );

    CREATE TABLE IF NOT EXISTS checklist_items (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id    INTEGER NOT NULL REFERENCES audit_sessions(id) ON DELETE CASCADE,
        criterion_id  TEXT NOT NULL,
        action        TEXT NOT NULL,
        owner         TEXT,
        due_date      TEXT,
        status        TEXT NOT NULL DEFAULT 'pending',
        created_at    TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS intake_messages (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL REFERENCES audit_sessions(id) ON DELETE CASCADE,
        role       TEXT NOT NULL,
        content    TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """

    for statement in schema.strip().split(";"):
        s = statement.strip()
        if s:
            conn.execute(s)
    conn.commit()

    # Seed demo users if not present
    seed_users = [
        ("admin@shearwater.com",   "System Admin",            "admin",   os.getenv("ADMIN_PASSWORD",   "changeme_admin")),
        ("auditor@shearwater.com", "AI Governance Auditor",   "auditor", os.getenv("AUDITOR_PASSWORD", "changeme_auditor")),
        ("dpo@shearwater.com",     "Data Protection Officer", "dpo",     os.getenv("DPO_PASSWORD",     "changeme_dpo")),
        ("user@shearwater.com",    "Demo User",               "user",    os.getenv("USER_PASSWORD",    "changeme_user")),
    ]
    for email, name, role, pwd in seed_users:
        exists = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if not exists:
            hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
            conn.execute(
                "INSERT INTO users (email, display_name, role, password_hash) VALUES (?,?,?,?)",
                (email, name, role, hashed)
            )
    conn.commit()
    conn.close()


# ── Users ─────────────────────────────────────────────────────────────────────

def get_user_by_email(email: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE email = ? AND is_active = 1", (email,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_last_login(user_id: int):
    conn = get_conn()
    conn.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()


# ── Audit Sessions ─────────────────────────────────────────────────────────────

def create_audit_session(user_id: int, title: str, use_case_raw: str) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO audit_sessions (user_id, title, use_case_raw) VALUES (?,?,?)",
        (user_id, title, use_case_raw)
    )
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return session_id


def update_session_enriched(session_id: int, enriched: str):
    conn = get_conn()
    conn.execute(
        "UPDATE audit_sessions SET use_case_enriched = ?, updated_at = ? WHERE id = ?",
        (enriched, datetime.now().isoformat(), session_id)
    )
    conn.commit()
    conn.close()


def update_session_scores(session_id: int, overall_pct: float, maturity_label: str,
                           maturity_color: str, maturity_desc: str):
    conn = get_conn()
    conn.execute(
        """UPDATE audit_sessions
           SET overall_pct=?, maturity_label=?, maturity_color=?,
               maturity_desc=?, status='scored', updated_at=?
           WHERE id=?""",
        (overall_pct, maturity_label, maturity_color, maturity_desc,
         datetime.now().isoformat(), session_id)
    )
    conn.commit()
    conn.close()


def update_session_status(session_id: int, status: str):
    conn = get_conn()
    conn.execute(
        "UPDATE audit_sessions SET status=?, updated_at=? WHERE id=?",
        (status, datetime.now().isoformat(), session_id)
    )
    conn.commit()
    conn.close()


def update_session_vendor(session_id: int, vendor_name: str):
    """Store the vendor name against an audit session."""
    conn = get_conn()
    conn.execute(
        "UPDATE audit_sessions SET vendor_name=?, updated_at=? WHERE id=?",
        (vendor_name, datetime.now().isoformat(), session_id)
    )
    conn.commit()
    conn.close()


def get_session(session_id: int):
    conn = get_conn()
    row = conn.execute("SELECT * FROM audit_sessions WHERE id = ?", (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_sessions_for_user(user_id: int):
    conn = get_conn()
    rows = conn.execute(
        """SELECT s.*, u.display_name, u.email
           FROM audit_sessions s JOIN users u ON s.user_id = u.id
           WHERE s.user_id = ?
           ORDER BY s.updated_at DESC""",
        (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_sessions():
    """For admin / auditor / DPO roles."""
    conn = get_conn()
    rows = conn.execute(
        """SELECT s.*, u.display_name, u.email
           FROM audit_sessions s JOIN users u ON s.user_id = u.id
           ORDER BY s.updated_at DESC"""
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Audit Results ──────────────────────────────────────────────────────────────

def save_audit_results(session_id: int, results: list):
    conn = get_conn()
    conn.execute("DELETE FROM audit_results WHERE session_id = ?", (session_id,))
    for r in results:
        conn.execute(
            """INSERT INTO audit_results
               (session_id, criterion_id, criterion_name, function, score,
                rationale, critical_flag, remediation, weighted_score, weight)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (session_id, r["id"], r["name"], r["function"], r["score"],
             r["rationale"], int(r["critical_flag"]), r["remediation"],
             r["weighted_score"], r["weight"])
        )
    conn.commit()
    conn.close()


def get_audit_results(session_id: int):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM audit_results WHERE session_id = ? ORDER BY id",
        (session_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Checklist ──────────────────────────────────────────────────────────────────

def save_checklist_items(session_id: int, items: list):
    conn = get_conn()
    conn.execute("DELETE FROM checklist_items WHERE session_id = ?", (session_id,))
    for item in items:
        conn.execute(
            """INSERT INTO checklist_items
               (session_id, criterion_id, action, owner, due_date, status)
               VALUES (?,?,?,?,?,?)""",
            (session_id, item.get("criterion_id",""), item["action"],
             item.get("owner",""), item.get("due_date",""), "pending")
        )
    conn.commit()
    conn.close()


def get_checklist(session_id: int):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM checklist_items WHERE session_id = ? ORDER BY id",
        (session_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_checklist_item(item_id: int, status: str, owner: str, due_date: str):
    conn = get_conn()
    conn.execute(
        """UPDATE checklist_items
           SET status=?, owner=?, due_date=?, updated_at=?
           WHERE id=?""",
        (status, owner, due_date, datetime.now().isoformat(), item_id)
    )
    conn.commit()
    conn.close()


# ── Intake Messages ────────────────────────────────────────────────────────────

def save_intake_message(session_id: int, role: str, content: str):
    conn = get_conn()
    conn.execute(
        "INSERT INTO intake_messages (session_id, role, content) VALUES (?,?,?)",
        (session_id, role, content)
    )
    conn.commit()
    conn.close()


def get_intake_messages(session_id: int):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM intake_messages WHERE session_id = ? ORDER BY created_at",
        (session_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
