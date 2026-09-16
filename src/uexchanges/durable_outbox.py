"""Durable SQLite implementation of the outbound effect outbox.

The durable effect identity intentionally excludes authoritative source version:
a newer infopack/source revision may change the prepared packet, but it must not
create permission for a second initial email for the same organisation/call/
application/intent.

SQLite is the first durable local reference. It provides transactional/CAS
semantics for one shared database file. A future remote/multi-host store must
preserve the same Outbox contract and state-transition invariants.
"""
from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from pathlib import Path
import sqlite3

from .outbound_gateway import EffectBlocked, EffectKey, EffectRecord, EffectState


SCHEMA_VERSION = 1


def stable_effect_digest(key: EffectKey) -> str:
    """Stable at-most-once identity, deliberately independent of source revision."""
    raw = "|".join((key.organization_id, key.call_id, key.application_id, key.intent))
    return sha256(raw.encode()).hexdigest()


def _dt(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("stored timestamp must be timezone-aware")
    return parsed


class SqliteOutbox:
    """Transactional durable Outbox implementation backed by one SQLite file."""

    def __init__(self, path: str | Path, *, timeout_seconds: float = 5.0) -> None:
        self.path = Path(path)
        if str(self.path) == ":memory:":
            raise ValueError("durable outbox requires a filesystem database path")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.timeout_seconds = timeout_seconds
        self._initialise()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.path,
            timeout=self.timeout_seconds,
            isolation_level=None,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    def _initialise(self) -> None:
        with self._connect() as conn:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS outbound_effects (
                    key_digest TEXT PRIMARY KEY,
                    packet_digest TEXT NOT NULL,
                    source_version TEXT NOT NULL,
                    state TEXT NOT NULL,
                    generation INTEGER NOT NULL CHECK(generation >= 1),
                    fence_lease_id TEXT NOT NULL,
                    reserved_at TEXT NOT NULL,
                    provider_message_id TEXT NOT NULL DEFAULT '',
                    provider_thread_id TEXT NOT NULL DEFAULT '',
                    reconciliation_ref TEXT NOT NULL DEFAULT ''
                )
                """
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS outbound_meta (k TEXT PRIMARY KEY, v TEXT NOT NULL)"
            )
            conn.execute(
                "INSERT INTO outbound_meta(k, v) VALUES('schema_version', ?) "
                "ON CONFLICT(k) DO UPDATE SET v=excluded.v",
                (str(SCHEMA_VERSION),),
            )

    @staticmethod
    def _record(row: sqlite3.Row) -> EffectRecord:
        return EffectRecord(
            key_digest=row["key_digest"],
            packet_digest=row["packet_digest"],
            state=EffectState(row["state"]),
            generation=int(row["generation"]),
            fence_lease_id=row["fence_lease_id"],
            reserved_at=_dt(row["reserved_at"]),
            provider_message_id=row["provider_message_id"],
            provider_thread_id=row["provider_thread_id"],
            reconciliation_ref=row["reconciliation_ref"],
        )

    @staticmethod
    def _select(conn: sqlite3.Connection, key_digest: str) -> sqlite3.Row | None:
        return conn.execute(
            "SELECT * FROM outbound_effects WHERE key_digest = ?",
            (key_digest,),
        ).fetchone()

    def reserve(
        self,
        key: EffectKey,
        packet_digest: str,
        lease_id: str,
        now: datetime,
    ) -> EffectRecord:
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must be timezone-aware")
        if not packet_digest.strip() or not lease_id.strip():
            raise ValueError("packet_digest and lease_id are required")
        kd = stable_effect_digest(key)
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            old = self._select(conn, kd)
            if old is None:
                generation = 1
                conn.execute(
                    """
                    INSERT INTO outbound_effects(
                        key_digest, packet_digest, source_version, state, generation,
                        fence_lease_id, reserved_at, provider_message_id,
                        provider_thread_id, reconciliation_ref
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, '', '', '')
                    """,
                    (
                        kd,
                        packet_digest,
                        key.authoritative_source_version,
                        EffectState.RESERVED.value,
                        generation,
                        lease_id,
                        now.isoformat(),
                    ),
                )
            else:
                state = EffectState(old["state"])
                if state is not EffectState.NOT_SENT:
                    raise EffectBlocked(f"EXISTING_EFFECT:{state.value}")
                generation = int(old["generation"]) + 1
                conn.execute(
                    """
                    UPDATE outbound_effects
                    SET packet_digest=?, source_version=?, state=?, generation=?,
                        fence_lease_id=?, reserved_at=?, provider_message_id='',
                        provider_thread_id='', reconciliation_ref=''
                    WHERE key_digest=? AND state=?
                    """,
                    (
                        packet_digest,
                        key.authoritative_source_version,
                        EffectState.RESERVED.value,
                        generation,
                        lease_id,
                        now.isoformat(),
                        kd,
                        EffectState.NOT_SENT.value,
                    ),
                )
            row = self._select(conn, kd)
            assert row is not None
            conn.execute("COMMIT")
            return self._record(row)
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def begin(self, key_digest: str, lease_id: str) -> EffectRecord:
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            old = self._select(conn, key_digest)
            if old is None or EffectState(old["state"]) is not EffectState.RESERVED:
                raise EffectBlocked("RESERVATION_REQUIRED")
            if old["fence_lease_id"] != lease_id:
                raise EffectBlocked("FENCE_TOKEN_MISMATCH")
            changed = conn.execute(
                "UPDATE outbound_effects SET state=? WHERE key_digest=? AND state=? AND fence_lease_id=?",
                (
                    EffectState.SEND_IN_PROGRESS.value,
                    key_digest,
                    EffectState.RESERVED.value,
                    lease_id,
                ),
            ).rowcount
            if changed != 1:
                raise EffectBlocked("RESERVATION_CHANGED_CONCURRENTLY")
            row = self._select(conn, key_digest)
            assert row is not None
            conn.execute("COMMIT")
            return self._record(row)
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def finish(
        self,
        key_digest: str,
        state: EffectState,
        *,
        message_id: str = "",
        thread_id: str = "",
        ref: str = "",
    ) -> EffectRecord:
        if state not in {
            EffectState.SEND_CONFIRMED,
            EffectState.OUTCOME_UNKNOWN,
            EffectState.DELIVERY_FAILED,
        }:
            raise ValueError("invalid finish state")
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            old = self._select(conn, key_digest)
            if old is None or EffectState(old["state"]) is not EffectState.SEND_IN_PROGRESS:
                raise EffectBlocked("SEND_IN_PROGRESS_REQUIRED")
            changed = conn.execute(
                """
                UPDATE outbound_effects
                SET state=?, provider_message_id=?, provider_thread_id=?, reconciliation_ref=?
                WHERE key_digest=? AND state=?
                """,
                (
                    state.value,
                    message_id,
                    thread_id,
                    ref,
                    key_digest,
                    EffectState.SEND_IN_PROGRESS.value,
                ),
            ).rowcount
            if changed != 1:
                raise EffectBlocked("SEND_STATE_CHANGED_CONCURRENTLY")
            row = self._select(conn, key_digest)
            assert row is not None
            conn.execute("COMMIT")
            return self._record(row)
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def get(self, key_digest: str) -> EffectRecord | None:
        with self._connect() as conn:
            row = self._select(conn, key_digest)
            return None if row is None else self._record(row)

    def reconcile_not_sent(self, key_digest: str, ref: str) -> EffectRecord:
        if not ref.strip():
            raise ValueError("authoritative reconciliation ref required")
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            old = self._select(conn, key_digest)
            allowed = {EffectState.OUTCOME_UNKNOWN, EffectState.DELIVERY_FAILED}
            if old is None or EffectState(old["state"]) not in allowed:
                raise EffectBlocked("RECONCILIATION_NOT_APPLICABLE")
            changed = conn.execute(
                """
                UPDATE outbound_effects
                SET state=?, reconciliation_ref=?
                WHERE key_digest=? AND state IN (?, ?)
                """,
                (
                    EffectState.NOT_SENT.value,
                    ref,
                    key_digest,
                    EffectState.OUTCOME_UNKNOWN.value,
                    EffectState.DELIVERY_FAILED.value,
                ),
            ).rowcount
            if changed != 1:
                raise EffectBlocked("RECONCILIATION_CHANGED_CONCURRENTLY")
            row = self._select(conn, key_digest)
            assert row is not None
            conn.execute("COMMIT")
            return self._record(row)
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def recover_in_progress_unknown(self, key_digest: str, ref: str) -> EffectRecord:
        """Fence crash recovery: in-progress may become UNKNOWN, never NOT_SENT."""
        if not ref.strip():
            raise ValueError("recovery ref required")
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            old = self._select(conn, key_digest)
            if old is None or EffectState(old["state"]) is not EffectState.SEND_IN_PROGRESS:
                raise EffectBlocked("IN_PROGRESS_RECOVERY_NOT_APPLICABLE")
            changed = conn.execute(
                """
                UPDATE outbound_effects
                SET state=?, reconciliation_ref=?
                WHERE key_digest=? AND state=?
                """,
                (
                    EffectState.OUTCOME_UNKNOWN.value,
                    ref,
                    key_digest,
                    EffectState.SEND_IN_PROGRESS.value,
                ),
            ).rowcount
            if changed != 1:
                raise EffectBlocked("IN_PROGRESS_CHANGED_CONCURRENTLY")
            row = self._select(conn, key_digest)
            assert row is not None
            conn.execute("COMMIT")
            return self._record(row)
        except Exception:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def source_version(self, key_digest: str) -> str | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT source_version FROM outbound_effects WHERE key_digest=?",
                (key_digest,),
            ).fetchone()
            return None if row is None else str(row[0])
