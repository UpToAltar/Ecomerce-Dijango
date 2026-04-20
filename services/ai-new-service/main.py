"""Main FastAPI application for ai-new-service."""
from __future__ import annotations
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

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
    logger.info("AI New Service started successfully.")
    yield
    logger.info("AI New Service shutting down.")


app = FastAPI(
    title="AI New Service — Behavior Analysis & Recommendation",
    description="RNN/LSTM/BiLSTM + Neo4j KB Graph + RAG Chat",
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

# Mount static files for plots
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount data/plots
plots_dir = Path("/app/data/plots")
plots_dir.mkdir(parents=True, exist_ok=True)

app.include_router(router)


@app.get("/")
async def root():
    return {"service": "ai-new-service", "status": "ok"}
