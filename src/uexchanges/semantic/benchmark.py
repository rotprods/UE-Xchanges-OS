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


@dataclass(frozen=True, slots=True)
class LatencySummary:
    samples: int
    mean_ms: float
    p50_ms: float
    p95_ms: float
    min_ms: float
    max_ms: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _percentile(values: list[float], quantile: float) -> float:
    if not values:
        raise ValueError("percentile requires at least one sample")
    if not 0.0 <= quantile <= 1.0:
        raise ValueError("quantile must be between 0 and 1")
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def summarize_latencies(seconds: list[float]) -> LatencySummary:
    if not seconds:
        raise ValueError("latency summary requires at least one sample")
    milliseconds = [value * 1000.0 for value in seconds]
    return LatencySummary(
        samples=len(milliseconds),
        mean_ms=round(statistics.fmean(milliseconds), 3),
        p50_ms=round(_percentile(milliseconds, 0.50), 3),
        p95_ms=round(_percentile(milliseconds, 0.95), 3),
        min_ms=round(min(milliseconds), 3),
        max_ms=round(max(milliseconds), 3),
    )


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


def _hit_ids(hits: list[dict[str, Any]], limit: int = 5) -> set[str]:
    return {str(hit.get("id")) for hit in hits[:limit] if hit.get("id") is not None}


def _hit_paths(hits: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for hit in hits[:limit]:
        payload = hit.get("payload") or {}
        out.append(
            {
                "path": payload.get("path") if isinstance(payload, dict) else None,
                "line_start": payload.get("line_start") if isinstance(payload, dict) else None,
                "score": round(float(hit.get("score", 0.0)), 6),
            }
        )
    return out


def run_live_retrieval_benchmark(
    *,
    embedder: Any,
    qdrant: Any,
    repo_id: str,
    semantic_vector_name: str,
    cos_vector_name: str,
    projection_seed: str,
    iterations: int = 8,
) -> dict[str, Any]:
    """Measure real local embedding + Qdrant retrieval latency after a completed index sync.

    This reports service performance and native-vs-COS neighbour overlap. It does not
    treat COS overlap as ground-truth relevance and never mutates repository/domain state.
    """
    if iterations < 3:
        raise ValueError("live benchmark requires at least 3 iterations")
    probes = [
        "multi-agent lease fencing and idempotency",
        "submission receipt authority and human frontier",
        "RuntimeGraph dead letters and source cursors",
        "graph operating protocol and evidence hierarchy",
    ]
    filter_ = {"must": [{"key": "repo", "match": {"value": repo_id}}]}
    projector = Cos20Projector(seed=projection_seed)

    # Warm both the model and Qdrant path; warmup is deliberately excluded from latency stats.
    warm = embedder.embed([probes[0]])[0]
    qdrant.query(warm, using=semantic_vector_name, limit=5, filter_=filter_)
    qdrant.query(projector.project(warm), using=cos_vector_name, limit=5, filter_=filter_)

    embed_latencies: list[float] = []
    semantic_latencies: list[float] = []
    cos_latencies: list[float] = []
    overlaps: list[float] = []
    probe_hits: dict[str, dict[str, list[dict[str, Any]]]] = {}
    embedding_dimensions: int | None = None

    for index in range(iterations):
        query = probes[index % len(probes)]
        started = time.perf_counter()
        semantic_vector = embedder.embed([query])[0]
        embed_latencies.append(max(time.perf_counter() - started, 0.0))
        embedding_dimensions = embedding_dimensions or len(semantic_vector)
        if len(semantic_vector) != embedding_dimensions:
            raise RuntimeError("embedding dimension changed during live benchmark")

        started = time.perf_counter()
        semantic_hits = qdrant.query(
            semantic_vector,
            using=semantic_vector_name,
            limit=5,
            filter_=filter_,
        )
        semantic_latencies.append(max(time.perf_counter() - started, 0.0))

        cos_vector = projector.project(semantic_vector)
        started = time.perf_counter()
        cos_hits = qdrant.query(
            cos_vector,
            using=cos_vector_name,
            limit=5,
            filter_=filter_,
        )
        cos_latencies.append(max(time.perf_counter() - started, 0.0))

        native_ids = _hit_ids(semantic_hits)
        cos_ids = _hit_ids(cos_hits)
        overlaps.append(len(native_ids & cos_ids) / max(len(native_ids), 1))
        if query not in probe_hits:
            probe_hits[query] = {
                "semantic_top3": _hit_paths(semantic_hits),
                "cos20_top3": _hit_paths(cos_hits),
            }

    return {
        "repo": repo_id,
        "iterations": iterations,
        "embedding_dimensions": embedding_dimensions,
        "embedding_latency": summarize_latencies(embed_latencies).to_dict(),
        "semantic_query_latency": summarize_latencies(semantic_latencies).to_dict(),
        "cos20_query_latency": summarize_latencies(cos_latencies).to_dict(),
        "semantic_queries_per_second_at_mean_latency": round(1.0 / statistics.fmean(semantic_latencies), 3),
        "cos20_queries_per_second_at_mean_latency": round(1.0 / statistics.fmean(cos_latencies), 3),
        "semantic_cos20_overlap_at_5": round(statistics.fmean(overlaps), 6),
        "overlap_semantics": "DIAGNOSTIC_ONLY_NOT_RELEVANCE_GROUND_TRUTH",
        "probe_hits": probe_hits,
    }
