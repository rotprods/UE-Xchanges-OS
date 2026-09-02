from __future__ import annotations

import math
import random
import statistics
import time
from dataclasses import asdict, dataclass
from typing import Any

from .cos20 import Cos20Projector, cosine_similarity


@dataclass(frozen=True, slots=True)
class ProjectionBenchmark:
    source_dimensions: int
    target_dimensions: int
    vectors: int
    pairs: int
    cosine_mae: float
    cosine_pearson: float
    recall_at_5: float
    projection_vectors_per_second: float
    deterministic: bool
    finite: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    numerator = sum((x - mx) * (y - my) for x, y in zip(xs, ys, strict=True))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return numerator / (dx * dy) if dx and dy else 0.0


def _top_k(vectors: list[list[float]], index: int, k: int) -> set[int]:
    scored = []
    for other in range(len(vectors)):
        if other == index:
            continue
        scored.append((cosine_similarity(vectors[index], vectors[other]), other))
    scored.sort(reverse=True)
    return {other for _, other in scored[:k]}


def run_projection_benchmark(
    *, source_dimensions: int = 1024, vectors: int = 72, seed: int = 1337
) -> ProjectionBenchmark:
    if source_dimensions < 20 or vectors < 8:
        raise ValueError("benchmark requires source_dimensions >= 20 and vectors >= 8")
    rng = random.Random(seed)
    # Clustered synthetic embeddings exercise neighbourhood preservation better than IID noise.
    cluster_count = 6
    centers = [
        [rng.gauss(0.0, 1.0) for _ in range(source_dimensions)]
        for _ in range(cluster_count)
    ]
    source: list[list[float]] = []
    for index in range(vectors):
        center = centers[index % cluster_count]
        source.append([value + rng.gauss(0.0, 0.28) for value in center])
    projector = Cos20Projector(seed="uexchanges-cos20-v1")
    started = time.perf_counter()
    projected = [projector.project(vector) for vector in source]
    elapsed = max(time.perf_counter() - started, 1e-9)
    deterministic = projector.project(source[0]) == projector.project(source[0])
    finite = all(math.isfinite(value) for vector in projected for value in vector)

    originals: list[float] = []
    sketches: list[float] = []
    pair_limit = min(600, vectors * (vectors - 1) // 2)
    pair_count = 0
    for i in range(vectors):
        for j in range(i + 1, vectors):
            originals.append(cosine_similarity(source[i], source[j]))
            sketches.append(cosine_similarity(projected[i], projected[j]))
            pair_count += 1
            if pair_count >= pair_limit:
                break
        if pair_count >= pair_limit:
            break
    mae = statistics.fmean(abs(a - b) for a, b in zip(originals, sketches, strict=True))
    recalls = []
    for index in range(min(vectors, 40)):
        native = _top_k(source, index, 5)
        sketch = _top_k(projected, index, 5)
        recalls.append(len(native & sketch) / 5.0)
    return ProjectionBenchmark(
        source_dimensions=source_dimensions,
        target_dimensions=20,
        vectors=vectors,
        pairs=pair_count,
        cosine_mae=round(mae, 6),
        cosine_pearson=round(_pearson(originals, sketches), 6),
        recall_at_5=round(statistics.fmean(recalls), 6),
        projection_vectors_per_second=round(vectors / elapsed, 2),
        deterministic=deterministic,
        finite=finite,
    )
