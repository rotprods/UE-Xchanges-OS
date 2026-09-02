import tempfile
import unittest
from pathlib import Path

from uexchanges.semantic.chunking import chunk_text, scan_repository


class ChunkingTests(unittest.TestCase):
    def test_chunk_ids_are_stable(self):
        text = "\n".join(f"line {index} " + "x" * 40 for index in range(80))
        first = list(chunk_text(path="docs/a.md", text=text, target_chars=700, overlap_chars=80))
        second = list(chunk_text(path="docs/a.md", text=text, target_chars=700, overlap_chars=80))
        self.assertEqual([item.point_id for item in first], [item.point_id for item in second])
        self.assertGreater(len(first), 1)
        self.assertTrue(all(item.line_start <= item.line_end for item in first))

    def test_scan_skips_private_and_binary_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "private").mkdir()
            (root / "docs" / "safe.md").write_text("safe semantic text\n" * 20, encoding="utf-8")
            (root / "private" / "secret.txt").write_text("never index me", encoding="utf-8")
            (root / ".env.local").write_text("API_TOKEN=never-index-me", encoding="utf-8")
            (root / ".env.example").write_text("API_TOKEN=", encoding="utf-8")
            (root / "image.png").write_bytes(b"\x89PNG\x00binary")
            chunks, stats = scan_repository(root, target_chars=512, overlap_chars=64)
            self.assertTrue(any(chunk.path == "docs/safe.md" for chunk in chunks))
            self.assertFalse(any("secret" in chunk.text for chunk in chunks))
            self.assertFalse(any("never-index-me" in chunk.text for chunk in chunks))
            self.assertTrue(any(chunk.path == ".env.example" for chunk in chunks))
            self.assertGreaterEqual(stats.skipped_secret, 2)
            self.assertGreaterEqual(stats.skipped_binary, 1)


if __name__ == "__main__":
    unittest.main()
