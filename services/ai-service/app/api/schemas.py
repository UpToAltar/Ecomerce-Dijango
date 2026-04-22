from __future__ import annotations
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: str = Field(default="default", max_length=100)
    user_id: str | None = None


class ChatResponse(BaseModel):
    message: str
    intent: str
    products: list[dict] = []
    session_id: str


class TrackBehaviorRequest(BaseModel):
    user_id: str
    product_id: str
    event_type: str = "view"


class RecommendResponse(BaseModel):
    user_id: str | None
    products: list[dict]
    source: str


class TrainRequest(BaseModel):
    force: bool = False


class TrainResponse(BaseModel):
    status: str
    message: str
    metrics: dict = {}


class KBStatusResponse(BaseModel):
    is_ready: bool
    document_count: int
    total_products: int


class HealthResponse(BaseModel):
    status: str
    service: str = "ai-service"
    kb_ready: bool
    model_ready: bool
    training_status: str
    total_products: int


class GraphStatusResponse(BaseModel):
    is_ready: bool
    is_connected: bool
    products: int = 0
    categories: int = 0
    brands: int = 0
    similar_edges: int = 0
    total_nodes: int = 0


class GraphNode(BaseModel):
    id: str
    labels: list[str]
    properties: dict


class GraphRelationship(BaseModel):
    id: str
    type: str
    start: str
    end: str
    properties: dict


class GraphExploreResponse(BaseModel):
    nodes: list[GraphNode]
    relationships: list[GraphRelationship]
