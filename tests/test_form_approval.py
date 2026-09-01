from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from uexchanges.forms import (
    AuthRequirement,
    FieldOwnership,
    FieldSensitivity,
    FormExecutionPlan,
    FormExecutionState,
    FormField,
    FormFieldType,
    SubmitAuthority,
)
from uexchanges.forms.approval import (
    ApprovalStatus,
    MAX_APPROVAL_TTL_SECONDS,
    issue_approval_token,
    verify_approval_token,
)
from uexchanges.models import AIPolicy


NOW = datetime(2026, 9, 1, 16, 30, tzinfo=timezone.utc)
SECRET = b"a" * 32
OTHER_SECRET = b"b" * 32


def make_field(*, answer="Roberto", evidence_ids=("ev-name",)) -> FormField:
    return FormField(
        field_key="name",
        label="Name",
        field_type=FormFieldType.TEXT,
        required=True,
        answer=answer,
        answer_source="profile:name",
        evidence_ids=evidence_ids,
        ownership=FieldOwnership.GREEN,
        sensitivity=FieldSensitivity.PRIVATE,
        editable_by_agent=True,
    )


def make_plan(**overrides) -> FormExecutionPlan:
    base = dict(
        plan_id="plan-approval-1",
        application_id="app-1",
        opportunity_id="opp-1",
        canonical_form_url="https://forms.example.org/apply",
        provider="generic_html",
        form_fingerprint="sha256:form-v1",
        fields=(make_field(),),
        ai_policy=AIPolicy.ASSIST_ONLY,
        auth_requirement=AuthRequirement.EXISTING_SESSION,
        submit_authority=SubmitAuthority.AGENT_AFTER_APPROVAL,
        allowed_origins=("https://forms.example.org",),
        created_at=NOW - timedelta(minutes=5),
        expires_at=NOW + timedelta(hours=1),
        source_version="source-v1",
        attachments=("drive:cv-v1",),
        state=FormExecutionState.HUMAN_APPROVED,
    )
    base.update(overrides)
    return FormExecutionPlan(**base)


def issue(plan: FormExecutionPlan, **overrides) -> str:
    args = dict(
        plan=plan,
        approved_by_ref="human:roberto",
        secret=SECRET,
        approved_at=NOW,
        ttl_seconds=300,
        nonce="test-nonce",
    )
    args.update(overrides)
    return issue_approval_token(**args)


class FormApprovalTests(unittest.TestCase):
    def test_valid_token_is_bound_to_exact_plan(self):
        plan = make_plan()
        token = issue(plan)
        result = verify_approval_token(token=token, plan=plan, secret=SECRET, now=NOW + timedelta(seconds=1))
        self.assertTrue(result.valid)
        self.assertIs(result.status, ApprovalStatus.VALID)
        self.assertEqual(result.claims.application_id, "app-1")

    def test_token_expires_and_cannot_be_reused(self):
        plan = make_plan()
        token = issue(plan, ttl_seconds=5)
        result = verify_approval_token(token=token, plan=plan, secret=SECRET, now=NOW + timedelta(seconds=5))
        self.assertFalse(result.valid)
        self.assertIs(result.status, ApprovalStatus.EXPIRED)

    def test_approval_is_capped_by_plan_expiry(self):
        plan = make_plan(expires_at=NOW + timedelta(seconds=20))
        token = issue(plan, ttl_seconds=300)
        valid = verify_approval_token(token=token, plan=plan, secret=SECRET, now=NOW + timedelta(seconds=19))
        expired = verify_approval_token(token=token, plan=plan, secret=SECRET, now=NOW + timedelta(seconds=20))
        self.assertTrue(valid.valid)
        self.assertIs(expired.status, ApprovalStatus.EXPIRED)

    def test_wrong_secret_and_tampering_fail_signature(self):
        plan = make_plan()
        token = issue(plan)
        wrong_secret = verify_approval_token(token=token, plan=plan, secret=OTHER_SECRET, now=NOW + timedelta(seconds=1))
        self.assertIs(wrong_secret.status, ApprovalStatus.INVALID_SIGNATURE)

        payload, signature = token.split(".", 1)
        tampered_signature = ("0" if signature[0] != "0" else "1") + signature[1:]
        tampered = verify_approval_token(token=f"{payload}.{tampered_signature}", plan=plan, secret=SECRET, now=NOW + timedelta(seconds=1))
        self.assertIs(tampered.status, ApprovalStatus.INVALID_SIGNATURE)

    def test_answer_change_invalidates_approval(self):
        plan = make_plan()
        token = issue(plan)
        changed = replace(plan, fields=(make_field(answer="Changed after approval"),))
        result = verify_approval_token(token=token, plan=changed, secret=SECRET, now=NOW + timedelta(seconds=1))
        self.assertIs(result.status, ApprovalStatus.BINDING_MISMATCH)

    def test_form_change_invalidates_approval(self):
        plan = make_plan()
        token = issue(plan)
        changed = replace(plan, form_fingerprint="sha256:form-v2")
        result = verify_approval_token(token=token, plan=changed, secret=SECRET, now=NOW + timedelta(seconds=1))
        self.assertIs(result.status, ApprovalStatus.BINDING_MISMATCH)

    def test_audit_plan_change_invalidates_even_if_payload_same(self):
        plan = make_plan()
        token = issue(plan)
        changed = replace(plan, fields=(make_field(evidence_ids=("ev-name-new",)),))
        result = verify_approval_token(token=token, plan=changed, secret=SECRET, now=NOW + timedelta(seconds=1))
        self.assertIs(result.status, ApprovalStatus.BINDING_MISMATCH)

    def test_plan_state_or_authority_change_invalidates(self):
        plan = make_plan()
        token = issue(plan)
        state_changed = replace(plan, state=FormExecutionState.PREFILLED)
        state_result = verify_approval_token(token=token, plan=state_changed, secret=SECRET, now=NOW + timedelta(seconds=1))
        self.assertIs(state_result.status, ApprovalStatus.BINDING_MISMATCH)

        authority_changed = replace(plan, submit_authority=SubmitAuthority.HUMAN_ONLY)
        authority_result = verify_approval_token(token=token, plan=authority_changed, secret=SECRET, now=NOW + timedelta(seconds=1))
        self.assertIs(authority_result.status, ApprovalStatus.BINDING_MISMATCH)

    def test_issue_requires_human_approved_agent_authority(self):
        with self.assertRaisesRegex(ValueError, "HUMAN_APPROVED"):
            issue(make_plan(state=FormExecutionState.VALIDATION_PASS))
        with self.assertRaisesRegex(ValueError, "AGENT_AFTER_APPROVAL"):
            issue(make_plan(submit_authority=SubmitAuthority.HUMAN_ONLY))

    def test_issue_rejects_weak_secret_and_excessive_ttl(self):
        with self.assertRaisesRegex(ValueError, "at least 32"):
            issue(make_plan(), secret=b"short")
        with self.assertRaisesRegex(ValueError, "between 1"):
            issue(make_plan(), ttl_seconds=MAX_APPROVAL_TTL_SECONDS + 1)

    def test_malformed_token_does_not_raise(self):
        result = verify_approval_token(token="not-a-token", plan=make_plan(), secret=SECRET, now=NOW)
        self.assertFalse(result.valid)
        self.assertIs(result.status, ApprovalStatus.MALFORMED)


if __name__ == "__main__":
    unittest.main()
