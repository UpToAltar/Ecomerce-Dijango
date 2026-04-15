from __future__ import annotations
import logging
from functools import lru_cache

from sentence_transformers import SentenceTransformer
from langchain_community.embeddings import HuggingFaceEmbeddings

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Wraps sentence-transformers for both direct encoding and LangChain usage."""

    def __init__(self) -> None:
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self._lc_embeddings: HuggingFaceEmbeddings | None = None
        logger.info("Embedding model loaded successfully.")

    def encode(self, text: str | list[str]) -> list[float] | list[list[float]]:
        embeddings = self._model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        if isinstance(text, str):
            return embeddings.tolist()
        return [e.tolist() for e in embeddings]

    def encode_query(self, text: str) -> list[float]:
        return self.encode(text)  # type: ignore[return-value]

    @property
    def langchain_embeddings(self) -> HuggingFaceEmbeddings:
        if self._lc_embeddings is None:
            self._lc_embeddings = HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
        return self._lc_embeddings


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
