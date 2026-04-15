from __future__ import annotations
import logging
from pathlib import Path

import chromadb
from langchain_core.documents import Document

from app.config import settings
from app.rag.embeddings import EmbeddingService

logger = logging.getLogger(__name__)

COLLECTION_NAME = "ecommerce_kb"


class VectorStore:
    """ChromaDB-backed vector store with LangChain integration."""

    def __init__(self, embedder: EmbeddingService) -> None:
        self.embedder = embedder
        Path(settings.CHROMA_DIR).mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
        self._lc_store: Chroma | None = None

    def _get_lc_store(self) -> Chroma:
        if self._lc_store is None:
            self._lc_store = Chroma(
                client=self._client,
                collection_name=COLLECTION_NAME,
                embedding_function=self.embedder.langchain_embeddings,
            )
        return self._lc_store

    def is_ready(self) -> bool:
        try:
            col = self._client.get_collection(COLLECTION_NAME)
            return col.count() > 0
        except Exception:
            return False

    def build(self, documents: list[Document]) -> None:
        logger.info(f"Building vector store with {len(documents)} documents...")
        try:
            self._client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

        self._lc_store = None

        ids = [doc.metadata.get("id", str(i)) for i, doc in enumerate(documents)]
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]

        collection = self._client.get_or_create_collection(
            COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_texts = texts[i:i + batch_size]
            batch_meta = metadatas[i:i + batch_size]
            batch_embs = self.embedder.encode(batch_texts)
            collection.add(
                ids=batch_ids,
                documents=batch_texts,
                embeddings=batch_embs,  # type: ignore[arg-type]
                metadatas=batch_meta,
            )

        logger.info(f"Vector store built: {collection.count()} documents indexed.")

    def search(
        self,
        query: str,
        n_results: int = 5,
        doc_type: str | None = None,
        category_slug: str | None = None,
        max_price: float | None = None,
        min_price: float | None = None,
    ) -> list[dict]:
        try:
            col = self._client.get_collection(COLLECTION_NAME)
        except Exception:
            return []

        query_emb = self.embedder.encode_query(query)
        where: dict = {}

        if doc_type:
            where["doc_type"] = {"$eq": doc_type}

        # Fetch more candidates when price filtering is active to avoid empty results
        multiplier = 6 if (max_price or min_price) else 3
        col_count = col.count()
        fetch_n = min(n_results * multiplier, max(col_count, 1))
        results = col.query(
            query_embeddings=[query_emb],
            n_results=fetch_n,
            where=where if where else None,
            include=["documents", "metadatas", "distances"],
        )

        items = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            if category_slug and meta.get("category_slug") != category_slug:
                continue
            try:
                price = float(meta.get("price") or 0)
            except (TypeError, ValueError):
                price = 0.0
            if max_price and price > max_price:
                continue
            if min_price and price < min_price:
                continue
            items.append({
                "text": doc,
                "metadata": meta,
                "score": 1 - dist,
            })
            if len(items) >= n_results:
                break

        return items

    def search_products(self, query: str, n_results: int = 5, **filters) -> list[dict]:
        return self.search(query, n_results=n_results, doc_type="product", **filters)

    def search_faq(self, query: str, n_results: int = 3) -> list[dict]:
        return self.search(query, n_results=n_results, doc_type="faq")

    def count(self) -> int:
        try:
            return self._client.get_collection(COLLECTION_NAME).count()
        except Exception:
            return 0
