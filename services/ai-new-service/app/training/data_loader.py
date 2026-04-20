"""Data loader: convert DB records to learnable sequences.
Key improvement: build sequences that have CLEAR action transition patterns."""
import logging
from collections import defaultdict, Counter
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from sqlalchemy import text

from app.database import SessionLocal
from app.config import settings

logger = logging.getLogger(__name__)

ACTIONS = ["view", "click", "add_to_cart", "purchase", "search", "wishlist", "remove_from_cart", "review"]
ACTION_TO_IDX = {a: i for i, a in enumerate(ACTIONS)}


class BehaviorSequenceDataset(Dataset):
    """Dataset of user behavior sequences."""

    def __init__(self, sequences, labels_action, labels_product):
        self.sequences = sequences
        self.labels_action = labels_action
        self.labels_product = labels_product

    def __len__(self):
        return len(self.sequences)

    def __getitem__(self, idx):
        user_ids, product_ids, action_ids = self.sequences[idx]
        return (
            torch.tensor(user_ids, dtype=torch.long),
            torch.tensor(product_ids, dtype=torch.long),
            torch.tensor(action_ids, dtype=torch.long),
            torch.tensor(self.labels_action[idx], dtype=torch.long),
            torch.tensor(self.labels_product[idx], dtype=torch.long),
        )


def load_behavior_data():
    """Load all behavior records from DB, build sequences with clear patterns."""
    db = SessionLocal()
    try:
        rows = db.execute(text(
            "SELECT user_id, product_id, action, timestamp "
            "FROM user_behavior_data ORDER BY user_id, timestamp"
        )).fetchall()

        if not rows:
            logger.warning("No behavior data found in DB.")
            return None

        logger.info(f"Loaded {len(rows)} behavior records from DB.")

        # Build user → sorted events
        user_events = defaultdict(list)
        all_users = set()
        all_products = set()

        for row in rows:
            uid, pid, action, ts = row
            all_users.add(uid)
            all_products.add(pid)
            user_events[uid].append((pid, action, ts))

        # Create mappings (start from 1, 0 is padding)
        user_list = sorted(all_users)
        product_list = sorted(all_products)
        user_to_idx = {u: i + 1 for i, u in enumerate(user_list)}
        product_to_idx = {p: i + 1 for i, p in enumerate(product_list)}

        # Build sequences
        seq_len = settings.SEQ_LENGTH
        sequences = []
        labels_action = []
        labels_product = []

        for uid, events in user_events.items():
            events.sort(key=lambda x: x[2])  # sort by timestamp
            if len(events) < seq_len + 1:
                continue

            user_idx = user_to_idx[uid]

            # Sliding window sequences
            for i in range(len(events) - seq_len):
                seq = events[i:i + seq_len]
                target = events[i + seq_len]

                user_ids = [user_idx] * seq_len
                product_ids = [product_to_idx.get(e[0], 0) for e in seq]
                action_ids = [ACTION_TO_IDX.get(e[1], 0) for e in seq]

                sequences.append((user_ids, product_ids, action_ids))
                labels_action.append(ACTION_TO_IDX.get(target[1], 0))
                labels_product.append(product_to_idx.get(target[0], 0))

        # Log class distribution
        action_dist = Counter(labels_action)
        logger.info(f"Built {len(sequences)} sequences from {len(user_list)} users, {len(product_list)} products")
        logger.info(f"Action distribution: {dict(action_dist)}")
        for idx, name in enumerate(ACTIONS):
            logger.info(f"  {name}: {action_dist.get(idx, 0)} ({action_dist.get(idx, 0)/len(labels_action)*100:.1f}%)")

        # Compute class weights for balanced training
        total_samples = len(labels_action)
        class_weights = []
        for i in range(len(ACTIONS)):
            count = action_dist.get(i, 1)
            weight = total_samples / (len(ACTIONS) * count) if count > 0 else 1.0
            class_weights.append(min(weight, 5.0))  # cap at 5x

        logger.info(f"Class weights: {[f'{w:.2f}' for w in class_weights]}")

        return {
            "sequences": sequences,
            "labels_action": labels_action,
            "labels_product": labels_product,
            "num_users": len(user_list) + 1,  # +1 for padding idx 0
            "num_products": len(product_list) + 1,
            "num_actions": len(ACTIONS),
            "user_to_idx": user_to_idx,
            "product_to_idx": product_to_idx,
            "idx_to_user": {v: k for k, v in user_to_idx.items()},
            "idx_to_product": {v: k for k, v in product_to_idx.items()},
            "action_names": ACTIONS,
            "class_weights": class_weights,
        }

    finally:
        db.close()


def create_dataloaders(data, batch_size=64, train_split=0.8):
    """Split data into train/test and create DataLoaders."""
    n = len(data["sequences"])
    indices = np.random.permutation(n)
    split = int(n * train_split)

    train_idx = indices[:split]
    test_idx = indices[split:]

    train_ds = BehaviorSequenceDataset(
        [data["sequences"][i] for i in train_idx],
        [data["labels_action"][i] for i in train_idx],
        [data["labels_product"][i] for i in train_idx],
    )
    test_ds = BehaviorSequenceDataset(
        [data["sequences"][i] for i in test_idx],
        [data["labels_action"][i] for i in test_idx],
        [data["labels_product"][i] for i in test_idx],
    )

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=False)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    logger.info(f"Train: {len(train_ds)} samples, Test: {len(test_ds)} samples")
    return train_loader, test_loader
