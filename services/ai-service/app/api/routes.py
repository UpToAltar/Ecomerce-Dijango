from __future__ import annotations
import logging
import uuid

import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks

from app.config import settings

from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    KBStatusResponse,
    RecommendResponse,
    TrackBehaviorRequest,
    TrainRequest,
    TrainResponse,
)
from app.state import app_state

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Health ──────────────────────────────────────────────────────────────────

def _health_payload() -> dict:
    return {
        "status": "ok",
        "service": "ai-service",
        "kb_ready": app_state.is_kb_ready,
        "model_ready": app_state.is_model_ready,
        "training_status": app_state.training_status,
        "total_products": app_state.total_products,
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return _health_payload()


@router.get("/api/ai/health", response_model=HealthResponse)
async def health_check_gateway():
    return _health_payload()


# ─── Chat (HTTP) ─────────────────────────────────────────────────────────────

@router.post("/api/ai/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    if app_state.chat_engine is None:
        raise HTTPException(status_code=503, detail="Chat engine not initialized yet.")

    if not req.session_id or req.session_id == "default":
        session_id = str(uuid.uuid4())
    else:
        session_id = req.session_id

    result = await app_state.chat_engine.chat(
        message=req.message,
        session_id=session_id,
        user_id=req.user_id,
    )
    return ChatResponse(**result)


# ─── Chat (WebSocket) ─────────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self) -> None:
        self._active: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._active[session_id] = ws

    def disconnect(self, session_id: str) -> None:
        self._active.pop(session_id, None)

    async def send(self, session_id: str, data: dict) -> None:
        ws = self._active.get(session_id)
        if ws:
            await ws.send_json(data)


manager = ConnectionManager()


@router.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str, user_id: str | None = None):
    await manager.connect(session_id, websocket)
    try:
        await websocket.send_json({
            "type": "connected",
            "message": (
                "Xin chào! Tôi là trợ lý tư vấn AI của cửa hàng. "
                "Tôi có thể giúp bạn tìm sản phẩm, so sánh và tư vấn mua sắm. Bạn cần gì hôm nay?"
            ),
            "session_id": session_id,
        })

        while True:
            data = await websocket.receive_json()
            message = data.get("message", "").strip()
            uid = data.get("user_id") or user_id

            if not message:
                continue

            await websocket.send_json({"type": "typing", "session_id": session_id})

            if app_state.chat_engine is None:
                await websocket.send_json({
                    "type": "message",
                    "message": "⚙️ Hệ thống đang khởi tạo, vui lòng thử lại sau.",
                    "intent": "system",
                    "products": [],
                    "session_id": session_id,
                })
                continue

            result = await app_state.chat_engine.chat(
                message=message,
                session_id=session_id,
                user_id=uid,
            )
            await websocket.send_json({"type": "message", **result})

    except WebSocketDisconnect:
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error [{session_id}]: {e}")
        manager.disconnect(session_id)


# ─── Track Behavior ───────────────────────────────────────────────────────────

async def _persist_to_analytics(user_id: str, product_id: str, event_type: str) -> None:
    """Fire-and-forget: persist behavior to product-service analytics DB."""
    base = settings.PRODUCT_SERVICE_URL
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            if event_type == "view_detail":
                await client.post(
                    f"{base}/api/analytics/view/",
                    json={
                        "product": product_id,
                        "user_id": user_id,
                        "session_id": "ai-track",
                        "source": "ai_widget",
                    },
                )
            else:
                await client.post(
                    f"{base}/api/analytics/event/",
                    json={
                        "user_id": user_id,
                        "session_id": "ai-track",
                        "event_type": event_type,
                        "product_id": product_id,
                    },
                )
    except Exception as e:
        logger.debug(f"[analytics] persist failed: {e}")


@router.post("/api/ai/track")
async def track_behavior(req: TrackBehaviorRequest, background_tasks: BackgroundTasks):
    if app_state.chat_engine:
        await app_state.chat_engine.track_behavior(req.user_id, [req.product_id])
    background_tasks.add_task(_persist_to_analytics, req.user_id, req.product_id, req.event_type)
    return {"status": "ok"}


# ─── Recommendations ─────────────────────────────────────────────────────────

def _safe_float(v, default: float = 0.0) -> float:
    try:
        return float(v) if v not in (None, "", "None") else default
    except (ValueError, TypeError):
        return default


async def _content_based_recommend(
    behavior: list[str],
    top_k: int,
    vs,
    idx_to_product: dict,
) -> tuple[list[dict], str]:
    """Find products similar to recently viewed ones using ChromaDB similarity search."""
    seen_ids = set(behavior)

    # Resolve product names and categories from recent behavior
    viewed: list[dict] = []
    for pid in behavior[-6:]:
        for p in idx_to_product.values():
            if str(p.get("id", "")) == pid:
                viewed.append(p)
                break

    if not viewed:
        return [], "popularity"

    # Build a rich query from viewed products
    parts: list[str] = []
    cat_counts: dict[str, int] = {}
    for p in viewed:
        name = p.get("name") or ""
        cat = p.get("category_slug") or p.get("category_name") or ""
        if name:
            parts.append(name)
        if cat:
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

    # Weight the dominant category in the query
    top_cats = sorted(cat_counts, key=lambda c: cat_counts[c], reverse=True)[:2]
    query = " ".join(parts[:3]) + (" " + " ".join(top_cats) if top_cats else "")

    # Category filter: use most-viewed category if ≥60% dominance
    cat_filter = None
    if top_cats and cat_counts[top_cats[0]] / len(viewed) >= 0.5:
        cat_filter = top_cats[0]

    results = vs.search_products(
        query, n_results=top_k * 3,
        category_slug=cat_filter,
    )

    # Filter out already-viewed, deduplicate
    seen_names: set[str] = set()
    filtered: list[dict] = []
    for r in results:
        meta = r["metadata"]
        pid = str(meta.get("id", ""))
        name = meta.get("name", "")
        if pid not in seen_ids and name not in seen_names:
            filtered.append(meta)
            seen_names.add(name)
        if len(filtered) >= top_k:
            break

    reason = f"content_based:{top_cats[0]}" if top_cats else "content_based"
    return filtered, reason


@router.get("/api/ai/recommend/{user_id}", response_model=RecommendResponse)
async def get_recommendations(user_id: str, top_k: int = 8):
    if app_state.trainer is None:
        raise HTTPException(status_code=503, detail="Model not ready yet.")

    behavior: list[str] = []
    if app_state.chat_engine:
        behavior = await app_state.chat_engine.get_user_behavior(user_id)

    products: list[dict] = []
    source = "popularity"

    # ── Tier 1: LSTM sequence model (best personalization) ──────────────────
    if behavior and app_state.is_model_ready:
        indices = app_state.trainer.recommend_for_sequence(behavior, top_k=top_k)
        products = [
            app_state.trainer.idx_to_product[i]
            for i in indices
            if i in app_state.trainer.idx_to_product
        ]
        # Fall through if sequence model returned too few results
        if len(products) >= max(2, top_k // 2):
            source = "sequence_model"

    # ── Tier 2: Content-based via ChromaDB (no model needed) ────────────────
    if (not products or source == "popularity") and behavior and app_state.is_kb_ready and app_state.chat_engine:
        products, source = await _content_based_recommend(
            behavior, top_k,
            app_state.chat_engine.vs,
            app_state.trainer.idx_to_product,
        )

    # ── Tier 3: Category-affinity popularity (behavior exists, no KB/model) ─
    if (not products or source == "popularity") and behavior and app_state.trainer.idx_to_product:
        all_products = list(app_state.trainer.idx_to_product.values())
        # Identify dominant categories in behavior
        cat_counts: dict[str, int] = {}
        for pid in behavior:
            for p in app_state.trainer.idx_to_product.values():
                if str(p.get("id", "")) == pid:
                    cat = p.get("category_slug") or ""
                    if cat:
                        cat_counts[cat] = cat_counts.get(cat, 0) + 1
                    break
        seen_ids = set(behavior)
        if cat_counts:
            top_cat = max(cat_counts, key=lambda c: cat_counts[c])
            cat_products = [p for p in all_products if p.get("category_slug") == top_cat and str(p.get("id", "")) not in seen_ids]
            products = app_state.trainer.recommend_popular(cat_products, top_k=top_k)
            source = f"category:{top_cat}"
        if not products:
            products = app_state.trainer.recommend_popular(all_products, top_k=top_k)
            source = "popularity"

    # ── Tier 4: Pure popularity ──────────────────────────────────────────────
    if not products:
        all_products = list(app_state.trainer.idx_to_product.values()) if app_state.trainer.idx_to_product else []
        products = app_state.trainer.recommend_popular(all_products, top_k=top_k)
        source = "popularity"

    # ── Enrich from ChromaDB for consistent metadata ─────────────────────────
    if app_state.is_kb_ready and app_state.chat_engine and source not in ("content_based", ) and not source.startswith("content_based"):
        enriched: list[dict] = []
        vs = app_state.chat_engine.vs
        seen_enriched: set[str] = set()
        for p in products[:top_k]:
            pid = str(p.get("id", ""))
            retrieved = vs.search_products(p.get("name", ""), n_results=1)
            if retrieved and str(retrieved[0]["metadata"].get("id", "")) not in seen_enriched:
                meta = retrieved[0]["metadata"]
                enriched.append(meta)
                seen_enriched.add(str(meta.get("id", "")))
            elif pid not in seen_enriched:
                enriched.append(p)
                seen_enriched.add(pid)
        products = enriched

    return RecommendResponse(user_id=user_id, products=products[:top_k], source=source)


# ─── Knowledge Base ───────────────────────────────────────────────────────────

@router.get("/api/ai/kb/status", response_model=KBStatusResponse)
async def kb_status():
    doc_count = 0
    if app_state.chat_engine:
        doc_count = app_state.chat_engine.vs.count()
    return KBStatusResponse(
        is_ready=app_state.is_kb_ready,
        document_count=doc_count,
        total_products=app_state.total_products,
    )


@router.post("/api/ai/kb/build")
async def rebuild_kb(background_tasks: BackgroundTasks):
    from app.startup import run_startup_pipeline
    background_tasks.add_task(run_startup_pipeline, force_rebuild=True)
    return {"status": "started", "message": "Knowledge base rebuild started in background."}


# ─── Model Training ───────────────────────────────────────────────────────────

@router.post("/api/ai/train", response_model=TrainResponse)
async def trigger_training(req: TrainRequest, background_tasks: BackgroundTasks):
    if app_state.training_status == "running":
        return TrainResponse(status="running", message="Training already in progress.")

    from app.startup import run_training_only
    background_tasks.add_task(run_training_only)
    return TrainResponse(status="started", message="Training started in background.")


@router.get("/api/ai/train/status")
async def training_status():
    return {
        "status": app_state.training_status,
        "progress": app_state.training_progress,
        "model_ready": app_state.is_model_ready,
        "behaviors_used": app_state.total_behaviors,
    }
