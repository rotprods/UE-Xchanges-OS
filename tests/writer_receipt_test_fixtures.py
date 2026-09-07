"""Synthetic fixtures only. Never represent real broker authorization."""

def valid_receipt():
    return {
        "contract": "UEX_WRITER_AUTHORIZATION_RECEIPT", "version": "1.0.0",
        "receipt_id": "WAZ-" + "a" * 24,
        "issued_at": "2026-01-01T12:00:00+00:00",
        "expires_at": "2026-01-01T12:02:00+00:00",
        "session_id": "SES-SYNTHETIC", "agent_id": "AGT-SYNTHETIC",
        "context_id": "CTX-SYNTHETIC", "manifest_version": "1.1.0",
        "observed_main_sha": "b" * 40, "intent": "DERIVED_PROJECTION",
        "proposed_lease_id": "LSE-SYNTHETIC", "scope_sha256": "c" * 64,
        "authorization_decision_digest": "d" * 64,
        "authorization_evaluated_at": "2026-01-01T11:59:59+00:00",
        "health_report_sha256": "e" * 64,
        "health_generated_at": "2026-01-01T11:59:58+00:00",
        "prelease_event_watermark": "EVT-SYNTHETIC",
        "prelease_lease_scan_at": "2026-01-01T11:59:57+00:00",
        "overlapping_lease_ids": [], "repair_plan_id": None,
        "coordination_allowed": True, "domain_authority": False,
        "external_capability": False,
    }
