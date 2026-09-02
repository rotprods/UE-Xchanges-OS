from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .config import SemanticConfig
from .qdrant import QdrantRESTClient


@dataclass(frozen=True, slots=True)
class SemanticNode:
    id: str
    path: str
    line_start: int | None
    line_end: int | None
    chunk_index: int | None


class CosGraphEngine:
    """Build a 20D semantic-neighbour graph from the reconstructible Qdrant projection."""

    def __init__(self, config: SemanticConfig, qdrant: QdrantRESTClient | None = None) -> None:
        self.config = config
        self.qdrant = qdrant or QdrantRESTClient(
            config.qdrant_url,
            config.qdrant_collection,
            api_key=config.qdrant_api_key,
        )

    def build(
        self,
        *,
        repo_id: str | None = None,
        top_k: int = 6,
        min_score: float = 0.72,
        max_nodes: int = 5000,
        query_batch_size: int = 64,
    ) -> dict[str, Any]:
        if top_k < 1 or query_batch_size < 1:
            raise ValueError("top_k and query_batch_size must be positive")
        filter_ = None
        if repo_id:
            filter_ = {"must": [{"key": "repo", "match": {"value": repo_id}}]}
        points = self.qdrant.scroll(
            filter_=filter_,
            vector_names=[self.config.cos_vector_name],
            max_points=max_nodes,
        )
        nodes: list[dict[str, Any]] = []
        vectors: list[list[float]] = []
        point_ids: list[str] = []
        for point in points:
            vector_map = point.get("vector", {})
            vector = vector_map.get(self.config.cos_vector_name) if isinstance(vector_map, dict) else None
            if not isinstance(vector, list) or len(vector) != 20:
                continue
            payload = point.get("payload", {}) or {}
            point_id = str(point.get("id"))
            point_ids.append(point_id)
            vectors.append([float(value) for value in vector])
            nodes.append(
                {
                    "id": point_id,
                    "type": "SEMANTIC_CHUNK",
                    "path": payload.get("path"),
                    "line_start": payload.get("line_start"),
                    "line_end": payload.get("line_end"),
                    "chunk_index": payload.get("chunk_index"),
                }
            )
        edges: dict[tuple[str, str], dict[str, Any]] = {}
        for offset in range(0, len(vectors), query_batch_size):
            batch_vectors = vectors[offset : offset + query_batch_size]
            searches = []
            for vector in batch_vectors:
                search: dict[str, Any] = {
                    "query": vector,
                    "using": self.config.cos_vector_name,
                    "limit": top_k + 1,
                    "score_threshold": min_score,
                    "with_payload": False,
                    "with_vector": False,
                }
                if filter_ is not None:
                    search["filter"] = filter_
                searches.append(search)
            results = self.qdrant.query_batch(searches)
            for local_index, neighbours in enumerate(results):
                source_id = point_ids[offset + local_index]
                for neighbour in neighbours:
                    target_id = str(neighbour.get("id"))
                    if target_id == source_id:
                        continue
                    a, b = sorted((source_id, target_id))
                    score = float(neighbour.get("score", 0.0))
                    previous = edges.get((a, b))
                    if previous is None or score > previous["score"]:
                        edges[(a, b)] = {
                            "source": a,
                            "target": b,
                            "type": "SEMANTICALLY_RELATED_COS20",
                            "score": round(score, 8),
                            "authority": "DERIVED_RECONSTRUCTIBLE_ONLY",
                        }
        return {
            "schema_version": "1.0.0",
            "engine": "COS-GRAPH-ENGINE",
            "dimensions": 20,
            "source_collection": self.config.qdrant_collection,
            "semantic_authority": "QDRANT_PROJECTION_ONLY_NOT_DOMAIN_TRUTH",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "parameters": {"top_k": top_k, "min_score": min_score, "max_nodes": max_nodes},
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": sorted(edges.values(), key=lambda item: (item["source"], item["target"])),
        }
