from __future__ import annotations

import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .chunking import RepoChunk, scan_repository
from .config import SemanticConfig
from .cos20 import Cos20Projector
from .ollama import OllamaEmbedder
from .qdrant import QdrantRESTClient


@dataclass(frozen=True, slots=True)
class IndexReport:
    repo: str
    commit: str
    chunks: int
    semantic_dimensions: int
    cos_dimensions: int
    files_indexed: int
    tracked_candidates: int
    skipped_binary: int
    skipped_secret: int
    skipped_large: int
    skipped_decode: int
    elapsed_seconds: float
    chunks_per_second: float
    collection: str
    embedding_model: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _git_value(repo_root: Path, *args: str, default: str) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        value = proc.stdout.strip()
        return value if proc.returncode == 0 and value else default
    except (OSError, subprocess.SubprocessError):
        return default


def _repo_identity(repo_root: Path) -> tuple[str, str]:
    commit = _git_value(repo_root, "rev-parse", "HEAD", default="UNVERSIONED")
    remote = _git_value(repo_root, "config", "--get", "remote.origin.url", default="")
    if remote:
        normalized = remote.removesuffix(".git").rstrip("/")
        if ":" in normalized and "://" not in normalized:
            normalized = normalized.split(":", 1)[1]
        parts = [part for part in normalized.split("/") if part]
        repo_id = "/".join(parts[-2:]) if len(parts) >= 2 else parts[-1]
    else:
        repo_id = repo_root.name
    return repo_id, commit


class SemanticIndexer:
    def __init__(
        self,
        config: SemanticConfig,
        *,
        embedder: OllamaEmbedder | None = None,
        qdrant: QdrantRESTClient | None = None,
    ) -> None:
        self.config = config
        self.embedder = embedder or OllamaEmbedder(config.ollama_url, config.ollama_model)
        self.qdrant = qdrant or QdrantRESTClient(
            config.qdrant_url,
            config.qdrant_collection,
            api_key=config.qdrant_api_key,
        )
        self.projector = Cos20Projector(seed=config.projection_seed)

    def _point(
        self,
        chunk: RepoChunk,
        semantic: list[float],
        *,
        repo_id: str,
        commit: str,
        indexed_at: str,
        index_build_id: str,
    ) -> dict[str, Any]:
        cos20 = self.projector.project(semantic)
        payload = chunk.payload()
        payload.update(
            {
                "repo": repo_id,
                "indexed_commit": commit,
                "indexed_at": indexed_at,
                "index_build_id": index_build_id,
                "embedding_model": self.config.ollama_model,
                "embedding_dimensions": len(semantic),
                "cos_dimensions": 20,
                "projection_seed": self.config.projection_seed,
                "projection_authority": "DERIVED_RECONSTRUCTIBLE_ONLY",
            }
        )
        return {
            "id": chunk.point_id,
            "vector": {
                self.config.semantic_vector_name: semantic,
                self.config.cos_vector_name: cos20,
            },
            "payload": payload,
        }

    def sync(self, *, recreate: bool = False, clear_repo: bool = True) -> IndexReport:
        start = time.perf_counter()
        chunks, stats = scan_repository(
            self.config.repo_root,
            target_chars=self.config.chunk_chars,
            overlap_chars=self.config.overlap_chars,
            max_file_bytes=self.config.max_file_bytes,
        )
        if not chunks:
            raise RuntimeError("repository scan produced zero indexable chunks")
        repo_id, commit = _repo_identity(self.config.repo_root)
        indexed_at = datetime.now(timezone.utc).isoformat()
        index_build_id = f"{repo_id}:{commit}:{indexed_at}"
        first_batch = chunks[: self.config.embed_batch_size]
        first_vectors = self.embedder.embed([chunk.text for chunk in first_batch])
        semantic_dimensions = len(first_vectors[0])
        self.qdrant.ensure_collection(
            semantic_dimensions,
            semantic_name=self.config.semantic_vector_name,
            cos_name=self.config.cos_vector_name,
            recreate=recreate,
        )
        pending_points: list[dict[str, Any]] = []

        def flush() -> None:
            nonlocal pending_points
            if pending_points:
                self.qdrant.upsert(pending_points)
                pending_points = []

        def append_batch(batch_chunks: list[RepoChunk], vectors: list[list[float]]) -> None:
            for chunk, vector in zip(batch_chunks, vectors, strict=True):
                if len(vector) != semantic_dimensions:
                    raise RuntimeError("embedding dimension changed during one index build")
                pending_points.append(
                    self._point(
                        chunk,
                        vector,
                        repo_id=repo_id,
                        commit=commit,
                        indexed_at=indexed_at,
                        index_build_id=index_build_id,
                    )
                )
                if len(pending_points) >= self.config.upsert_batch_size:
                    flush()

        append_batch(first_batch, first_vectors)
        for offset in range(len(first_batch), len(chunks), self.config.embed_batch_size):
            batch = chunks[offset : offset + self.config.embed_batch_size]
            vectors = self.embedder.embed([chunk.text for chunk in batch])
            append_batch(batch, vectors)
        flush()
        if clear_repo:
            self.qdrant.delete_stale_repo_points(repo_id, index_build_id)
        elapsed = max(time.perf_counter() - start, 1e-9)
        return IndexReport(
            repo=repo_id,
            commit=commit,
            chunks=len(chunks),
            semantic_dimensions=semantic_dimensions,
            cos_dimensions=20,
            files_indexed=stats.indexed_files,
            tracked_candidates=stats.tracked_candidates,
            skipped_binary=stats.skipped_binary,
            skipped_secret=stats.skipped_secret,
            skipped_large=stats.skipped_large,
            skipped_decode=stats.skipped_decode,
            elapsed_seconds=round(elapsed, 6),
            chunks_per_second=round(len(chunks) / elapsed, 3),
            collection=self.config.qdrant_collection,
            embedding_model=self.config.ollama_model,
        )
