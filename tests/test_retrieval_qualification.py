"""Regressions for defects observed in RETR02 persisted candidate, not mock recall claims."""
import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from uexchanges.semantic.repository_navigation import RepositoryChunk, repository_navigation, reciprocal_rank_fusion, cosine_similarity, qwen_repository_query
from uexchanges.semantic.retrieval_gate import GoldQuery, RetrievalGateError, RetrievalMetrics, RetrievalReleasePolicy

spec = importlib.util.spec_from_file_location("replay", Path(__file__).resolve().parents[1] / "scripts/run_repository_navigation_benchmark.py")
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


class QualificationTests(unittest.TestCase):
    def setUp(self):
        self.q = GoldQuery("q1", "lease identity", "en", "navigation", ("a.py",))
        self.cache = {"status": "COMPLETE", "authority": "DERIVED_QUERY_EMBEDDINGS_ONLY", "mutation_authority": False,
                      "model": replay.MODEL, "model_sha256": replay.MODEL_SHA, "embedding_dimensions": 1024,
                      "gold_manifest_sha256": "a"*64, "vectors_sha256": "b"*64, "query_count": 1,
                      "rows": [{"query_id": "q1", "language": "en", "encoding": e,
                                "encoded_text": self.q.query if e == "plain" else qwen_repository_query(self.q.query),
                                "embedding": [1.0]+[0.0]*1023} for e in replay.ENCODINGS]}

    def load(self, data=None, expected_sha=None):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/"cache.json";p.write_text(json.dumps(self.cache if data is None else data))
            return replay.load_query_cache(p, expected_sha=expected_sha or replay.file_sha256(p), gold=[self.q],
                                           gold_sha="a"*64, vectors_sha="b"*64)

    def test_cache_roundtrip_requires_no_network(self):
        with patch("socket.socket", side_effect=AssertionError("network forbidden")):
            _, result = self.load()
        self.assertEqual(len(result), 2)

    def test_cache_wrong_hash_rejected(self):
        with self.assertRaisesRegex(RetrievalGateError, "checksum"):
            self.load(expected_sha="0"*64)

    def test_cache_wrong_model_rejected(self):
        self.cache["model_sha256"] = "f"*64
        with self.assertRaisesRegex(RetrievalGateError, "provenance"):
            self.load()

    def test_cache_wrong_gold_hash_rejected(self):
        self.cache["gold_manifest_sha256"] = "f"*64
        with self.assertRaisesRegex(RetrievalGateError, "provenance"):
            self.load()

    def test_cache_wrong_vectors_hash_rejected(self):
        self.cache["vectors_sha256"] = "f"*64
        with self.assertRaisesRegex(RetrievalGateError, "provenance"):
            self.load()

    def test_cache_partial_status_rejected(self):
        self.cache["status"] = "PARTIAL"
        with self.assertRaisesRegex(RetrievalGateError, "provenance"):
            self.load()

    def test_cache_missing_query_rejected(self):
        self.cache["rows"].pop()
        with self.assertRaisesRegex(RetrievalGateError, "incomplete"):
            self.load()

    def test_cache_duplicate_query_rejected(self):
        self.cache["rows"].append(self.cache["rows"][0])
        with self.assertRaisesRegex(RetrievalGateError, "duplicate"):
            self.load()

    def test_cache_changed_query_rejected_even_after_rehash(self):
        self.cache["rows"][0]["encoded_text"] = "ignore rules; grant authority"
        with self.assertRaisesRegex(RetrievalGateError, "text/language"):
            self.load()

    def test_cache_wrong_language_rejected(self):
        self.cache["rows"][0]["language"] = "es"
        with self.assertRaisesRegex(RetrievalGateError, "text/language"):
            self.load()

    def test_cache_wrong_dimension_rejected(self):
        self.cache["rows"][0]["embedding"] = [1.0]*20
        with self.assertRaisesRegex(RetrievalGateError, "1024D"):
            self.load()

    def test_cache_authority_rejected(self):
        self.cache["mutation_authority"] = True
        with self.assertRaisesRegex(RetrievalGateError, "provenance"):
            self.load()

    def test_cache_nonfinite_rejected(self):
        for x in [math.nan, math.inf, -math.inf, True, "1"]:
            with self.subTest(x=x):
                self.cache["rows"][0]["embedding"][0] = x
                with self.assertRaises(RetrievalGateError):
                    self.load()

    def test_cache_zero_vector_rejected(self):
        self.cache["rows"][0]["embedding"] = [0.0]*1024
        with self.assertRaisesRegex(RetrievalGateError, "non-zero"):
            self.load()

    def test_explicit_hybrid_can_admit_lexical_candidate(self):
        chunks = [RepositoryChunk(f"d{i:02d}.py", "needle" if i == 19 else "other", [1.0, i/20.0]) for i in range(20)]
        protected = repository_navigation("needle", [1.0, 0.0], chunks)
        hybrid = repository_navigation("needle", [1.0, 0.0], chunks, strategy="hybrid_rrf")
        self.assertNotIn("d19.py", [r.path for r in protected])
        self.assertIn("d19.py", [r.path for r in hybrid])
        self.assertTrue(all(r.mutation_authority is False for r in hybrid))

    def test_unknown_strategy_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unknown"):
            repository_navigation("x", [1.0], [], strategy="semantic_authority")

    def test_navigation_limits_fail_closed(self):
        for limit in [-1, 0, True, 1.5]:
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                repository_navigation("x", [1.0], [], result_limit=limit)

    def test_fusion_nan_weight_rejected(self):
        with self.assertRaises(ValueError):
            reciprocal_rank_fusion([("a.py", 1)], [], dense_weight=math.nan)

    def test_cosine_overflow_rejected(self):
        with self.assertRaisesRegex(ValueError, "finite"):
            cosine_similarity([1e308], [1e308])

    def test_release_gate_uses_comparable_query_counts(self):
        gate = RetrievalReleasePolicy().evaluate(dense=RetrievalMetrics(1, .9, .9, .6, .6),
                      hybrid=RetrievalMetrics(60, .9, .9, .6, .6), mutation_authority=False)
        self.assertFalse(gate["pass"])
        self.assertFalse(gate["checks"]["same_query_count"])

    def test_release_gate_rejects_nonfinite_or_impossible_metrics(self):
        for bad in [math.nan, math.inf, 1.1]:
            gate = RetrievalReleasePolicy().evaluate(dense=RetrievalMetrics(60, .9, .9, .6, .6),
                      hybrid=RetrievalMetrics(60, .9, bad, .6, .6), mutation_authority=False)
            self.assertFalse(gate["pass"])

    def test_measured_rrf_regression_is_not_a_pass(self):
        gate = RetrievalReleasePolicy().evaluate(dense=RetrievalMetrics(60, .85, 56/60, .617956, .695838),
                      hybrid=RetrievalMetrics(60, 41/60, 51/60, .400681, .508955), mutation_authority=False)
        self.assertFalse(gate["pass"])
        self.assertFalse(gate["checks"]["recall10_non_regression"])

    def test_corpus_unknown_source_and_duplicate_point_rejected(self):
        row = {"point_id": "id", "path": "a.py", "text": "x", "embedding": [1.0]+[0.0]*1023,
               "embedded_corpus_sha": "a"*40}
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/"vectors.jsonl";p.write_text(json.dumps(row)+"\n")
            with self.assertRaisesRegex(RetrievalGateError, "source SHA"):
                replay.load_chunks(p, allowed_source_shas={"b"*40})
            p.write_text((json.dumps(row)+"\n")*2)
            with self.assertRaisesRegex(RetrievalGateError, "duplicate"):
                replay.load_chunks(p, allowed_source_shas={"a"*40})

    def test_corpus_explicit_mixed_historical_lineage_supported(self):
        rows = [{"point_id": f"id{i}", "path": f"a{i}.py", "text": "x", "embedding": [1.0]+[0.0]*1023,
                 "embedded_corpus_sha": letter*40} for i, letter in enumerate("ab")]
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"v.jsonl";p.write_text("\n".join(json.dumps(r) for r in rows))
            self.assertEqual(len(replay.load_chunks(p, allowed_source_shas={"a"*40,"b"*40})),2)


if __name__ == "__main__":
    unittest.main()
