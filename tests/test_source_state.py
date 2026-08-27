import os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from uexchanges.source_state import SourceStateStore


class StateStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        self.tmp.close()
        self.store = SourceStateStore(self.tmp.name)

    def tearDown(self):
        self.store.close()
        os.unlink(self.tmp.name)

    def test_change_detection(self):
        self.assertTrue(self.store.record_fetch("s", "https://x", status=200, content_hash="a"))
        self.assertFalse(self.store.record_fetch("s", "https://x", status=200, content_hash="a"))
        self.assertTrue(self.store.record_fetch("s", "https://x", status=200, content_hash="b"))

    def test_conditional_headers(self):
        self.store.record_fetch("s", "https://x", status=200, content_hash="a", etag='"abc"', last_modified="Wed")
        self.assertEqual(self.store.conditional_headers("s", "https://x"), {"If-None-Match": '"abc"', "If-Modified-Since": "Wed"})

    def test_candidate_seen_is_idempotent(self):
        self.assertTrue(self.store.mark_candidate_seen("fp", "s", "https://x/a"))
        self.assertFalse(self.store.mark_candidate_seen("fp", "s", "https://x/a"))
        self.assertEqual(self.store.candidate_count("s"), 1)
