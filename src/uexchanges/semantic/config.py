from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


class SemanticConfigError(ValueError):
    """Raised when semantic infrastructure configuration is unsafe or invalid."""


_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def require_local_endpoint(url: str, *, allow_remote: bool = False) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise SemanticConfigError(f"invalid endpoint URL: {url!r}")
    if not allow_remote and parsed.hostname.lower() not in _LOCAL_HOSTS:
        raise SemanticConfigError(
            f"refusing non-loopback semantic endpoint {url!r}; "
            "set SEMANTIC_ALLOW_REMOTE=1 only after an explicit privacy review"
        )
    return url.rstrip("/")


@dataclass(frozen=True, slots=True)
class SemanticConfig:
    repo_root: Path
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3-embedding:0.6b"
    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_collection: str = "uexchanges_repo_semantic"
    qdrant_api_key: str | None = None
    semantic_vector_name: str = "semantic"
    cos_vector_name: str = "cos20"
    cos_dimensions: int = 20
    projection_seed: str = "uexchanges-cos20-v1"
    chunk_chars: int = 3600
    overlap_chars: int = 420
    embed_batch_size: int = 16
    upsert_batch_size: int = 64
    max_file_bytes: int = 2_000_000
    allow_remote: bool = False

    @classmethod
    def from_env(cls, repo_root: str | Path = ".") -> "SemanticConfig":
        allow_remote = _bool_env("SEMANTIC_ALLOW_REMOTE", False)
        ollama_url = require_local_endpoint(
            os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"),
            allow_remote=allow_remote,
        )
        qdrant_url = require_local_endpoint(
            os.getenv("QDRANT_URL", "http://127.0.0.1:6333"),
            allow_remote=allow_remote,
        )
        cfg = cls(
            repo_root=Path(repo_root).resolve(),
            ollama_url=ollama_url,
            ollama_model=os.getenv("OLLAMA_EMBED_MODEL", "qwen3-embedding:0.6b"),
            qdrant_url=qdrant_url,
            qdrant_collection=os.getenv("QDRANT_COLLECTION", "uexchanges_repo_semantic"),
            qdrant_api_key=os.getenv("QDRANT_API_KEY") or None,
            semantic_vector_name=os.getenv("SEMANTIC_VECTOR_NAME", "semantic"),
            cos_vector_name=os.getenv("COS_VECTOR_NAME", "cos20"),
            cos_dimensions=int(os.getenv("COS_DIMENSIONS", "20")),
            projection_seed=os.getenv("COS_PROJECTION_SEED", "uexchanges-cos20-v1"),
            chunk_chars=int(os.getenv("SEMANTIC_CHUNK_CHARS", "3600")),
            overlap_chars=int(os.getenv("SEMANTIC_CHUNK_OVERLAP_CHARS", "420")),
            embed_batch_size=int(os.getenv("SEMANTIC_EMBED_BATCH", "16")),
            upsert_batch_size=int(os.getenv("SEMANTIC_UPSERT_BATCH", "64")),
            max_file_bytes=int(os.getenv("SEMANTIC_MAX_FILE_BYTES", "2000000")),
            allow_remote=allow_remote,
        )
        cfg.validate()
        return cfg

    def validate(self) -> None:
        if self.cos_dimensions != 20:
            raise SemanticConfigError("COS Graph Engine contract is fixed at 20 dimensions")
        if self.chunk_chars < 512:
            raise SemanticConfigError("SEMANTIC_CHUNK_CHARS must be >= 512")
        if not 0 <= self.overlap_chars < self.chunk_chars:
            raise SemanticConfigError("chunk overlap must be >= 0 and smaller than chunk size")
        if self.embed_batch_size < 1 or self.upsert_batch_size < 1:
            raise SemanticConfigError("batch sizes must be positive")
        if not self.semantic_vector_name or not self.cos_vector_name:
            raise SemanticConfigError("vector names cannot be empty")
        if self.semantic_vector_name == self.cos_vector_name:
            raise SemanticConfigError("semantic and COS vectors require distinct Qdrant names")
