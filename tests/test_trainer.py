import os,sys,unittest
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","src"))
from uexchanges.models import GateResult
from uexchanges.trainer import TrainerActivity,evaluate_toy_reference

class TrainerTests(unittest.TestCase):
    def activity(self,**kw):
        base=dict(international=True,youth_work_field=True,days=3,non_formal_learning=True,full_time_trainer=True,responsible_for_educational_goals=True,reference_validatable=True); base.update(kw); return TrainerActivity(**base)
    def test_qualifying_reference(self): self.assertEqual(evaluate_toy_reference(self.activity()).result,GateResult.PASS)
    def test_isolated_short_workshop_fails(self): self.assertEqual(evaluate_toy_reference(self.activity(days=1)).result,GateResult.FAIL)
    def test_unknown_is_not_pass(self): self.assertEqual(evaluate_toy_reference(self.activity(full_time_trainer=None)).result,GateResult.UNKNOWN)
