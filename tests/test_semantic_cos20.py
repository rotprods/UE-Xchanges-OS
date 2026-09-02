import math
import unittest

from uexchanges.semantic.benchmark import run_projection_benchmark
from uexchanges.semantic.cos20 import Cos20Projector


class Cos20Tests(unittest.TestCase):
    def test_projection_is_20d_deterministic_and_normalized(self):
        projector = Cos20Projector(seed="test-seed")
        source = [float(index + 1) for index in range(1024)]
        first = projector.project(source)
        second = projector.project(source)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 20)
        self.assertAlmostEqual(math.sqrt(sum(value * value for value in first)), 1.0, places=10)

    def test_offline_benchmark_is_finite(self):
        report = run_projection_benchmark(source_dimensions=128, vectors=24)
        self.assertTrue(report.deterministic)
        self.assertTrue(report.finite)
        self.assertEqual(report.target_dimensions, 20)
        self.assertGreater(report.projection_vectors_per_second, 0)
        self.assertGreaterEqual(report.cosine_pearson, -1.0)
        self.assertLessEqual(report.cosine_pearson, 1.0)


if __name__ == "__main__":
    unittest.main()
