from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.forms import (
    AnswerAuthor,
    AnswerCandidate,
    AuthRequirement,
    FieldOwnership,
    FieldSensitivity,
    FormField,
    FormFieldType,
    SubmitAuthority,
    compile_execution_plan,
    form_schema_fingerprint,
)
from uexchanges.models import AIPolicy


NOW = datetime(2026, 9, 1, 16, 0, tzinfo=timezone.utc)
VALIDATION_V1 = "sha256:" + "1" * 64
VALIDATION_V2 = "sha256:" + "2" * 64


def captured_text(*, key="motivation", label="Motivation", required=True, maxlength=500):
    return FormField(
        field_key=key,
        label=label,
        field_type=FormFieldType.TEXTAREA,
        required=required,
        maxlength=maxlength,
        ownership=FieldOwnership.UNRESOLVED,
        sensitivity=FieldSensitivity.PRIVATE,
        editable_by_agent=False,
    )


def candidate(*, key="motivation", value="Because this project matches my goals.", ownership=FieldOwnership.YELLOW, author=AnswerAuthor.AGENT, evidence_ids=()):
    return AnswerCandidate(
        field_key=key,
        value=value,
        source="answer-pack:v1",
        evidence_ids=evidence_ids,
        ownership=ownership,
        sensitivity=FieldSensitivity.PRIVATE,
        author=author,
        human_confirmed=author is AnswerAuthor.HUMAN,
    )


def compile_one(field: FormField, answer: AnswerCandidate | None, *, policy=AIPolicy.ASSIST_ONLY, validation_signature=None):
    return compile_execution_plan(
        application_id="app-1",
        opportunity_id="opp-1",
        canonical_form_url="https://forms.example.org/apply#ignored",
        provider="generic_html",
        captured_fields=(field,),
        answers=() if answer is None else (answer,),
        ai_policy=policy,
        auth_requirement=AuthRequirement.EXISTING_SESSION,
        submit_authority=SubmitAuthority.HUMAN_ONLY,
        allowed_origins=("https://forms.example.org",),
        created_at=NOW,
        expires_at=NOW + timedelta(hours=1),
        source_version="form-v1",
        validation_signature=validation_signature,
    )


class FormCompilerTests(unittest.TestCase):
    def test_verified_green_fact_compiles_under_ai_unknown(self):
        field = FormField(
            field_key="email",
            label="Email",
            field_type=FormFieldType.EMAIL,
            required=True,
            ownership=FieldOwnership.UNRESOLVED,
            sensitivity=FieldSensitivity.PRIVATE,
        )
        answer = AnswerCandidate(
            field_key="email",
            value="candidate@example.com",
            source="profile:email",
            evidence_ids=("ev-email",),
            ownership=FieldOwnership.GREEN,
            sensitivity=FieldSensitivity.PRIVATE,
            author=AnswerAuthor.VERIFIED_FACT,
        )
        result = compile_one(field, answer, policy=AIPolicy.UNKNOWN)
        self.assertEqual(result.issues, ())
        self.assertTrue(result.ready_for_prefill)
        self.assertTrue(result.plan.fields[0].editable_by_agent)

    def test_ai_unknown_blocks_agent_authored_yellow_narrative(self):
        result = compile_one(captured_text(), candidate(), policy=AIPolicy.UNKNOWN)
        self.assertFalse(result.ready_for_prefill)
        self.assertIn("ai_policy_unknown", {issue.code for issue in result.issues})
        self.assertIsNone(result.plan.fields[0].answer)

    def test_final_text_prohibited_blocks_agent_but_allows_human_owned_final(self):
        blocked = compile_one(captured_text(), candidate(), policy=AIPolicy.FINAL_TEXT_PROHIBITED)
        self.assertIn("ai_final_text_prohibited", {issue.code for issue in blocked.issues})

        human = candidate(author=AnswerAuthor.HUMAN)
        allowed = compile_one(captured_text(), human, policy=AIPolicy.FINAL_TEXT_PROHIBITED)
        self.assertEqual(allowed.issues, ())
        self.assertTrue(allowed.ready_for_prefill)
        self.assertFalse(allowed.plan.fields[0].editable_by_agent)

    def test_red_field_requires_human_confirmation(self):
        red_agent = candidate(ownership=FieldOwnership.RED, author=AnswerAuthor.AGENT)
        blocked = compile_one(captured_text(), red_agent)
        self.assertIn("red_requires_human_confirmation", {issue.code for issue in blocked.issues})

        red_human = candidate(ownership=FieldOwnership.RED, author=AnswerAuthor.HUMAN)
        allowed = compile_one(captured_text(), red_human)
        self.assertEqual(allowed.issues, ())
        self.assertFalse(allowed.plan.fields[0].editable_by_agent)

    def test_black_field_surfaces_human_interaction_gate(self):
        black = FormField(
            field_key="otp",
            label="One-time password",
            field_type=FormFieldType.TEXT,
            required=True,
            ownership=FieldOwnership.BLACK,
            sensitivity=FieldSensitivity.SECRET,
            editable_by_agent=False,
        )
        result = compile_one(black, None)
        self.assertFalse(result.ready_for_prefill)
        self.assertIn("black_field_human_interaction_required", {issue.code for issue in result.issues})

    def test_missing_required_field_blocks(self):
        result = compile_one(captured_text(), None)
        self.assertIn("required_answer_missing", {issue.code for issue in result.issues})
        self.assertFalse(result.ready_for_prefill)

    def test_invalid_choice_and_maxlength_are_rejected(self):
        choice = FormField(
            field_key="country",
            label="Country",
            field_type=FormFieldType.SELECT,
            required=True,
            options=("Spain", "Portugal"),
            ownership=FieldOwnership.UNRESOLVED,
            sensitivity=FieldSensitivity.PUBLIC,
        )
        wrong = AnswerCandidate(
            field_key="country",
            value="France",
            source="profile:country",
            evidence_ids=("ev-country",),
            ownership=FieldOwnership.GREEN,
            sensitivity=FieldSensitivity.PUBLIC,
            author=AnswerAuthor.VERIFIED_FACT,
        )
        result = compile_one(choice, wrong)
        self.assertIn("invalid_option", {issue.code for issue in result.issues})

        long = compile_one(captured_text(maxlength=5), candidate(value="123456"))
        self.assertIn("maxlength_exceeded", {issue.code for issue in long.issues})

    def test_fingerprint_is_structural_not_answer_dependent(self):
        field = captured_text()
        fp1 = form_schema_fingerprint(provider="Generic_HTML", canonical_form_url="https://forms.example.org/apply#one", fields=(field,))
        answered = FormField(
            field_key=field.field_key,
            label=field.label,
            field_type=field.field_type,
            required=field.required,
            maxlength=field.maxlength,
            answer="different answer",
            answer_source="x",
            ownership=FieldOwnership.YELLOW,
            sensitivity=FieldSensitivity.PRIVATE,
            editable_by_agent=True,
        )
        fp2 = form_schema_fingerprint(provider="generic_html", canonical_form_url="https://forms.example.org/apply#two", fields=(answered,))
        self.assertEqual(fp1, fp2)

        changed = captured_text(label="A changed question")
        fp3 = form_schema_fingerprint(provider="generic_html", canonical_form_url="https://forms.example.org/apply", fields=(changed,))
        self.assertNotEqual(fp1, fp3)

    def test_validation_signature_is_carried_and_changes_plan_identity(self):
        field = captured_text()
        answer = candidate()
        unbound = compile_one(field, answer)
        first = compile_one(field, answer, validation_signature=VALIDATION_V1)
        second = compile_one(field, answer, validation_signature=VALIDATION_V2)
        self.assertIsNone(unbound.plan.validation_signature)
        self.assertEqual(first.plan.validation_signature, VALIDATION_V1)
        self.assertNotEqual(unbound.plan.plan_id, first.plan.plan_id)
        self.assertNotEqual(first.plan.plan_id, second.plan.plan_id)


if __name__ == "__main__":
    unittest.main()
