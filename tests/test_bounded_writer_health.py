from datetime import datetime, timedelta, timezone

import pytest

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


def slo_map(evidence):
    return {item.name: item.passed for item in evidence.report.slos}


def test_clean_current_writer_passes_required_normal_writer_slos_without_claiming_global_hygiene():
    evidence = evaluate_bounded_writer_authorization_health(
        now=NOW,
        current_session_id="SES-CURRENT",
        current_session_rows=(session(),),
        bootstrap_compliant=True,
        currently_unexpired_leases=(),
    )

    slos = slo_map(evidence)
    assert slos["bootstrap_compliance"] is True
    assert slos["session_identity_uniqueness"] is True
    assert slos["lease_fencing_integrity"] is True
    assert evidence.scope == BOUNDED_WRITER_HEALTH_SCOPE
    assert evidence.historical_hygiene_evaluated is False


def test_missing_current_session_row_fails_closed_instead_of_looking_unique():
    with pytest.raises(ValueError, match="no rows"):
        evaluate_bounded_writer_authorization_health(
            now=NOW,
            current_session_id="SES-CURRENT",
            current_session_rows=(),
            bootstrap_compliant=True,
            currently_unexpired_leases=(),
        )


def test_duplicate_current_session_id_fails_identity_slo():
    evidence = evaluate_bounded_writer_authorization_health(
        now=NOW,
        current_session_id="SES-CURRENT",
        current_session_rows=(session(), session()),
        bootstrap_compliant=True,
        currently_unexpired_leases=(),
    )
    assert slo_map(evidence)["session_identity_uniqueness"] is False


def test_current_writer_bootstrap_failure_fails_bootstrap_slo():
    evidence = evaluate_bounded_writer_authorization_health(
        now=NOW,
        current_session_id="SES-CURRENT",
        current_session_rows=(session(),),
        bootstrap_compliant=False,
        currently_unexpired_leases=(),
    )
    assert slo_map(evidence)["bootstrap_compliance"] is False


def test_unexpired_lease_with_closed_owner_fails_fencing_slo():
    evidence = evaluate_bounded_writer_authorization_health(
        now=NOW,
        current_session_id="SES-CURRENT",
        current_session_rows=(session(),),
        bootstrap_compliant=True,
        currently_unexpired_leases=(lease(),),
        live_owner_session_rows=(
            session("SES-OWNER", agent_id="AGT-OWNER", status="COMPLETED"),
        ),
    )
    assert slo_map(evidence)["lease_fencing_integrity"] is False


def test_unexpired_lease_with_matching_active_owner_preserves_fencing_pass():
    evidence = evaluate_bounded_writer_authorization_health(
        now=NOW,
        current_session_id="SES-CURRENT",
        current_session_rows=(session(),),
        bootstrap_compliant=True,
        currently_unexpired_leases=(lease(),),
        live_owner_session_rows=(session("SES-OWNER", agent_id="AGT-OWNER"),),
    )
    assert slo_map(evidence)["lease_fencing_integrity"] is True
    assert evidence.report.metrics["effective_active_leases"] == 1


def test_expired_row_is_rejected_from_unexpired_input_contract():
    expired = lease(expires_delta=timedelta(seconds=-1))
    with pytest.raises(ValueError, match="expired lease"):
        evaluate_bounded_writer_authorization_health(
            now=NOW,
            current_session_id="SES-CURRENT",
            current_session_rows=(session(),),
            bootstrap_compliant=True,
            currently_unexpired_leases=(expired,),
        )


def test_different_session_id_in_exact_lookup_is_rejected():
    with pytest.raises(ValueError, match="different session_id"):
        evaluate_bounded_writer_authorization_health(
            now=NOW,
            current_session_id="SES-CURRENT",
            current_session_rows=(session("SES-WRONG"),),
            bootstrap_compliant=True,
            currently_unexpired_leases=(),
        )
