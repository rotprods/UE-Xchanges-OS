import unittest

from uexchanges.semantic.ollama import OllamaEmbedder, OllamaError


class FakeOllama(OllamaEmbedder):
    def __init__(self, response):
        super().__init__("http://127.0.0.1:11434", "qwen3-embedding:0.6b")
        self.response = response
        self.calls = []

    def _request(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        return self.response


class OllamaTests(unittest.TestCase):
    def test_embed_uses_batch_api_and_preserves_width(self):
        client = FakeOllama({"embeddings": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]})
        vectors = client.embed(["alpha", "beta"])
        self.assertEqual(len(vectors), 2)
        self.assertEqual(len(vectors[0]), 3)
        self.assertEqual(client.calls[0][0:2], ("POST", "/api/embed"))
        self.assertEqual(client.calls[0][2]["model"], "qwen3-embedding:0.6b")
        self.assertEqual(client.calls[0][2]["input"], ["alpha", "beta"])
        self.assertTrue(client.calls[0][2]["truncate"])

    def test_embed_rejects_inconsistent_dimensions(self):
        client = FakeOllama({"embeddings": [[0.1, 0.2], [0.3]]})
        with self.assertRaises(OllamaError):
            client.embed(["alpha", "beta"])


if __name__ == "__main__":
    unittest.main()
