import hashlib, os, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from uexchanges.providers import AccessMode, PagePayload, ProviderScanner, ProviderSpec, salto_page_url
from uexchanges.source_state import SourceStateStore


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        self.tmp.close()
        self.state = SourceStateStore(self.tmp.name)
        self.scanner = ProviderScanner(self.state)

    def tearDown(self):
        self.state.close(); os.unlink(self.tmp.name)

    def test_salto_pagination_preserves_filters(self):
        u = salto_page_url("https://www.salto-youth.net/tools/european-training-calendar/browse/?b_country=ES", 20, 10)
        self.assertIn("b_country=ES", u); self.assertIn("b_offset=20", u); self.assertIn("b_limit=10", u)

    def test_static_scan_discovers_and_dedupes(self):
        pages = {
            0: '<a href="/tools/european-training-calendar/training/a.100/">A</a><a href="/tools/european-training-calendar/training/b.101/">B</a>',
            2: ''
        }
        def fetch(url, headers):
            offset = 2 if "b_offset=2" in url else 0
            text = pages[offset]
            return PagePayload(url, 200, text, hashlib.sha256(text.encode()).hexdigest())
        spec = ProviderSpec("salto_calendar", "https://www.salto-youth.net/tools/european-training-calendar/browse/", AccessMode.STATIC_PAGINATED_HTML, page_size=2, max_pages=4)
        r = self.scanner.scan(spec, fetch)
        self.assertEqual(r.candidates_found, 2); self.assertEqual(r.new_candidates, 2)
        r2 = self.scanner.scan(spec, fetch)
        self.assertEqual(r2.new_candidates, 0)

    def test_dynamic_index_fails_explicitly(self):
        spec = ProviderSpec("eyp_esc", "https://youth.europa.eu", AccessMode.DYNAMIC_INDEX)
        r = self.scanner.scan(spec, lambda *_: None)
        self.assertIsNotNone(r.blocked_reason); self.assertEqual(r.pages_fetched, 0)

    def test_auth_index_does_not_bypass(self):
        spec = ProviderSpec("salto_trainers", "https://www.salto-youth.net/tools/call-for-trainers/", AccessMode.AUTH_INDEX_PUBLIC_DETAILS)
        r = self.scanner.scan(spec, lambda *_: None)
        self.assertIn("authentication", r.blocked_reason.lower())

    def test_external_ingest_dedupes(self):
        r = self.scanner.ingest_external_candidates("eurodesk", ["https://x/a?utm_source=z", "https://x/a"])
        self.assertEqual(r.candidates_found, 1); self.assertEqual(r.new_candidates, 1)
