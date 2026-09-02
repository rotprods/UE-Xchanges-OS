from __future__ import annotations

import json
import math
import urllib.error
import urllib.request
from collections.abc import Sequence


class OllamaError(RuntimeError):
    pass


class OllamaEmbedder:
    def __init__(self, base_url: str, model: str, *, timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise OllamaError(f"Ollama HTTP {exc.code}: {body[:500]}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise OllamaError(f"Ollama request failed: {exc}") from exc

    def doctor(self) -> dict:
        response = self._request("GET", "/api/tags")
        models = response.get("models") or []
        names = {str(item.get("name", "")) for item in models if isinstance(item, dict)}
        return {"reachable": True, "model": self.model, "model_present": self.model in names or any(name.startswith(self.model + ":") for name in names), "models": sorted(names)}

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        response = self._request(
            "POST",
            "/api/embed",
            {"model": self.model, "input": list(texts), "truncate": True},
        )
        embeddings = response.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise OllamaError("Ollama returned an invalid embedding batch")
        vectors: list[list[float]] = []
        width: int | None = None
        for raw in embeddings:
            if not isinstance(raw, list) or not raw:
                raise OllamaError("Ollama returned an empty embedding")
            vector = [float(value) for value in raw]
            if any(not math.isfinite(value) for value in vector):
                raise OllamaError("Ollama returned non-finite embedding values")
            width = width or len(vector)
            if len(vector) != width:
                raise OllamaError("Ollama returned inconsistent embedding dimensions")
            vectors.append(vector)
        return vectors
