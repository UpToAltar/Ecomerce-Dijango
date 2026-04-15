from __future__ import annotations
import json
from pathlib import Path

import torch
import torch.nn as nn


class NCFModel(nn.Module):
    """Neural Collaborative Filtering: GMF + MLP fusion for user-item interaction prediction."""

    def __init__(self, n_users: int, n_items: int, emb_dim: int = 64) -> None:
        super().__init__()
        self.n_users = n_users
        self.n_items = n_items

        # GMF pathway
        self.user_emb_gmf = nn.Embedding(n_users + 2, emb_dim)
        self.item_emb_gmf = nn.Embedding(n_items + 2, emb_dim)

        # MLP pathway
        self.user_emb_mlp = nn.Embedding(n_users + 2, emb_dim)
        self.item_emb_mlp = nn.Embedding(n_items + 2, emb_dim)

        self.mlp = nn.Sequential(
            nn.Linear(2 * emb_dim, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
        )

        self.output_layer = nn.Linear(emb_dim + 32, 1)
        self._init_weights()

    def _init_weights(self) -> None:
        nn.init.normal_(self.user_emb_gmf.weight, std=0.01)
        nn.init.normal_(self.item_emb_gmf.weight, std=0.01)
        nn.init.normal_(self.user_emb_mlp.weight, std=0.01)
        nn.init.normal_(self.item_emb_mlp.weight, std=0.01)

    def forward(self, user_ids: torch.Tensor, item_ids: torch.Tensor) -> torch.Tensor:
        u_gmf = self.user_emb_gmf(user_ids)
        i_gmf = self.item_emb_gmf(item_ids)
        gmf_out = u_gmf * i_gmf

        u_mlp = self.user_emb_mlp(user_ids)
        i_mlp = self.item_emb_mlp(item_ids)
        mlp_out = self.mlp(torch.cat([u_mlp, i_mlp], dim=-1))

        combined = torch.cat([gmf_out, mlp_out], dim=-1)
        return torch.sigmoid(self.output_layer(combined)).squeeze(-1)


class SequenceModel(nn.Module):
    """LSTM-based session recommendation model for next-item prediction."""

    def __init__(self, n_items: int, emb_dim: int = 128, hidden_dim: int = 256) -> None:
        super().__init__()
        self.n_items = n_items

        self.item_emb = nn.Embedding(n_items + 2, emb_dim, padding_idx=0)
        self.lstm = nn.LSTM(
            emb_dim, hidden_dim,
            num_layers=2, batch_first=True,
            dropout=0.3, bidirectional=False,
        )
        self.attention = nn.Linear(hidden_dim, 1)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 256),
            nn.LayerNorm(256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, n_items + 2),
        )

    def forward(self, seq: torch.Tensor) -> torch.Tensor:
        emb = self.item_emb(seq)
        lstm_out, _ = self.lstm(emb)

        attn_weights = torch.softmax(self.attention(lstm_out), dim=1)
        context = (attn_weights * lstm_out).sum(dim=1)

        return self.fc(context)


class ModelRegistry:
    """Handles saving/loading models and vocabulary mappings."""

    def __init__(self, model_dir: str) -> None:
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        ncf: NCFModel,
        seq: SequenceModel,
        user_map: dict[str, int],
        item_map: dict[str, int],
        metrics: dict,
    ) -> None:
        torch.save(ncf.state_dict(), self.model_dir / 'ncf.pt')
        torch.save(seq.state_dict(), self.model_dir / 'seq.pt')

        meta = {
            'n_users': ncf.n_users,
            'n_items': ncf.n_items,
            'seq_n_items': seq.n_items,
            'user_map': user_map,
            'item_map': item_map,
            'metrics': metrics,
        }
        with open(self.model_dir / 'meta.json', 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    def load(self) -> tuple[NCFModel, SequenceModel, dict[str, int], dict[str, int]] | None:
        meta_path = self.model_dir / 'meta.json'
        if not meta_path.exists():
            return None

        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)

        ncf = NCFModel(meta['n_users'], meta['n_items'])
        ncf.load_state_dict(torch.load(self.model_dir / 'ncf.pt', map_location='cpu'))
        ncf.eval()

        seq = SequenceModel(meta['seq_n_items'])
        seq.load_state_dict(torch.load(self.model_dir / 'seq.pt', map_location='cpu'))
        seq.eval()

        return ncf, seq, meta['user_map'], meta['item_map']

    def exists(self) -> bool:
        return (self.model_dir / 'meta.json').exists()
