import tempfile
import unittest
from pathlib import Path

from uexchanges.semantic.config import SemanticConfig
from uexchanges.semantic.indexer import SemanticIndexer


class FakeEmbedder:
    def embed(self, texts):
        return [[float((index % 7) + 1) for index in range(32)] for _ in texts]


class FakeQdrant:
    def __init__(self):
        self.ensure = None
        self.deleted = None
        self.stale_cleanup = None
        self.points = []
        self.operations = []

    def ensure_collection(self, dimensions, **kwargs):
        self.ensure = (dimensions, kwargs)

    def delete_repo_points(self, repo_id):
        self.deleted = repo_id
        self.operations.append(("delete_all", repo_id))

    def delete_stale_repo_points(self, repo_id, index_build_id):
        self.stale_cleanup = (repo_id, index_build_id)
        self.operations.append(("cleanup_stale", repo_id, index_build_id))

    def upsert(self, points):
        self.points.extend(points)
        self.operations.append(("upsert", len(points)))


class IndexerTests(unittest.TestCase):
    def test_sync_stores_semantic_and_cos20_named_vectors(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("semantic repository graph\n" * 80, encoding="utf-8")
            config = SemanticConfig(repo_root=root, chunk_chars=512, overlap_chars=64, embed_batch_size=2, upsert_batch_size=2)
            qdrant = FakeQdrant()
            report = SemanticIndexer(config, embedder=FakeEmbedder(), qdrant=qdrant).sync()
            self.assertEqual(report.semantic_dimensions, 32)
            self.assertEqual(report.cos_dimensions, 20)
            self.assertTrue(qdrant.points)
            point = qdrant.points[0]
            self.assertEqual(len(point["vector"]["semantic"]), 32)
            self.assertEqual(len(point["vector"]["cos20"]), 20)
            self.assertEqual(point["payload"]["projection_authority"], "DERIVED_RECONSTRUCTIBLE_ONLY")
            self.assertTrue(point["payload"]["index_build_id"])
            self.assertIsNone(qdrant.deleted)
            self.assertIsNotNone(qdrant.stale_cleanup)
            self.assertEqual(qdrant.operations[-1][0], "cleanup_stale")
            self.assertTrue(any(op[0] == "upsert" for op in qdrant.operations[:-1]))


if __name__ == "__main__":
    unittest.main()
