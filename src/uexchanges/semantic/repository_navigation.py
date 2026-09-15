from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Sequence

_TOKEN_RE = re.compile(r"[\w./:+-]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    """Tokenize repository text deterministically without external NLP deps."""
    return [t.lower() for t in _TOKEN_RE.findall(text) if len(t) > 1]


@dataclass(frozen=True, slots=True)
class RepositoryChunk:
    path: str
    text: str
    embedding: Sequence[float] | None = None
    chunk_id: str | None = None

    def __post_init__(self) -> None:
        parsed = PurePosixPath(self.path)
        if (
            not self.path
            or self.path.startswith("/")
            or "\\" in self.path
            or any(part == ".." for part in parsed.parts)
        ):
            raise ValueError("repository path must be a safe relative POSIX path")


@dataclass(frozen=True, slots=True)
class NavigationResult:
    path: str
    score: float
    dense_rank: int | None
    lexical_rank: int | None
    sources: tuple[str, ...]
    mutation_authority: bool = False


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("vectors must have the same non-zero dimensionality")
    dot = 0.0
    aa = 0.0
    bb = 0.0
    for av, bv in zip(a, b, strict=True):
        af = float(av)
        bf = float(bv)
        if not math.isfinite(af) or not math.isfinite(bf):
            raise ValueError("vectors must contain only finite values")
        dot += af * bf
        aa += af * af
        bb += bf * bf
    if aa <= 0.0 or bb <= 0.0:
        raise ValueError("vectors must be non-zero")
    return dot / math.sqrt(aa * bb)


def rank_dense_paths(
    query_embedding: Sequence[float], chunks: Sequence[RepositoryChunk], *, limit: int | None = None
) -> list[tuple[str, float]]:
    """Rank paths by the best chunk cosine score; path dedup is mandatory."""
    best: dict[str, float] = {}
    expected_dim = len(query_embedding)
    if expected_dim == 0:
        raise ValueError("query embedding cannot be empty")
    for chunk in chunks:
        if chunk.embedding is None:
            continue
        if len(chunk.embedding) != expected_dim:
            raise ValueError(
                f"embedding dimension mismatch for {chunk.path}: "
                f"{len(chunk.embedding)} != {expected_dim}"
            )
        score = cosine_similarity(query_embedding, chunk.embedding)
        if score > best.get(chunk.path, float("-inf")):
            best[chunk.path] = score
    ranked = sorted(best.items(), key=lambda item: (-item[1], item[0]))
    return ranked if limit is None else ranked[:limit]


def rank_bm25_paths(
    query: str,
    chunks: Sequence[RepositoryChunk],
    *,
    k1: float = 1.5,
    b: float = 0.75,
    limit: int | None = None,
) -> list[tuple[str, float]]:
    """Deterministic chunk BM25 followed by max-score path dedup."""
    if k1 <= 0 or not 0 <= b <= 1:
        raise ValueError("invalid BM25 parameters")
    q_terms = tokenize(query)
    if not q_terms:
        return []
    tokenized = [tokenize(chunk.text) for chunk in chunks]
    n_docs = len(tokenized)
    if n_docs == 0:
        return []
    avgdl = sum(len(tokens) for tokens in tokenized) / n_docs or 1.0
    df: Counter[str] = Counter()
    q_unique = set(q_terms)
    for tokens in tokenized:
        present = set(tokens)
        for term in q_unique & present:
            df[term] += 1
    best: dict[str, float] = {}
    qtf = Counter(q_terms)
    for chunk, tokens in zip(chunks, tokenized, strict=True):
        if not tokens:
            continue
        tf = Counter(tokens)
        dl = len(tokens)
        score = 0.0
        for term, q_count in qtf.items():
            freq = tf.get(term, 0)
            if not freq:
                continue
            idf = math.log(1.0 + (n_docs - df.get(term, 0) + 0.5) / (df.get(term, 0) + 0.5))
            denom = freq + k1 * (1.0 - b + b * dl / avgdl)
            score += q_count * idf * (freq * (k1 + 1.0) / denom)
        if score > 0.0 and score > best.get(chunk.path, 0.0):
            best[chunk.path] = score
    ranked = sorted(best.items(), key=lambda item: (-item[1], item[0]))
    return ranked if limit is None else ranked[:limit]


def reciprocal_rank_fusion(
    dense_ranking: Sequence[tuple[str, float]],
    lexical_ranking: Sequence[tuple[str, float]],
    *,
    dense_weight: float = 0.62,
    lexical_weight: float = 0.38,
    rrf_k: int = 60,
    limit: int = 10,
) -> list[NavigationResult]:
    """Fuse independent rankings without pretending their raw scores are calibrated."""
    if dense_weight < 0 or lexical_weight < 0 or dense_weight + lexical_weight <= 0:
        raise ValueError("fusion weights must be non-negative and not both zero")
    if rrf_k < 1 or limit < 1:
        raise ValueError("rrf_k and limit must be positive")

    dense_rank: dict[str, int] = {}
    lexical_rank: dict[str, int] = {}
    for rank, (path, _score) in enumerate(dense_ranking, 1):
        dense_rank.setdefault(path, rank)
    for rank, (path, _score) in enumerate(lexical_ranking, 1):
        lexical_rank.setdefault(path, rank)

    paths = set(dense_rank) | set(lexical_rank)
    results: list[NavigationResult] = []
    for path in paths:
        dr = dense_rank.get(path)
        lr = lexical_rank.get(path)
        score = 0.0
        sources: list[str] = []
        if dr is not None:
            score += dense_weight / (rrf_k + dr)
            sources.append("dense")
        if lr is not None:
            score += lexical_weight / (rrf_k + lr)
            sources.append("lexical")
        results.append(
            NavigationResult(
                path=path,
                score=score,
                dense_rank=dr,
                lexical_rank=lr,
                sources=tuple(sources),
                mutation_authority=False,
            )
        )
    results.sort(key=lambda item: (-item.score, item.path))
    return results[:limit]


def dense_first_reciprocal_rank_fusion(
    dense_ranking: Sequence[tuple[str, float]],
    lexical_ranking: Sequence[tuple[str, float]],
    *,
    preserve_dense_top: int = 10,
    dense_weight: float = 0.62,
    lexical_weight: float = 0.38,
    rrf_k: int = 60,
    limit: int = 10,
) -> list[NavigationResult]:
    """Fuse lexical evidence without allowing it to evict trusted dense top-k paths."""
    if preserve_dense_top < 0 or limit < 1:
        raise ValueError("preserve_dense_top must be >= 0 and limit positive")
    if dense_weight < 0 or lexical_weight < 0 or dense_weight + lexical_weight <= 0:
        raise ValueError("fusion weights must be non-negative and not both zero")
    if rrf_k < 1:
        raise ValueError("rrf_k must be positive")

    dense_rank: dict[str, int] = {}
    lexical_rank: dict[str, int] = {}
    dense_order: list[str] = []
    for rank, (path, _score) in enumerate(dense_ranking, 1):
        if path not in dense_rank:
            dense_rank[path] = rank
            dense_order.append(path)
    for rank, (path, _score) in enumerate(lexical_ranking, 1):
        lexical_rank.setdefault(path, rank)

    protected = dense_order[: min(preserve_dense_top, limit)]
    results: list[NavigationResult] = []
    for path in protected:
        dr = dense_rank[path]
        lr = lexical_rank.get(path)
        score = dense_weight / (rrf_k + dr)
        sources = ["dense"]
        if lr is not None:
            score += lexical_weight / (rrf_k + lr)
            sources.append("lexical")
        results.append(NavigationResult(path, score, dr, lr, tuple(sources), False))

    if len(results) >= limit:
        return results[:limit]

    protected_set = set(protected)
    tail: list[NavigationResult] = []
    for path in (set(dense_rank) | set(lexical_rank)) - protected_set:
        dr = dense_rank.get(path)
        lr = lexical_rank.get(path)
        score = 0.0
        sources: list[str] = []
        if dr is not None:
            score += dense_weight / (rrf_k + dr)
            sources.append("dense")
        if lr is not None:
            score += lexical_weight / (rrf_k + lr)
            sources.append("lexical")
        tail.append(NavigationResult(path, score, dr, lr, tuple(sources), False))
    tail.sort(key=lambda item: (-item.score, item.path))
    results.extend(tail[: limit - len(results)])
    return results


def repository_navigation(
    query: str,
    query_embedding: Sequence[float],
    chunks: Sequence[RepositoryChunk],
    *,
    dense_limit: int = 100,
    lexical_limit: int = 100,
    result_limit: int = 10,
) -> list[NavigationResult]:
    dense = rank_dense_paths(query_embedding, chunks, limit=dense_limit)
    lexical = rank_bm25_paths(query, chunks, limit=lexical_limit)
    return dense_first_reciprocal_rank_fusion(
        dense, lexical, preserve_dense_top=min(10, result_limit), limit=result_limit
    )


def qwen_repository_query(query: str) -> str:
    clean = " ".join(query.split())
    if not clean:
        raise ValueError("query cannot be blank")
    return (
        "Instruct: Retrieve the repository files that best answer the engineering question. "
        "Prefer exact implementation, contract, schema, test, or runbook files over merely related prose.\n"
        f"Query: {clean}"
    )
