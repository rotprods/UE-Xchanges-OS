import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from uexchanges.coordination import (
    AgentSession,
    EventApplyAction,
    LeaseAction,
    LeaseStatus,
    SessionStatus,
    WorkLease,
    build_idempotency_key,
    create_agent_event,
    decide_lease,
    evaluate_event_application,
    heartbeat_lease,
    heartbeat_session,
    make_session_id,
    release_lease,
)

UTC = timezone.utc
NOW = datetime(2026, 8, 29, 18, 0, tzinfo=UTC)


class SessionTests(unittest.TestCase):
    def test_session_id_is_stable_and_readable(self):
        self.assertEqual(
            make_session_id(
                project_id="UE-Xchanges-OS",
                platform="ChatGPT",
                started_at=NOW,
                sequence=1,
            ),
            "SES-UE-XCHANGES-OS-CHATGPT-20260829T180000-01",
        )

    def test_naive_session_time_is_rejected(self):
        with self.assertRaises(ValueError):
            make_session_id(
                project_id="UEX",
                platform="ChatGPT",
                started_at=datetime(2026, 8, 29),
                sequence=1,
            )

    def test_session_heartbeat_is_monotonic(self):
        session = AgentSession("s", "a", "p", "c", NOW, NOW)
        updated = heartbeat_session(session, at=NOW + timedelta(minutes=5))
        self.assertEqual(updated.last_heartbeat, NOW + timedelta(minutes=5))
        with self.assertRaises(ValueError):
            heartbeat_session(updated, at=NOW)

    def test_terminal_session_cannot_heartbeat(self):
        session = AgentSession(
            "s", "a", "p", "c", NOW, NOW, status=SessionStatus.COMPLETED
        )
        with self.assertRaises(ValueError):
            heartbeat_session(session, at=NOW + timedelta(minutes=1))


class LeaseTests(unittest.TestCase):
    def request(self, existing=None, session="s1", agent="a1", now=NOW):
        return decide_lease(
            existing=existing,
            lease_id=f"lease-{session}",
            project_id="project",
            context_id="context",
            resource_type="opportunity",
            resource_id="opp-1",
            requester_agent_id=agent,
            requester_session_id=session,
            now=now,
            expires_at=now + timedelta(hours=2),
        )

    def test_acquire_when_unowned(self):
        decision = self.request()
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, LeaseAction.ACQUIRE)

    def test_same_owner_renews(self):
        first = self.request().lease
        decision = self.request(existing=first, now=NOW + timedelta(minutes=10))
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, LeaseAction.RENEW)
        self.assertEqual(decision.lease.lease_id, first.lease_id)

    def test_other_active_owner_is_blocked(self):
        first = self.request().lease
        decision = self.request(existing=first, session="s2", agent="a2")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.action, LeaseAction.BLOCK_CONFLICT)

    def test_expired_lease_can_be_taken_over(self):
        first = self.request().lease
        decision = self.request(
            existing=first,
            session="s2",
            agent="a2",
            now=NOW + timedelta(hours=3),
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, LeaseAction.TAKEOVER_EXPIRED)
        self.assertEqual(decision.lease.owner_session_id, "s2")

    def test_release_requires_owner(self):
        lease = self.request().lease
        with self.assertRaises(ValueError):
            release_lease(
                lease,
                requester_session_id="other",
                at=NOW + timedelta(minutes=5),
                reason="done",
            )
        released = release_lease(
            lease,
            requester_session_id="s1",
            at=NOW + timedelta(minutes=5),
            reason="handoff complete",
        )
        self.assertEqual(released.status, LeaseStatus.RELEASED)

    def test_expired_lease_cannot_heartbeat(self):
        lease = self.request().lease
        with self.assertRaises(ValueError):
            heartbeat_lease(lease, at=NOW + timedelta(hours=2))


class EventTests(unittest.TestCase):
    def event(self, *, session="s1", agent="a1", lease_id="lease-s1"):
        return create_agent_event(
            occurred_at=NOW,
            project_id="project",
            context_id="context",
            session_id=session,
            agent_id=agent,
            event_type="SOURCE_VERIFIED",
            entity_type="opportunity",
            entity_id="opp-1",
            operation="VERIFY",
            authoritative_source_version="sha256:source-v1",
            lease_id=lease_id,
        )

    def lease(self):
        return decide_lease(
            existing=None,
            lease_id="lease-s1",
            project_id="project",
            context_id="context",
            resource_type="opportunity",
            resource_id="opp-1",
            requester_agent_id="a1",
            requester_session_id="s1",
            now=NOW - timedelta(minutes=1),
            expires_at=NOW + timedelta(hours=1),
        ).lease

    def test_idempotency_key_and_event_id_are_deterministic(self):
        key1 = build_idempotency_key(
            project_id="p",
            entity_type="opportunity",
            entity_id="o",
            operation="VERIFY",
            authoritative_source_version="v1",
        )
        key2 = build_idempotency_key(
            project_id="p",
            entity_type="opportunity",
            entity_id="o",
            operation="VERIFY",
            authoritative_source_version="v1",
        )
        self.assertEqual(key1, key2)
        self.assertEqual(self.event().event_id, self.event().event_id)

    def test_duplicate_is_ignored_before_lease_evaluation(self):
        event = self.event()
        decision = evaluate_event_application(
            event=event,
            seen_idempotency_keys={event.idempotency_key},
            lease=None,
            now=NOW,
        )
        self.assertEqual(decision.action, EventApplyAction.IGNORE_DUPLICATE)

    def test_mutation_without_lease_is_blocked(self):
        decision = evaluate_event_application(
            event=self.event(), seen_idempotency_keys=set(), lease=None, now=NOW
        )
        self.assertEqual(decision.action, EventApplyAction.BLOCK_NO_LEASE)

    def test_wrong_owner_is_blocked(self):
        decision = evaluate_event_application(
            event=self.event(session="s2", agent="a2"),
            seen_idempotency_keys=set(),
            lease=self.lease(),
            now=NOW,
        )
        self.assertEqual(decision.action, EventApplyAction.BLOCK_WRONG_OWNER)

    def test_scope_mismatch_is_blocked(self):
        event = create_agent_event(
            occurred_at=NOW,
            project_id="project",
            context_id="context",
            session_id="s1",
            agent_id="a1",
            event_type="SOURCE_VERIFIED",
            entity_type="opportunity",
            entity_id="opp-2",
            operation="VERIFY",
            authoritative_source_version="v1",
            lease_id="lease-s1",
        )
        decision = evaluate_event_application(
            event=event,
            seen_idempotency_keys=set(),
            lease=self.lease(),
            now=NOW,
        )
        self.assertEqual(decision.action, EventApplyAction.BLOCK_SCOPE_MISMATCH)

    def test_owned_active_lease_allows_mutation(self):
        decision = evaluate_event_application(
            event=self.event(),
            seen_idempotency_keys=set(),
            lease=self.lease(),
            now=NOW,
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.action, EventApplyAction.APPLY)

    def test_read_only_event_does_not_require_lease(self):
        decision = evaluate_event_application(
            event=self.event(lease_id=""),
            seen_idempotency_keys=set(),
            lease=None,
            now=NOW,
            mutating=False,
        )
        self.assertTrue(decision.allowed)


if __name__ == "__main__":
    unittest.main()
