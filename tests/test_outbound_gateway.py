from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from hashlib import sha256
from threading import Barrier, Lock
import unittest

from uexchanges.outbound_gateway import (
    AttachmentExpectation,
    DefiniteProviderFailure,
    EffectBlocked,
    EffectKey,
    EffectState,
    EmailCapability,
    InMemoryOutbox,
    PreparedEmail,
    ProviderDisposition,
    ProviderResult,
    WriterFence,
    send_once,
)

NOW = datetime(2026, 9, 16, 14, 20, tzinfo=timezone.utc)
MAIN = "f53e47cb256c5feff4334e7cd442862167fa366b"
MARKER = 'data-uex-signature="erasmus-v2"'
ATTACHMENT_BYTES = b"%PDF-1.7\nunit-test-cv"
ATTACHMENT_SHA = sha256(ATTACHMENT_BYTES).hexdigest()


def effect_key(source_version: str = "official-call:v7") -> EffectKey:
    return EffectKey("org-example", "call-example-2026", "app-example", "APPLICATION", source_version)


def prepared(**changes) -> PreparedEmail:
    base = PreparedEmail(
        key=effect_key(),
        sender="applicant@example.com",
        recipient="organiser@example.org",
        subject="Application — Example Erasmus+ project",
        html_body=f"<p>Hello.</p><div {MARKER}>Signature</div>",
        text_body="Hello.\n\nApplicant signature",
        signature_marker=MARKER,
        attachments=(AttachmentExpectation("Roberto_Erasmus_CV.pdf", ATTACHMENT_SHA),),
        preflight_ref="preflight:exact-app-example:v1",
        preflight_allowed=True,
    )
    return replace(base, **changes)


def fence(**changes) -> WriterFence:
    base = WriterFence(
        session_id="SES-UEX-TEST-001",
        agent_id="AGT-UEX-TEST",
        writer_authorization_receipt_id="WAZ-test-001",
        writer_authorization_digest="a" * 64,
        lease_id="LSE-test-001",
        lease_expires_at=NOW + timedelta(minutes=30),
        observed_main_sha=MAIN,
        coordination_allowed=True,
    )
    return replace(base, **changes)


def capability(**changes) -> EmailCapability:
    base = EmailCapability(
        capability_id="EMAILCAP-test-001",
        session_id="SES-UEX-TEST-001",
        action="EMAIL_SEND",
        expires_at=NOW + timedelta(minutes=10),
        provider_connection_ref="gmail:connected-user:scoped-send",
    )
    return replace(base, **changes)


def delivered_mime(p: PreparedEmail, *, marker_count: int = 1, include_plain: bool = True,
                   sender: str | None = None, recipient: str | None = None,
                   subject: str | None = None, attachment_bytes: bytes = ATTACHMENT_BYTES,
                   include_attachment: bool = True, cc: str | None = None,
                   duplicate_attachment: bool = False) -> bytes:
    msg = EmailMessage()
    msg["From"] = sender or p.sender
    msg["To"] = recipient or p.recipient
    msg["Subject"] = subject or p.subject
    if cc:
        msg["Cc"] = cc
    if include_plain:
        msg.set_content(p.text_body)
        html = "<p>Delivered.</p>" + "".join(
            f'<div {p.signature_marker}>Signature</div>' for _ in range(marker_count)
        )
        msg.add_alternative(html, subtype="html")
    else:
        msg.set_content(
            "<p>Delivered.</p>" + "".join(
                f'<div {p.signature_marker}>Signature</div>' for _ in range(marker_count)
            ),
            subtype="html",
        )
    if include_attachment:
        msg.add_attachment(
            attachment_bytes,
            maintype="application",
            subtype="pdf",
            filename="Roberto_Erasmus_CV.pdf",
        )
        if duplicate_attachment:
            msg.add_attachment(
                attachment_bytes,
                maintype="application",
                subtype="pdf",
                filename="Roberto_Erasmus_CV.pdf",
            )
    return msg.as_bytes()


def confirmed_result(p: PreparedEmail, **mime_changes) -> ProviderResult:
    return ProviderResult(
        ProviderDisposition.CONFIRMED,
        provider_message_id="gmail-message-001",
        provider_thread_id="gmail-thread-001",
        raw_mime=delivered_mime(p, **mime_changes),
    )


class GatewayTests(unittest.TestCase):
    def send(self, *, box=None, p=None, f=None, cap=None, provider=None,
             writer_ok=True, capability_ok=True, current_main=MAIN):
        box = box or InMemoryOutbox()
        p = p or prepared()
        f = f or fence()
        cap = cap or capability()
        provider = provider or (lambda mail, token: confirmed_result(mail))
        result = send_once(
            outbox=box,
            prepared=p,
            fence=f,
            capability=cap,
            now=NOW,
            current_main_sha=current_main,
            writer_fence_verifier=lambda _: writer_ok,
            email_capability_verifier=lambda _: capability_ok,
            provider_send=provider,
        )
        return box, result

    def test_confirmed_send_calls_provider_once_and_records_ids(self):
        calls = []
        def provider(mail, token):
            calls.append(token)
            return confirmed_result(mail)
        box, result = self.send(provider=provider)
        self.assertEqual(EffectState.SEND_CONFIRMED, result.state)
        self.assertEqual("gmail-message-001", result.provider_message_id)
        self.assertEqual("gmail-thread-001", result.provider_thread_id)
        self.assertEqual(1, len(calls))
        self.assertEqual(EffectState.SEND_CONFIRMED, box.get(effect_key().digest()).state)

    def test_concurrent_writers_same_effect_invoke_provider_at_most_once(self):
        box = InMemoryOutbox()
        calls = 0
        lock = Lock()
        barrier = Barrier(2)
        def provider(mail, token):
            nonlocal calls
            with lock:
                calls += 1
            return confirmed_result(mail)
        def worker():
            barrier.wait(timeout=2)
            try:
                return self.send(box=box, provider=provider)[1].state
            except EffectBlocked as exc:
                return str(exc)
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: worker(), range(2)))
        self.assertEqual(1, calls)
        self.assertIn(EffectState.SEND_CONFIRMED, results)
        self.assertTrue(any(str(x).startswith("EXISTING_EFFECT:") for x in results if isinstance(x, str)))

    def test_second_send_after_confirmation_is_blocked(self):
        box, _ = self.send()
        with self.assertRaisesRegex(EffectBlocked, "EXISTING_EFFECT:SEND_CONFIRMED"):
            self.send(box=box)

    def test_provider_exception_becomes_unknown_and_retry_is_blocked(self):
        box, result = self.send(provider=lambda mail, token: (_ for _ in ()).throw(TimeoutError("timeout")))
        self.assertEqual(EffectState.OUTCOME_UNKNOWN, result.state)
        with self.assertRaisesRegex(EffectBlocked, "EXISTING_EFFECT:OUTCOME_UNKNOWN"):
            self.send(box=box)

    def test_unknown_can_retry_only_after_authoritative_not_sent_reconciliation(self):
        box, first = self.send(provider=lambda mail, token: ProviderResult(ProviderDisposition.UNKNOWN, error_ref="gmail:timeout"))
        self.assertEqual(EffectState.OUTCOME_UNKNOWN, first.state)
        row = box.reconcile_not_sent(first.key_digest, "gmail:authoritative-search:no-message")
        self.assertEqual(EffectState.NOT_SENT, row.state)
        _, second = self.send(box=box)
        self.assertEqual(EffectState.SEND_CONFIRMED, second.state)
        self.assertEqual(2, second.generation)

    def test_reconciliation_requires_reference_and_not_confirmed_state(self):
        box, result = self.send()
        with self.assertRaises(ValueError):
            box.reconcile_not_sent(result.key_digest, "")
        with self.assertRaisesRegex(EffectBlocked, "RECONCILIATION_NOT_APPLICABLE"):
            box.reconcile_not_sent(result.key_digest, "gmail:no-message")

    def test_definite_failure_is_sticky_until_reconciled(self):
        box, result = self.send(provider=lambda mail, token: ProviderResult(ProviderDisposition.DEFINITE_FAILURE, error_ref="gmail:550"))
        self.assertEqual(EffectState.DELIVERY_FAILED, result.state)
        with self.assertRaisesRegex(EffectBlocked, "EXISTING_EFFECT:DELIVERY_FAILED"):
            self.send(box=box)

    def test_definite_provider_exception_becomes_delivery_failed(self):
        _, result = self.send(provider=lambda mail, token: (_ for _ in ()).throw(DefiniteProviderFailure("gmail:hard-failure")))
        self.assertEqual(EffectState.DELIVERY_FAILED, result.state)

    def test_stale_lease_blocks_before_provider_or_reservation(self):
        calls = []
        box = InMemoryOutbox()
        with self.assertRaisesRegex(EffectBlocked, "LEASE_EXPIRED"):
            self.send(box=box, f=fence(lease_expires_at=NOW), provider=lambda m, t: calls.append(t))
        self.assertEqual([], calls)
        self.assertIsNone(box.get(effect_key().digest()))

    def test_main_drift_blocks_before_provider(self):
        calls = []
        with self.assertRaisesRegex(EffectBlocked, "MAIN_DRIFT"):
            self.send(current_main="different", provider=lambda m, t: calls.append(t))
        self.assertEqual([], calls)

    def test_writer_verifier_false_blocks_before_provider(self):
        calls = []
        with self.assertRaisesRegex(EffectBlocked, "WRITER_FENCE_NOT_AUTHENTICATED"):
            self.send(writer_ok=False, provider=lambda m, t: calls.append(t))
        self.assertEqual([], calls)

    def test_email_capability_verifier_false_blocks_before_provider(self):
        calls = []
        with self.assertRaisesRegex(EffectBlocked, "EMAIL_CAPABILITY_NOT_AUTHENTICATED"):
            self.send(capability_ok=False, provider=lambda m, t: calls.append(t))
        self.assertEqual([], calls)

    def test_email_capability_expired_or_scope_mismatch_blocks(self):
        with self.assertRaisesRegex(EffectBlocked, "EMAIL_CAPABILITY_EXPIRED"):
            self.send(cap=capability(expires_at=NOW))
        with self.assertRaisesRegex(EffectBlocked, "EMAIL_CAPABILITY_SCOPE_MISMATCH"):
            self.send(cap=capability(session_id="other"))
        with self.assertRaisesRegex(EffectBlocked, "EMAIL_CAPABILITY_SCOPE_MISMATCH"):
            self.send(cap=capability(action="EMAIL_READ"))

    def test_coordination_denied_blocks(self):
        with self.assertRaisesRegex(EffectBlocked, "WRITER_AUTHORIZATION_DENIED"):
            self.send(f=fence(coordination_allowed=False))

    def test_preflight_is_mandatory(self):
        with self.assertRaisesRegex(EffectBlocked, "PREPARED_PREFLIGHT_REQUIRED"):
            self.send(p=prepared(preflight_allowed=False))
        with self.assertRaisesRegex(EffectBlocked, "PREPARED_PREFLIGHT_REQUIRED"):
            self.send(p=prepared(preflight_ref=""))

    def test_signature_marker_must_be_exactly_once_in_prepared_html(self):
        with self.assertRaisesRegex(EffectBlocked, "SIGNATURE_EXACTLY_ONCE_REQUIRED"):
            self.send(p=prepared(html_body="<p>No signature</p>"))
        with self.assertRaisesRegex(EffectBlocked, "SIGNATURE_EXACTLY_ONCE_REQUIRED"):
            self.send(p=prepared(html_body=f"<div {MARKER}></div><div {MARKER}></div>"))

    def test_attachment_manifest_rejects_bad_digest_and_duplicate_name(self):
        bad = AttachmentExpectation("cv.pdf", "not-a-digest")
        with self.assertRaisesRegex(EffectBlocked, "ATTACHMENT_MANIFEST_INVALID"):
            self.send(p=prepared(attachments=(bad,)))
        dup = AttachmentExpectation("Roberto_Erasmus_CV.pdf", ATTACHMENT_SHA)
        with self.assertRaisesRegex(EffectBlocked, "ATTACHMENT_MANIFEST_INVALID"):
            self.send(p=prepared(attachments=(dup, dup)))

    def assert_mime_unknown(self, result):
        self.assertEqual(EffectState.OUTCOME_UNKNOWN, result.state)
        self.assertTrue(result.reason.startswith("MIME_RECONCILIATION:"))

    def test_confirmed_provider_without_ids_is_unknown(self):
        _, result = self.send(provider=lambda mail, token: ProviderResult(ProviderDisposition.CONFIRMED, raw_mime=delivered_mime(mail)))
        self.assert_mime_unknown(result)

    def test_delivered_headers_mismatch_is_unknown(self):
        _, result = self.send(provider=lambda mail, token: confirmed_result(mail, recipient="other@example.org"))
        self.assert_mime_unknown(result)

    def test_delivered_signature_missing_or_duplicate_is_unknown(self):
        for count in (0, 2):
            with self.subTest(count=count):
                _, result = self.send(provider=lambda mail, token, c=count: confirmed_result(mail, marker_count=c))
                self.assert_mime_unknown(result)

    def test_delivered_plain_fallback_missing_is_unknown(self):
        _, result = self.send(provider=lambda mail, token: confirmed_result(mail, include_plain=False))
        self.assert_mime_unknown(result)

    def test_delivered_attachment_missing_or_tampered_is_unknown(self):
        _, missing = self.send(provider=lambda mail, token: confirmed_result(mail, include_attachment=False))
        self.assert_mime_unknown(missing)
        _, changed = self.send(provider=lambda mail, token: confirmed_result(mail, attachment_bytes=b"%PDF-different"))
        self.assert_mime_unknown(changed)

    def test_delivered_cc_header_is_unknown(self):
        _, result = self.send(provider=lambda mail, token: confirmed_result(mail, cc="third@example.net"))
        self.assert_mime_unknown(result)

    def test_delivered_duplicate_attachment_name_is_unknown(self):
        _, result = self.send(provider=lambda mail, token: confirmed_result(mail, duplicate_attachment=True))
        self.assert_mime_unknown(result)

    def test_malformed_provider_result_is_unknown_not_stuck_in_progress(self):
        _, result = self.send(provider=lambda mail, token: object())
        self.assertEqual(EffectState.OUTCOME_UNKNOWN, result.state)
        self.assertEqual("INVALID_PROVIDER_RESULT", result.reason)

    def test_invalid_provider_disposition_is_unknown(self):
        malformed = ProviderResult("CONFIRMED", provider_message_id="m", provider_thread_id="t")  # type: ignore[arg-type]
        _, result = self.send(provider=lambda mail, token: malformed)
        self.assertEqual(EffectState.OUTCOME_UNKNOWN, result.state)
        self.assertEqual("INVALID_PROVIDER_RESULT", result.reason)

    def test_effect_key_changes_with_authoritative_source_version(self):
        self.assertNotEqual(effect_key("official:v1").digest(), effect_key("official:v2").digest())

    def test_packet_digest_changes_with_body_or_attachment(self):
        p = prepared()
        self.assertNotEqual(p.digest(), replace(p, text_body=p.text_body + " changed").digest())
        changed_att = AttachmentExpectation("Roberto_Erasmus_CV.pdf", "b" * 64)
        self.assertNotEqual(p.digest(), replace(p, attachments=(changed_att,)).digest())

    def test_fence_token_mismatch_cannot_begin_reserved_effect(self):
        box = InMemoryOutbox()
        p = prepared()
        row = box.reserve(p.key, p.digest(), "lease-A", NOW)
        with self.assertRaisesRegex(EffectBlocked, "FENCE_TOKEN_MISMATCH"):
            box.begin(row.key_digest, "lease-B")


if __name__ == "__main__":
    unittest.main(verbosity=2)
