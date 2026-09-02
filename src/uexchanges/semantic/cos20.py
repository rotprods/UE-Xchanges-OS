from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence

COS_DIMENSIONS = 20


def l2_normalize(vector: Sequence[float]) -> list[float]:
    norm_sq = sum(float(value) * float(value) for value in vector)
    if not math.isfinite(norm_sq) or norm_sq <= 0.0:
        raise ValueError("vector must contain finite non-zero values")
    inv_norm = 1.0 / math.sqrt(norm_sq)
    return [float(value) * inv_norm for value in vector]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("cosine vectors must have the same non-zero length")
    an = l2_normalize(a)
    bn = l2_normalize(b)
    return sum(x * y for x, y in zip(an, bn, strict=True))


class Cos20Projector:
    """Deterministic signed-hash projection from dense embeddings to 20D.

    The 20D representation is a reconstructible topology/search diagnostic vector.
    It is intentionally not the authoritative semantic-retrieval vector.
    """

    def __init__(self, *, seed: str = "uexchanges-cos20-v1") -> None:
        if not seed:
            raise ValueError("projection seed cannot be empty")
        self.seed = seed
        self.dimensions = COS_DIMENSIONS

    def _bucket_and_sign(self, source_index: int) -> tuple[int, float]:
        digest = hashlib.blake2b(
            f"{self.seed}:{source_index}".encode("utf-8"), digest_size=8
        ).digest()
        raw = int.from_bytes(digest, "big", signed=False)
        bucket = raw % self.dimensions
        sign = 1.0 if (raw >> 8) & 1 else -1.0
        return bucket, sign

    def project(self, vector: Sequence[float]) -> list[float]:
        if not vector:
            raise ValueError("cannot project an empty vector")
        source = l2_normalize(vector)
        out = [0.0] * self.dimensions
        for index, value in enumerate(source):
            bucket, sign = self._bucket_and_sign(index)
            out[bucket] += sign * value
        return l2_normalize(out)
