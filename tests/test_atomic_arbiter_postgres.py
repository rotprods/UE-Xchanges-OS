"""PostgreSQL integration gauntlet for the atomic arbiter.

The normal Python unit matrix skips this module because it deliberately has no
runtime DB dependency.  The dedicated CI job sets TEST_DATABASE_URL and installs
psycopg, then runs these tests against an ephemeral PostgreSQL service.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path
import unittest


DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")
if DATABASE_URL:
    import psycopg  # type: ignore[import-not-found]
else:  # pragma: no cover - exercised by the dependency-free unit matrix
    psycopg = None

ROOT = Path(__file__).resolve().parents[1]
SQL = (ROOT / "sql" / "atomic_arbiter_v1.sql").read_text(encoding="utf-8")
MAIN = "a" * 40
BOOTSTRAP = "1.2.0"
PAYLOAD = sha256(b"payload").hexdigest()


@unittest.skipUnless(DATABASE_URL, "TEST_DATABASE_URL is required for PostgreSQL gauntlet")
class AtomicArbiterPostgresTests(unittest.TestCase):
    def connect(self):
        assert psycopg is not None
        return psycopg.connect(DATABASE_URL, autocommit=True)

    def setUp(self) -> None:
        with self.connect() as conn:
            conn.execute("DROP SCHEMA IF EXISTS uex_arbiter CASCADE")
            conn.execute(SQL, prepare=False)

    def register(self, session: str, agent: str | None = None) -> None:
        with self.connect() as conn:
            conn.execute(
                "SELECT uex_arbiter.register_agent_session(%s,%s,%s,%s,%s::jsonb)",
                (session, agent or f"agent-{session}", MAIN, BOOTSTRAP, json.dumps({"test": True})),
            )

    def claim(
        self,
        session: str,
        lease: str,
        scopes: list[str],
        *,
        ttl: int = 900,
        expected_revision: str = MAIN,
    ) -> tuple[str, int, str]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT lease_id, fencing_token, scope_hash "
                "FROM uex_arbiter.claim_scope_set(%s,%s,%s,%s,%s)",
                (lease, session, scopes, expected_revision, ttl),
            ).fetchone()
            assert row is not None
            return str(row[0]), int(row[1]), str(row[2])

    def reserve(
        self,
        *,
        effect_key: str,
        application_id: str,
        session: str,
        lease: str,
        token: int,
    ) -> tuple[str, int]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT state, attempt_no FROM uex_arbiter.reserve_external_effect(" 
                "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (
                    effect_key,
                    "EMAIL_INITIAL",
                    application_id,
                    "org-1",
                    "gmail",
                    "organiser@example.org",
                    PAYLOAD,
                    lease,
                    session,
                    token,
                ),
            ).fetchone()
            assert row is not None
            return str(row[0]), int(row[1])

    def expire_lease_for_test(self, lease_id: str) -> None:
        """Move a lease into a valid historical interval entirely in the past.

        Production rows keep the invariant ``expires_at > acquired_at``.  Tests
        must not disable or violate that integrity check merely to simulate time.
        """
        with self.connect() as conn:
            conn.execute(
                "UPDATE uex_arbiter.work_leases "
                "SET acquired_at=clock_timestamp()-interval '2 seconds', "
                "    expires_at=clock_timestamp()-interval '1 second' "
                "WHERE lease_id=%s",
                (lease_id,),
            )

    def test_fifty_contenders_exactly_one_scope_winner(self):
        contenders = 50
        for i in range(contenders):
            self.register(f"s{i}")

        def compete(i: int) -> str:
            try:
                self.claim(f"s{i}", f"l{i}", ["APPLICATION:app-same"])
                return "won"
            except Exception as exc:
                self.assertIn("SCOPE_CONFLICT", str(exc))
                return "blocked"

        with ThreadPoolExecutor(max_workers=contenders) as pool:
            results = list(pool.map(compete, range(contenders)))
        self.assertEqual(results.count("won"), 1)
        self.assertEqual(results.count("blocked"), contenders - 1)

        with self.connect() as conn:
            active = conn.execute(
                "SELECT count(*) FROM uex_arbiter.work_leases WHERE state='ACTIVE'"
            ).fetchone()[0]
            owners = conn.execute("SELECT count(*) FROM uex_arbiter.scope_owners").fetchone()[0]
        self.assertEqual(active, 1)
        self.assertEqual(owners, 1)

    def test_opposite_scope_order_has_no_deadlock_and_one_winner(self):
        self.register("s1")
        self.register("s2")
        scopes_a = ["APPLICATION:app", "ORGCALL:org:call"]
        scopes_b = list(reversed(scopes_a))

        def claim_one(session: str, lease: str, scopes: list[str]) -> str:
            try:
                self.claim(session, lease, scopes)
                return "won"
            except Exception as exc:
                self.assertIn("SCOPE_CONFLICT", str(exc))
                return "blocked"

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [
                pool.submit(claim_one, "s1", "l1", scopes_a),
                pool.submit(claim_one, "s2", "l2", scopes_b),
            ]
            results = [f.result(timeout=10) for f in futures]
        self.assertEqual(results.count("won"), 1)
        self.assertEqual(results.count("blocked"), 1)

    def test_one_mutable_lease_per_session(self):
        self.register("s1")
        self.claim("s1", "l1", ["APPLICATION:one"])
        with self.assertRaises(Exception) as ctx:
            self.claim("s1", "l2", ["APPLICATION:two"])
        self.assertIn("SESSION_ALREADY_HAS_ACTIVE_LEASE", str(ctx.exception))

    def test_expired_takeover_increments_fence_and_zombie_token_fails(self):
        self.register("s1")
        self.register("s2")
        _, old_token, _ = self.claim("s1", "l1", ["APPLICATION:app"])
        self.expire_lease_for_test("l1")
        _, new_token, _ = self.claim("s2", "l2", ["APPLICATION:app"])
        self.assertGreater(new_token, old_token)

        with self.connect() as conn:
            with self.assertRaises(Exception) as ctx:
                conn.execute(
                    "SELECT uex_arbiter.heartbeat_lease(%s,%s,%s,%s)",
                    ("l1", "s1", old_token, 900),
                )
        self.assertIn("LEASE_NOT_ACTIVE", str(ctx.exception))

    def test_concurrent_effect_reservation_exactly_one_winner(self):
        self.register("s1")
        _, token, _ = self.claim("s1", "l1", ["APPLICATION:app"])
        effect = "v1:EMAIL_INITIAL:app"

        def compete(_: int) -> str:
            try:
                self.reserve(
                    effect_key=effect,
                    application_id="app",
                    session="s1",
                    lease="l1",
                    token=token,
                )
                return "won"
            except Exception as exc:
                self.assertIn("EFFECT_BLOCKED:RESERVED", str(exc))
                return "blocked"

        with ThreadPoolExecutor(max_workers=20) as pool:
            results = list(pool.map(compete, range(20)))
        self.assertEqual(results.count("won"), 1)
        self.assertEqual(results.count("blocked"), 19)

    def test_started_effect_survives_process_death_and_requires_reconciliation(self):
        self.register("s1")
        self.register("s2")
        _, token1, _ = self.claim("s1", "l1", ["APPLICATION:app"])
        effect = "v1:EMAIL_INITIAL:app"
        self.reserve(
            effect_key=effect,
            application_id="app",
            session="s1",
            lease="l1",
            token=token1,
        )
        with self.connect() as conn:
            conn.execute(
                "SELECT uex_arbiter.mark_effect_started(%s,%s,%s,%s)",
                (effect, "l1", "s1", token1),
            )
        # Simulate worker death after provider invocation while preserving all
        # lease integrity constraints.
        self.expire_lease_for_test("l1")

        _, token2, _ = self.claim("s2", "l2", ["APPLICATION:app"])
        with self.assertRaises(Exception) as ctx:
            self.reserve(
                effect_key=effect,
                application_id="app",
                session="s2",
                lease="l2",
                token=token2,
            )
        self.assertIn("EFFECT_BLOCKED:STARTED", str(ctx.exception))

        with self.connect() as conn:
            conn.execute(
                "SELECT uex_arbiter.resolve_external_effect(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (effect, "UNCERTAIN", "l2", "s2", token2, "provider-timeout", "", "", "TIMEOUT"),
            )
        with self.assertRaises(Exception) as ctx2:
            self.reserve(
                effect_key=effect,
                application_id="app",
                session="s2",
                lease="l2",
                token=token2,
            )
        self.assertIn("EFFECT_BLOCKED:UNCERTAIN", str(ctx2.exception))

        # Only authoritative no-effect reconciliation opens a new attempt.
        with self.connect() as conn:
            conn.execute(
                "SELECT uex_arbiter.resolve_external_effect(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (effect, "FAILED_NO_EFFECT", "l2", "s2", token2, "gmail-search-no-match", "", "", "PROVEN_NOT_SENT"),
            )
        state, attempt = self.reserve(
            effect_key=effect,
            application_id="app",
            session="s2",
            lease="l2",
            token=token2,
        )
        self.assertEqual((state, attempt), ("RESERVED", 2))

    def test_confirmed_effect_is_terminal_for_reservation(self):
        self.register("s1")
        _, token, _ = self.claim("s1", "l1", ["APPLICATION:app"])
        effect = "v1:EMAIL_INITIAL:app"
        self.reserve(
            effect_key=effect,
            application_id="app",
            session="s1",
            lease="l1",
            token=token,
        )
        with self.connect() as conn:
            conn.execute(
                "SELECT uex_arbiter.mark_effect_started(%s,%s,%s,%s)",
                (effect, "l1", "s1", token),
            )
            conn.execute(
                "SELECT uex_arbiter.resolve_external_effect(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (effect, "CONFIRMED", "l1", "s1", token, "gmail-readback", "msg-1", "", ""),
            )
        with self.assertRaises(Exception) as ctx:
            self.reserve(
                effect_key=effect,
                application_id="app",
                session="s1",
                lease="l1",
                token=token,
            )
        self.assertIn("EFFECT_BLOCKED:CONFIRMED", str(ctx.exception))

    def test_outbox_is_transactional_and_conflict_creates_no_false_event(self):
        self.register("s1")
        self.register("s2")
        self.claim("s1", "l1", ["APPLICATION:app"])
        with self.assertRaises(Exception):
            self.claim("s2", "l2", ["APPLICATION:app"])

        with self.connect() as conn:
            acquired = conn.execute(
                "SELECT count(*) FROM uex_arbiter.coordination_outbox "
                "WHERE event_type='LEASE_ACQUIRED'"
            ).fetchone()[0]
            false_l2 = conn.execute(
                "SELECT count(*) FROM uex_arbiter.coordination_outbox "
                "WHERE idempotency_key='LEASE_ACQUIRED:l2'"
            ).fetchone()[0]
        self.assertEqual(acquired, 1)
        self.assertEqual(false_l2, 0)

    def test_release_removes_scope_owner_and_old_fence_cannot_mutate(self):
        self.register("s1")
        _, token, _ = self.claim("s1", "l1", ["APPLICATION:app"])
        with self.connect() as conn:
            conn.execute(
                "SELECT uex_arbiter.release_lease(%s,%s,%s,%s)",
                ("l1", "s1", token, "done"),
            )
            owners = conn.execute("SELECT count(*) FROM uex_arbiter.scope_owners").fetchone()[0]
            state = conn.execute(
                "SELECT state FROM uex_arbiter.work_leases WHERE lease_id='l1'"
            ).fetchone()[0]
            with self.assertRaises(Exception) as ctx:
                conn.execute(
                    "SELECT uex_arbiter.heartbeat_lease(%s,%s,%s,%s)",
                    ("l1", "s1", token, 900),
                )
        self.assertEqual(owners, 0)
        self.assertEqual(state, "RELEASED")
        self.assertIn("LEASE_NOT_ACTIVE", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
