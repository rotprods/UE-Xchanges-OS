from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class FetchState:
    source_id: str
    url: str
    etag: str | None
    last_modified: str | None
    content_hash: str | None
    last_status: int | None
    last_fetched_at: str | None
    last_changed_at: str | None


class SourceStateStore:
    """Small durable state store for incremental collectors.

    SQLite is deliberately sufficient for the single-operator v1. The schema is
    migration-friendly and can later be projected into Postgres/Supabase.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def _migrate(self) -> None:
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS fetch_state (
              source_id TEXT NOT NULL,
              url TEXT NOT NULL,
              etag TEXT,
              last_modified TEXT,
              content_hash TEXT,
              last_status INTEGER,
              last_fetched_at TEXT,
              last_changed_at TEXT,
              PRIMARY KEY (source_id, url)
            );
            CREATE TABLE IF NOT EXISTS candidate_seen (
              fingerprint TEXT PRIMARY KEY,
              source_id TEXT NOT NULL,
              canonical_url TEXT NOT NULL,
              first_seen_at TEXT NOT NULL,
              last_seen_at TEXT NOT NULL,
              last_content_hash TEXT,
              status TEXT NOT NULL DEFAULT 'discovered'
            );
            CREATE INDEX IF NOT EXISTS idx_candidate_source ON candidate_seen(source_id);
            CREATE INDEX IF NOT EXISTS idx_candidate_url ON candidate_seen(canonical_url);
            """
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def get_fetch_state(self, source_id: str, url: str) -> FetchState | None:
        row = self._conn.execute(
            "SELECT * FROM fetch_state WHERE source_id=? AND url=?", (source_id, url)
        ).fetchone()
        if row is None:
            return None
        return FetchState(**dict(row))

    def conditional_headers(self, source_id: str, url: str) -> dict[str, str]:
        state = self.get_fetch_state(source_id, url)
        if state is None:
            return {}
        headers: dict[str, str] = {}
        if state.etag:
            headers["If-None-Match"] = state.etag
        if state.last_modified:
            headers["If-Modified-Since"] = state.last_modified
        return headers

    def record_fetch(
        self,
        source_id: str,
        url: str,
        *,
        status: int,
        content_hash: str | None,
        etag: str | None = None,
        last_modified: str | None = None,
        fetched_at: str | None = None,
    ) -> bool:
        """Persist fetch metadata and return True only when content changed."""
        fetched_at = fetched_at or _now()
        previous = self.get_fetch_state(source_id, url)
        changed = previous is None or (
            content_hash is not None and content_hash != previous.content_hash
        )
        changed_at = fetched_at if changed else (previous.last_changed_at if previous else fetched_at)
        self._conn.execute(
            """
            INSERT INTO fetch_state(source_id,url,etag,last_modified,content_hash,last_status,last_fetched_at,last_changed_at)
            VALUES(?,?,?,?,?,?,?,?)
            ON CONFLICT(source_id,url) DO UPDATE SET
              etag=excluded.etag,
              last_modified=excluded.last_modified,
              content_hash=COALESCE(excluded.content_hash, fetch_state.content_hash),
              last_status=excluded.last_status,
              last_fetched_at=excluded.last_fetched_at,
              last_changed_at=excluded.last_changed_at
            """,
            (source_id, url, etag, last_modified, content_hash, status, fetched_at, changed_at),
        )
        self._conn.commit()
        return changed

    def mark_candidate_seen(
        self,
        fingerprint: str,
        source_id: str,
        canonical_url: str,
        *,
        content_hash: str | None = None,
        seen_at: str | None = None,
    ) -> bool:
        """Return True when this fingerprint is new to the local state store."""
        seen_at = seen_at or _now()
        existing = self._conn.execute(
            "SELECT fingerprint FROM candidate_seen WHERE fingerprint=?", (fingerprint,)
        ).fetchone()
        self._conn.execute(
            """
            INSERT INTO candidate_seen(fingerprint,source_id,canonical_url,first_seen_at,last_seen_at,last_content_hash)
            VALUES(?,?,?,?,?,?)
            ON CONFLICT(fingerprint) DO UPDATE SET
              last_seen_at=excluded.last_seen_at,
              last_content_hash=COALESCE(excluded.last_content_hash, candidate_seen.last_content_hash)
            """,
            (fingerprint, source_id, canonical_url, seen_at, seen_at, content_hash),
        )
        self._conn.commit()
        return existing is None

    def candidate_count(self, source_id: str | None = None) -> int:
        if source_id is None:
            row = self._conn.execute("SELECT COUNT(*) AS n FROM candidate_seen").fetchone()
        else:
            row = self._conn.execute(
                "SELECT COUNT(*) AS n FROM candidate_seen WHERE source_id=?", (source_id,)
            ).fetchone()
        return int(row["n"])
