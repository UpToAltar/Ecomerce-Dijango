from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.rag.chat_engine import ChatEngine
    from app.training.trainer import BehaviorTrainer
    from app.graph.graph_store import KnowledgeGraph


class AppState:
    chat_engine: "ChatEngine | None" = None
    trainer: "BehaviorTrainer | None" = None
    graph_store: "KnowledgeGraph | None" = None
    is_kb_ready: bool = False
    is_model_ready: bool = False
    is_graph_ready: bool = False
    training_status: str = "not_started"
    training_progress: str = ""
    total_products: int = 0
    total_behaviors: int = 0


app_state = AppState()
