from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


class RetrievalGateError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class GoldQuery:
    query_id: str
    query: str
    language: str
    intent: str
    expected_paths: tuple[str, ...]
    acceptable_related_paths: tuple[str, ...] = ()
    strict: bool = True
    notes: str = ""


@dataclass(frozen=True, slots=True)
class RetrievalMetrics:
    query_count: int
    recall_at_5: float
    recall_at_10: float
    mrr: float
    ndcg_at_10: float

    def as_dict(self) -> dict[str, float | int]:
        return {
            "query_count": self.query_count,
            "recall_at_5": self.recall_at_5,
            "recall_at_10": self.recall_at_10,
            "mrr": self.mrr,
            "ndcg_at_10": self.ndcg_at_10,
        }


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_gold_set(manifest_path: str | Path) -> list[GoldQuery]:
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "2.0.0":
        raise RetrievalGateError("unsupported gold manifest schema")
    if manifest.get("authority") != "DERIVED_BENCHMARK_FIXTURE_ONLY":
        raise RetrievalGateError("gold fixture cannot claim domain authority")
    queries: list[GoldQuery] = []
    seen: set[str] = set()
    base = manifest_path.parent.resolve()
    for shard in manifest.get("shards", []):
        relative = str(shard["path"])
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise RetrievalGateError(f"unsafe gold shard path: {relative}")
        path = (base / relative_path).resolve()
        try:
            path.relative_to(base)
        except ValueError as exc:
            raise RetrievalGateError(f"unsafe gold shard path: {relative}") from exc
        expected_sha = shard["sha256"]
        actual_sha = file_sha256(path)
        if actual_sha != expected_sha:
            raise RetrievalGateError(f"gold shard checksum mismatch: {relative}")
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise RetrievalGateError("gold shard must contain a list")
        for raw in data:
            q = GoldQuery(
                query_id=str(raw["query_id"]),
                query=str(raw["query"]),
                language=str(raw["language"]),
                intent=str(raw["intent"]),
                expected_paths=tuple(raw["expected_paths"]),
                acceptable_related_paths=tuple(raw.get("acceptable_related_paths", [])),
                strict=bool(raw.get("strict", True)),
                notes=str(raw.get("notes", "")),
            )
            if q.query_id in seen:
                raise RetrievalGateError(f"duplicate query id {q.query_id}")
            if q.language not in {"en", "es"} or not q.query.strip() or not q.expected_paths:
                raise RetrievalGateError(f"invalid gold query {q.query_id}")
            seen.add(q.query_id)
            queries.append(q)
    if len(queries) != manifest.get("query_count"):
        raise RetrievalGateError("gold manifest query_count mismatch")
    if len(queries) < 50:
        raise RetrievalGateError("release gold set must contain at least 50 queries")
    if {q.language for q in queries} != {"en", "es"}:
        raise RetrievalGateError("release gold set must be bilingual EN/ES")
    return queries


def evaluate_rankings(
    gold: Sequence[GoldQuery], rankings: Mapping[str, Sequence[str]]
) -> RetrievalMetrics:
    if not gold:
        raise RetrievalGateError("gold set cannot be empty")
    # Legacy recall fields are query-level hit rates; MRR is truncated at 10.
    # For the frozen singleton-label Gold V2 these hit rates equal Recall@k.
    hits5 = 0
    hits10 = 0
    reciprocal = 0.0
    ndcg = 0.0
    for q in gold:
        ranked = list(dict.fromkeys(rankings.get(q.query_id, ())))
        expected = set(q.expected_paths)
        first_rank: int | None = None
        dcg = 0.0
        for rank, path in enumerate(ranked[:10], 1):
            if path in expected:
                if first_rank is None:
                    first_rank = rank
                dcg += 1.0 / math.log2(rank + 1)
        if any(path in expected for path in ranked[:5]):
            hits5 += 1
        if any(path in expected for path in ranked[:10]):
            hits10 += 1
        if first_rank is not None:
            reciprocal += 1.0 / first_rank
        ideal_hits = min(len(expected), 10)
        idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
        if idcg:
            ndcg += dcg / idcg
    n = len(gold)
    return RetrievalMetrics(n, hits5 / n, hits10 / n, reciprocal / n, ndcg / n)


@dataclass(frozen=True, slots=True)
class RetrievalReleasePolicy:
    min_queries: int = 50
    min_hybrid_recall_at_10: float = 0.70
    min_hybrid_mrr: float = 0.40
    min_hybrid_ndcg_at_10: float = 0.40
    max_recall10_regression_vs_dense: float = 0.02

    def evaluate(
        self, *, dense: RetrievalMetrics, hybrid: RetrievalMetrics, mutation_authority: bool
    ) -> dict[str, Any]:
        def valid(m: RetrievalMetrics) -> bool:
            return (type(m.query_count) is int and m.query_count > 0
                    and all(type(v) in (int, float) and math.isfinite(v) and 0 <= v <= 1
                            for v in (m.recall_at_5, m.recall_at_10, m.mrr, m.ndcg_at_10))
                    and m.recall_at_5 <= m.recall_at_10)

        checks = {
            "finite_metric_ranges": valid(dense) and valid(hybrid),
            "same_query_count": dense.query_count == hybrid.query_count,
            "query_count": hybrid.query_count >= self.min_queries,
            "hybrid_recall_at_10": hybrid.recall_at_10 >= self.min_hybrid_recall_at_10,
            "hybrid_mrr": hybrid.mrr >= self.min_hybrid_mrr,
            "hybrid_ndcg_at_10": hybrid.ndcg_at_10 >= self.min_hybrid_ndcg_at_10,
            "recall10_non_regression": hybrid.recall_at_10
            >= dense.recall_at_10 - self.max_recall10_regression_vs_dense,
            "mutation_authority_false": mutation_authority is False,
        }
        return {
            "pass": all(checks.values()),
            "checks": checks,
            "policy": {
                "min_queries": self.min_queries,
                "min_hybrid_recall_at_10": self.min_hybrid_recall_at_10,
                "min_hybrid_mrr": self.min_hybrid_mrr,
                "min_hybrid_ndcg_at_10": self.min_hybrid_ndcg_at_10,
                "max_recall10_regression_vs_dense": self.max_recall10_regression_vs_dense,
            },
        }
