import os,sys,unittest
sys.path.insert(0,os.path.join(os.path.dirname(__file__),"..","src"))
from uexchanges.discovery import canonicalize_url, discover_from_html, opportunity_fingerprint, dedupe_discovered, DiscoveredURL

class DiscoveryTests(unittest.TestCase):
    def test_canonicalize_removes_tracking_fragment_and_sorts_query(self):
        u=canonicalize_url("HTTPS://Example.COM/a/?utm_source=x&b=2&a=1#frag")
        self.assertEqual(u,"https://example.com/a?a=1&b=2")
    def test_eyp_link_filter(self):
        html='<a href="/solidarity/opportunity/53807_en?utm_source=x">ESC</a><a href="/news">News</a>'
        items=discover_from_html("eyp_esc",html,"https://youth.europa.eu/")
        self.assertEqual(len(items),1); self.assertIn("/solidarity/opportunity/53807_en",items[0].canonical_url)
    def test_provider_id_beats_title_for_identity(self):
        a=opportunity_fingerprint(provider_id="53807",title="A")
        b=opportunity_fingerprint(provider_id="53807",title="B")
        self.assertEqual(a,b)
    def test_dedupe(self):
        x=DiscoveredURL("s","https://x/a","https://x/a")
        self.assertEqual(len(dedupe_discovered([x,x])),1)
