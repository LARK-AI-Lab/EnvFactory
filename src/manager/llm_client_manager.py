import itertools
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from dotenv import load_dotenv
import numpy as np
from openai import OpenAI
import os
import requests
from requests.adapters import HTTPAdapter
from tqdm import tqdm

load_dotenv()


def _retry_with_backoff(func, *args, max_retries: int = 3, base_delay: float = 1.0, **kwargs):
    """Call func with exponential backoff retry. Returns (result, None) or (None, exception)."""
    last_exc = None
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs), None
        except Exception as e:  # pylint: disable=broad-except
            last_exc = e
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))
    return None, last_exc


class LLMClientManager:
    def __init__(
        self,
        batch_size: int = None,
        inference_workers: int = 16,
        encode_batch_size: int = None,
    ):
        if batch_size is not None:
            self.inference_workers = batch_size
            self.encode_batch_size = encode_batch_size or batch_size
        else:
            self.inference_workers = inference_workers
            self.encode_batch_size = encode_batch_size or 16

        self._chat_api_key = os.environ.get("CHAT_API_KEY")
        self._chat_url = os.environ.get("CHAT_URL")
        self._chat_model = os.environ.get("CHAT_MODEL")
        self._embedding_model = os.environ.get("EMBEDDING_MODEL")
        self._embedding_api_key = os.environ.get("EMBEDDING_API_KEY")
        self._embedding_url = os.environ.get("EMBEDDING_URL")

        self.chat_client = OpenAI(
            api_key=self._chat_api_key,
            base_url=self._chat_url,
        )

        pool_size = max(self.inference_workers, 4)
        self._session = requests.Session()
        adapter = HTTPAdapter(
            pool_connections=pool_size,
            pool_maxsize=pool_size,
        )
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        self._embed_headers = {
            "Authorization": f"Bearer {self._embedding_api_key}",
            "Content-Type": "application/json",
        }

        self._executor = ThreadPoolExecutor(max_workers=pool_size)

    def _batch_inference(self, messages: list[dict], **kwargs) -> str:
        result, exc = _retry_with_backoff(
            self.chat_client.chat.completions.create,
            model=self._chat_model,
            messages=messages,
            **kwargs,
            max_retries=3,
        )
        if exc is not None:
            print(f"Error when processing {messages}: {exc}")
            return None
        return result.choices[0].message.content

    def inference(
        self,
        prompts: str | list[str] | list[dict],
        disable_progress_bar: bool = False,
        **kwargs,
    ) -> list[str]:
        """Perform batch inference on a list of prompts."""
        if isinstance(prompts, str):
            prompts = [prompts]

        messages = []
        for prompt in prompts:
            if isinstance(prompt, str):
                messages.append([{"role": "user", "content": prompt}])
            elif isinstance(prompt, dict):
                messages.append([prompt])
            else:
                raise NotImplementedError

        fn = partial(self._batch_inference, **kwargs)
        results = list(
            tqdm(
                self._executor.map(fn, messages),
                total=len(messages),
                disable=disable_progress_bar,
            )
        )
        return results

    def _batch_encode(self, batch_texts: list[str]) -> list[list[float]]:
        """Encode a single batch of texts (with retry)."""
        payload = {
            "model": self._embedding_model,
            "input": batch_texts,
        }
        result, exc = _retry_with_backoff(
            self._session.post,
            self._embedding_url,
            json=payload,
            headers=self._embed_headers,
            max_retries=3,
        )
        if exc is not None:
            raise exc
        result.raise_for_status()
        data = result.json()
        return [item["embedding"] for item in data["data"]]

    def encode(
        self,
        texts: str | list[str],
        disable_progress_bar: bool = False,
    ) -> np.ndarray:
        """Encode texts with batched concurrent requests."""
        if isinstance(texts, str):
            texts = [texts]

        batch_size = self.encode_batch_size
        batches = [
            texts[i : i + batch_size]
            for i in range(0, len(texts), batch_size)
        ]
        if not batches:
            return np.array([])

        batch_embeddings = list(
            tqdm(
                self._executor.map(self._batch_encode, batches),
                total=len(batches),
                desc="Generating embeddings in a batch.",
                disable=disable_progress_bar,
            )
        )
        return np.array(list(itertools.chain.from_iterable(batch_embeddings)))

    def similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> np.ndarray:
        """Compute cosine similarity matrix between two sets of embeddings.

        Args:
            emb1: Array of shape [a, b] where a is number of vectors and b is embedding dimension
            emb2: Array of shape [c, b] where c is number of vectors and b is embedding dimension

        Returns:
            Similarity matrix of shape [a, c] where element [i, j] is the cosine similarity between emb1[i] and emb2[j]
        """
        emb1 = np.atleast_2d(emb1)
        emb2 = np.atleast_2d(emb2)

        emb1_norms = np.linalg.norm(emb1, axis=1, keepdims=True)
        emb2_norms = np.linalg.norm(emb2, axis=1, keepdims=True)

        with np.errstate(divide="ignore", invalid="ignore"):
            emb1_norm = np.where(emb1_norms > 0, emb1 / emb1_norms, emb1)
            emb2_norm = np.where(emb2_norms > 0, emb2 / emb2_norms, emb2)

        similarity_matrix = np.dot(emb1_norm, emb2_norm.T)
        return similarity_matrix

    @property
    def batch_size(self) -> int:
        """Backward compatibility: same as encode_batch_size."""
        return self.encode_batch_size

    def shutdown(self):
        """Release thread pool and HTTP session resources."""
        self._executor.shutdown(wait=False)
        self._session.close()

    def __del__(self):
        try:
            self.shutdown()
        except Exception:
            pass


LLMClient = LLMClientManager()
