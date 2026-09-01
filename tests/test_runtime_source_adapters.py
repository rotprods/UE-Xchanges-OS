import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.forms.models import (
    AuthRequirement,
    FormExecutionPlan,
    FormExecutionState,
    SubmissionReceipt,
    SubmitAuthority,
)
from uexchanges.models import AIPolicy, GateResult
from uexchanges.runtime_v2.models import RuntimeEventKind
from uexchanges.runtime_v2.source_adapters import (
    FormGatewayAdapter,
    GmailSourceAdapter,
    OfficialSourceAdapter,
    ReceiptSourceAdapter,
)

NOW = datetime(2026, 9, 2, 0, 16, tzinfo=timezone(timedelta(hours=2)))


class RuntimeSourceAdapterTests(unittest.TestCase):
    def test_gmail_adapter_emits_explicit_gate_fact_without_raw_body(self):
        ingress = GmailSourceAdapter().gate_fact(
            message_id="m-1",
            source_version="gmail:m-1:v1",
            observed_at=NOW,
            application_id="app-1",
            gate_name="Spain Gate",
            result=GateResult.PASS,
            reason_code="ORGANISER_CONFIRMED_SPAIN_ROUTE",
            sequence=9,
        )
        self.assertEqual(ingress.kind, RuntimeEventKind.GATE_RESOLVED)
        self.assertEqual(ingress.payload["result"], "pass")
        self.assertEqual(ingress.source_ref, "gmail:m-1")
        self.assertNotIn("body", ingress.payload)
        self.assertFalse(hasattr(GmailSourceAdapter(), "receipt_ingress"))

    def test_gmail_adapter_rejects_raw_multiline_reason(self):
        with self.assertRaises(ValueError):
            GmailSourceAdapter().gate_fact(
                message_id="m-2",
                source_version="gmail:m-2:v1",
                observed_at=NOW,
                application_id="app-1",
                gate_name="Route Gate",
                result=GateResult.PASS,
                reason_code="Hello Roberto,\nthis is raw provider prose and should stay upstream.",
            )

    def test_official_source_deadline_is_timezone_aware_and_explicit(self):
        deadline = NOW + timedelta(days=3)
        ingress = OfficialSourceAdapter("salto").deadline_fact(
            call_id="15184",
            source_version="salto:15184:2026-09-02",
            observed_at=NOW,
            deadline=deadline,
            opportunity_id="opp-15184",
        )
        self.assertEqual(ingress.kind, RuntimeEventKind.DEADLINE_UPDATED)
        self.assertEqual(ingress.payload["deadline"], deadline.isoformat())
        with self.assertRaises(ValueError):
            OfficialSourceAdapter("salto").deadline_fact(
                call_id="15184",
                source_version="v2",
                observed_at=NOW,
                deadline=datetime(2026, 9, 4, 12, 0),
                opportunity_id="opp-15184",
            )

    def test_form_gateway_uses_existing_value_free_bridge(self):
        plan = FormExecutionPlan(
            plan_id="plan-1",
            application_id="app-1",
            opportunity_id="opp-1",
            canonical_form_url="https://forms.example.org/apply",
            provider="generic_html",
            form_fingerprint="fingerprint-1",
            fields=(),
            ai_policy=AIPolicy.UNKNOWN,
            auth_requirement=AuthRequirement.NONE,
            submit_authority=SubmitAuthority.HUMAN_ONLY,
            allowed_origins=("https://forms.example.org",),
            created_at=NOW,
            expires_at=NOW + timedelta(hours=2),
            source_version="form:plan-1:v1",
            state=FormExecutionState.FORM_SCHEMA_VERIFIED,
        )
        ingresses = FormGatewayAdapter().plan_ingresses(
            plan=plan,
            observed_at=NOW,
            sequence_base=20,
        )
        self.assertEqual(len(ingresses), 2)
        self.assertEqual(ingresses[0].kind, RuntimeEventKind.EVIDENCE_ADDED)
        self.assertEqual(ingresses[1].kind, RuntimeEventKind.GATE_RESOLVED)
        self.assertEqual(ingresses[1].payload["result"], "unknown")
        serialized = repr(tuple(dict(item.payload) for item in ingresses)).lower()
        self.assertNotIn("answer", serialized)
        self.assertNotIn("password", serialized)
        self.assertNotIn("cookie", serialized)

    def test_receipt_adapter_accepts_only_canonical_strong_receipt(self):
        receipt = SubmissionReceipt(
            receipt_id="rcpt-1",
            application_id="app-1",
            submission_key="sha256:" + "a" * 64,
            submitted_at=NOW,
            form_fingerprint="fp-1",
            plan_hash="sha256:" + "b" * 64,
            email_receipt_ref="gmail:receipt-message-1",
            evidence_refs=("gmail:receipt-message-1",),
        )
        ingress = ReceiptSourceAdapter().receipt_ingress(
            receipt=receipt,
            observed_at=NOW + timedelta(seconds=1),
        )
        self.assertEqual(ingress.kind, RuntimeEventKind.RECEIPT_CONFIRMED)
        self.assertEqual(ingress.authority, "email_receipt")
        self.assertTrue(ingress.payload["submission_identity_bound"])
        self.assertEqual(ingress.payload["receipt_ref"], "receipt:rcpt-1")


if __name__ == "__main__":
    unittest.main()
