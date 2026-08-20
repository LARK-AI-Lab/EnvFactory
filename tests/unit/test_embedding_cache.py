from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from src.graph.embedding import (
    CachedEmbeddingBackend,
    EmbeddingValidationError,
    HTTPEmbeddingBackend,
    SentenceTransformersBackend,
)


class FakeBackend:
    identity = "fake:unit-test"

    def __init__(self, values=None):
        self.calls: list[list[str]] = []
        self.values = values

    def encode(self, texts: list[str]) -> np.ndarray:
        self.calls.append(list(texts))
        if self.values is not None:
            return self.values
        return np.asarray([[len(text), sum(text.encode("utf-8"))] for text in texts], dtype=np.float64)


def test_cache_deduplicates_normalizes_and_restores_order(tmp_path) -> None:
    backend = FakeBackend()
    cached = CachedEmbeddingBackend(backend, tmp_path / "embeddings.sqlite3")

    first = cached.encode(["alpha", "beta", "alpha"])
    assert backend.calls == [["alpha", "beta"]]
    assert first.shape == (3, 2)
    assert first.dtype == np.float32
    np.testing.assert_allclose(np.linalg.norm(first, axis=1), np.ones(3), rtol=1e-6)
    np.testing.assert_array_equal(first[0], first[2])
    assert (cached.hits, cached.misses) == (0, 2)

    second_backend = FakeBackend()
    second = CachedEmbeddingBackend(second_backend, tmp_path / "embeddings.sqlite3")
    np.testing.assert_array_equal(second.encode(["beta", "alpha"]), first[[1, 0]])
    assert second_backend.calls == []
    assert (second.hits, second.misses) == (2, 0)


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ([[1.0, 2.0]], "returned 1 rows"),
        ([[1.0, 2.0], [3.0]], "two-dimensional"),
        ([[1.0, float("nan")], [2.0, 3.0]], "non-finite"),
        ([[1, 2], [3, 4]], "floating-point dtype"),
        ([[0.0, 0.0], [1.0, 2.0]], "zero-norm"),
    ],
)
def test_cache_rejects_invalid_backend_outputs(tmp_path, values, message) -> None:
    cached = CachedEmbeddingBackend(FakeBackend(values), tmp_path / "bad.sqlite3")
    with pytest.raises(EmbeddingValidationError, match=message):
        cached.encode(["one", "two"])


def test_sentence_transformers_backend_is_lazy_and_cpu_configured() -> None:
    calls = []

    class FakeModel:
        def encode(self, texts, **kwargs):
            calls.append((texts, kwargs))
            return np.asarray([[3.0, 4.0] for _ in texts])

    loaded = []

    def load(model, *, device):
        loaded.append((model, device))
        return FakeModel()

    backend = SentenceTransformersBackend(
        "BAAI/bge-small-en-v1.5", device="cpu", batch_size=7, model_loader=load
    )
    assert loaded == []
    vectors = backend.encode(["one", "two"])
    assert loaded == [("BAAI/bge-small-en-v1.5", "cpu")]
    assert calls[0][1]["batch_size"] == 7
    assert calls[0][1]["show_progress_bar"] is False
    np.testing.assert_allclose(vectors, [[0.6, 0.8], [0.6, 0.8]])


def test_http_backend_preserves_openai_style_remote_embeddings() -> None:
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "data": [
                    {"index": 1, "embedding": [0.0, 2.0]},
                    {"index": 0, "embedding": [3.0, 0.0]},
                ]
            }

    session = SimpleNamespace(post=lambda *args, **kwargs: Response())
    backend = HTTPEmbeddingBackend(
        url="https://embeddings.invalid/v1/embeddings",
        model="existing-model",
        api_key="test-only",
        session=session,
    )
    np.testing.assert_array_equal(backend.encode(["first", "second"]), np.eye(2, dtype=np.float32))
