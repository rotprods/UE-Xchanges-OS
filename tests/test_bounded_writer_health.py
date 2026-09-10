import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.bootstrap_guard import GuardCode, GuardDecision
from uexchanges.bounded_writer_health import (
    BOUNDED_WRITER_HEALTH_SCOPE,
    evaluate_bounded_writer_authorization_health,
)
from uexchanges.control_plane_health import LeaseHealthRecord, SessionHealthRecord

NOW = datetime(2026, 9, 10, 10, 0, tzinfo=timezone.utc)


def session(
    session_id: str = "SES-CURRENT",
    *,
    agent_id: str = "AGT-CURRENT",
    status: str = "ACTIVE",
    heartbeat_age: int = 5,
) -> SessionHealthRecord:
    return SessionHealthRecord(
        session_id=session_id,
        agent_id=agent_id,
        context_id="CTX-1",
        started_at=NOW - timedelta(minutes=2),
        last_heartbeat=NOW - timedelta(seconds=heartbeat_age),
        status=status,
    )


def lease(
    lease_id: str = "LSE-LIVE",
    *,
    owner_session_id: str = "SES-OWNER",
    owner_agent_id: str = "AGT-OWNER",
    expires_delta: timedelta = timedelta(minutes=10),
) -> LeaseHealthRecord:
    return LeaseHealthRecord(
        lease_id=lease_id,
        owner_session_id=owner_session_id,
        owner_agent_id=owner_agent_id,
        context_id="CTX-1",
        scope="derived:runtimegraph",
        acquired_at=NOW - timedelta(minutes=1),
        expires_at=NOW + expires_delta,
        last_heartbeat=NOW - timedelta(seconds=10),
        status="ACTIVE",
    )


def compliant_guard() -> GuardDecision:
    return GuardDecision(True, (GuardCode.COMPLIANT,))


def denied_guard() -> GuardDecision:
    return GuardDecision(False, (GuardCode.MISSING_BOOTSTRAP_ACK,))


def slo_map(evidence):
    return {item.name: item.passed for item in evidence.report.slos}


class BoundedWriterHealthTests(unittest.TestCase):
    def test_clean_current_writer_passes_required_normal_writer_slos_without_claiming_global_hygiene(self):
        evidence = evaluate_bounded_writer_authorization_health(
            now=NOW,
            current_session_id="SES-CURRENT",
            current_session_rows=(session(),),
            bootstrap_decision=compliant_guard(),
            currently_unexpired_leases=(),
        )

        slos = slo_map(evidence)
        self.assertTrue(slos["bootstrap_compliance"])
        self.assertTrue(slos["session_identity_uniqueness"])
        self.assertTrue(slos["lease_fencing_integrity"])
        self.assertEqual(evidence.scope, BOUNDED_WRITER_HEALTH_SCOPE)
        self.assertFalse(evidence.historical_hygiene_evaluated)
        self.assertEqual(evidence.bootstrap_codes, ("COMPLIANT",))

    def test_missing_current_session_row_fails_closed_instead_of_looking_unique(self):
        with self.assertRaisesRegex(ValueError, "no rows"):
            evaluate_bounded_writer_authorization_health(
                now=NOW,
                current_session_id="SES-CURRENT",
                current_session_rows=(),
                bootstrap_decision=compliant_guard(),
                currently_unexpired_leases=(),
            )

    def test_duplicate_current_session_id_fails_identity_slo(self):
        evidence = evaluate_bounded_writer_authorization_health(
            now=NOW,
            current_session_id="SES-CURRENT",
            current_session_rows=(session(), session()),
            bootstrap_decision=compliant_guard(),
            currently_unexpired_leases=(),
        )
        self.assertFalse(slo_map(evidence)["session_identity_uniqueness"])

    def test_denied_bootstrap_guard_fails_bootstrap_slo(self):
        evidence = evaluate_bounded_writer_authorization_health(
            now=NOW,
            current_session_id="SES-CURRENT",
            current_session_rows=(session(),),
            bootstrap_decision=denied_guard(),
            currently_unexpired_leases=(),
        )
        self.assertFalse(slo_map(evidence)["bootstrap_compliance"])
        self.assertEqual(evidence.bootstrap_codes, ("MISSING_BOOTSTRAP_ACK",))

    def test_bare_boolean_cannot_replace_bootstrap_guard_decision(self):
        with self.assertRaisesRegex(TypeError, "GuardDecision"):
            evaluate_bounded_writer_authorization_health(
                now=NOW,
                current_session_id="SES-CURRENT",
                current_session_rows=(session(),),
                bootstrap_decision=True,  # type: ignore[arg-type]
                currently_unexpired_leases=(),
            )

    def test_unexpired_lease_with_closed_owner_fails_fencing_slo(self):
        evidence = evaluate_bounded_writer_authorization_health(
            now=NOW,
            current_session_id="SES-CURRENT",
            current_session_rows=(session(),),
            bootstrap_decision=compliant_guard(),
            currently_unexpired_leases=(lease(),),
            live_owner_session_rows=(
                session("SES-OWNER", agent_id="AGT-OWNER", status="COMPLETED"),
            ),
        )
        self.assertFalse(slo_map(evidence)["lease_fencing_integrity"])

    def test_unexpired_lease_with_matching_active_owner_preserves_fencing_pass(self):
        evidence = evaluate_bounded_writer_authorization_health(
            now=NOW,
            current_session_id="SES-CURRENT",
            current_session_rows=(session(),),
            bootstrap_decision=compliant_guard(),
            currently_unexpired_leases=(lease(),),
            live_owner_session_rows=(session("SES-OWNER", agent_id="AGT-OWNER"),),
        )
        self.assertTrue(slo_map(evidence)["lease_fencing_integrity"])
        self.assertEqual(evidence.report.metrics["effective_active_leases"], 1)

    def test_expired_row_is_rejected_from_unexpired_input_contract(self):
        expired = lease(expires_delta=timedelta(seconds=-1))
        with self.assertRaisesRegex(ValueError, "expired lease"):
            evaluate_bounded_writer_authorization_health(
                now=NOW,
                current_session_id="SES-CURRENT",
                current_session_rows=(session(),),
                bootstrap_decision=compliant_guard(),
                currently_unexpired_leases=(expired,),
            )

    def test_different_session_id_in_exact_lookup_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "different session_id"):
            evaluate_bounded_writer_authorization_health(
                now=NOW,
                current_session_id="SES-CURRENT",
                current_session_rows=(session("SES-WRONG"),),
                bootstrap_decision=compliant_guard(),
                currently_unexpired_leases=(),
            )


if __name__ == "__main__":
    unittest.main()
