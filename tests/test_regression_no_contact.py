import unittest
from dataclasses import replace
from tests.test_outreach_preflight import BASE, NOW, SIG
from uexchanges.outreach_preflight import preflight, Intent

class NoContactRegression(unittest.TestCase):
    def test_requested_reply_label_does_not_bypass_do_not_contact(self):
        c=replace(BASE, intent=Intent.REQUESTED_REPLY, project_state='NO_CONTACT',
                  requested_reply_message_id='not-a-consent-reset')
        result=preflight(c, (), now=NOW, history_observed_at=NOW,
                         history_complete=True, signature=SIG)
        self.assertFalse(result.preparation_ok)
        self.assertIn('NO_CONTACT_REQUIRES_SEPARATE_CONSENT_RESET', result.blockers)
