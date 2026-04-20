"""Startup initialization for ai-new-service."""
import logging
import asyncio

from app.database import init_db
from app.data_generator import generate_behavior_data
from app.training.trainer import ModelTrainer
from app.knowledge_base.kb_graph import KnowledgeBaseGraph
from app.rag.chat_engine import RAGChatEngine
from app.api.routes import set_globals

logger = logging.getLogger(__name__)


async def initialize_services():
    """Initialize all components on startup."""
    logger.info("Initializing ai-new-service...")

    # 1. Create DB tables
    logger.info("Creating database tables...")
    init_db()

    # 2. Generate behavior data
    logger.info("Generating behavior data...")
    try:
        await generate_behavior_data()
    except Exception as e:
        logger.error(f"Data generation failed: {e}")

    # 3. Initialize trainer and train models
    trainer = ModelTrainer()
    try:
        logger.info("Training models (RNN, LSTM, BiLSTM)...")
        trainer.train_all()
        logger.info(f"Training completed. Best model: {trainer.best_model_name}")
    except Exception as e:
        logger.error(f"Training failed: {e}")

    # 4. Initialize KB Graph
    kb_graph = KnowledgeBaseGraph()
    try:
        logger.info("Building Knowledge Base Graph...")
        await kb_graph.build_graph()
        logger.info("KB Graph built successfully.")
    except Exception as e:
        logger.error(f"KB Graph build failed (Neo4j may not be ready): {e}")

    # 5. Initialize RAG Chat Engine
    chat_engine = RAGChatEngine(kb_graph)
    try:
        logger.info("Initializing RAG Chat Engine...")
        chat_engine.initialize()
        await chat_engine.index_products()
        logger.info("RAG Chat Engine ready.")
    except Exception as e:
        logger.error(f"RAG Engine init failed: {e}")

    # Set globals for routes
    set_globals(trainer, kb_graph, chat_engine)
    logger.info("ai-new-service initialization complete.")
