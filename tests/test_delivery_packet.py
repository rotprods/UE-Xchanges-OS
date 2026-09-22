from dataclasses import replace
from datetime import timedelta, datetime
from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from uexchanges.outreach_preflight import Intent
from uexchanges.delivery_packet import Attachment, InboundRequest, Timing, prepare_packet
from tests.test_outreach_preflight import BASE, NOW, SIG

class PacketTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.cv=self.root/'cv.pdf'
        self.cv.write_bytes(b'%PDF-1.7\n% test fixture, not a production CV')
        self.asset=Attachment(str(self.cv),sha256(self.cv.read_bytes()).hexdigest(),'CV')
    def check(self,c=BASE,**kwargs):
        d=dict(now=NOW,history_observed_at=NOW,history_complete=True,signature=SIG,
               timing=Timing(NOW),attachment_root=self.root,attachments=[self.asset]); d.update(kwargs)
        return prepare_packet(c,(),**d)
    def reply(self):
        return replace(BASE,intent=Intent.REQUESTED_REPLY,project_state='SELECTED',requested_reply_message_id='msg-01')
    def inbound(self):
        return InboundRequest('msg-01',BASE.organization_id,BASE.call_id,BASE.application_id,
                              BASE.recipient,NOW-timedelta(hours=1),True)
    def test_valid_packet_never_authorizes_send(self):
        r=self.check(); self.assertTrue(r.preparation_ok); self.assertFalse(r.send_authorized)
    def test_initial_requires_actual_cv(self):
        self.assertIn('INITIAL_CANDIDATURE_CV_REQUIRED',self.check(attachments=[]).blockers)
    def test_missing_file(self):
        self.cv.unlink(); self.assertIn('ATTACHMENT_NOT_READABLE',self.check().blockers)
    def test_tampered_file(self):
        self.cv.write_bytes(b'%PDF-changed'); self.assertIn('ATTACHMENT_DIGEST_MISMATCH',self.check().blockers)
    def test_private_audit_not_attached(self):
        self.assertIn('ATTACHMENT_ROLE_NOT_FOR_ORGANISER',self.check(attachments=[replace(self.asset,role='AUDIT')]).blockers)
    def test_file_outside_root(self):
        d=self.root/'sub';d.mkdir(); self.assertIn('ATTACHMENT_OUTSIDE_APPROVED_ROOT',self.check(attachment_root=d).blockers)
    def test_symlink_rejected(self):
        p=self.root/'alias.pdf';p.symlink_to(self.cv)
        self.assertIn('ATTACHMENT_OUTSIDE_APPROVED_ROOT',self.check(attachments=[replace(self.asset,path=str(p))]).blockers)
    def test_no_duplicate_attachments(self):
        self.assertIn('DUPLICATE_ATTACHMENT',self.check(attachments=[self.asset,self.asset]).blockers)
    def test_pdf_extension_is_not_sufficient(self):
        self.cv.write_text('<html>private</html>'); self.assertIn('ATTACHMENT_NOT_PDF',self.check().blockers)
    def test_size_limit(self):
        self.assertIn('ATTACHMENT_SIZE_LIMIT',self.check(max_bytes=3).blockers)
    def test_deadline_enforced(self):
        self.assertIn('DEADLINE_PASSED_NO_EXPLICIT_LATE_PERMISSION',self.check(timing=Timing(NOW,NOW)).blockers)
    def test_explicit_trusted_late_permission(self):
        self.assertTrue(self.check(timing=Timing(NOW,NOW,'organiser:exact-permission')).preparation_ok)
    def test_unspecified_deadline_not_invented(self):
        self.assertTrue(self.check(timing=Timing(NOW,None)).preparation_ok)
    def test_stale_source(self):
        self.assertIn('SOURCE_STALE_OR_FUTURE',self.check(timing=Timing(NOW-timedelta(days=2))).blockers)
    def test_future_source(self):
        self.assertIn('SOURCE_STALE_OR_FUTURE',self.check(timing=Timing(NOW+timedelta(seconds=1))).blockers)
    def test_naive_deadline(self):
        self.assertIn('DEADLINE_TIMEZONE_REQUIRED',self.check(timing=Timing(NOW,datetime(2026,9,20))).blockers)
    def test_reply_label_alone_not_sufficient(self):
        self.assertIn('INBOUND_REQUEST_EXACT_BINDING_REQUIRED',self.check(self.reply()).blockers)
    def test_requested_reply_needs_no_cv(self):
        self.assertTrue(self.check(self.reply(),inbound=self.inbound(),attachments=[]).preparation_ok)
    def test_wrong_organisation_inbound(self):
        self.assertFalse(self.check(self.reply(),inbound=replace(self.inbound(),organization_id='different')).preparation_ok)
    def test_wrong_sender(self):
        self.assertFalse(self.check(self.reply(),inbound=replace(self.inbound(),sender='bad@example.org')).preparation_ok)
    def test_wrong_application_inbound(self):
        self.assertFalse(self.check(self.reply(),inbound=replace(self.inbound(),application_id='different')).preparation_ok)
    def test_already_resolved_reply_no_repeat(self):
        self.assertFalse(self.check(self.reply(),inbound=replace(self.inbound(),resolved=True)).preparation_ok)
    def test_future_request_blocked(self):
        self.assertIn('INBOUND_TIMESTAMP_INVALID',self.check(self.reply(),inbound=replace(self.inbound(),received_at=NOW+timedelta(days=1))).blockers)
    def test_logistics_reply_after_application_deadline(self):
        self.assertTrue(self.check(self.reply(),inbound=self.inbound(),timing=Timing(NOW,NOW-timedelta(days=1)),attachments=[]).preparation_ok)
    def test_no_contact_even_with_exact_request(self):
        self.assertFalse(self.check(replace(self.reply(),project_state='NO_CONTACT'),inbound=self.inbound()).preparation_ok)

if __name__=='__main__':unittest.main(verbosity=2)
