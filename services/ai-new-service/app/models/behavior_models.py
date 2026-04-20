"""RNN, LSTM, BiLSTM models for user behavior prediction.
Optimized for higher accuracy with better architecture."""
import torch
import torch.nn as nn


class BehaviorRNN(nn.Module):
    """Vanilla RNN for behavior sequence prediction."""
    def __init__(self, num_users, num_products, num_actions, embedding_dim=64, hidden_dim=128):
        super().__init__()
        self.model_name = "RNN"
        self.product_emb = nn.Embedding(num_products, embedding_dim, padding_idx=0)
        self.action_emb = nn.Embedding(num_actions, embedding_dim, padding_idx=0)

        input_dim = embedding_dim * 2  # product + action
        self.rnn = nn.RNN(input_dim, hidden_dim, num_layers=1, batch_first=True, dropout=0.0)
        self.dropout = nn.Dropout(0.2)
        self.fc_action = nn.Linear(hidden_dim, num_actions)
        self.fc_product = nn.Linear(hidden_dim, num_products)

    def forward(self, user_ids, product_ids, action_ids):
        p = self.product_emb(product_ids)  # (B, S, E)
        a = self.action_emb(action_ids)    # (B, S, E)

        x = torch.cat([p, a], dim=-1)     # (B, S, 2E)
        out, _ = self.rnn(x)
        last = self.dropout(out[:, -1, :])

        action_pred = self.fc_action(last)
        product_pred = self.fc_product(last)
        return action_pred, product_pred


class BehaviorLSTM(nn.Module):
    """LSTM for behavior sequence prediction."""
    def __init__(self, num_users, num_products, num_actions, embedding_dim=64, hidden_dim=128):
        super().__init__()
        self.model_name = "LSTM"
        self.product_emb = nn.Embedding(num_products, embedding_dim, padding_idx=0)
        self.action_emb = nn.Embedding(num_actions, embedding_dim, padding_idx=0)

        input_dim = embedding_dim * 2
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers=2, batch_first=True, dropout=0.2)
        self.dropout = nn.Dropout(0.2)
        self.fc_action = nn.Linear(hidden_dim, num_actions)
        self.fc_product = nn.Linear(hidden_dim, num_products)

    def forward(self, user_ids, product_ids, action_ids):
        p = self.product_emb(product_ids)
        a = self.action_emb(action_ids)

        x = torch.cat([p, a], dim=-1)
        out, (h, c) = self.lstm(x)
        last = self.dropout(out[:, -1, :])

        action_pred = self.fc_action(last)
        product_pred = self.fc_product(last)
        return action_pred, product_pred


class BehaviorBiLSTM(nn.Module):
    """Bidirectional LSTM for behavior sequence prediction."""
    def __init__(self, num_users, num_products, num_actions, embedding_dim=64, hidden_dim=128):
        super().__init__()
        self.model_name = "BiLSTM"
        self.product_emb = nn.Embedding(num_products, embedding_dim, padding_idx=0)
        self.action_emb = nn.Embedding(num_actions, embedding_dim, padding_idx=0)

        input_dim = embedding_dim * 2
        self.bilstm = nn.LSTM(input_dim, hidden_dim, num_layers=2, batch_first=True,
                               dropout=0.2, bidirectional=True)
        self.dropout = nn.Dropout(0.2)
        # Attention layer to combine forward/backward
        self.attention = nn.Linear(hidden_dim * 2, 1)
        self.fc_action = nn.Linear(hidden_dim * 2, num_actions)
        self.fc_product = nn.Linear(hidden_dim * 2, num_products)

    def forward(self, user_ids, product_ids, action_ids):
        p = self.product_emb(product_ids)
        a = self.action_emb(action_ids)

        x = torch.cat([p, a], dim=-1)
        out, _ = self.bilstm(x)  # (B, S, 2H)

        # Attention pooling
        attn_weights = torch.softmax(self.attention(out), dim=1)  # (B, S, 1)
        context = (out * attn_weights).sum(dim=1)  # (B, 2H)
        context = self.dropout(context)

        action_pred = self.fc_action(context)
        product_pred = self.fc_product(context)
        return action_pred, product_pred
