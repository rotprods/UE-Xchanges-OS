import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from uexchanges.models import Opportunity, Role
from uexchanges.platform_policy import apply_platform_requirements, requirements_for_source


class PlatformPolicyTests(unittest.TestCase):
    def opportunity(self):
        return Opportunity(
            opportunity_id="x",
            title="Training",
            programme="Erasmus+ Training",
            role=Role.YOUTH_WORKER,
            source_url="https://example.invalid",
        )

    def test_salto_calendar_requires_youth_work_context(self):
        req = requirements_for_source("salto_calendar")
        self.assertTrue(req.requires_youth_work_context)
        self.assertEqual(req.decision_code, "VERIFY_YOUTH_WORK_CONTEXT")

    def test_unknown_platform_does_not_invent_requirement(self):
        req = requirements_for_source("unknown")
        self.assertFalse(req.requires_youth_work_context)

    def test_apply_platform_requirement_tightens_opportunity(self):
        opportunity = apply_platform_requirements(self.opportunity(), "salto_calendar")
        self.assertTrue(opportunity.requires_youth_work_context)
        self.assertEqual(opportunity.facts["platform_eligibility_decision_code"], "VERIFY_YOUTH_WORK_CONTEXT")

    def test_non_salto_source_keeps_default(self):
        opportunity = apply_platform_requirements(self.opportunity(), "eyp_esc")
        self.assertFalse(opportunity.requires_youth_work_context)


if __name__ == "__main__":
    unittest.main()
