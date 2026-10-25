from abc import ABC, abstractmethod
from typing import List
import math
import hashlib
import logging
from app.core.config import settings

logger = logging.getLogger("finpilot.rag.embeddings")

VECTOR_DIMENSION = 768


class BaseEmbeddingProvider(ABC):
    @property
    def dimension(self) -> int:
        return VECTOR_DIMENSION

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass


class DeterministicEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic 768-dimensional feature-hashing embedding generator.
    Produces repeatable normalized vectors using term n-grams and hashing.
    Used for local development, automated testing, and offline fallback with zero cloud dependencies.
    """

    def embed_text(self, text: str) -> List[float]:
        vec = [0.0] * self.dimension
        words = text.lower().split()
        if not words:
            return vec

        # Term and bigram hashing
        tokens = list(words)
        for i in range(len(words) - 1):
            tokens.append(f"{words[i]}_{words[i+1]}")

        for token in tokens:
            # Deterministic hash to dimension index
            h = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if (h // self.dimension) % 2 == 0 else -1.0
            vec[idx] += sign * (1.0 + math.log(1 + len(token)))

        # L2 Normalization
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 1e-9:
            vec = [x / norm for x in vec]
        return vec

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


class CloudGeminiEmbeddingProvider(BaseEmbeddingProvider):
    """
    Cloud embedding provider using Google Gemini's text-embedding-004 model (768 dims).
    Falls back gracefully to DeterministicEmbeddingProvider if no API key or network fails.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-embedding-001"):
        self.api_key = api_key
        self.model_name = model_name
        self.fallback = DeterministicEmbeddingProvider()

    def embed_text(self, text: str) -> List[float]:
        if not self.api_key:
            return self.fallback.embed_text(text)

        for model in [self.model_name, "gemini-embedding-001", "text-embedding-004"]:
            try:
                from google import genai
                client = genai.Client(api_key=self.api_key)
                resp = client.models.embed_content(
                    model=model,
                    contents=text
                )
                if hasattr(resp, "embeddings") and resp.embeddings:
                    return resp.embeddings[0].values
                elif hasattr(resp, "embedding") and resp.embedding:
                    return resp.embedding.values
            except Exception:
                continue

        return self.fallback.embed_text(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


def get_embedding_provider() -> BaseEmbeddingProvider:
    if settings.LLM_PROVIDER.lower() == "gemini" and settings.LLM_API_KEY:
        return CloudGeminiEmbeddingProvider(api_key=settings.LLM_API_KEY)
    return DeterministicEmbeddingProvider()
