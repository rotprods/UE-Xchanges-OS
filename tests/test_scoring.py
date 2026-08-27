import os,sys,unittest
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","src"))
from uexchanges.models import EligibilityDecision,GateDecision,GateResult
from uexchanges.scoring import DEFAULT_WEIGHTS,DEFAULT_FIT_WEIGHTS,score_opportunity,score_fit,score_execution_priority

class ScoringTests(unittest.TestCase):
    def test_failed_eligibility_is_zero(self):
        d=EligibilityDecision(GateResult.FAIL,[GateDecision("country",GateResult.FAIL,"no")]); s=score_opportunity(d,{k:1.0 for k in DEFAULT_WEIGHTS}); self.assertEqual(s.total,0); self.assertEqual(s.band,"BLOCKED")

    def test_full_score(self):
        d=EligibilityDecision(GateResult.PASS,[]); s=score_opportunity(d,{k:1.0 for k in DEFAULT_WEIGHTS}); self.assertEqual(s.total,100.0); self.assertEqual(s.band,"A+")

    def test_unknown_is_capped_below_a_in_legacy_score(self):
        d=EligibilityDecision(GateResult.UNKNOWN,[GateDecision("age",GateResult.UNKNOWN,"unknown")]); self.assertLess(score_opportunity(d,{k:1.0 for k in DEFAULT_WEIGHTS}).total,80)

    def test_fit_is_independent_of_deadline_and_eligibility(self):
        s=score_fit({k:1.0 for k in DEFAULT_FIT_WEIGHTS}); self.assertEqual(s.total,100.0); self.assertEqual(s.band,"A+")

    def test_execution_priority_fail_is_zero(self):
        d=EligibilityDecision(GateResult.FAIL,[GateDecision("country",GateResult.FAIL,"no")]); s=score_execution_priority(d,fit_score=100,media_value=100,trainer_leverage=100,deadline_urgency=100); self.assertEqual(s.total,0); self.assertEqual(s.band,"BLOCKED")

    def test_unknown_can_be_urgent_for_verification(self):
        d=EligibilityDecision(GateResult.UNKNOWN,[GateDecision("country",GateResult.UNKNOWN,"unknown")]); s=score_execution_priority(d,fit_score=100,media_value=100,trainer_leverage=100,deadline_urgency=100); self.assertEqual(s.total,100.0); self.assertIn("verification",s.blocked_reason.lower())
