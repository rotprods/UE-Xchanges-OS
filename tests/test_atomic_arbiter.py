import unittest

from uexchanges.atomic_arbiter import (
    ArbiterContractError,
    ExternalEffectState,
    Fence,
    application_scope,
    assert_current_fence,
    authorised_resubmission_effect_key,
    build_scope_set,
    can_reserve_effect,
    canonical_scope_set,
    followup_email_effect_key,
    initial_email_effect_key,
    initial_form_effect_key,
    organisation_call_scope,
    reply_email_effect_key,
    require_effect_reservable,
    scope_set_hash,
    validate_effect_transition,
)


class ScopeIdentityTests(unittest.TestCase):
    def test_scope_set_is_sorted_and_hash_is_order_independent(self):
        left = ["ORGCALL:ticket2europe:lead-right", "APPLICATION:app-lead-right"]
        right = list(reversed(left))
        self.assertEqual(
            canonical_scope_set(left),
            ("APPLICATION:app-lead-right", "ORGCALL:ticket2europe:lead-right"),
        )
        self.assertEqual(scope_set_hash(left), scope_set_hash(right))
        built = build_scope_set(right)
        self.assertEqual(built.scopes, canonical_scope_set(left))
        self.assertEqual(built.sha256, scope_set_hash(left))

    def test_scope_set_rejects_empty_duplicates_and_control_characters(self):
        bad = [[], ["A", "A"], ["A", ""], ["A", "B\nC"]]
        for scopes in bad:
            with self.subTest(scopes=scopes):
                with self.assertRaises(ArbiterContractError):
                    canonical_scope_set(scopes)

    def test_scope_helpers_escape_delimiters(self):
        self.assertEqual(application_scope("app:1"), "APPLICATION:app%3A1")
        self.assertEqual(
            organisation_call_scope("ticket:2", "call/1"),
            "ORGCALL:ticket%3A2:call%2F1",
        )


class ExternalEffectIdentityTests(unittest.TestCase):
    def test_initial_email_identity_does_not_accept_payload_or_source_revision(self):
        # There is intentionally no payload/source-version parameter. Text edits cannot
        # mint permission for another initial email.
        self.assertEqual(
            initial_email_effect_key("app-lead-right"),
            "v1:EMAIL_INITIAL:app-lead-right",
        )

    def test_initial_form_identity_is_application_plus_form_not_answer_payload(self):
        key = initial_form_effect_key("app-1", "google-form-abc")
        self.assertEqual(key, "v1:FORM_INITIAL:app-1:google-form-abc")

    def test_followup_number_and_reply_identity_are_explicit(self):
        self.assertEqual(
            followup_email_effect_key("app-1", 1),
            "v1:EMAIL_FOLLOWUP:app-1:1",
        )
        self.assertEqual(
            reply_email_effect_key("thread-1", "msg-9", "route clarification"),
            "v1:EMAIL_REPLY:thread-1:msg-9:route%20clarification",
        )
        for value in (0, -1, True):
            with self.subTest(value=value):
                with self.assertRaises(ArbiterContractError):
                    followup_email_effect_key("app", value)

    def test_resubmission_requires_explicit_provider_authorisation_identity(self):
        a = authorised_resubmission_effect_key("app", "form", "organiser-msg-1")
        b = authorised_resubmission_effect_key("app", "form", "organiser-msg-2")
        self.assertTrue(a.startswith("v1:FORM_RESUBMISSION:app:form:"))
        self.assertNotEqual(a, b)


class EffectStateMachineTests(unittest.TestCase):
    def test_started_uncertain_and_confirmed_never_allow_new_reservation(self):
        for state in (
            ExternalEffectState.RESERVED,
            ExternalEffectState.STARTED,
            ExternalEffectState.UNCERTAIN,
            ExternalEffectState.CONFIRMED,
        ):
            with self.subTest(state=state):
                self.assertFalse(can_reserve_effect(state))
                with self.assertRaises(ArbiterContractError):
                    require_effect_reservable(state)

    def test_only_absence_failed_no_effect_or_cancelled_are_reservable(self):
        self.assertTrue(can_reserve_effect(None))
        self.assertTrue(can_reserve_effect(ExternalEffectState.FAILED_NO_EFFECT))
        self.assertTrue(can_reserve_effect(ExternalEffectState.CANCELLED_BEFORE_START))

    def test_transition_graph_forbids_blind_retry(self):
        valid = [
            (ExternalEffectState.RESERVED, ExternalEffectState.STARTED),
            (ExternalEffectState.RESERVED, ExternalEffectState.CANCELLED_BEFORE_START),
            (ExternalEffectState.STARTED, ExternalEffectState.UNCERTAIN),
            (ExternalEffectState.STARTED, ExternalEffectState.CONFIRMED),
            (ExternalEffectState.STARTED, ExternalEffectState.FAILED_NO_EFFECT),
            (ExternalEffectState.UNCERTAIN, ExternalEffectState.CONFIRMED),
            (ExternalEffectState.UNCERTAIN, ExternalEffectState.FAILED_NO_EFFECT),
            (ExternalEffectState.FAILED_NO_EFFECT, ExternalEffectState.RESERVED),
            (ExternalEffectState.CANCELLED_BEFORE_START, ExternalEffectState.RESERVED),
        ]
        for current, target in valid:
            with self.subTest(current=current, target=target):
                validate_effect_transition(current, target)

        invalid = [
            (ExternalEffectState.STARTED, ExternalEffectState.RESERVED),
            (ExternalEffectState.UNCERTAIN, ExternalEffectState.RESERVED),
            (ExternalEffectState.CONFIRMED, ExternalEffectState.RESERVED),
            (ExternalEffectState.CONFIRMED, ExternalEffectState.STARTED),
        ]
        for current, target in invalid:
            with self.subTest(current=current, target=target):
                with self.assertRaises(ArbiterContractError):
                    validate_effect_transition(current, target)


class FencingTests(unittest.TestCase):
    def test_old_fencing_token_is_rejected(self):
        fresh = Fence("lease-new", "session-2", 22)
        assert_current_fence(current_token=22, presented=fresh)
        zombie = Fence("lease-old", "session-1", 21)
        with self.assertRaises(ArbiterContractError):
            assert_current_fence(current_token=22, presented=zombie)

    def test_fence_identity_must_be_complete(self):
        with self.assertRaises(ArbiterContractError):
            Fence("", "session", 1)
        with self.assertRaises(ArbiterContractError):
            Fence("lease", "session", 0)


if __name__ == "__main__":
    unittest.main()
