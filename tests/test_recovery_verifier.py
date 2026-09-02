import unittest
from datetime import datetime, timedelta, timezone

from uexchanges.recovery_verifier import (
    RecoveryArtifact,
    RecoveryCode,
    RecoveryStatus,
    scan_stable_document,
    verify_recovery,
)

NOW = datetime(2026, 9, 2, 9, 30, tzinfo=timezone.utc)
MAIN = "a" * 40
REQUIRED = ("goal.md", "AGENTS.md", "MEMORY.md", "HANDOFF.md")
PRIVATE = {
    "Context_Registry": True,
    "Agent_Sessions": True,
    "Work_Leases": True,
    "Agent_Event_Bus": True,
    "RuntimeGraphV2CommandCenter": True,
}


def artifacts(*, stale=False, missing=None, old_main=False):
    result = []
    for path in REQUIRED:
        result.append(
            RecoveryArtifact(
                path=path,
                exists=path != missing,
                role="required",
                updated_at=NOW - (timedelta(hours=8) if stale else timedelta(minutes=10)),
                embedded_main_sha=("b" * 40 if old_main else MAIN),
                snapshot=path == "HANDOFF.md",
            )
        )
    return tuple(result)


class RecoveryVerifierTests(unittest.TestCase):
    def test_clean_recovery_surface_is_recoverable(self):
        report = verify_recovery(
            now=NOW,
            current_main_sha=MAIN,
            event_watermark="EVT-1",
            required_public_paths=REQUIRED,
            manifest_required_reads=REQUIRED,
            artifacts=artifacts(),
            private_sources_available=PRIVATE,
            command_center_available=True,
            stable_documents={"MEMORY.md": "# durable memory\nUNKNOWN is verification debt", "goal.md": "# goal"},
        )
        self.assertEqual(report.status, RecoveryStatus.RECOVERABLE)
        self.assertEqual(report.score, 100)
        self.assertFalse(report.findings)

    def test_missing_required_artifact_is_fatal(self):
        report = verify_recovery(
            now=NOW,
            current_main_sha=MAIN,
            event_watermark="EVT-1",
            required_public_paths=REQUIRED,
            manifest_required_reads=REQUIRED,
            artifacts=artifacts(missing="HANDOFF.md"),
            private_sources_available=PRIVATE,
            command_center_available=True,
        )
        self.assertEqual(report.status, RecoveryStatus.NOT_RECOVERABLE)
        self.assertIn(RecoveryCode.REQUIRED_ARTIFACT_MISSING, {item.code for item in report.findings})

    def test_manifest_omission_is_fatal(self):
        report = verify_recovery(
            now=NOW,
            current_main_sha=MAIN,
            event_watermark="EVT-1",
            required_public_paths=REQUIRED,
            manifest_required_reads=REQUIRED[:-1],
            artifacts=artifacts(),
            private_sources_available=PRIVATE,
            command_center_available=True,
        )
        self.assertEqual(report.status, RecoveryStatus.NOT_RECOVERABLE)
        self.assertIn(RecoveryCode.MANIFEST_READSET_INCOMPLETE, {item.code for item in report.findings})

    def test_stale_snapshot_is_degraded_not_false_authority(self):
        report = verify_recovery(
            now=NOW,
            current_main_sha=MAIN,
            event_watermark="EVT-1",
            required_public_paths=REQUIRED,
            manifest_required_reads=REQUIRED,
            artifacts=artifacts(stale=True, old_main=True),
            private_sources_available=PRIVATE,
            command_center_available=True,
        )
        codes = {item.code for item in report.findings}
        self.assertIn(RecoveryCode.SNAPSHOT_STALE, codes)
        self.assertIn(RecoveryCode.SNAPSHOT_MAIN_STALE, codes)
        self.assertEqual(report.status, RecoveryStatus.DEGRADED)

    def test_private_source_loss_is_fatal(self):
        private = dict(PRIVATE)
        private["Agent_Event_Bus"] = False
        report = verify_recovery(
            now=NOW,
            current_main_sha=MAIN,
            event_watermark="EVT-1",
            required_public_paths=REQUIRED,
            manifest_required_reads=REQUIRED,
            artifacts=artifacts(),
            private_sources_available=private,
            command_center_available=True,
        )
        self.assertEqual(report.status, RecoveryStatus.NOT_RECOVERABLE)
        self.assertIn(RecoveryCode.PRIVATE_CONTROL_PLANE_UNAVAILABLE, {item.code for item in report.findings})

    def test_memory_and_goal_stable_doc_drift_detection(self):
        memory_findings = scan_stable_document("MEMORY.md", "- Opportunities: 176\n")
        goal_findings = scan_stable_document("goal.md", "# Goal\n## Current canonical scale\n- 176\n")
        self.assertEqual(memory_findings[0].code, RecoveryCode.MEMORY_CONTAINS_VOLATILE_STATE)
        self.assertEqual(goal_findings[0].code, RecoveryCode.STABLE_GOAL_EMBEDS_VOLATILE_SCALE)

    def test_missing_main_or_watermark_is_fatal(self):
        report = verify_recovery(
            now=NOW,
            current_main_sha=None,
            event_watermark=None,
            required_public_paths=REQUIRED,
            manifest_required_reads=REQUIRED,
            artifacts=artifacts(),
            private_sources_available=PRIVATE,
            command_center_available=True,
        )
        codes = {item.code for item in report.findings}
        self.assertIn(RecoveryCode.CURRENT_MAIN_UNAVAILABLE, codes)
        self.assertIn(RecoveryCode.EVENT_WATERMARK_MISSING, codes)
        self.assertEqual(report.status, RecoveryStatus.NOT_RECOVERABLE)


if __name__ == "__main__":
    unittest.main()
