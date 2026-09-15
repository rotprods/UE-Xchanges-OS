#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path

from uexchanges.semantic.config import require_local_endpoint
from uexchanges.semantic.repository_navigation import (
    RepositoryChunk,
    qwen_repository_query,
    rank_bm25_paths,
    rank_dense_paths,
    reciprocal_rank_fusion,
    dense_first_reciprocal_rank_fusion,
)
from uexchanges.semantic.retrieval_gate import (
    RetrievalReleasePolicy,
    evaluate_rankings,
    file_sha256,
    load_gold_set,
)


def load_chunks(path: Path) -> list[RepositoryChunk]:
    chunks: list[RepositoryChunk] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            raw = json.loads(line)
            chunks.append(
                RepositoryChunk(
                    path=raw["path"],
                    text=raw["text"],
                    embedding=raw["embedding"],
                    chunk_id=raw.get("point_id"),
                )
            )
    return chunks


def embed_batch(url: str, model: str, texts: list[str]) -> list[list[float]]:
    body = json.dumps({"model": model, "input": texts, "keep_alive": 0}).encode()
    req = urllib.request.Request(
        url.rstrip("/") + "/api/embed",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as response:
        payload = json.load(response)
    embeddings = payload.get("embeddings")
    if not isinstance(embeddings, list) or len(embeddings) != len(texts):
        raise RuntimeError("Ollama returned unexpected embedding batch shape")
    for vector in embeddings:
        if len(vector) != 1024:
            raise RuntimeError(f"expected 1024D query embedding, got {len(vector)}")
    return embeddings


def embed_queries(url: str, model: str, texts: list[str], batch_size: int) -> list[list[float]]:
    out: list[list[float]] = []
    for start in range(0, len(texts), batch_size):
        out.extend(embed_batch(url, model, texts[start : start + batch_size]))
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gold-manifest", type=Path, required=True)
    parser.add_argument("--vectors", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    parser.add_argument("--model", default="qwen3-embedding:0.6b")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--include-per-query", action="store_true")
    args = parser.parse_args()
    args.ollama_url = require_local_endpoint(args.ollama_url, allow_remote=False)

    started = time.perf_counter()
    gold = load_gold_set(args.gold_manifest)
    chunks = load_chunks(args.vectors)
    plain_queries = [q.query for q in gold]
    instructed_queries = [qwen_repository_query(q.query) for q in gold]

    plain_embeddings = embed_queries(args.ollama_url, args.model, plain_queries, args.batch_size)
    instructed_embeddings = embed_queries(args.ollama_url, args.model, instructed_queries, args.batch_size)

    dense_plain: dict[str, list[str]] = {}
    dense_instruction: dict[str, list[str]] = {}
    lexical: dict[str, list[str]] = {}
    hybrid_unconstrained: dict[str, list[str]] = {}
    hybrid: dict[str, list[str]] = {}
    per_query: list[dict[str, object]] = []

    for q, plain_vec, instruction_vec in zip(gold, plain_embeddings, instructed_embeddings, strict=True):
        plain_rank = rank_dense_paths(plain_vec, chunks, limit=100)
        instruction_rank = rank_dense_paths(instruction_vec, chunks, limit=100)
        lexical_rank = rank_bm25_paths(q.query, chunks, limit=100)
        unconstrained = reciprocal_rank_fusion(instruction_rank, lexical_rank, limit=100)
        fused = dense_first_reciprocal_rank_fusion(
            instruction_rank, lexical_rank, preserve_dense_top=10, limit=100
        )
        dense_plain[q.query_id] = [path for path, _ in plain_rank]
        dense_instruction[q.query_id] = [path for path, _ in instruction_rank]
        lexical[q.query_id] = [path for path, _ in lexical_rank]
        hybrid_unconstrained[q.query_id] = [row.path for row in unconstrained]
        hybrid[q.query_id] = [row.path for row in fused]
        per_query.append(
            {
                "query_id": q.query_id,
                "expected_paths": list(q.expected_paths),
                "dense_plain_top10": dense_plain[q.query_id][:10],
                "dense_instruction_top10": dense_instruction[q.query_id][:10],
                "lexical_top10": lexical[q.query_id][:10],
                "hybrid_unconstrained_top10": hybrid_unconstrained[q.query_id][:10],
                "hybrid_top10": hybrid[q.query_id][:10],
            }
        )

    metrics = {
        "dense_plain": evaluate_rankings(gold, dense_plain).as_dict(),
        "dense_instruction": evaluate_rankings(gold, dense_instruction).as_dict(),
        "lexical": evaluate_rankings(gold, lexical).as_dict(),
        "hybrid_unconstrained": evaluate_rankings(gold, hybrid_unconstrained).as_dict(),
        "hybrid": evaluate_rankings(gold, hybrid).as_dict(),
    }
    gate = RetrievalReleasePolicy().evaluate(
        dense=evaluate_rankings(gold, dense_instruction),
        hybrid=evaluate_rankings(gold, hybrid),
        mutation_authority=False,
    )
    per_query_bytes = json.dumps(
        per_query, sort_keys=True, separators=(",", ":")
    ).encode()
    report = {
        "schema_version": "2.0.0",
        "benchmark_id": "UEX-REPOSITORY-NAVIGATION-BENCHMARK-V2",
        "authority": "DERIVED_BENCHMARK_ONLY",
        "mutation_authority": False,
        "historical_index_source_sha": "5bd92696e3b9d04be9eda0c2a6e5dcb929235870",
        "model": args.model,
        "embedding_dimensions": 1024,
        "gold_manifest": str(args.gold_manifest.name),
        "gold_manifest_sha256": file_sha256(args.gold_manifest),
        "vectors_sha256": file_sha256(args.vectors),
        "corpus_points": len(chunks),
        "corpus_paths": len({chunk.path for chunk in chunks}),
        "metrics": metrics,
        "release_gate": gate,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "per_query_sha256": hashlib.sha256(per_query_bytes).hexdigest(),
        "per_query_count": len(per_query),
    }
    if args.include_per_query:
        report["per_query"] = per_query
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"metrics": metrics, "release_gate": gate, "elapsed_seconds": report["elapsed_seconds"]}, indent=2, sort_keys=True))
    return 0 if gate["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
