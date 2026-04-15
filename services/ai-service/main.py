from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.startup import initialize_services

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await initialize_services()
    logger.info("AI Service started successfully.")
    yield
    logger.info("AI Service shutting down.")


app = FastAPI(
    title="AI Service — E-commerce Advisor",
    description="Phân tích hành vi khách hàng + RAG chat tư vấn",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(router)


@app.get("/")
async def root():
    return {"service": "ai-service", "status": "ok", "chat_ui": "/chat"}


@app.get("/chat", response_class=HTMLResponse)
async def chat_ui():
    chat_html = static_dir / "chat.html"
    if chat_html.exists():
        return FileResponse(str(chat_html))
    return HTMLResponse("<h1>Chat UI not found</h1>", status_code=404)
