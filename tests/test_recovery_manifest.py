import unittest
from datetime import datetime, timezone

from uexchanges.recovery_manifest import (
    PrivateRecoverySource,
    RecoveryArtifactDigest,
    RecoveryManifest,
    build_recovery_manifest,
    digest_public_artifacts,
    sha256_text,
)

NOW = datetime(2026, 9, 2, 9, 0, tzinfo=timezone.utc)
MAIN = "a" * 40


def manifest():
    return build_recovery_manifest(
        generated_at=NOW,
        current_main_sha=MAIN,
        event_watermark="EVT-2",
        bootstrap_manifest_version="1.0.0",
        command_center_ref="drive:cc",
        command_center_watermark="EVT-1",
        public_artifacts=(
            RecoveryArtifactDigest("goal.md", "b" * 64, "mission"),
            RecoveryArtifactDigest("AGENTS.md", "c" * 64, "writer-contract"),
        ),
        private_sources=(
            PrivateRecoverySource("Agent_Event_Bus", True, "EVT-2"),
            PrivateRecoverySource("Work_Leases", True, "scan-1"),
        ),
    )


class RecoveryManifestTests(unittest.TestCase):
    def test_bundle_hash_is_content_addressed_not_generation_time(self):
        first = manifest()
        second = build_recovery_manifest(
            generated_at=datetime(2026, 9, 2, 10, 0, tzinfo=timezone.utc),
            current_main_sha=MAIN,
            event_watermark="EVT-2",
            bootstrap_manifest_version="1.0.0",
            command_center_ref="drive:cc",
            command_center_watermark="EVT-1",
            public_artifacts=tuple(reversed(first.public_artifacts)),
            private_sources=tuple(reversed(first.private_sources)),
        )
        self.assertEqual(first.bundle_hash, second.bundle_hash)

    def test_artifact_change_changes_bundle_hash(self):
        first = manifest()
        changed = build_recovery_manifest(
            generated_at=NOW,
            current_main_sha=MAIN,
            event_watermark="EVT-2",
            bootstrap_manifest_version="1.0.0",
            command_center_ref="drive:cc",
            command_center_watermark="EVT-1",
            public_artifacts=(RecoveryArtifactDigest("goal.md", "d" * 64, "mission"),),
            private_sources=first.private_sources,
        )
        self.assertNotEqual(first.bundle_hash, changed.bundle_hash)

    def test_manifest_rejects_tampered_bundle_hash(self):
        first = manifest()
        with self.assertRaises(ValueError):
            RecoveryManifest(
                generated_at=first.generated_at,
                current_main_sha=first.current_main_sha,
                event_watermark=first.event_watermark,
                bootstrap_manifest_version=first.bootstrap_manifest_version,
                command_center_ref=first.command_center_ref,
                command_center_watermark=first.command_center_watermark,
                public_artifacts=first.public_artifacts,
                private_sources=first.private_sources,
                bundle_hash="0" * 64,
            )

    def test_digest_public_artifacts_is_deterministic(self):
        digests = digest_public_artifacts(
            {
                "MEMORY.md": ("memory", "semantic-memory", True),
                "goal.md": ("goal", "mission", True),
            }
        )
        self.assertEqual([item.path for item in digests], ["MEMORY.md", "goal.md"])
        self.assertEqual(digests[1].sha256, sha256_text("goal"))

    def test_secret_like_private_source_name_is_rejected(self):
        with self.assertRaises(ValueError):
            PrivateRecoverySource("browser_cookie_token", True)

    def test_public_artifact_path_is_relative_and_safe(self):
        with self.assertRaises(ValueError):
            RecoveryArtifactDigest("../private.txt", "a" * 64, "bad")


if __name__ == "__main__":
    unittest.main()
