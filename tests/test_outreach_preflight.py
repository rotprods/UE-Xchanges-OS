from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from uexchanges.outreach_preflight import *

ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 9, 16, 10, tzinfo=timezone.utc)
SIG = load_signature(ROOT / 'docs/application-assets/email-signature.html')
BASE = Candidate('org-example', 'call-example-2026', 'app-example', 'contact@example.org',
                 'Application for a youth project',
                 'Hello, I would like to apply. I work in photography and filmmaking and can contribute visual storytelling.',
                 Route.EMAIL, 'official-call:2026', True, 'OPEN', 'DE')

class Guards(unittest.TestCase):
    def check(self, c=BASE, history=(), **kwargs):
        opts=dict(now=NOW, history_observed_at=NOW, history_complete=True, signature=SIG)
        opts.update(kwargs)
        return preflight(c, history, **opts)
    def test_baseline_prepares_but_never_authorizes_send(self):
        r=self.check(); self.assertTrue(r.preparation_ok); self.assertFalse(r.send_authorized)
    def test_exact_signature_images_and_links(self):
        self.assertEqual(SIG.count('<img '),9); self.assertEqual(SIG.count('<a '),10)
    def test_signature_tamper_rejected(self):
        self.assertIn('OUTREACH_SIGNATURE_GATE_FAIL',self.check(signature=SIG+' ').blockers)
    def test_signature_source_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'s.html'; p.write_text((ROOT/'docs/application-assets/email-signature.html').read_text()+' ')
            with self.assertRaises(ValueError): load_signature(p)
    def test_fragment_renderer_escapes_body(self):
        out=render_email('<script>alert(1)</script>',SIG)
        self.assertNotIn('<script>',out); self.assertTrue(out.endswith(SIG)); self.assertEqual(out.count(SIG),1)
    def test_renderer_rejects_substitute_signature(self):
        with self.assertRaises(ValueError): render_email('Hello','Regards')
    def test_no_duplicate_across_threads(self):
        h=[Contact('org-example','call-example-2026','app-other-alias',Intent.APPLICATION,NOW-timedelta(days=9),'SENT')]
        self.assertIn('DUPLICATE_CANDIDATURE_ACROSS_THREADS',self.check(history=h).blockers)
    def test_unknown_result_no_retry(self):
        h=[Contact('org-example','other-call','app-other',Intent.APPLICATION,NOW-timedelta(days=1),'OUTCOME_UNKNOWN')]
        self.assertIn('RECONCILE_PRIOR_EFFECT_BEFORE_CONTACT',self.check(history=h).blockers)
    def test_reserved_also_blocks(self):
        h=[Contact('org-example','other-call','app-other',Intent.APPLICATION,NOW,'RESERVED')]
        self.assertFalse(self.check(history=h).preparation_ok)
    def test_distinct_organisation_can_prepare(self):
        h=[Contact('org-other','call-example-2026','app-other',Intent.APPLICATION,NOW,'SENT')]
        self.assertTrue(self.check(history=h).preparation_ok)
    def test_other_call_same_org_cooldown(self):
        h=[Contact('org-example','other-call','app-other',Intent.APPLICATION,NOW-timedelta(minutes=7),'SENT')]
        self.assertIn('ORGANIZATION_24H_COOLDOWN',self.check(history=h).blockers)
    def test_unverified_history_blocks(self):
        self.assertFalse(self.check(history_complete=False).preparation_ok)
    def test_stale_history_blocks(self):
        self.assertFalse(self.check(history_observed_at=NOW-timedelta(seconds=301)).preparation_ok)
    def test_future_history_blocks(self):
        self.assertFalse(self.check(history_observed_at=NOW+timedelta(seconds=1)).preparation_ok)
    def test_naive_timestamp_blocks(self):
        self.assertFalse(self.check(now=datetime(2026,9,16)).preparation_ok)
    def test_missing_route_not_guessed(self):
        self.assertFalse(self.check(replace(BASE,route=Route.UNKNOWN)).preparation_ok)
    def test_required_form_not_skipped(self):
        self.assertIn('REQUIRED_FORM_NOT_REPLACED_BY_EMAIL',self.check(replace(BASE,route=Route.FORM_REQUIRED)).blockers)
    def test_email_then_form_is_not_selection(self):
        r=self.check(replace(BASE,route=Route.EMAIL_THEN_FORM)); self.assertTrue(r.preparation_ok); self.assertFalse(r.send_authorized)
    def test_unknown_project_state_blocks(self):
        self.assertFalse(self.check(replace(BASE,project_state="SOMETHING_UNKNOWN")).preparation_ok)
    def test_withdrawal_blocks(self):
        self.assertFalse(self.check(replace(BASE,project_state='WITHDRAWN')).preparation_ok)
    def test_waitlist_does_not_trigger_chasing(self):
        self.assertIn('WAIT_WITHOUT_CHASING',self.check(replace(BASE,project_state='WAITLIST')).blockers)
    def test_requested_reply_to_selected_allowed(self):
        c=replace(BASE,intent=Intent.REQUESTED_REPLY,project_state='SELECTED',requested_reply_message_id='actual-provider-id')
        self.assertTrue(self.check(c).preparation_ok)
    def test_requested_reply_needs_actual_inbound_id(self):
        self.assertFalse(self.check(replace(BASE,intent=Intent.REQUESTED_REPLY)).preparation_ok)
    def test_destination_preference_applied(self):
        self.assertFalse(self.check(replace(BASE,country_iso='PT'),excluded_countries=frozenset({'PT'})).preparation_ok)
    def test_internal_ai_question_blocked(self):
        self.assertFalse(self.check(replace(BASE,body='Please confirm any rule on AI-assisted editing.')).preparation_ok)
    def test_ai_professional_experience_not_censored(self):
        self.assertTrue(self.check(replace(BASE,body='I work in applied AI and software engineering.')).preparation_ok)
    def test_explicit_authorship_rule_requires_evidence(self):
        self.assertFalse(self.check(replace(BASE,human_original_required=True)).preparation_ok)
    def test_unknown_ai_policy_not_an_invented_hard_gate(self):
        self.assertTrue(self.check().preparation_ok)
    def test_header_injection(self):
        self.assertIn('HEADER_INJECTION',self.check(replace(BASE,subject='Hi\r\nBcc: other@example.org')).blockers)
    def test_multi_recipient_rejected(self):
        self.assertFalse(self.check(replace(BASE,recipient='a@example.org,b@example.org')).preparation_ok)
    def test_one_question(self):
        self.assertFalse(self.check(replace(BASE,body='What is the date? Can I apply?')).preparation_ok)
    def test_word_budget(self):
        self.assertFalse(self.check(replace(BASE,body='word '*201)).preparation_ok)
    def test_followup_without_application_blocked(self):
        self.assertFalse(self.check(replace(BASE,intent=Intent.FOLLOWUP)).preparation_ok)
    def test_second_followup_blocked(self):
        h=[Contact('org-example','call-example-2026','app-example',Intent.APPLICATION,NOW-timedelta(days=20),'SENT'),
           Contact('org-example','call-example-2026','app-example',Intent.FOLLOWUP,NOW-timedelta(days=9),'SENT')]
        self.assertIn('FOLLOWUP_BUDGET_EXHAUSTED',self.check(replace(BASE,intent=Intent.FOLLOWUP),h).blockers)
    def test_first_followup_after_business_days(self):
        h=[Contact('org-example','call-example-2026','app-example',Intent.APPLICATION,NOW-timedelta(days=9),'SENT')]
        self.assertTrue(self.check(replace(BASE,intent=Intent.FOLLOWUP),h).preparation_ok)
    def test_receipt_notes_not_proof(self):
        for x in ['No acceptance conflict because submission is blocked','All option-cost decisions deferred',
                  'All other decisions deferred','GOOGLE_FORM_CONFIRMATION_VISUAL:Your response has been recorded',None,{}]:
            with self.subTest(value=x): self.assertFalse(validate_receipt_structure(x,'app-example'))
    def receipt(self):
        return dict(kind='FORM_SUBMITTED',application_id='app-example',adapter_verified=True,receipt_id='r-001',
                    provider_object_id='form-submission-id',evidence_ref='private-evidence:001',captured_at=NOW.isoformat(),submission_identity='app-example/form/version')
    def test_typed_receipt(self): self.assertTrue(validate_receipt_structure(self.receipt(),'app-example'))
    def test_wrong_application_receipt(self): self.assertFalse(validate_receipt_structure(self.receipt(),'app-other'))
    def test_selection_not_a_submission_receipt(self):
        x=self.receipt(); x['kind']='SELECTED'; self.assertFalse(validate_receipt_structure(x,'app-example'))
    def test_unverified_adapter_rejected(self):
        x=self.receipt(); x['adapter_verified']=False; self.assertFalse(validate_receipt_structure(x,'app-example'))
    def test_naive_receipt_timestamp(self):
        x=self.receipt(); x['captured_at']='2026-09-16T10:00:00'; self.assertFalse(validate_receipt_structure(x,'app-example'))
    def test_false_is_valid_confirmed_form_answer(self):
        self.assertFalse(form_preflight(provider='TinyFish',required_fields=['answer'],values={'answer':False},
                                       allowed_organizations=['org-correct'],organization='org-correct',steps=1,unchanged_steps=0))
    def test_wrong_sending_organization_never_selected(self):
        e=form_preflight(provider='TinyFish',required_fields=[],values={},allowed_organizations=['org-wrong'],organization='org-correct',steps=1,unchanged_steps=0)
        self.assertIn('SENDING_ORGANIZATION_OPTION_MISMATCH',e)
    def test_browser_loop_budget(self):
        e=form_preflight(provider='TinyFish',required_fields=[],values={},allowed_organizations=['org-correct'],organization='org-correct',steps=94,unchanged_steps=3)
        self.assertIn('STOP_NO_PROGRESS_OR_BUDGET',e)
    def test_missing_profile_field_not_auth_problem(self):
        e=form_preflight(provider='TinyFish',required_fields=['phone'],values={},allowed_organizations=['org-correct'],organization='org-correct',steps=1,unchanged_steps=0)
        self.assertEqual(e,('MISSING_REQUIRED:phone',))
    def test_required_provider(self):
        self.assertIn('USE_TINYFISH',form_preflight(provider='other',required_fields=[],values={},allowed_organizations=['ok'],organization='ok',steps=1,unchanged_steps=0))

if __name__ == '__main__': unittest.main(verbosity=2)
