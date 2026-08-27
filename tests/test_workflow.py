import os,sys,unittest
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","src"))

from uexchanges.models import AIPolicy,GateResult
from uexchanges.workflow import NextAction,route_application


class WorkflowTests(unittest.TestCase):
    def test_duplicate_wins_over_high_priority(self):
        d=route_application(eligibility=GateResult.PASS,ai_policy=AIPolicy.ALLOWED,execution_priority=100,duplicate=True)
        self.assertEqual(d.action,NextAction.DUPLICATE_MERGED)

    def test_conflict_blocks_submission(self):
        d=route_application(eligibility=GateResult.PASS,ai_policy=AIPolicy.ALLOWED,execution_priority=100,conflicting_authoritative_facts=True)
        self.assertEqual(d.action,NextAction.VERIFY_CONFLICT)

    def test_fail_blocks(self):
        d=route_application(eligibility=GateResult.FAIL,ai_policy=AIPolicy.ALLOWED,execution_priority=100)
        self.assertEqual(d.action,NextAction.BLOCK_INELIGIBLE)

    def test_unknown_routes_to_verification(self):
        d=route_application(eligibility=GateResult.UNKNOWN,ai_policy=AIPolicy.ALLOWED,execution_priority=100)
        self.assertEqual(d.action,NextAction.VERIFY_ELIGIBILITY)

    def test_unknown_ai_policy_routes_to_policy_verification(self):
        d=route_application(eligibility=GateResult.PASS,ai_policy=AIPolicy.UNKNOWN,execution_priority=100)
        self.assertEqual(d.action,NextAction.VERIFY_AI_POLICY)

    def test_ai_final_text_prohibition_routes_human_write(self):
        d=route_application(eligibility=GateResult.PASS,ai_policy=AIPolicy.FINAL_TEXT_PROHIBITED,execution_priority=100)
        self.assertEqual(d.action,NextAction.HUMAN_WRITE)

    def test_missing_evidence_blocks_dossier_readiness(self):
        d=route_application(eligibility=GateResult.PASS,ai_policy=AIPolicy.ALLOWED,execution_priority=100,evidence_gaps=True)
        self.assertEqual(d.action,NextAction.BUILD_EVIDENCE)

    def test_high_priority_ready_applies(self):
        d=route_application(eligibility=GateResult.PASS,ai_policy=AIPolicy.ALLOWED,execution_priority=80)
        self.assertEqual(d.action,NextAction.APPLY_NOW)
