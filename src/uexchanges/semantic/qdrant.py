from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Sequence
from typing import Any


class QdrantError(RuntimeError):
    pass


Transport = Callable[[str, str, dict[str, Any] | None], dict[str, Any]]


def collection_spec(
    semantic_dimensions: int,
    *,
    semantic_name: str = "semantic",
    cos_name: str = "cos20",
    cos_dimensions: int = 20,
) -> dict[str, Any]:
    if semantic_dimensions < 1:
        raise ValueError("semantic vector dimension must be positive")
    if cos_dimensions != 20:
        raise ValueError("COS graph contract requires 20 dimensions")
    return {
        "vectors": {
            semantic_name: {"size": semantic_dimensions, "distance": "Cosine"},
            cos_name: {"size": cos_dimensions, "distance": "Cosine"},
        },
        "on_disk_payload": True,
    }


class QdrantRESTClient:
    def __init__(
        self,
        base_url: str,
        collection: str,
        *,
        api_key: str | None = None,
        timeout: float = 60.0,
        transport: Transport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.collection = collection
        self.api_key = api_key
        self.timeout = timeout
        self._transport = transport

    @property
    def _collection_path(self) -> str:
        return "/collections/" + urllib.parse.quote(self.collection, safe="")

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if self._transport is not None:
            return self._transport(method, path, payload)
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key
        request = urllib.request.Request(
            f"{self.base_url}{path}", data=data, method=method, headers=headers
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise QdrantError(f"Qdrant HTTP {exc.code}: {body[:700]}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise QdrantError(f"Qdrant request failed: {exc}") from exc

    def doctor(self) -> dict[str, Any]:
        response = self._request("GET", "/")
        return {"reachable": True, "title": response.get("title"), "version": response.get("version")}

    def collection_info(self) -> dict[str, Any] | None:
        try:
            return self._request("GET", self._collection_path)
        except QdrantError as exc:
            if "HTTP 404" in str(exc):
                return None
            raise

    def delete_collection(self) -> None:
        self._request("DELETE", self._collection_path)

    def ensure_collection(
        self,
        semantic_dimensions: int,
        *,
        semantic_name: str = "semantic",
        cos_name: str = "cos20",
        recreate: bool = False,
    ) -> None:
        spec = collection_spec(
            semantic_dimensions,
            semantic_name=semantic_name,
            cos_name=cos_name,
        )
        existing = self.collection_info()
        if existing is not None and recreate:
            self.delete_collection()
            existing = None
        if existing is None:
            self._request("PUT", self._collection_path, spec)
            return
        vectors = (
            existing.get("result", {})
            .get("config", {})
            .get("params", {})
            .get("vectors", {})
        )
        expected = spec["vectors"]
        for name, params in expected.items():
            current = vectors.get(name) if isinstance(vectors, dict) else None
            if not isinstance(current, dict) or int(current.get("size", -1)) != params["size"]:
                raise QdrantError(
                    f"collection {self.collection!r} vector {name!r} is incompatible; "
                    "run index --recreate after confirming the collection is reconstructible"
                )

    def delete_repo_points(self, repo_id: str) -> None:
        self._request(
            "POST",
            f"{self._collection_path}/points/delete?wait=true",
            {"filter": {"must": [{"key": "repo", "match": {"value": repo_id}}]}},
        )

    def delete_stale_repo_points(self, repo_id: str, index_build_id: str) -> None:
        """Delete prior repository points only after a complete replacement build was upserted."""
        self._request(
            "POST",
            f"{self._collection_path}/points/delete?wait=true",
            {
                "filter": {
                    "must": [{"key": "repo", "match": {"value": repo_id}}],
                    "must_not": [
                        {"key": "index_build_id", "match": {"value": index_build_id}}
                    ],
                }
            },
        )

    def upsert(self, points: Sequence[dict[str, Any]]) -> None:
        if not points:
            return
        self._request(
            "PUT",
            f"{self._collection_path}/points?wait=true",
            {"points": list(points)},
        )

    def query(
        self,
        vector: Sequence[float],
        *,
        using: str,
        limit: int = 10,
        score_threshold: float | None = None,
        filter_: dict[str, Any] | None = None,
        with_vectors: bool | list[str] = False,
    ) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "query": list(vector),
            "using": using,
            "limit": limit,
            "with_payload": True,
            "with_vector": with_vectors,
        }
        if score_threshold is not None:
            payload["score_threshold"] = score_threshold
        if filter_ is not None:
            payload["filter"] = filter_
        response = self._request("POST", f"{self._collection_path}/points/query", payload)
        result = response.get("result", {})
        if isinstance(result, dict):
            points = result.get("points", [])
        else:
            points = result
        return list(points) if isinstance(points, list) else []

    def query_batch(self, searches: Sequence[dict[str, Any]]) -> list[list[dict[str, Any]]]:
        if not searches:
            return []
        response = self._request(
            "POST", f"{self._collection_path}/points/query/batch", {"searches": list(searches)}
        )
        result = response.get("result", [])
        out: list[list[dict[str, Any]]] = []
        for item in result if isinstance(result, list) else []:
            points = item.get("points", []) if isinstance(item, dict) else []
            out.append(list(points) if isinstance(points, list) else [])
        return out

    def scroll(
        self,
        *,
        filter_: dict[str, Any] | None = None,
        vector_names: list[str] | None = None,
        page_size: int = 256,
        max_points: int | None = None,
    ) -> list[dict[str, Any]]:
        points: list[dict[str, Any]] = []
        offset: str | int | None = None
        while True:
            payload: dict[str, Any] = {
                "limit": page_size,
                "with_payload": True,
                "with_vector": vector_names if vector_names is not None else False,
            }
            if filter_ is not None:
                payload["filter"] = filter_
            if offset is not None:
                payload["offset"] = offset
            response = self._request("POST", f"{self._collection_path}/points/scroll", payload)
            result = response.get("result", {})
            batch = result.get("points", []) if isinstance(result, dict) else []
            points.extend(batch if isinstance(batch, list) else [])
            if max_points is not None and len(points) >= max_points:
                return points[:max_points]
            offset = result.get("next_page_offset") if isinstance(result, dict) else None
            if offset is None or not batch:
                break
        return points
