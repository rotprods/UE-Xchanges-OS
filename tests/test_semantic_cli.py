import unittest

from uexchanges.semantic.cli import _graph_alias_argv


class CliTests(unittest.TestCase):
    def test_graph_alias_moves_repo_before_subcommand(self):
        self.assertEqual(
            _graph_alias_argv(["--repo", "/tmp/repo", "--top-k", "4"]),
            ["--repo", "/tmp/repo", "graphify", "--top-k", "4"],
        )


if __name__ == "__main__":
    unittest.main()
