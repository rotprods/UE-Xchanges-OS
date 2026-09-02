import unittest

from uexchanges.semantic.qdrant import QdrantRESTClient, collection_spec


class QdrantTests(unittest.TestCase):
    def test_named_vector_collection_contract(self):
        spec = collection_spec(1024)
        self.assertEqual(spec["vectors"]["semantic"]["size"], 1024)
        self.assertEqual(spec["vectors"]["semantic"]["distance"], "Cosine")
        self.assertEqual(spec["vectors"]["cos20"]["size"], 20)

    def test_query_uses_named_vector_and_batch_endpoint(self):
        calls = []

        def transport(method, path, payload):
            calls.append((method, path, payload))
            if path.endswith("/points/query"):
                return {"result": {"points": [{"id": "a", "score": 0.9}]}}
            if path.endswith("/points/query/batch"):
                return {"result": [{"points": [{"id": "b", "score": 0.8}]}]}
            return {"result": {}}

        client = QdrantRESTClient("http://127.0.0.1:6333", "repo", transport=transport)
        hits = client.query([0.1] * 20, using="cos20", limit=3)
        batches = client.query_batch([{"query": [0.1] * 20, "using": "cos20", "limit": 2}])
        self.assertEqual(hits[0]["id"], "a")
        self.assertEqual(batches[0][0]["id"], "b")
        self.assertEqual(calls[0][2]["using"], "cos20")
        self.assertTrue(calls[1][1].endswith("/points/query/batch"))

    def test_stale_cleanup_is_scoped_to_repo_and_current_build(self):
        calls = []

        def transport(method, path, payload):
            calls.append((method, path, payload))
            return {"result": {}}

        client = QdrantRESTClient("http://127.0.0.1:6333", "repo", transport=transport)
        client.delete_stale_repo_points("rotprods/UE-Xchanges-OS", "build-123")
        filter_ = calls[0][2]["filter"]
        self.assertEqual(filter_["must"][0]["match"]["value"], "rotprods/UE-Xchanges-OS")
        self.assertEqual(filter_["must_not"][0]["match"]["value"], "build-123")


if __name__ == "__main__":
    unittest.main()
