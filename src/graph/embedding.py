"""Embedding backends and a validated content-addressed SQLite cache."""

from __future__ import annotations

import hashlib
import os
import sqlite3
import threading
from pathlib import Path
from typing import Callable, Protocol, runtime_checkable

import numpy as np
import requests


class EmbeddingError(RuntimeError):
    """Base error raised by embedding backends and caches."""


class EmbeddingValidationError(EmbeddingError, ValueError):
    """Raised when a backend or cache returns an invalid embedding matrix."""


@runtime_checkable
class EmbeddingBackend(Protocol):
    """Small interface shared by remote and local embedding implementations."""

    @property
    def identity(self) -> str:
        """Return a stable, secret-free identifier for cache partitioning."""

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode each input text into one row, preserving input order."""


def _validated_normalized(vectors: object, expected_rows: int, *, source: str) -> np.ndarray:
    """Validate an embedding matrix and return unit-normalized float32 rows."""
    try:
        array = np.asarray(vectors)
    except (TypeError, ValueError) as exc:
        raise EmbeddingValidationError(
            f"{source} did not return a rectangular two-dimensional matrix"
        ) from exc
    if array.ndim != 2:
        raise EmbeddingValidationError(
            f"{source} returned rank {array.ndim}; expected a two-dimensional matrix"
        )
    if array.shape[0] != expected_rows:
        raise EmbeddingValidationError(
            f"{source} returned {array.shape[0]} rows for {expected_rows} texts"
        )
    if expected_rows == 0:
        return np.empty((0, array.shape[1]), dtype=np.float32)
    if array.shape[1] <= 0:
        raise EmbeddingValidationError(f"{source} returned zero-dimensional vectors")
    if array.dtype.kind != "f":
        raise EmbeddingValidationError(
            f"{source} returned dtype {array.dtype}; expected a floating-point dtype"
        )
    if not np.isfinite(array).all():
        raise EmbeddingValidationError(f"{source} returned non-finite values")

    float_vectors = np.asarray(array, dtype=np.float32)
    norms = np.linalg.norm(float_vectors, axis=1, keepdims=True)
    if not np.isfinite(norms).all() or np.any(norms <= 0):
        raise EmbeddingValidationError(f"{source} returned a zero-norm vector")
    normalized = float_vectors / norms
    return np.ascontiguousarray(normalized, dtype=np.float32)


class HTTPEmbeddingBackend:
    """OpenAI-style HTTP embeddings, preserving EnvFactory's remote backend."""

    def __init__(
        self,
        *,
        url: str,
        model: str,
        api_key: str,
        batch_size: int = 64,
        timeout_seconds: float = 60.0,
        session: requests.Session | None = None,
    ) -> None:
        if not url or not model or not api_key:
            raise EmbeddingError("HTTP embeddings require a URL, model, and API key")
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self.url = url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.batch_size = batch_size
        self.timeout_seconds = timeout_seconds
        self._session = session or requests.Session()

    @classmethod
    def from_environment(
        cls, *, model: str | None = None, batch_size: int = 64
    ) -> "HTTPEmbeddingBackend":
        """Create the compatibility HTTP backend from existing environment names."""
        return cls(
            url=os.environ.get("EMBEDDING_URL", ""),
            model=model or os.environ.get("EMBEDDING_MODEL", ""),
            api_key=os.environ.get("EMBEDDING_API_KEY", ""),
            batch_size=batch_size,
        )

    @property
    def identity(self) -> str:
        return f"http:{self.model}@{self.url}"

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 0), dtype=np.float32)
        rows: list[object] = []
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            try:
                response = self._session.post(
                    self.url,
                    json={"model": self.model, "input": batch},
                    headers=headers,
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                payload = response.json()
            except Exception as exc:
                raise EmbeddingError(
                    f"HTTP embedding request failed with {type(exc).__name__}"
                ) from exc
            data = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(data, list):
                raise EmbeddingValidationError("HTTP embedding response has no data list")
            try:
                ordered = sorted(data, key=lambda item: item.get("index", 0))
                rows.extend(item["embedding"] for item in ordered)
            except (KeyError, TypeError) as exc:
                raise EmbeddingValidationError("HTTP embedding response has invalid rows") from exc
        return _validated_normalized(rows, len(texts), source=self.identity)


class SentenceTransformersBackend:
    """Lazy local sentence-transformers backend suitable for CPU graph builds."""

    def __init__(
        self,
        model: str,
        *,
        device: str = "cpu",
        batch_size: int = 64,
        model_loader: Callable[..., object] | None = None,
    ) -> None:
        if not model.strip() or not device.strip():
            raise ValueError("model and device must be non-empty")
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self.model = model
        self.device = device
        self.batch_size = batch_size
        self._model_loader = model_loader
        self._model: object | None = None
        self._lock = threading.Lock()

    @property
    def identity(self) -> str:
        return f"sentence-transformers:{self.model}@{self.device}"

    def _load_model(self) -> object:
        with self._lock:
            if self._model is not None:
                return self._model
            loader = self._model_loader
            if loader is None:
                try:
                    from sentence_transformers import SentenceTransformer
                except ImportError as exc:
                    raise EmbeddingError(
                        "sentence-transformers is required for the local embedding backend; "
                        "install the 'mini' extra"
                    ) from exc
                loader = SentenceTransformer
            try:
                self._model = loader(self.model, device=self.device)
            except Exception as exc:
                raise EmbeddingError(
                    f"failed to load embedding model {self.model!r} with {type(exc).__name__}"
                ) from exc
            return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 0), dtype=np.float32)
        model = self._load_model()
        try:
            vectors = model.encode(
                texts,
                batch_size=self.batch_size,
                convert_to_numpy=True,
                normalize_embeddings=False,
                show_progress_bar=False,
            )
        except Exception as exc:
            raise EmbeddingError(
                f"embedding model inference failed with {type(exc).__name__}"
            ) from exc
        return _validated_normalized(vectors, len(texts), source=self.identity)


class CachedEmbeddingBackend:
    """Deduplicating SQLite cache keyed by backend identity and UTF-8 SHA-256."""

    _SCHEMA = """
        CREATE TABLE IF NOT EXISTS embeddings (
            backend_identity TEXT NOT NULL,
            text_sha256 TEXT NOT NULL,
            dimension INTEGER NOT NULL,
            vector BLOB NOT NULL,
            PRIMARY KEY (backend_identity, text_sha256)
        )
    """

    def __init__(self, backend: EmbeddingBackend, path: str | Path) -> None:
        if not isinstance(backend, EmbeddingBackend):
            raise TypeError("backend must implement EmbeddingBackend")
        self.backend = backend
        self.path = Path(path)
        self.hits = 0
        self.misses = 0

    @property
    def identity(self) -> str:
        return self.backend.identity

    @staticmethod
    def text_hash(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=30)
        connection.execute(self._SCHEMA)
        return connection

    def encode(self, texts: list[str]) -> np.ndarray:
        if any(not isinstance(text, str) for text in texts):
            raise TypeError("embedding inputs must be strings")
        if not texts:
            return np.empty((0, 0), dtype=np.float32)

        unique_texts = list(dict.fromkeys(texts))
        vectors_by_text: dict[str, np.ndarray] = {}
        missing: list[str] = []
        with self._connect() as connection:
            for text in unique_texts:
                text_hash = self.text_hash(text)
                row = connection.execute(
                    "SELECT dimension, vector FROM embeddings "
                    "WHERE backend_identity = ? AND text_sha256 = ?",
                    (self.identity, text_hash),
                ).fetchone()
                if row is None:
                    missing.append(text)
                    continue
                dimension, blob = row
                vector = np.frombuffer(blob, dtype=np.float32)
                if dimension <= 0 or vector.size != dimension or not np.isfinite(vector).all():
                    raise EmbeddingValidationError(
                        f"invalid cached vector for backend {self.identity} and text {text_hash}"
                    )
                norm = float(np.linalg.norm(vector))
                if not np.isclose(norm, 1.0, rtol=1e-5, atol=1e-6):
                    raise EmbeddingValidationError(
                        f"cached vector is not normalized for backend {self.identity} "
                        f"and text {text_hash}"
                    )
                vectors_by_text[text] = vector.copy()

            self.hits += len(unique_texts) - len(missing)
            self.misses += len(missing)
            if missing:
                encoded = _validated_normalized(
                    self.backend.encode(missing), len(missing), source=self.identity
                )
                for text, vector in zip(missing, encoded, strict=True):
                    text_hash = self.text_hash(text)
                    connection.execute(
                        "INSERT OR REPLACE INTO embeddings "
                        "(backend_identity, text_sha256, dimension, vector) VALUES (?, ?, ?, ?)",
                        (self.identity, text_hash, vector.size, vector.tobytes()),
                    )
                    vectors_by_text[text] = vector

        try:
            ordered = np.stack([vectors_by_text[text] for text in texts])
        except ValueError as exc:
            raise EmbeddingValidationError(
                f"cached and computed dimensions differ for backend {self.identity}"
            ) from exc
        return _validated_normalized(ordered, len(texts), source=f"cache:{self.identity}")


__all__ = [
    "CachedEmbeddingBackend",
    "EmbeddingBackend",
    "EmbeddingError",
    "EmbeddingValidationError",
    "HTTPEmbeddingBackend",
    "SentenceTransformersBackend",
]
