import os,sys,unittest
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","src"))
from uexchanges.models import EligibilityDecision,GateDecision,GateResult
from uexchanges.scoring import DEFAULT_WEIGHTS,score_opportunity
class ScoringTests(unittest.TestCase):
    def test_failed_eligibility_is_zero(self):
        d=EligibilityDecision(GateResult.FAIL,[GateDecision("country",GateResult.FAIL,"no")]); s=score_opportunity(d,{k:1.0 for k in DEFAULT_WEIGHTS}); self.assertEqual(s.total,0); self.assertEqual(s.band,"BLOCKED")
    def test_full_score(self):
        d=EligibilityDecision(GateResult.PASS,[]); s=score_opportunity(d,{k:1.0 for k in DEFAULT_WEIGHTS}); self.assertEqual(s.total,100.0); self.assertEqual(s.band,"A+")
    def test_unknown_is_capped_below_a(self):
        d=EligibilityDecision(GateResult.UNKNOWN,[GateDecision("age",GateResult.UNKNOWN,"unknown")]); self.assertLess(score_opportunity(d,{k:1.0 for k in DEFAULT_WEIGHTS}).total,80)
