import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    id TEXT PRIMARY KEY,
    sgg_cd TEXT NOT NULL,
    umd TEXT,
    apt_seq TEXT,
    apt_name TEXT NOT NULL,
    jibun TEXT,
    area REAL NOT NULL,
    floor INTEGER,
    build_year INTEGER,
    deal_date TEXT NOT NULL,
    deal_ym TEXT NOT NULL,
    price INTEGER NOT NULL,          -- 만원
    canceled INTEGER NOT NULL DEFAULT 0,
    dealing_type TEXT,
    collected_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_trades_sgg_ym ON trades(sgg_cd, deal_ym);
CREATE INDEX IF NOT EXISTS ix_trades_complex ON trades(sgg_cd, apt_seq, apt_name);

CREATE TABLE IF NOT EXISTS posts (
    slug TEXT PRIMARY KEY,
    kind TEXT NOT NULL,              -- gu_monthly | complex
    region_code TEXT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    body_md TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]',
    facts_json TEXT NOT NULL,
    trade_count INTEGER NOT NULL,
    charts TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    revision INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS rejections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL,
    reasons TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS videos (
    slug TEXT PRIMARY KEY,            -- 원본 글 slug 와 동일
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    tags TEXT NOT NULL,
    seconds REAL NOT NULL,
    status TEXT NOT NULL,             -- rendered | uploaded | upload_failed
    youtube_id TEXT,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT,
    summary TEXT
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect(path: Path | str = DB_PATH) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert_trades(conn: sqlite3.Connection, rows: list[dict]) -> int:
    """새로 들어온 거래 수를 반환. 기존 거래는 해제(취소) 여부만 갱신."""
    before = count_trades(conn)
    for r in rows:
        conn.execute(
            """INSERT INTO trades (id, sgg_cd, umd, apt_seq, apt_name, jibun, area, floor,
                   build_year, deal_date, deal_ym, price, canceled, dealing_type, collected_at)
               VALUES (:id, :sgg_cd, :umd, :apt_seq, :apt_name, :jibun, :area, :floor,
                   :build_year, :deal_date, :deal_ym, :price, :canceled, :dealing_type, :collected_at)
               ON CONFLICT(id) DO UPDATE SET canceled = excluded.canceled""",
            {**r, "collected_at": now_iso()},
        )
    conn.commit()
    return count_trades(conn) - before


def count_trades(conn) -> int:
    return conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]


def get_post(conn, slug: str):
    return conn.execute("SELECT * FROM posts WHERE slug = ?", (slug,)).fetchone()


def save_post(conn, post: dict) -> None:
    existing = get_post(conn, post["slug"])
    ts = now_iso()
    payload = {
        **post,
        "tags": json.dumps(post.get("tags", []), ensure_ascii=False),
        "charts": json.dumps(post.get("charts", []), ensure_ascii=False),
        "facts_json": json.dumps(post["facts"], ensure_ascii=False, sort_keys=True),
        "updated_at": ts,
    }
    if existing:
        conn.execute(
            """UPDATE posts SET title=:title, description=:description, body_md=:body_md, tags=:tags,
                   facts_json=:facts_json, trade_count=:trade_count, charts=:charts,
                   updated_at=:updated_at, revision=revision+1 WHERE slug=:slug""",
            payload,
        )
    else:
        conn.execute(
            """INSERT INTO posts (slug, kind, region_code, title, description, body_md, tags,
                   facts_json, trade_count, charts, created_at, updated_at)
               VALUES (:slug, :kind, :region_code, :title, :description, :body_md, :tags,
                   :facts_json, :trade_count, :charts, :updated_at, :updated_at)""",
            payload,
        )
    conn.commit()


def log_rejection(conn, slug: str, reasons: list[str]) -> None:
    conn.execute(
        "INSERT INTO rejections (slug, reasons, created_at) VALUES (?, ?, ?)",
        (slug, json.dumps(reasons, ensure_ascii=False), now_iso()),
    )
    conn.commit()


def start_run(conn) -> int:
    cur = conn.execute("INSERT INTO runs (started_at) VALUES (?)", (now_iso(),))
    conn.commit()
    return cur.lastrowid


def finish_run(conn, run_id: int, status: str, summary: dict) -> None:
    conn.execute(
        "UPDATE runs SET finished_at=?, status=?, summary=? WHERE id=?",
        (now_iso(), status, json.dumps(summary, ensure_ascii=False), run_id),
    )
    conn.commit()
