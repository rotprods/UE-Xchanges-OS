#!/usr/bin/env python3
"""Replay frozen, checksummed real model outputs without network or model services.

This qualifies retrieval rankings, not current-main freshness or model inference
reproducibility. The real query-cache capture and its provenance remain separate
artifacts. No automatic model/provider download is attempted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
from pathlib import Path

from uexchanges.semantic.repository_navigation import (
    RepositoryChunk, qwen_repository_query, rank_bm25_paths, rank_dense_paths,
    reciprocal_rank_fusion, dense_first_reciprocal_rank_fusion,
)
from uexchanges.semantic.retrieval_gate import (
    RetrievalGateError, RetrievalReleasePolicy, evaluate_rankings, file_sha256, load_gold_set,
)

MODEL = "qwen3-embedding:0.6b"
MODEL_SHA = "06507c7b42688469c4e7298b0a1e16deff06caf291cf0a5b278c308249c3e439"
ENCODINGS = ("plain", "instruction")


def canonical_hash(value: object) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(data).hexdigest()


def validate_vector(vector: object) -> None:
    if not isinstance(vector, list) or len(vector) != 1024:
        raise RetrievalGateError("expected exactly 1024D")
    if not all(type(v) in (int, float) and math.isfinite(v) for v in vector):
        raise RetrievalGateError("embedding must be numeric and finite")
    norm2 = sum(v*v for v in vector)
    if not math.isfinite(norm2) or norm2 <= 0:
        raise RetrievalGateError("embedding must have finite non-zero norm")


def load_chunks(path: Path, *, allowed_source_shas: set[str]) -> list[RepositoryChunk]:
    chunks, seen = [], set()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            raw = json.loads(line)
            if raw.get("embedded_corpus_sha") not in allowed_source_shas:
                raise RetrievalGateError("corpus source SHA mismatch")
            point_id = raw.get("point_id")
            if not isinstance(point_id, str) or not point_id or point_id in seen:
                raise RetrievalGateError("missing or duplicate point ID")
            seen.add(point_id)
            validate_vector(raw.get("embedding"))
            if not isinstance(raw.get("text"), str):
                raise RetrievalGateError("chunk text must be a string")
            chunks.append(RepositoryChunk(raw["path"], raw["text"], raw["embedding"], point_id))
    if not chunks:
        raise RetrievalGateError("empty corpus")
    return chunks


def load_query_cache(path: Path, *, expected_sha: str, gold, gold_sha: str,
                     vectors_sha: str) -> tuple[dict, dict]:
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha) or file_sha256(path) != expected_sha:
        raise RetrievalGateError("query cache checksum mismatch")
    data = json.loads(path.read_text(encoding="utf-8"))
    expected = {"status": "COMPLETE", "authority": "DERIVED_QUERY_EMBEDDINGS_ONLY",
                "model": MODEL, "model_sha256": MODEL_SHA, "embedding_dimensions": 1024,
                "gold_manifest_sha256": gold_sha, "vectors_sha256": vectors_sha,
                "query_count": len(gold)}
    if any(data.get(k) != v for k, v in expected.items()) or data.get("mutation_authority") is not False:
        raise RetrievalGateError("query cache provenance mismatch")
    by_id = {q.query_id: q for q in gold}
    lookup = {}
    for row in data.get("rows", []):
        key = (row.get("query_id"), row.get("encoding"))
        if key in lookup or key[0] not in by_id or key[1] not in ENCODINGS:
            raise RetrievalGateError("duplicate or unknown query cache row")
        q = by_id[key[0]]
        expected_text = q.query if key[1] == "plain" else qwen_repository_query(q.query)
        if row.get("encoded_text") != expected_text or row.get("language") != q.language:
            raise RetrievalGateError("query cache text/language mismatch")
        validate_vector(row.get("embedding"))
        lookup[key] = row["embedding"]
    if set(lookup) != {(q.query_id, e) for q in gold for e in ENCODINGS}:
        raise RetrievalGateError("query cache incomplete")
    return data, lookup


def run_benchmark(*, gold_manifest: Path, vectors: Path, query_cache: Path,
                  expected_query_cache_sha256: str, source_sha: str, corpus_manifest: Path,
                  expected_corpus_manifest_sha256: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise RetrievalGateError("source SHA must be exact")
    started = time.perf_counter()
    gold = load_gold_set(gold_manifest)
    gold_sha, vectors_sha = file_sha256(gold_manifest), file_sha256(vectors)
    if file_sha256(corpus_manifest) != expected_corpus_manifest_sha256:
        raise RetrievalGateError("corpus manifest checksum mismatch")
    manifest = json.loads(corpus_manifest.read_text(encoding="utf-8"))
    if (manifest.get("source_commit") != source_sha or manifest.get("vectors_sha256") != vectors_sha
        or manifest.get("model_blob_sha256") != MODEL_SHA
        or manifest.get("authority") != "DERIVED_RECONSTRUCTIBLE_ONLY"
        or manifest.get("dimensions", {}).get("semantic") != 1024):
        raise RetrievalGateError("corpus manifest provenance mismatch")
    allowed = manifest.get("allowed_embedding_source_commits")
    if not isinstance(allowed, list) or not allowed or any(not isinstance(v, str) or not re.fullmatch(r"[0-9a-f]{40}", v) for v in allowed):
        raise RetrievalGateError("invalid embedding lineage allowlist")
    chunks = load_chunks(vectors, allowed_source_shas=set(allowed))
    if len(chunks) != manifest.get("points"):
        raise RetrievalGateError("corpus manifest point count mismatch")
    paths = {c.path for c in chunks}
    if any(not set(q.expected_paths).issubset(paths) for q in gold):
        raise RetrievalGateError("gold expected path missing from corpus")
    cache, embeddings = load_query_cache(query_cache, expected_sha=expected_query_cache_sha256,
                                         gold=gold, gold_sha=gold_sha, vectors_sha=vectors_sha)
    names = ("dense_plain", "dense_instruction", "lexical", "hybrid_rrf", "dense_protected")
    rankings = {name: {} for name in names}
    per_query, latency = [], []
    for q in gold:
        begin = time.perf_counter()
        plain = rank_dense_paths(embeddings[(q.query_id, "plain")], chunks, limit=100)
        dense = rank_dense_paths(embeddings[(q.query_id, "instruction")], chunks, limit=100)
        lexical = rank_bm25_paths(q.query, chunks, limit=100)
        hybrid = reciprocal_rank_fusion(dense, lexical, limit=100)
        protected = dense_first_reciprocal_rank_fusion(dense, lexical, preserve_dense_top=10, limit=100)
        for name, result in zip(names, (plain, dense, lexical, hybrid, protected), strict=True):
            rankings[name][q.query_id] = [r[0] if isinstance(r, tuple) else r.path for r in result]
        latency.append(time.perf_counter()-begin)
        per_query.append({"query_id": q.query_id, "language": q.language,
                          "expected_paths": list(q.expected_paths),
                          "rankings": {n: rankings[n][q.query_id] for n in names}})
    measured = {n: evaluate_rankings(gold, rankings[n]) for n in names}
    gate = RetrievalReleasePolicy().evaluate(dense=measured["dense_instruction"],
                                            hybrid=measured["hybrid_rrf"], mutation_authority=False)
    equivalent = sum(rankings["dense_instruction"][q.query_id][:10] ==
                     rankings["dense_protected"][q.query_id][:10] for q in gold)
    result = {
        "schema_version": "3.0.0", "benchmark_id": "UEX-RETR03-FROZEN-REPLAY",
        "authority": "DERIVED_BENCHMARK_ONLY", "mutation_authority": False,
        "historical_index_source_sha": source_sha, "freshness": "HISTORICAL_ONLY",
        "allowed_embedding_source_commits": allowed, "corpus_manifest_sha256": expected_corpus_manifest_sha256,
        "model": MODEL, "model_sha256": MODEL_SHA, "ollama_capture_version": cache.get("ollama_version"),
        "embedding_dimensions": 1024, "corpus_points": len(chunks), "corpus_paths": len(paths),
        "gold_manifest_sha256": gold_sha, "vectors_sha256": vectors_sha,
        "query_cache_sha256": expected_query_cache_sha256,
        "implementation_sha256": {str(p.relative_to(Path(__file__).resolve().parents[1])): file_sha256(p)
             for p in [Path(__file__).resolve(), *sorted((Path(__file__).resolve().parents[1]/"src/uexchanges/semantic").glob("*.py"))]},
        "metrics": {n: m.as_dict() for n, m in measured.items()},
        "metric_definitions": {"recall_at_k": "query-level hit rate; equals recall for frozen singleton labels",
                               "mrr": "mean reciprocal rank truncated at 10", "ndcg_at_10": "binary expected-path relevance"},
        "paired_query_caveat": "60 queries = 30 paired EN/ES intents, not 60 independent topics; no held-out tuning claim",
        "gate_surface": "hybrid_rrf", "release_gate": gate,
        "dense_protected_top10_equal_count": equivalent,
        "selected_default": "dense_protected", "hybrid_promotion": "ELIGIBLE_FOR_FURTHER_REVIEW" if gate["pass"] else "BLOCKED_REGRESSION",
        "rankings_sha256": canonical_hash(per_query), "per_query": per_query,
        "execution": {"mode": "FROZEN_REAL_EMBEDDINGS_REPLAY", "network_used": False,
                      "model_inference_executed_in_replay": False,
                      "elapsed_seconds": time.perf_counter()-started,
                      "ranking_all_five_surfaces_seconds": latency,
                      "latency_semantics": "offline full five-surface ranking cost per query; not model inference or end-user latency"},
    }
    return result


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ("gold-manifest", "vectors", "query-cache", "corpus-manifest", "output"):
        p.add_argument("--"+flag, type=Path, required=True)
    p.add_argument("--expected-query-cache-sha256", required=True)
    p.add_argument("--source-sha", required=True)
    p.add_argument("--expected-corpus-manifest-sha256", required=True)
    a = p.parse_args()
    try:
        report = run_benchmark(gold_manifest=a.gold_manifest, vectors=a.vectors, query_cache=a.query_cache,
                               expected_query_cache_sha256=a.expected_query_cache_sha256, source_sha=a.source_sha,
                               corpus_manifest=a.corpus_manifest, expected_corpus_manifest_sha256=a.expected_corpus_manifest_sha256)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        p.exit(3, f"FAIL_CLOSED: {type(exc).__name__}: {exc}\n")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"rankings_sha256": report["rankings_sha256"], "release_gate": report["release_gate"],
                      "metrics": report["metrics"]}, indent=2, sort_keys=True))
    return 0 if report["release_gate"]["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
