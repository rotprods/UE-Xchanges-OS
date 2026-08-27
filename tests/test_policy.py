import os,sys,unittest
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","src"))
from uexchanges.models import AIPolicy
from uexchanges.policy import detect_ai_policy,final_text_generation_allowed
class PolicyTests(unittest.TestCase):
    def test_explicit_chatgpt_prohibition(self):
        p=detect_ai_policy("Applications written with ChatGPT and other AI tools will not be considered."); self.assertEqual(p,AIPolicy.FINAL_TEXT_PROHIBITED); self.assertFalse(final_text_generation_allowed(p))
    def test_unknown_stays_unknown(self): self.assertEqual(detect_ai_policy("Tell us why you want to join."),AIPolicy.UNKNOWN)
