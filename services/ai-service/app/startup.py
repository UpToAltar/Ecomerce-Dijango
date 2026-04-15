from __future__ import annotations
import asyncio
import logging

from app.config import settings
from app.knowledge_base.builder import build_documents, fetch_products_with_retry
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore
from app.rag.chat_engine import ChatEngine
from app.training.trainer import BehaviorTrainer
from app.state import app_state

logger = logging.getLogger(__name__)

_embedder: EmbeddingService | None = None
_vector_store: VectorStore | None = None
_products_cache: list = []


def get_vector_store() -> VectorStore | None:
    return _vector_store


async def initialize_services() -> None:
    global _embedder, _vector_store

    logger.info("Initializing AI service...")
    _embedder = EmbeddingService()
    _vector_store = VectorStore(_embedder)
    trainer = BehaviorTrainer()
    app_state.trainer = trainer

    chat_engine = ChatEngine(_vector_store)
    app_state.chat_engine = chat_engine

    if _vector_store.is_ready():
        logger.info("Vector store already built, skipping KB rebuild.")
        app_state.is_kb_ready = True
    else:
        logger.info("Vector store empty, scheduling initial build.")

    if trainer.load_if_exists():
        app_state.is_model_ready = True
        app_state.training_status = "completed"
        logger.info("Existing model loaded. Rebuilding product cache...")

    asyncio.create_task(_startup_pipeline())


async def _startup_pipeline() -> None:
    await asyncio.sleep(5)
    await run_startup_pipeline()


async def run_startup_pipeline(force_rebuild: bool = False) -> None:
    global _products_cache

    logger.info("Starting knowledge base and model pipeline...")

    products = await fetch_products_with_retry(retries=8, delay=10.0)
    if not products:
        logger.error("No products fetched; skipping pipeline.")
        return

    _products_cache = products
    app_state.total_products = len(products)

    # Always rebuild idx_to_product so recommendations work after reload
    if app_state.trainer:
        app_state.trainer.idx_to_product = {i: p for i, p in enumerate(products)}
        logger.info(f"Product cache rebuilt: {len(products)} products.")

    if not app_state.is_kb_ready or force_rebuild:
        try:
            documents = build_documents(products)
            _vector_store.build(documents)  # type: ignore[union-attr]
            app_state.is_kb_ready = True
            logger.info(f"Knowledge base built with {len(documents)} documents.")
        except Exception as e:
            logger.error(f"KB build failed: {e}")

    if not app_state.is_model_ready or force_rebuild:
        await run_training_only()


async def run_training_only() -> None:
    global _products_cache

    if not _products_cache:
        _products_cache = await fetch_products_with_retry()
        if not _products_cache:
            logger.error("No products for training.")
            return

    try:
        trainer = app_state.trainer
        if trainer is None:
            from app.training.trainer import BehaviorTrainer
            trainer = BehaviorTrainer()
            app_state.trainer = trainer

        metrics = await trainer.train(_products_cache)
        app_state.is_model_ready = True
        logger.info(f"Model training completed: {metrics}")
    except Exception as e:
        app_state.training_status = "failed"
        app_state.training_progress = str(e)
        logger.error(f"Training failed: {e}")
