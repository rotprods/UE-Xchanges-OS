from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Barrier, Lock
import unittest

from uexchanges.durable_outbox import SqliteOutbox, stable_effect_digest
from uexchanges.outbound_gateway import (
    AttachmentExpectation,
    EffectBlocked,
    EffectKey,
    EffectState,
    EmailCapability,
    PreparedEmail,
    ProviderDisposition,
    ProviderResult,
    WriterFence,
    send_once,
)

NOW = datetime(2026, 9, 16, 14, 35, tzinfo=timezone.utc)
MAIN = "98e22f2d3d9968aee98b38a7eb60c704aed94c48"
MARKER = 'data-uex-signature="erasmus-v2"'
PDF = b"%PDF-1.7\ndurable-outbox-test"
PDF_SHA = sha256(PDF).hexdigest()


def key(version: str = "official:v1") -> EffectKey:
    return EffectKey("org-durable", "call-durable-2026", "app-durable", "APPLICATION", version)


def prepared(version: str = "official:v1") -> PreparedEmail:
    return PreparedEmail(
        key=key(version),
        sender="applicant@example.com",
        recipient="organiser@example.org",
        subject="Application — Durable test",
        html_body=f"<p>Hello.</p><div {MARKER}>Signature</div>",
        text_body="Hello.\n\nApplicant signature",
        signature_marker=MARKER,
        attachments=(AttachmentExpectation("CV.pdf", PDF_SHA),),
        preflight_ref=f"preflight:{version}",
        preflight_allowed=True,
    )


def fence(lease: str = "LSE-durable-001") -> WriterFence:
    return WriterFence(
        session_id="SES-UEX-DURABLE-001",
        agent_id="AGT-UEX-DURABLE",
        writer_authorization_receipt_id="WAZ-durable-001",
        writer_authorization_digest="a" * 64,
        lease_id=lease,
        lease_expires_at=NOW + timedelta(minutes=30),
        observed_main_sha=MAIN,
        coordination_allowed=True,
    )


def capability() -> EmailCapability:
    return EmailCapability(
        capability_id="EMAILCAP-durable-001",
        session_id="SES-UEX-DURABLE-001",
        action="EMAIL_SEND",
        expires_at=NOW + timedelta(minutes=10),
        provider_connection_ref="gmail:test-only",
    )


def mime(p: PreparedEmail) -> bytes:
    msg = EmailMessage()
    msg["From"] = p.sender
    msg["To"] = p.recipient
    msg["Subject"] = p.subject
    msg.set_content(p.text_body)
    msg.add_alternative(f'<p>Delivered.</p><div {MARKER}>Signature</div>', subtype="html")
    msg.add_attachment(PDF, maintype="application", subtype="pdf", filename="CV.pdf")
    return msg.as_bytes()


def confirmed(p: PreparedEmail) -> ProviderResult:
    return ProviderResult(
        ProviderDisposition.CONFIRMED,
        provider_message_id="gmail-durable-message",
        provider_thread_id="gmail-durable-thread",
        raw_mime=mime(p),
    )


class DurableOutboxTests(unittest.TestCase):
    def db(self, directory: str) -> Path:
        return Path(directory) / "outbound.sqlite3"

    def test_stable_identity_excludes_source_version_but_packet_digest_does_not(self):
        k1, k2 = key("official:v1"), key("official:v2")
        self.assertNotEqual(k1.digest(), k2.digest())
        self.assertEqual(stable_effect_digest(k1), stable_effect_digest(k2))
        self.assertNotEqual(prepared("official:v1").digest(), prepared("official:v2").digest())

    def test_confirmed_effect_persists_across_restart(self):
        with TemporaryDirectory() as tmp:
            path = self.db(tmp)
            box1 = SqliteOutbox(path)
            p = prepared()
            row = box1.reserve(p.key, p.digest(), "lease-1", NOW)
            box1.begin(row.key_digest, "lease-1")
            box1.finish(row.key_digest, EffectState.SEND_CONFIRMED, message_id="m1", thread_id="t1")

            box2 = SqliteOutbox(path)
            persisted = box2.get(stable_effect_digest(p.key))
            self.assertIsNotNone(persisted)
            self.assertEqual(EffectState.SEND_CONFIRMED, persisted.state)
            self.assertEqual("m1", persisted.provider_message_id)

    def test_source_revision_cannot_open_second_send(self):
        with TemporaryDirectory() as tmp:
            box = SqliteOutbox(self.db(tmp))
            p1 = prepared("official:v1")
            row = box.reserve(p1.key, p1.digest(), "lease-1", NOW)
            box.begin(row.key_digest, "lease-1")
            box.finish(row.key_digest, EffectState.SEND_CONFIRMED, message_id="m", thread_id="t")

            p2 = prepared("official:v2")
            self.assertEqual(stable_effect_digest(p1.key), stable_effect_digest(p2.key))
            with self.assertRaisesRegex(EffectBlocked, "EXISTING_EFFECT:SEND_CONFIRMED"):
                box.reserve(p2.key, p2.digest(), "lease-2", NOW)

    def test_two_sqlite_instances_race_only_one_reservation(self):
        with TemporaryDirectory() as tmp:
            path = self.db(tmp)
            box1, box2 = SqliteOutbox(path), SqliteOutbox(path)
            p = prepared()
            barrier = Barrier(2)

            def reserve(box: SqliteOutbox, lease: str):
                barrier.wait(timeout=2)
                try:
                    return box.reserve(p.key, p.digest(), lease, NOW).state
                except EffectBlocked as exc:
                    return str(exc)

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda args: reserve(*args), ((box1, "lease-1"), (box2, "lease-2"))))

            self.assertEqual(1, sum(result is EffectState.RESERVED for result in results))
            self.assertEqual(1, sum(isinstance(result, str) and result.startswith("EXISTING_EFFECT:") for result in results))

    def test_two_gateway_writers_share_durable_outbox_and_call_provider_once(self):
        with TemporaryDirectory() as tmp:
            path = self.db(tmp)
            boxes = (SqliteOutbox(path), SqliteOutbox(path))
            p = prepared()
            calls = 0
            lock = Lock()
            barrier = Barrier(2)

            def provider(mail: PreparedEmail, token: str) -> ProviderResult:
                nonlocal calls
                with lock:
                    calls += 1
                return confirmed(mail)

            def writer(box: SqliteOutbox, lease: str):
                barrier.wait(timeout=2)
                try:
                    return send_once(
                        outbox=box,
                        prepared=p,
                        fence=fence(lease),
                        capability=capability(),
                        now=NOW,
                        current_main_sha=MAIN,
                        writer_fence_verifier=lambda _: True,
                        email_capability_verifier=lambda _: True,
                        provider_send=provider,
                    ).state
                except EffectBlocked as exc:
                    return str(exc)

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda args: writer(*args), ((boxes[0], "lease-A"), (boxes[1], "lease-B"))))

            self.assertEqual(1, calls)
            self.assertIn(EffectState.SEND_CONFIRMED, results)
            self.assertTrue(any(isinstance(x, str) and x.startswith("EXISTING_EFFECT:") for x in results))

    def test_in_progress_survives_restart_and_only_recovers_to_unknown(self):
        with TemporaryDirectory() as tmp:
            path = self.db(tmp)
            box1 = SqliteOutbox(path)
            p = prepared()
            row = box1.reserve(p.key, p.digest(), "lease-A", NOW)
            box1.begin(row.key_digest, "lease-A")

            box2 = SqliteOutbox(path)
            persisted = box2.get(row.key_digest)
            self.assertEqual(EffectState.SEND_IN_PROGRESS, persisted.state)
            with self.assertRaisesRegex(EffectBlocked, "EXISTING_EFFECT:SEND_IN_PROGRESS"):
                box2.reserve(p.key, p.digest(), "lease-B", NOW)
            recovered = box2.recover_in_progress_unknown(row.key_digest, "recovery:process-crash")
            self.assertEqual(EffectState.OUTCOME_UNKNOWN, recovered.state)
            with self.assertRaisesRegex(EffectBlocked, "EXISTING_EFFECT:OUTCOME_UNKNOWN"):
                box2.reserve(p.key, p.digest(), "lease-C", NOW)

    def test_unknown_requires_authoritative_not_sent_before_new_generation(self):
        with TemporaryDirectory() as tmp:
            box = SqliteOutbox(self.db(tmp))
            p = prepared()
            row = box.reserve(p.key, p.digest(), "lease-A", NOW)
            box.begin(row.key_digest, "lease-A")
            box.finish(row.key_digest, EffectState.OUTCOME_UNKNOWN, ref="gmail:timeout")
            with self.assertRaises(ValueError):
                box.reconcile_not_sent(row.key_digest, "")
            cleared = box.reconcile_not_sent(row.key_digest, "gmail:authoritative-search:no-message")
            self.assertEqual(EffectState.NOT_SENT, cleared.state)
            second = box.reserve(p.key, p.digest(), "lease-B", NOW)
            self.assertEqual(2, second.generation)

    def test_fence_mismatch_is_transactionally_blocked(self):
        with TemporaryDirectory() as tmp:
            box = SqliteOutbox(self.db(tmp))
            p = prepared()
            row = box.reserve(p.key, p.digest(), "lease-A", NOW)
            with self.assertRaisesRegex(EffectBlocked, "FENCE_TOKEN_MISMATCH"):
                box.begin(row.key_digest, "lease-B")
            self.assertEqual(EffectState.RESERVED, SqliteOutbox(self.db(tmp)).get(row.key_digest).state)

    def test_source_version_is_audited_in_durable_row(self):
        with TemporaryDirectory() as tmp:
            box = SqliteOutbox(self.db(tmp))
            p = prepared("official:v44")
            row = box.reserve(p.key, p.digest(), "lease", NOW)
            self.assertEqual("official:v44", box.source_version(row.key_digest))


if __name__ == "__main__":
    unittest.main(verbosity=2)
