import unittest

from uexchanges.semantic.config import SemanticConfigError, require_local_endpoint


class ConfigTests(unittest.TestCase):
    def test_loopback_is_allowed(self):
        self.assertEqual(require_local_endpoint("http://127.0.0.1:6333"), "http://127.0.0.1:6333")
        self.assertEqual(require_local_endpoint("http://localhost:11434/"), "http://localhost:11434")

    def test_remote_is_refused_by_default(self):
        with self.assertRaises(SemanticConfigError):
            require_local_endpoint("https://vectors.example.com")
        self.assertEqual(
            require_local_endpoint("https://vectors.example.com", allow_remote=True),
            "https://vectors.example.com",
        )


if __name__ == "__main__":
    unittest.main()
