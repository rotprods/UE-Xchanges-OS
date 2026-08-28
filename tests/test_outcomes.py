import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from uexchanges.outcomes import CausalStrength, OutcomeRecord, OutcomeType, learning_policy


class OutcomeLearningTests(unittest.TestCase):
    def test_completed_acceptance_is_positive_but_not_component_causal(self):
        policy = learning_policy(OutcomeRecord(OutcomeType.ACCEPTED_COMPLETED))
        self.assertTrue(policy.update_positive_selection_prior)
        self.assertTrue(policy.update_organisation_relationship_prior)
        self.assertFalse(policy.update_criterion_heuristics)
        self.assertIn("infer_every_application_component_caused_acceptance", policy.forbidden_inferences)

    def test_waitlist_rank_one_is_near_accept_not_negative(self):
        policy = learning_policy(OutcomeRecord(OutcomeType.WAITLIST_PRIORITY, waitlist_rank=1))
        self.assertTrue(policy.near_accept)
        self.assertTrue(policy.update_positive_selection_prior)
        self.assertFalse(policy.update_negative_selection_prior)
        self.assertIn("train_negative_application_penalty_from_waitlist", policy.forbidden_inferences)

    def test_high_competition_rejection_updates_base_rate_only(self):
        policy = learning_policy(OutcomeRecord(OutcomeType.REJECTED_HIGH_COMPETITION, competition_pool=430))
        self.assertEqual(policy.causal_strength, CausalStrength.NONE)
        self.assertTrue(policy.update_competition_prior)
        self.assertFalse(policy.update_negative_selection_prior)
        self.assertFalse(policy.update_criterion_heuristics)
        self.assertIn("penalise_application_quality_from_high_competition_rejection", policy.forbidden_inferences)

    def test_specific_feedback_allows_specific_heuristic_update(self):
        policy = learning_policy(OutcomeRecord(OutcomeType.REJECTED_WITH_FEEDBACK, explicit_feedback=True))
        self.assertEqual(policy.causal_strength, CausalStrength.HIGH_SPECIFIC)
        self.assertTrue(policy.update_negative_selection_prior)
        self.assertTrue(policy.update_criterion_heuristics)
        self.assertIn("generalise_specific_feedback_beyond_supported_criterion", policy.forbidden_inferences)

    def test_feedback_type_requires_actual_feedback(self):
        with self.assertRaises(ValueError):
            OutcomeRecord(OutcomeType.REJECTED_WITH_FEEDBACK, explicit_feedback=False)
            # Validation is deliberately enforced by learning_policy.
            learning_policy(OutcomeRecord(OutcomeType.REJECTED_WITH_FEEDBACK, explicit_feedback=False))

    def test_no_response_is_not_rejection(self):
        policy = learning_policy(OutcomeRecord(OutcomeType.NO_RESPONSE))
        self.assertTrue(policy.update_organisation_response_prior)
        self.assertFalse(policy.update_negative_selection_prior)
        self.assertIn("treat_no_response_as_rejection", policy.forbidden_inferences)

    def test_waitlist_requires_rank(self):
        with self.assertRaises(ValueError):
            OutcomeRecord(OutcomeType.WAITLIST_PRIORITY)

    def test_invalid_waitlist_rank_rejected(self):
        with self.assertRaises(ValueError):
            OutcomeRecord(OutcomeType.WAITLIST_PRIORITY, waitlist_rank=0)


if __name__ == "__main__":
    unittest.main()
