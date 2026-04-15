from __future__ import annotations
import logging
import random
import uuid
from typing import Any

import httpx
import numpy as np
import torch
from torch.utils.data import Dataset

from app.config import settings

logger = logging.getLogger(__name__)

USER_PROFILES = [
    {"dien-thoai": 0.4, "laptop": 0.3, "am-thanh": 0.2, "dong-ho": 0.1},
    {"thoi-trang-nu": 0.35, "my-pham": 0.3, "dong-ho": 0.2, "sach": 0.15},
    {"thoi-trang-nam": 0.35, "the-thao": 0.25, "dong-ho": 0.25, "sach": 0.15},
    {"the-thao": 0.4, "dong-ho": 0.25, "do-gia-dung": 0.2, "sach": 0.15},
    {"sach": 0.5, "do-gia-dung": 0.2, "my-pham": 0.15, "am-thanh": 0.15},
    {"my-pham": 0.45, "thoi-trang-nu": 0.3, "dong-ho": 0.15, "sach": 0.1},
    {"am-thanh": 0.5, "dien-thoai": 0.25, "laptop": 0.15, "sach": 0.1},
    {"dong-ho": 0.55, "thoi-trang-nam": 0.2, "am-thanh": 0.15, "sach": 0.1},
    {"dien-thoai": 0.2, "laptop": 0.2, "thoi-trang-nam": 0.12, "thoi-trang-nu": 0.12,
     "do-gia-dung": 0.1, "am-thanh": 0.13, "dong-ho": 0.13},
    {"laptop": 0.3, "am-thanh": 0.2, "dong-ho": 0.2, "do-gia-dung": 0.15, "sach": 0.15},
]


async def fetch_behavior_data() -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20) as client:
        try:
            resp = await client.get(
                f"{settings.PRODUCT_SERVICE_URL}/api/analytics/behavior/",
                params={"limit": 10000},
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning(f"Could not fetch behavior data: {e}")
    return {"views": [], "clicks": [], "searches": []}


def generate_synthetic_interactions(
    products: list[dict[str, Any]],
    n_users: int = 500,
) -> tuple[list[tuple[int, int, float]], list[tuple[int, list[int]]]]:
    cat_products: dict[str, list[int]] = {}
    for idx, p in enumerate(products):
        cat = (
            p.get("category_slug")
            or (p.get("category") or {}).get("slug", "other")
        )
        cat_products.setdefault(cat, []).append(idx)

    interactions: list[tuple[int, int, float]] = []
    sequences: list[tuple[int, list[int]]] = []
    all_item_idxs = list(range(len(products)))

    for user_idx in range(n_users):
        profile = USER_PROFILES[user_idx % len(USER_PROFILES)]
        valid_cats = {c: w for c, w in profile.items() if c in cat_products and cat_products[c]}
        if not valid_cats:
            continue

        n_interactions = random.randint(8, 25)
        cats = list(valid_cats.keys())
        weights = list(valid_cats.values())
        pos_items = set()

        for _ in range(n_interactions):
            cat = random.choices(cats, weights=weights, k=1)[0]
            item_idx = random.choice(cat_products[cat])
            pos_items.add(item_idx)
            weight = random.uniform(0.7, 1.0)
            interactions.append((user_idx, item_idx, weight))

        neg_pool = [i for i in all_item_idxs if i not in pos_items]
        n_neg = min(len(pos_items), len(neg_pool))
        for item_idx in random.sample(neg_pool, n_neg):
            interactions.append((user_idx, item_idx, 0.0))

        pos_list = list(pos_items)
        random.shuffle(pos_list)
        if len(pos_list) >= 3:
            sequences.append((user_idx, pos_list))

    return interactions, sequences


def build_from_real_data(
    behavior: dict[str, Any],
    products: list[dict[str, Any]],
) -> tuple[list[tuple[int, int, float]], list[tuple[int, list[int]]]]:
    product_id_to_idx: dict[str, int] = {str(p["id"]): i for i, p in enumerate(products)}
    user_ids: list[str] = []
    user_id_map: dict[str, int] = {}

    def get_user_idx(uid: str) -> int:
        if uid not in user_id_map:
            user_id_map[uid] = len(user_ids)
            user_ids.append(uid)
        return user_id_map[uid]

    user_items: dict[int, list[int]] = {}
    interactions: list[tuple[int, int, float]] = []

    for event in behavior.get("views", []):
        uid = str(event.get("user_id") or "")
        pid = str(event.get("product_id") or "")
        if not uid or pid not in product_id_to_idx:
            continue
        u = get_user_idx(uid)
        i = product_id_to_idx[pid]
        user_items.setdefault(u, []).append(i)
        interactions.append((u, i, 0.7))

    for event in behavior.get("clicks", []):
        uid = str(event.get("user_id") or "")
        pid = str(event.get("product_id") or "")
        if not uid or pid not in product_id_to_idx:
            continue
        u = get_user_idx(uid)
        i = product_id_to_idx[pid]
        if u not in user_items:
            user_items[u] = []
        if i not in user_items[u]:
            user_items[u].append(i)
        interactions.append((u, i, 1.0))

    all_items = list(range(len(products)))
    for u, pos_list in user_items.items():
        pos_set = set(pos_list)
        neg_pool = [i for i in all_items if i not in pos_set]
        for i in random.sample(neg_pool, min(len(pos_list), len(neg_pool))):
            interactions.append((u, i, 0.0))

    sequences = [
        (u, items) for u, items in user_items.items() if len(items) >= 3
    ]

    logger.info(f"Built {len(interactions)} interactions from {len(user_id_map)} real users.")
    return interactions, sequences


class InteractionDataset(Dataset):
    def __init__(self, interactions: list[tuple[int, int, float]]) -> None:
        self.user_ids = torch.tensor([x[0] for x in interactions], dtype=torch.long)
        self.item_ids = torch.tensor([x[1] for x in interactions], dtype=torch.long)
        self.labels = torch.tensor([x[2] for x in interactions], dtype=torch.float)

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        return self.user_ids[idx], self.item_ids[idx], self.labels[idx]


class SequenceDataset(Dataset):
    def __init__(
        self,
        sequences: list[tuple[int, list[int]]],
        seq_len: int = 10,
        n_items: int = 0,
    ) -> None:
        self.samples: list[tuple[torch.Tensor, torch.Tensor]] = []
        for _, item_list in sequences:
            for j in range(1, len(item_list)):
                start = max(0, j - seq_len)
                seq = item_list[start:j]
                target = item_list[j]
                if len(seq) < seq_len:
                    seq = [0] * (seq_len - len(seq)) + seq
                self.samples.append((
                    torch.tensor(seq, dtype=torch.long),
                    torch.tensor(target, dtype=torch.long),
                ))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        return self.samples[idx]
