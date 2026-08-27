import os,sys,unittest
from datetime import date,datetime,timezone
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","src"))
from uexchanges.eligibility import evaluate_eligibility
from uexchanges.models import ApplicantProfile,GateResult,Opportunity,Role

class EligibilityTests(unittest.TestCase):
    def base(self):
        p=ApplicantProfile(residence_country="ES",age=24,languages={"English"},available_from=date(2026,1,1),available_to=date(2027,12,31))
        o=Opportunity(opportunity_id="x",title="x",programme="Erasmus+",role=Role.PARTICIPANT,source_url="https://example.invalid",deadline=datetime(2026,9,1,tzinfo=timezone.utc),start_date=date(2026,10,1),end_date=date(2026,10,8),eligible_countries={"ES"},age_min=18,age_max=30,required_languages={"English"})
        return p,o
    def test_pass(self):
        p,o=self.base(); self.assertEqual(evaluate_eligibility(p,o,now=datetime(2026,8,27,tzinfo=timezone.utc)).result,GateResult.PASS)
    def test_country_fail(self):
        p,o=self.base(); o.eligible_countries={"PT"}; self.assertEqual(evaluate_eligibility(p,o,now=datetime(2026,8,27,tzinfo=timezone.utc)).result,GateResult.FAIL)
    def test_expired_fail(self):
        p,o=self.base(); self.assertEqual(evaluate_eligibility(p,o,now=datetime(2026,9,2,tzinfo=timezone.utc)).result,GateResult.FAIL)
    def test_unknown_not_assumed_pass(self):
        p,o=self.base(); o.eligible_countries=None; self.assertEqual(evaluate_eligibility(p,o,now=datetime(2026,8,27,tzinfo=timezone.utc)).result,GateResult.UNKNOWN)
