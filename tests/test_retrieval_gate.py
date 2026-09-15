from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from uexchanges.semantic.retrieval_gate import (
    GoldQuery,
    RetrievalGateError,
    RetrievalMetrics,
    RetrievalReleasePolicy,
    evaluate_rankings,
    file_sha256,
    load_gold_set,
)


class RetrievalGateTests(unittest.TestCase):
    def test_metric_calculation_is_deterministic(self) -> None:
        gold = [
            GoldQuery("q1", "one", "en", "test", ("a",)),
            GoldQuery("q2", "two", "es", "test", ("b",)),
        ]
        metrics = evaluate_rankings(gold, {"q1": ["x", "a"], "q2": ["b"]})
        self.assertEqual(metrics.query_count, 2)
        self.assertEqual(metrics.recall_at_5, 1.0)
        self.assertEqual(metrics.recall_at_10, 1.0)
        self.assertAlmostEqual(metrics.mrr, 0.75)
        self.assertGreater(metrics.ndcg_at_10, 0.8)

    def test_release_gate_enforces_non_mutating_boundary(self) -> None:
        good = RetrievalMetrics(60, 0.8, 0.8, 0.5, 0.5)
        gate = RetrievalReleasePolicy().evaluate(dense=good, hybrid=good, mutation_authority=True)
        self.assertFalse(gate["pass"])
        self.assertFalse(gate["checks"]["mutation_authority_false"])

    def test_checksum_corruption_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            shard = root / "s.json"
            shard.write_text("[]\n", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": "2.0.0",
                "authority": "DERIVED_BENCHMARK_FIXTURE_ONLY",
                "query_count": 50,
                "shards": [{"path": "s.json", "sha256": "0" * 64}],
            }), encoding="utf-8")
            with self.assertRaisesRegex(RetrievalGateError, "checksum mismatch"):
                load_gold_set(manifest)

    def test_manifest_shard_path_traversal_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "gold"
            root.mkdir()
            outside = Path(td) / "outside.json"
            outside.write_text("[]", encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": "2.0.0",
                "authority": "DERIVED_BENCHMARK_FIXTURE_ONLY",
                "query_count": 50,
                "shards": [{"path": "../outside.json", "sha256": file_sha256(outside)}],
            }), encoding="utf-8")
            with self.assertRaisesRegex(RetrievalGateError, "unsafe gold shard path"):
                load_gold_set(manifest)

    def test_under_50_queries_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rows = [
                {
                    "query_id": f"q{i}", "query": "x", "language": "en" if i % 2 else "es",
                    "intent": "test", "expected_paths": ["a.py"],
                }
                for i in range(2)
            ]
            shard = root / "s.json"
            shard.write_text(json.dumps(rows), encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": "2.0.0",
                "authority": "DERIVED_BENCHMARK_FIXTURE_ONLY",
                "query_count": 2,
                "shards": [{"path": "s.json", "sha256": file_sha256(shard)}],
            }), encoding="utf-8")
            with self.assertRaisesRegex(RetrievalGateError, "at least 50"):
                load_gold_set(manifest)

    def test_real_gold_manifest_is_60_query_bilingual(self) -> None:
        manifest = Path("benchmarks/semantic/repository_navigation_gold_v2.manifest.json")
        gold = load_gold_set(manifest)
        self.assertEqual(len(gold), 60)
        self.assertEqual({q.language for q in gold}, {"en", "es"})
        self.assertTrue(all(q.expected_paths for q in gold))


if __name__ == "__main__":
    unittest.main()
