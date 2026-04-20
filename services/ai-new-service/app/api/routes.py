"""API Routes for ai-new-service."""
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db, UserBehaviorData
from app.api.schemas import (
    BehaviorTrackRequest, ChatRequest, ChatResponse,
    RecommendResponse, TrainRequest, TrainStatusResponse,
)
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Global state references (set in startup)
_trainer = None
_kb_graph = None
_chat_engine = None


def set_globals(trainer, kb_graph, chat_engine):
    global _trainer, _kb_graph, _chat_engine
    _trainer = trainer
    _kb_graph = kb_graph
    _chat_engine = chat_engine


# ─── Health ─────────────────────────────────────
@router.get("/health")
async def health():
    return {"status": "ok", "service": "ai-new-service"}


# ─── Behavior Tracking ─────────────────────────
@router.post("/api/ai-new/track")
async def track_behavior(req: BehaviorTrackRequest, db: Session = Depends(get_db)):
    """Track user behavior (called from frontend or other services)."""
    valid_actions = ["view", "click", "add_to_cart", "purchase", "search", "wishlist", "remove_from_cart", "review"]
    if req.action not in valid_actions:
        raise HTTPException(400, f"Invalid action. Must be one of: {valid_actions}")

    record = UserBehaviorData(
        user_id=req.user_id,
        product_id=req.product_id,
        action=req.action,
        timestamp=datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    return {"status": "tracked", "action": req.action}


# ─── Recommendations ───────────────────────────
@router.get("/api/ai-new/recommend/{user_id}")
async def recommend(user_id: str, db: Session = Depends(get_db)):
    """Get recommendations for user using hybrid: model + graph."""
    recommended = []
    predicted_action = None
    source = "fallback"

    # 1. Try model prediction
    if _trainer and _trainer.best_model:
        recent = db.query(UserBehaviorData).filter(
            UserBehaviorData.user_id == user_id
        ).order_by(UserBehaviorData.timestamp.desc()).limit(settings.SEQ_LENGTH).all()

        if len(recent) >= 3:
            behaviors = [{"product_id": r.product_id, "action": r.action} for r in reversed(recent)]
            prediction = _trainer.predict_next_action(user_id, behaviors)
            if prediction:
                recommended = prediction["recommended_product_ids"]
                predicted_action = prediction["predicted_action"]
                source = "model"

    # 2. Augment with graph recommendations
    if _kb_graph and _kb_graph.ready:
        graph_recs = _kb_graph.query_user_recommendations(user_id, 10)
        graph_ids = [r["id"] for r in graph_recs if r["id"] not in recommended]
        if graph_ids:
            recommended.extend(graph_ids[:5])
            if source == "model":
                source = "hybrid"
            else:
                source = "graph"

    # 3. Enrich with product details by fetching from product-service
    enriched = []
    if recommended:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Fetch all products in one call and match
                resp = await client.get(
                    f"{settings.PRODUCT_SERVICE_URL}/api/products/",
                    params={"page_size": 200}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    all_products = data if isinstance(data, list) else data.get("results", [])
                    # Build lookup by ID
                    product_map = {str(p["id"]): p for p in all_products}

                    for pid in recommended[:10]:
                        p = product_map.get(str(pid))
                        if p:
                            enriched.append({
                                "id": str(p["id"]),
                                "name": p.get("name", ""),
                                "price": p.get("price", 0),
                                "image_url": p.get("image_url", ""),
                                "brand": p.get("brand", ""),
                                "rating_avg": p.get("rating_avg", 0),
                                "slug": p.get("slug", ""),
                                "category_name": p.get("category_name", ""),
                                "stock_quantity": p.get("stock_quantity", 0),
                                "discount_percent": p.get("discount_percent", 0),
                                "compare_price": p.get("compare_price", 0),
                            })

                # If still missing some, try individual lookups by UUID slug
                if len(enriched) < len(recommended[:10]):
                    found_ids = {e["id"] for e in enriched}
                    for pid in recommended[:10]:
                        if str(pid) in found_ids:
                            continue
                        try:
                            resp2 = await client.get(f"{settings.PRODUCT_SERVICE_URL}/api/products/{pid}/")
                            if resp2.status_code == 200:
                                p = resp2.json()
                                enriched.append({
                                    "id": str(p["id"]),
                                    "name": p.get("name", ""),
                                    "price": p.get("price", 0),
                                    "image_url": p.get("image_url", ""),
                                    "brand": p.get("brand", ""),
                                    "rating_avg": p.get("rating_avg", 0),
                                    "slug": p.get("slug", ""),
                                    "category_name": p.get("category_name", ""),
                                    "stock_quantity": p.get("stock_quantity", 0),
                                    "discount_percent": p.get("discount_percent", 0),
                                    "compare_price": p.get("compare_price", 0),
                                })
                        except Exception:
                            pass
        except Exception as e:
            logger.warning(f"Failed to enrich products: {e}")

    # 4. Fallback: if no model/graph recs, return popular products
    if not enriched and not recommended:
        import httpx
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{settings.PRODUCT_SERVICE_URL}/api/products/featured/"
                )
                if resp.status_code == 200:
                    data = resp.json()
                    prods = data if isinstance(data, list) else data.get("results", [])
                    for p in prods[:10]:
                        enriched.append({
                            "id": str(p["id"]),
                            "name": p.get("name", ""),
                            "price": p.get("price", 0),
                            "image_url": p.get("image_url", ""),
                            "brand": p.get("brand", ""),
                            "rating_avg": p.get("rating_avg", 0),
                            "slug": p.get("slug", ""),
                            "category_name": p.get("category_name", ""),
                            "stock_quantity": p.get("stock_quantity", 0),
                            "discount_percent": p.get("discount_percent", 0),
                            "compare_price": p.get("compare_price", 0),
                        })
                    source = "popular"
        except Exception:
            pass

    return {
        "user_id": user_id,
        "recommended_products": enriched,
        "predicted_action": predicted_action,
        "source": source,
    }


# ─── Chat (RAG) ────────────────────────────────
@router.post("/api/ai-new/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Chat with RAG system."""
    if not _chat_engine or not _chat_engine.ready:
        return ChatResponse(reply="Hệ thống AI đang khởi tạo, vui lòng thử lại sau.", session_id=req.session_id)

    reply = _chat_engine.chat(
        user_message=req.message,
        user_id=req.user_id,
        product_id=req.product_id,
    )
    return ChatResponse(reply=reply, session_id=req.session_id)


# ─── Training ──────────────────────────────────
@router.post("/api/ai-new/train")
async def train_model(req: TrainRequest, background_tasks: BackgroundTasks):
    """Trigger model training."""
    if _trainer and _trainer.training_status == "training":
        return {"status": "already_training"}

    background_tasks.add_task(_run_training)
    return {"status": "training_started"}


async def _run_training():
    if _trainer:
        try:
            _trainer.train_all()
        except Exception as e:
            logger.error(f"Training failed: {e}")


@router.get("/api/ai-new/train/status")
async def train_status():
    if not _trainer:
        return {"status": "not_initialized"}
    result = {
        "status": _trainer.training_status,
        "best_model": _trainer.best_model_name,
    }
    if _trainer.training_status == "completed":
        result["results"] = {
            k: {
                "accuracy": v["metrics"]["action_accuracy"],
                "f1": v["metrics"]["action_f1"],
            } for k, v in _trainer.results.items()
        }
    return result


# ─── KB Graph ──────────────────────────────────
@router.get("/api/ai-new/kb/status")
async def kb_status():
    if not _kb_graph:
        return {"status": "not_initialized"}
    return {"status": "ready" if _kb_graph.ready else "not_built"}


@router.post("/api/ai-new/kb/build")
async def kb_build(background_tasks: BackgroundTasks):
    """Trigger KB graph rebuild."""
    background_tasks.add_task(_build_kb)
    return {"status": "building"}


async def _build_kb():
    if _kb_graph:
        try:
            await _kb_graph.build_graph()
        except Exception as e:
            logger.error(f"KB build failed: {e}")


# ─── Data Generation ───────────────────────────
@router.post("/api/ai-new/generate-data")
async def generate_data(background_tasks: BackgroundTasks):
    """Generate synthetic behavior data."""
    from app.data_generator import generate_behavior_data
    background_tasks.add_task(generate_behavior_data)
    return {"status": "generating"}


# ─── Plots & Reports ──────────────────────────
@router.get("/api/ai-new/plots")
async def list_plots():
    """List all available plot files."""
    plots_path = Path(settings.PLOTS_DIR)
    if not plots_path.exists():
        return {"plots": []}
    files = sorted([f.name for f in plots_path.glob("*.png")])
    return {
        "plots": files,
        "urls": [f"/api/ai-new/plots/{f}" for f in files],
        "total": len(files),
    }


@router.get("/api/ai-new/plots/{filename}")
async def get_plot(filename: str):
    path = Path(settings.PLOTS_DIR) / filename
    if not path.exists():
        raise HTTPException(404, "Plot not found")
    return FileResponse(str(path), media_type="image/png")


@router.get("/api/ai-new/report")
async def get_report():
    path = Path(settings.DATA_DIR) / "model_evaluation_report.md"
    if not path.exists():
        raise HTTPException(404, "Report not generated yet. Train models first.")
    return FileResponse(str(path), media_type="text/markdown")


# ─── Behavior Data Stats ──────────────────────
@router.get("/api/ai-new/stats")
async def get_stats(db: Session = Depends(get_db)):
    from sqlalchemy import func
    total = db.query(func.count(UserBehaviorData.id)).scalar()
    users = db.query(func.count(func.distinct(UserBehaviorData.user_id))).scalar()
    actions = db.query(
        UserBehaviorData.action, func.count(UserBehaviorData.id)
    ).group_by(UserBehaviorData.action).all()

    return {
        "total_records": total,
        "unique_users": users,
        "action_distribution": {a: c for a, c in actions},
    }
