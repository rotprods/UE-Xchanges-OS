from __future__ import annotations

import json
from dataclasses import asdict
import tempfile
import unittest
from pathlib import Path

from uexchanges.semantic.artifact_registry import (
    ArtifactRegistryError,
    SemanticArtifactRecord,
    SemanticArtifactRegistry,
)

H = "a" * 64
MAIN = "b" * 40
OLD = "c" * 40


def record(*, artifact_id: str = "base", source_sha: str = OLD, freshness: str = "HISTORICAL_ONLY", parent=None, baseline="base"):
    return SemanticArtifactRecord(
        artifact_id=artifact_id,
        source_repo="rotprods/UE-Xchanges-OS",
        source_sha=source_sha,
        created_at="2026-09-15T16:53:24+02:00",
        model="qwen3-embedding:0.6b",
        model_sha256=H,
        embedding_dimensions=1024,
        chunk_contract="semantic-chunking-v1",
        points=676,
        paths=397,
        snapshot_sha256=H,
        vectors_sha256=H,
        graph_sha256=H,
        baseline_id=baseline,
        delta_parent=parent,
        freshness=freshness,
        authority="DERIVED_RECONSTRUCTIBLE_ONLY",
        benchmark_ref=None,
        backup_locations=("drive:folder:durable",),
        restore_status="AIR_GAPPED_RESTORE_PASS",
        cos_dimensions=20,
        mutation_authority=False,
    )


class RegistryTests(unittest.TestCase):
    def test_historical_baseline_valid_current_is_none(self) -> None:
        registry = SemanticArtifactRegistry()
        registry.add(record())
        registry.validate()
        self.assertEqual(registry.baseline_id, "base")
        self.assertIsNone(registry.current_id)

    def test_current_requires_exact_main(self) -> None:
        registry = SemanticArtifactRegistry()
        registry.add(record(artifact_id="base"))
        with self.assertRaisesRegex(ArtifactRegistryError, "does not match main"):
            registry.add(
                record(
                    artifact_id="current",
                    source_sha=OLD,
                    freshness="CURRENT_EXACT_SOURCE",
                    parent="base",
                    baseline="base",
                ),
                observed_main_sha=MAIN,
            )

    def test_current_pointer_rejects_historical(self) -> None:
        registry = SemanticArtifactRegistry()
        registry.add(record())
        with self.assertRaisesRegex(ArtifactRegistryError, "CURRENT_EXACT_SOURCE"):
            registry.set_current("base", observed_main_sha=MAIN)

    def test_duplicate_id_fails(self) -> None:
        registry = SemanticArtifactRegistry()
        registry.add(record())
        with self.assertRaisesRegex(ArtifactRegistryError, "duplicate"):
            registry.add(record())

    def test_broken_parent_fails(self) -> None:
        registry = SemanticArtifactRegistry()
        with self.assertRaisesRegex(ArtifactRegistryError, "delta_parent"):
            registry.add(record(artifact_id="delta", parent="missing", baseline="delta"))

    def test_authority_boundary_fails_closed(self) -> None:
        raw = record()
        values = asdict(raw)
        values["mutation_authority"] = True
        with self.assertRaisesRegex(ArtifactRegistryError, "non-mutating"):
            SemanticArtifactRecord(**values).validate()

    def test_load_does_not_depend_on_artifact_sort_order(self) -> None:
        base = record(artifact_id="z-base", baseline="z-base")
        delta = record(artifact_id="a-delta", parent="z-base", baseline="z-base")
        payload = {
            "schema_version": "1.0.0",
            "authority": "DERIVED_RECONSTRUCTIBLE_ONLY",
            "mutation_authority": False,
            "baseline_id": "z-base",
            "current_id": None,
            "artifacts": [asdict(delta), asdict(base)],
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "registry.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            loaded = SemanticArtifactRegistry.load(path)
            self.assertEqual(set(loaded.artifacts), {"z-base", "a-delta"})

    def test_roundtrip_preserves_digest(self) -> None:
        registry = SemanticArtifactRegistry()
        registry.add(record())
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "registry.json"
            registry.dump(path)
            loaded = SemanticArtifactRegistry.load(path)
            self.assertEqual(loaded.digest(), registry.digest())


if __name__ == "__main__":
    unittest.main()
