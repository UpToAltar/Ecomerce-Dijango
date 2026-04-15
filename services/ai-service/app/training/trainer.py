from __future__ import annotations
import asyncio
import logging
from typing import Any

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from app.config import settings
from app.models.behavior_model import NCFModel, SequenceModel, ModelRegistry
from app.training.data_loader import (
    InteractionDataset,
    SequenceDataset,
    build_from_real_data,
    fetch_behavior_data,
    generate_synthetic_interactions,
)
from app.state import app_state

logger = logging.getLogger(__name__)


class BehaviorTrainer:
    def __init__(self) -> None:
        self.registry = ModelRegistry(settings.MODEL_DIR)
        self.ncf: NCFModel | None = None
        self.seq: SequenceModel | None = None
        self.user_map: dict[str, int] = {}
        self.item_map: dict[str, int] = {}
        self.idx_to_product: dict[int, dict[str, Any]] = {}

    def load_if_exists(self) -> bool:
        result = self.registry.load()
        if result is None:
            return False
        self.ncf, self.seq, self.user_map, self.item_map = result
        logger.info("Loaded existing behavior models.")
        return True

    async def train(self, products: list[dict[str, Any]]) -> dict[str, float]:
        app_state.training_status = "running"
        app_state.training_progress = "Fetching behavior data..."

        behavior = await fetch_behavior_data()
        total_events = behavior.get("total_views", 0) + behavior.get("total_clicks", 0)
        app_state.total_behaviors = total_events

        self.idx_to_product = {i: p for i, p in enumerate(products)}
        item_map: dict[str, int] = {str(p["id"]): i for i, p in enumerate(products)}

        if total_events >= 500:
            logger.info("Using real behavior data for training.")
            interactions, sequences = build_from_real_data(behavior, products)
        else:
            logger.info("Insufficient real data; using synthetic training data.")
            interactions, sequences = generate_synthetic_interactions(products)

        app_state.training_progress = f"Training on {len(interactions)} interactions..."
        logger.info(f"Training data: {len(interactions)} interactions, {len(sequences)} sequences.")

        n_users = max(u for u, _, _ in interactions) + 1
        n_items = len(products)

        user_set = {u for u, _, _ in interactions}
        user_map = {str(i): i for i in user_set}

        ncf_metrics = await asyncio.get_event_loop().run_in_executor(
            None,
            self._train_ncf,
            interactions, n_users, n_items,
        )
        app_state.training_progress = f"NCF done (loss={ncf_metrics['final_loss']:.4f}). Training sequence model..."

        seq_metrics = await asyncio.get_event_loop().run_in_executor(
            None,
            self._train_seq,
            sequences, n_items,
        )
        app_state.training_progress = "Saving models..."

        metrics = {**ncf_metrics, **{f"seq_{k}": v for k, v in seq_metrics.items()}}
        self.registry.save(self.ncf, self.seq, user_map, item_map, metrics)  # type: ignore[arg-type]
        self.user_map = user_map
        self.item_map = item_map

        app_state.training_status = "completed"
        app_state.training_progress = f"Training completed: NCF loss={ncf_metrics['final_loss']:.4f}"
        app_state.is_model_ready = True
        logger.info(f"Training done. Metrics: {metrics}")
        return metrics

    def _train_ncf(
        self,
        interactions: list[tuple[int, int, float]],
        n_users: int,
        n_items: int,
    ) -> dict[str, float]:
        self.ncf = NCFModel(n_users, n_items, emb_dim=settings.NCF_EMB_DIM)
        optimizer = torch.optim.Adam(self.ncf.parameters(), lr=settings.LEARNING_RATE, weight_decay=1e-5)
        criterion = nn.BCELoss()

        dataset = InteractionDataset(interactions)
        loader = DataLoader(dataset, batch_size=settings.BATCH_SIZE, shuffle=True, num_workers=0)

        self.ncf.train()
        history: list[float] = []

        for epoch in range(settings.TRAIN_EPOCHS):
            epoch_loss = 0.0
            for user_ids, item_ids, labels in loader:
                optimizer.zero_grad()
                preds = self.ncf(user_ids, item_ids)
                loss = criterion(preds, labels)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.ncf.parameters(), 1.0)
                optimizer.step()
                epoch_loss += loss.item()
            avg = epoch_loss / max(len(loader), 1)
            history.append(avg)
            if (epoch + 1) % 5 == 0:
                logger.info(f"  NCF Epoch {epoch + 1}/{settings.TRAIN_EPOCHS} loss={avg:.4f}")

        self.ncf.eval()
        return {"final_loss": history[-1], "initial_loss": history[0]}

    def _train_seq(
        self,
        sequences: list[tuple[int, list[int]]],
        n_items: int,
    ) -> dict[str, float]:
        self.seq = SequenceModel(n_items, emb_dim=settings.SEQ_EMB_DIM, hidden_dim=settings.LSTM_HIDDEN)
        optimizer = torch.optim.Adam(self.seq.parameters(), lr=settings.LEARNING_RATE, weight_decay=1e-5)
        criterion = nn.CrossEntropyLoss()

        dataset = SequenceDataset(sequences, seq_len=settings.SEQ_LEN, n_items=n_items)
        if len(dataset) == 0:
            logger.warning("No sequences for LSTM training.")
            return {"final_loss": 0.0}

        loader = DataLoader(dataset, batch_size=128, shuffle=True, num_workers=0)
        self.seq.train()
        history: list[float] = []

        for epoch in range(settings.TRAIN_EPOCHS):
            epoch_loss = 0.0
            for seq_batch, target_batch in loader:
                optimizer.zero_grad()
                output = self.seq(seq_batch)
                loss = criterion(output, target_batch)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.seq.parameters(), 1.0)
                optimizer.step()
                epoch_loss += loss.item()
            avg = epoch_loss / max(len(loader), 1)
            history.append(avg)
            if (epoch + 1) % 5 == 0:
                logger.info(f"  SEQ Epoch {epoch + 1}/{settings.TRAIN_EPOCHS} loss={avg:.4f}")

        self.seq.eval()
        return {"final_loss": history[-1]}

    def recommend_for_sequence(
        self,
        recent_product_ids: list[str],
        top_k: int = 10,
    ) -> list[int]:
        if self.seq is None or not recent_product_ids:
            return []

        # Map product IDs → item indices; count how many are actually in item_map
        resolved = [(pid, self.item_map.get(pid, 0)) for pid in recent_product_ids[-settings.SEQ_LEN:]]
        known_count = sum(1 for _, idx in resolved if idx != 0)

        # If less than half of the behavior is known to the model, result would be unreliable
        if known_count < max(1, len(resolved) // 2):
            logger.info(f"Only {known_count}/{len(resolved)} products known to model — skipping LSTM")
            return []

        idxs = [idx for _, idx in resolved]
        padded = [0] * (settings.SEQ_LEN - len(idxs)) + idxs
        seq_tensor = torch.tensor([padded], dtype=torch.long)
        with torch.no_grad():
            logits = self.seq(seq_tensor)[0]

        # Boost scores for items in same category as recently viewed
        seen_cat_idxs: set[int] = set()
        for pid, _ in resolved:
            for idx, p in self.idx_to_product.items():
                if str(p.get("id", "")) == pid:
                    # Collect all items from the same category
                    cat = p.get("category_slug", "")
                    for i2, p2 in self.idx_to_product.items():
                        if p2.get("category_slug", "") == cat:
                            seen_cat_idxs.add(i2)
                    break

        if seen_cat_idxs:
            boost = torch.zeros_like(logits)
            for i in seen_cat_idxs:
                if 0 < i < len(logits):
                    boost[i] = 0.5
            logits = logits + boost

        top_indices = logits.argsort(descending=True).tolist()
        seen = set(idxs)
        seen.discard(0)  # don't exclude padding index
        return [i for i in top_indices if i not in seen and 0 < i < len(self.idx_to_product)][:top_k]

    def recommend_popular(self, products: list[dict[str, Any]], top_k: int = 10) -> list[dict[str, Any]]:
        scored = sorted(
            products,
            key=lambda p: float(p.get("rating_avg") or 0) * 0.4 + float(p.get("sold_count") or 0) / 500 * 0.6,
            reverse=True,
        )
        return scored[:top_k]
