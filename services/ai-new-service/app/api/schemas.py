"""Pydantic schemas for API."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class BehaviorTrackRequest(BaseModel):
    user_id: str
    product_id: str
    action: str  # view, click, add_to_cart, purchase, search, wishlist, remove_from_cart, review


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    product_id: Optional[str] = None
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    session_id: Optional[str] = None


class RecommendResponse(BaseModel):
    user_id: str
    recommended_products: list
    predicted_action: Optional[str] = None
    source: str  # "model", "graph", "hybrid"


class TrainRequest(BaseModel):
    force: bool = False


class TrainStatusResponse(BaseModel):
    status: str
    best_model: Optional[str] = None
    results: Optional[dict] = None
