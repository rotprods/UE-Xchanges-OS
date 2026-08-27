import os,sys,unittest
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","src"))
from uexchanges.models import AIPolicy,GateResult
from uexchanges.personalization import CriterionMatch
from uexchanges.readiness import evaluate_application_readiness

class ReadinessTests(unittest.TestCase):
    def test_duplicate_blocks(self):
        r=evaluate_application_readiness(eligibility=GateResult.PASS,ai_policy=AIPolicy.ALLOWED,criterion_matches=[],duplicate_already_submitted=True)
        self.assertEqual(r.status,"blocked")
    def test_ai_prohibition_requires_human_write(self):
        r=evaluate_application_readiness(eligibility=GateResult.PASS,ai_policy=AIPolicy.FINAL_TEXT_PROHIBITED,criterion_matches=[])
        self.assertEqual(r.status,"human_write_required"); self.assertFalse(r.final_text_generation_allowed)
    def test_evidence_gap_needs_verification(self):
        r=evaluate_application_readiness(eligibility=GateResult.PASS,ai_policy=AIPolicy.ALLOWED,criterion_matches=[CriterionMatch("leadership",(),True)])
        self.assertEqual(r.status,"needs_verification")
