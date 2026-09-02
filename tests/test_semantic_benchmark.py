import unittest

from uexchanges.semantic.benchmark import run_live_retrieval_benchmark, summarize_latencies


class FakeEmbedder:
    def embed(self, texts):
        vectors = []
        for text in texts:
            base = float((sum(ord(char) for char in text) % 7) + 1)
            vectors.append([base + (index % 3) for index in range(32)])
        return vectors


class FakeQdrant:
    def query(self, vector, *, using, limit, filter_):
        self.last_filter = filter_
        if using == "semantic":
            return [
                {"id": "a", "score": 0.95, "payload": {"path": "docs/A.md", "line_start": 1}},
                {"id": "b", "score": 0.90, "payload": {"path": "docs/B.md", "line_start": 2}},
                {"id": "c", "score": 0.85, "payload": {"path": "docs/C.md", "line_start": 3}},
            ]
        return [
            {"id": "b", "score": 0.91, "payload": {"path": "docs/B.md", "line_start": 2}},
            {"id": "a", "score": 0.89, "payload": {"path": "docs/A.md", "line_start": 1}},
            {"id": "z", "score": 0.70, "payload": {"path": "docs/Z.md", "line_start": 9}},
        ]


class BenchmarkTests(unittest.TestCase):
    def test_latency_summary_interpolates_p95(self):
        summary = summarize_latencies([0.001, 0.002, 0.003, 0.004])
        self.assertEqual(summary.samples, 4)
        self.assertEqual(summary.p50_ms, 2.5)
        self.assertAlmostEqual(summary.p95_ms, 3.85, places=3)

    def test_live_benchmark_reports_latency_overlap_and_paths(self):
        qdrant = FakeQdrant()
        report = run_live_retrieval_benchmark(
            embedder=FakeEmbedder(),
            qdrant=qdrant,
            repo_id="rotprods/UE-Xchanges-OS",
            semantic_vector_name="semantic",
            cos_vector_name="cos20",
            projection_seed="test-seed",
            iterations=4,
        )
        self.assertEqual(report["embedding_dimensions"], 32)
        self.assertEqual(report["embedding_latency"]["samples"], 4)
        self.assertEqual(report["semantic_query_latency"]["samples"], 4)
        self.assertEqual(report["cos20_query_latency"]["samples"], 4)
        self.assertAlmostEqual(report["semantic_cos20_overlap_at_5"], 2 / 3, places=6)
        self.assertEqual(report["overlap_semantics"], "DIAGNOSTIC_ONLY_NOT_RELEVANCE_GROUND_TRUTH")
        self.assertEqual(qdrant.last_filter["must"][0]["match"]["value"], "rotprods/UE-Xchanges-OS")
        first_probe = next(iter(report["probe_hits"].values()))
        self.assertEqual(first_probe["semantic_top3"][0]["path"], "docs/A.md")


if __name__ == "__main__":
    unittest.main()
