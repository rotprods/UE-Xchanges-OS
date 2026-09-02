import unittest
from pathlib import Path

from uexchanges.semantic.config import SemanticConfig
from uexchanges.semantic.graphify import CosGraphEngine


class FakeQdrant:
    def __init__(self):
        self.search_batches = []

    def scroll(self, **kwargs):
        self.scroll_kwargs = kwargs
        return [
            {"id": "a", "payload": {"path": "a.md", "line_start": 1, "line_end": 5, "chunk_index": 0}, "vector": {"cos20": [1.0] + [0.0] * 19}},
            {"id": "b", "payload": {"path": "b.md", "line_start": 1, "line_end": 5, "chunk_index": 0}, "vector": {"cos20": [0.9, 0.1] + [0.0] * 18}},
            {"id": "c", "payload": {"path": "c.md", "line_start": 1, "line_end": 5, "chunk_index": 0}, "vector": {"cos20": [0.0, 1.0] + [0.0] * 18}},
        ]

    def query_batch(self, searches):
        self.search_batches.append(searches)
        by_vector = []
        for search in searches:
            vector = search["query"]
            if vector[0] == 1.0:
                by_vector.append([{"id": "a", "score": 1.0}, {"id": "b", "score": 0.94}])
            elif vector[0] == 0.9:
                by_vector.append([{"id": "b", "score": 1.0}, {"id": "a", "score": 0.93}])
            else:
                by_vector.append([{"id": "c", "score": 1.0}])
        return by_vector


class GraphifyTests(unittest.TestCase):
    def test_cos20_graph_is_batched_deduped_and_derived_only(self):
        config = SemanticConfig(repo_root=Path("."))
        qdrant = FakeQdrant()
        graph = CosGraphEngine(config, qdrant=qdrant).build(
            repo_id="rotprods/UE-Xchanges-OS",
            top_k=2,
            min_score=0.72,
            query_batch_size=2,
        )
        self.assertEqual(graph["dimensions"], 20)
        self.assertEqual(graph["semantic_authority"], "QDRANT_PROJECTION_ONLY_NOT_DOMAIN_TRUTH")
        self.assertEqual(graph["node_count"], 3)
        self.assertEqual(graph["edge_count"], 1)
        self.assertEqual(graph["edges"][0]["source"], "a")
        self.assertEqual(graph["edges"][0]["target"], "b")
        self.assertEqual(graph["edges"][0]["authority"], "DERIVED_RECONSTRUCTIBLE_ONLY")
        self.assertEqual(len(qdrant.search_batches), 2)
        first_search = qdrant.search_batches[0][0]
        self.assertEqual(first_search["using"], "cos20")
        self.assertEqual(first_search["filter"]["must"][0]["match"]["value"], "rotprods/UE-Xchanges-OS")


if __name__ == "__main__":
    unittest.main()
