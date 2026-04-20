"""Trainer: train RNN/LSTM/BiLSTM with class-weighted loss, evaluate, compare, select best."""
import logging
import os
import json
import time
from pathlib import Path
from collections import Counter

import numpy as np
import torch
import torch.nn as nn
from torch.optim.lr_scheduler import CosineAnnealingLR
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report,
)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from app.config import settings
from app.models.behavior_models import BehaviorRNN, BehaviorLSTM, BehaviorBiLSTM
from app.training.data_loader import load_behavior_data, create_dataloaders, ACTIONS

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Train and evaluate 3 models, select best."""

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.data = None
        self.models = {}
        self.results = {}
        self.best_model_name = None
        self.best_model = None
        self.data_info = None
        self.training_status = "idle"

    def load_data(self):
        self.data = load_behavior_data()
        if not self.data:
            raise ValueError("No behavior data available for training.")
        self.data_info = {
            "num_users": self.data["num_users"],
            "num_products": self.data["num_products"],
            "num_actions": self.data["num_actions"],
            "num_sequences": len(self.data["sequences"]),
        }
        return self.data_info

    def _build_models(self):
        nu = self.data["num_users"]
        np_ = self.data["num_products"]
        na = self.data["num_actions"]
        ed, hd = settings.EMBEDDING_DIM, settings.HIDDEN_DIM
        return {
            "RNN": BehaviorRNN(nu, np_, na, ed, hd).to(self.device),
            "LSTM": BehaviorLSTM(nu, np_, na, ed, hd).to(self.device),
            "BiLSTM": BehaviorBiLSTM(nu, np_, na, ed, hd).to(self.device),
        }

    def _train_single(self, model, train_loader, test_loader, class_weights, epochs=30):
        optimizer = torch.optim.Adam(model.parameters(), lr=settings.LEARNING_RATE, weight_decay=1e-4)
        scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

        # Class-weighted loss for imbalanced action distribution
        weight_tensor = torch.tensor(class_weights, dtype=torch.float32).to(self.device)
        criterion_action = nn.CrossEntropyLoss(weight=weight_tensor)
        criterion_product = nn.CrossEntropyLoss()

        train_losses = []
        val_losses = []
        train_accs = []
        val_accs = []
        best_val_f1 = 0
        best_state = None
        patience = 8
        no_improve = 0

        for epoch in range(epochs):
            model.train()
            total_loss = 0
            correct = 0
            total = 0

            for user_ids, product_ids, action_ids, lbl_action, lbl_product in train_loader:
                user_ids = user_ids.to(self.device)
                product_ids = product_ids.to(self.device)
                action_ids = action_ids.to(self.device)
                lbl_action = lbl_action.to(self.device)
                lbl_product = lbl_product.to(self.device)

                optimizer.zero_grad()
                action_pred, product_pred = model(user_ids, product_ids, action_ids)

                # Combined loss: focus more on action prediction
                loss = criterion_action(action_pred, lbl_action) + 0.3 * criterion_product(product_pred, lbl_product)
                loss.backward()
                nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                optimizer.step()

                total_loss += loss.item() * user_ids.size(0)
                preds = action_pred.argmax(dim=1)
                correct += (preds == lbl_action).sum().item()
                total += user_ids.size(0)

            scheduler.step()
            train_losses.append(total_loss / total)
            train_accs.append(correct / total)

            # Validation
            model.eval()
            val_loss = 0
            val_correct = 0
            val_total = 0
            all_val_true = []
            all_val_pred = []

            with torch.no_grad():
                for user_ids, product_ids, action_ids, lbl_action, lbl_product in test_loader:
                    user_ids = user_ids.to(self.device)
                    product_ids = product_ids.to(self.device)
                    action_ids = action_ids.to(self.device)
                    lbl_action = lbl_action.to(self.device)
                    lbl_product = lbl_product.to(self.device)

                    action_pred, product_pred = model(user_ids, product_ids, action_ids)
                    loss = criterion_action(action_pred, lbl_action) + 0.3 * criterion_product(product_pred, lbl_product)
                    val_loss += loss.item() * user_ids.size(0)
                    preds = action_pred.argmax(dim=1)
                    val_correct += (preds == lbl_action).sum().item()
                    val_total += user_ids.size(0)
                    all_val_true.extend(lbl_action.cpu().numpy())
                    all_val_pred.extend(preds.cpu().numpy())

            val_losses.append(val_loss / val_total)
            val_accs.append(val_correct / val_total)

            # Early stopping on F1
            val_f1 = f1_score(all_val_true, all_val_pred, average="weighted", zero_division=0)
            if val_f1 > best_val_f1:
                best_val_f1 = val_f1
                best_state = {k: v.clone() for k, v in model.state_dict().items()}
                no_improve = 0
            else:
                no_improve += 1

            if (epoch + 1) % 5 == 0:
                logger.info(f"  [{model.model_name}] Epoch {epoch+1}/{epochs} — "
                            f"Train Loss: {train_losses[-1]:.4f}, Acc: {train_accs[-1]:.4f} | "
                            f"Val Loss: {val_losses[-1]:.4f}, Acc: {val_accs[-1]:.4f}, F1: {val_f1:.4f}")

            if no_improve >= patience:
                logger.info(f"  [{model.model_name}] Early stopping at epoch {epoch+1}")
                break

        # Restore best weights
        if best_state:
            model.load_state_dict(best_state)

        return {
            "train_losses": train_losses,
            "val_losses": val_losses,
            "train_accs": train_accs,
            "val_accs": val_accs,
        }

    def _evaluate(self, model, test_loader):
        model.eval()
        all_true_actions = []
        all_pred_actions = []
        all_true_products = []
        all_pred_products = []

        with torch.no_grad():
            for user_ids, product_ids, action_ids, lbl_action, lbl_product in test_loader:
                user_ids = user_ids.to(self.device)
                product_ids = product_ids.to(self.device)
                action_ids = action_ids.to(self.device)

                action_pred, product_pred = model(user_ids, product_ids, action_ids)
                all_true_actions.extend(lbl_action.numpy())
                all_pred_actions.extend(action_pred.cpu().argmax(dim=1).numpy())
                all_true_products.extend(lbl_product.numpy())
                all_pred_products.extend(product_pred.cpu().argmax(dim=1).numpy())

        action_acc = accuracy_score(all_true_actions, all_pred_actions)
        action_precision = precision_score(all_true_actions, all_pred_actions, average="weighted", zero_division=0)
        action_recall = recall_score(all_true_actions, all_pred_actions, average="weighted", zero_division=0)
        action_f1 = f1_score(all_true_actions, all_pred_actions, average="weighted", zero_division=0)
        action_cm = confusion_matrix(all_true_actions, all_pred_actions)
        action_report = classification_report(all_true_actions, all_pred_actions,
                                               target_names=ACTIONS, zero_division=0, output_dict=True)

        product_acc = accuracy_score(all_true_products, all_pred_products)

        # Top-5 product accuracy
        # (computed separately since argmax is top-1)

        return {
            "action_accuracy": action_acc,
            "action_precision": action_precision,
            "action_recall": action_recall,
            "action_f1": action_f1,
            "action_confusion_matrix": action_cm.tolist(),
            "action_classification_report": action_report,
            "product_accuracy": product_acc,
        }

    def _plot_results(self):
        plots_dir = Path(settings.PLOTS_DIR)
        plots_dir.mkdir(parents=True, exist_ok=True)
        model_names = list(self.results.keys())
        colors = ["#3498db", "#e74c3c", "#2ecc71"]
        color_map = {name: colors[i] for i, name in enumerate(model_names)}
        metrics = ["action_accuracy", "action_precision", "action_recall", "action_f1"]
        metric_labels = ["Accuracy", "Precision", "Recall", "F1-Score"]

        # ═══════════════════════════════════════════
        # A. COMBINED PLOTS (3 models cùng 1 ảnh)
        # ═══════════════════════════════════════════

        # A1. Training Curves — All models
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        for name in model_names:
            r = self.results[name]
            axes[0].plot(r["history"]["train_losses"], label=f"{name} Train")
            axes[0].plot(r["history"]["val_losses"], label=f"{name} Val", linestyle="--")
        axes[0].set_title("Training & Validation Loss", fontsize=14, fontweight="bold")
        axes[0].set_xlabel("Epoch"); axes[0].set_ylabel("Loss")
        axes[0].legend(); axes[0].grid(True, alpha=0.3)
        for name in model_names:
            r = self.results[name]
            axes[1].plot(r["history"]["train_accs"], label=f"{name} Train")
            axes[1].plot(r["history"]["val_accs"], label=f"{name} Val", linestyle="--")
        axes[1].set_title("Training & Validation Accuracy", fontsize=14, fontweight="bold")
        axes[1].set_xlabel("Epoch"); axes[1].set_ylabel("Accuracy")
        axes[1].legend(); axes[1].grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(str(plots_dir / "all_training_curves.png"), dpi=150, bbox_inches="tight")
        plt.close()

        # A2. Metrics Comparison Bar Chart
        fig, ax = plt.subplots(figsize=(12, 6))
        x = np.arange(len(metrics)); width = 0.25
        for i, name in enumerate(model_names):
            vals = [self.results[name]["metrics"][m] for m in metrics]
            bars = ax.bar(x + i * width, vals, width, label=name, color=colors[i], alpha=0.85)
            for bar, val in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f"{val:.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
        ax.set_xlabel("Metrics", fontsize=12); ax.set_ylabel("Score", fontsize=12)
        ax.set_title("Model Comparison: Action Classification Metrics", fontsize=14, fontweight="bold")
        ax.set_xticks(x + width); ax.set_xticklabels(metric_labels)
        ax.legend(); ax.set_ylim(0, 1.15); ax.grid(True, alpha=0.3, axis="y")
        plt.tight_layout()
        plt.savefig(str(plots_dir / "all_metrics_comparison.png"), dpi=150, bbox_inches="tight")
        plt.close()

        # A3. All Confusion Matrices side-by-side
        fig, axes = plt.subplots(1, 3, figsize=(24, 7))
        for i, name in enumerate(model_names):
            cm = np.array(self.results[name]["metrics"]["action_confusion_matrix"])
            sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                       xticklabels=ACTIONS, yticklabels=ACTIONS,
                       ax=axes[i], cbar_kws={"shrink": 0.8})
            axes[i].set_title(f"{name} — Confusion Matrix", fontsize=13, fontweight="bold")
            axes[i].set_xlabel("Predicted"); axes[i].set_ylabel("True")
            axes[i].tick_params(axis="x", rotation=45); axes[i].tick_params(axis="y", rotation=0)
        plt.tight_layout()
        plt.savefig(str(plots_dir / "all_confusion_matrices.png"), dpi=150, bbox_inches="tight")
        plt.close()

        # A4. Per-class F1 Score — All models
        fig, ax = plt.subplots(figsize=(14, 6))
        for i, name in enumerate(model_names):
            report = self.results[name]["metrics"]["action_classification_report"]
            f1s = [report.get(a, {}).get("f1-score", 0) for a in ACTIONS]
            ax.bar(np.arange(len(ACTIONS)) + i * 0.25, f1s, 0.25, label=name, color=colors[i], alpha=0.85)
        ax.set_xlabel("Action Type", fontsize=12); ax.set_ylabel("F1-Score", fontsize=12)
        ax.set_title("Per-Class F1-Score by Model", fontsize=14, fontweight="bold")
        ax.set_xticks(np.arange(len(ACTIONS)) + 0.25)
        ax.set_xticklabels(ACTIONS, rotation=45, ha="right")
        ax.legend(); ax.grid(True, alpha=0.3, axis="y")
        plt.tight_layout()
        plt.savefig(str(plots_dir / "all_per_class_f1.png"), dpi=150, bbox_inches="tight")
        plt.close()

        # A5. Radar Chart — All models
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection="polar"))
        angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
        angles += angles[:1]
        for i, name in enumerate(model_names):
            vals = [self.results[name]["metrics"][m] for m in metrics]
            vals += vals[:1]
            ax.plot(angles, vals, "o-", label=name, color=colors[i], linewidth=2)
            ax.fill(angles, vals, color=colors[i], alpha=0.1)
        ax.set_xticks(angles[:-1]); ax.set_xticklabels(metric_labels)
        ax.set_title("Model Performance Radar Chart", fontsize=14, fontweight="bold", y=1.08)
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0)); ax.set_ylim(0, 1)
        plt.tight_layout()
        plt.savefig(str(plots_dir / "all_radar_chart.png"), dpi=150, bbox_inches="tight")
        plt.close()

        # ═══════════════════════════════════════════
        # B. PER-MODEL PLOTS (mỗi model riêng)
        # ═══════════════════════════════════════════
        for name in model_names:
            r = self.results[name]
            m = r["metrics"]
            h = r["history"]
            c = color_map[name]
            name_lower = name.lower()

            # B1. Training Curve riêng từng model
            fig, axes = plt.subplots(1, 2, figsize=(14, 5))
            axes[0].plot(h["train_losses"], label="Train Loss", color=c, linewidth=2)
            axes[0].plot(h["val_losses"], label="Val Loss", color=c, linewidth=2, linestyle="--")
            axes[0].set_title(f"{name} — Loss", fontsize=14, fontweight="bold")
            axes[0].set_xlabel("Epoch"); axes[0].set_ylabel("Loss")
            axes[0].legend(); axes[0].grid(True, alpha=0.3)
            axes[0].fill_between(range(len(h["train_losses"])), h["train_losses"], h["val_losses"], alpha=0.1, color=c)

            axes[1].plot(h["train_accs"], label="Train Acc", color=c, linewidth=2)
            axes[1].plot(h["val_accs"], label="Val Acc", color=c, linewidth=2, linestyle="--")
            axes[1].set_title(f"{name} — Accuracy", fontsize=14, fontweight="bold")
            axes[1].set_xlabel("Epoch"); axes[1].set_ylabel("Accuracy")
            axes[1].legend(); axes[1].grid(True, alpha=0.3)
            axes[1].fill_between(range(len(h["train_accs"])), h["train_accs"], h["val_accs"], alpha=0.1, color=c)
            plt.tight_layout()
            plt.savefig(str(plots_dir / f"{name_lower}_training_curve.png"), dpi=150, bbox_inches="tight")
            plt.close()

            # B2. Confusion Matrix riêng từng model (lớn hơn, rõ hơn)
            fig, ax = plt.subplots(figsize=(10, 8))
            cm = np.array(m["action_confusion_matrix"])
            # Normalized confusion matrix
            cm_norm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
            cm_norm = np.nan_to_num(cm_norm)
            sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                       xticklabels=ACTIONS, yticklabels=ACTIONS,
                       ax=ax, cbar_kws={"shrink": 0.8},
                       linewidths=0.5, linecolor='white')
            # Overlay percentages
            for i_row in range(cm.shape[0]):
                for j_col in range(cm.shape[1]):
                    pct = cm_norm[i_row, j_col] * 100
                    if pct > 0:
                        ax.text(j_col + 0.5, i_row + 0.75, f"({pct:.0f}%)",
                               ha="center", va="center", fontsize=7, color="gray")
            ax.set_title(f"{name} — Confusion Matrix (count + %)", fontsize=14, fontweight="bold")
            ax.set_xlabel("Predicted Action", fontsize=12); ax.set_ylabel("True Action", fontsize=12)
            ax.tick_params(axis="x", rotation=45); ax.tick_params(axis="y", rotation=0)
            plt.tight_layout()
            plt.savefig(str(plots_dir / f"{name_lower}_confusion_matrix.png"), dpi=150, bbox_inches="tight")
            plt.close()

            # B3. Per-class metrics riêng từng model (Precision/Recall/F1 per class)
            fig, ax = plt.subplots(figsize=(14, 6))
            report = m["action_classification_report"]
            precs = [report.get(a, {}).get("precision", 0) for a in ACTIONS]
            recs = [report.get(a, {}).get("recall", 0) for a in ACTIONS]
            f1s = [report.get(a, {}).get("f1-score", 0) for a in ACTIONS]
            x_pos = np.arange(len(ACTIONS))
            w = 0.25
            ax.bar(x_pos - w, precs, w, label="Precision", color="#3498db", alpha=0.85)
            ax.bar(x_pos, recs, w, label="Recall", color="#e74c3c", alpha=0.85)
            ax.bar(x_pos + w, f1s, w, label="F1-Score", color="#2ecc71", alpha=0.85)
            # Add value labels
            for xi, (p, r, f) in enumerate(zip(precs, recs, f1s)):
                ax.text(xi - w, p + 0.01, f"{p:.2f}", ha="center", fontsize=7, fontweight="bold")
                ax.text(xi, r + 0.01, f"{r:.2f}", ha="center", fontsize=7, fontweight="bold")
                ax.text(xi + w, f + 0.01, f"{f:.2f}", ha="center", fontsize=7, fontweight="bold")
            ax.set_xlabel("Action Type", fontsize=12); ax.set_ylabel("Score", fontsize=12)
            ax.set_title(f"{name} — Per-Class Precision / Recall / F1-Score", fontsize=14, fontweight="bold")
            ax.set_xticks(x_pos); ax.set_xticklabels(ACTIONS, rotation=45, ha="right")
            ax.legend(); ax.set_ylim(0, 1.15); ax.grid(True, alpha=0.3, axis="y")
            plt.tight_layout()
            plt.savefig(str(plots_dir / f"{name_lower}_per_class_metrics.png"), dpi=150, bbox_inches="tight")
            plt.close()

            # B4. Prediction Distribution riêng từng model (pie chart)
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            # True distribution
            true_counts = [0] * len(ACTIONS)
            pred_counts = [0] * len(ACTIONS)
            report = m["action_classification_report"]
            for idx_a, a in enumerate(ACTIONS):
                if a in report:
                    true_counts[idx_a] = int(report[a].get("support", 0))
            # Predicted distribution from confusion matrix
            cm_arr = np.array(m["action_confusion_matrix"])
            for idx_a in range(len(ACTIONS)):
                pred_counts[idx_a] = int(cm_arr[:, idx_a].sum()) if idx_a < cm_arr.shape[1] else 0

            pie_colors = plt.cm.Set3(np.linspace(0, 1, len(ACTIONS)))
            non_zero_true = [(ACTIONS[i], true_counts[i]) for i in range(len(ACTIONS)) if true_counts[i] > 0]
            non_zero_pred = [(ACTIONS[i], pred_counts[i]) for i in range(len(ACTIONS)) if pred_counts[i] > 0]

            if non_zero_true:
                labels_t, vals_t = zip(*non_zero_true)
                axes[0].pie(vals_t, labels=labels_t, autopct="%1.1f%%", startangle=90,
                           colors=pie_colors[:len(vals_t)])
                axes[0].set_title(f"{name} — True Label Distribution", fontsize=12, fontweight="bold")

            if non_zero_pred:
                labels_p, vals_p = zip(*non_zero_pred)
                axes[1].pie(vals_p, labels=labels_p, autopct="%1.1f%%", startangle=90,
                           colors=pie_colors[:len(vals_p)])
                axes[1].set_title(f"{name} — Predicted Label Distribution", fontsize=12, fontweight="bold")
            plt.tight_layout()
            plt.savefig(str(plots_dir / f"{name_lower}_prediction_distribution.png"), dpi=150, bbox_inches="tight")
            plt.close()

        # ═══════════════════════════════════════════
        # C. EXTRA COMPARISON PLOTS
        # ═══════════════════════════════════════════

        # C1. Training Time Comparison
        fig, ax = plt.subplots(figsize=(8, 5))
        times = [self.results[n]["training_time"] for n in model_names]
        bars = ax.bar(model_names, times, color=colors[:len(model_names)], alpha=0.85, width=0.5)
        for bar, t in zip(bars, times):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                    f"{t:.1f}s", ha="center", fontweight="bold", fontsize=11)
        ax.set_ylabel("Training Time (seconds)", fontsize=12)
        ax.set_title("Training Time Comparison", fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3, axis="y")
        plt.tight_layout()
        plt.savefig(str(plots_dir / "all_training_time.png"), dpi=150, bbox_inches="tight")
        plt.close()

        # C2. Final Val Loss + Val Acc comparison
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        final_losses = [self.results[n]["history"]["val_losses"][-1] for n in model_names]
        final_accs = [self.results[n]["history"]["val_accs"][-1] for n in model_names]
        bars1 = axes[0].bar(model_names, final_losses, color=colors[:len(model_names)], alpha=0.85)
        for bar, v in zip(bars1, final_losses):
            axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                        f"{v:.4f}", ha="center", fontweight="bold", fontsize=10)
        axes[0].set_ylabel("Loss"); axes[0].set_title("Final Validation Loss", fontsize=13, fontweight="bold")
        axes[0].grid(True, alpha=0.3, axis="y")

        bars2 = axes[1].bar(model_names, final_accs, color=colors[:len(model_names)], alpha=0.85)
        for bar, v in zip(bars2, final_accs):
            axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                        f"{v:.4f}", ha="center", fontweight="bold", fontsize=10)
        axes[1].set_ylabel("Accuracy"); axes[1].set_title("Final Validation Accuracy", fontsize=13, fontweight="bold")
        axes[1].grid(True, alpha=0.3, axis="y")
        plt.tight_layout()
        plt.savefig(str(plots_dir / "all_final_val_metrics.png"), dpi=150, bbox_inches="tight")
        plt.close()

        total_plots = 5 + len(model_names) * 4 + 2
        logger.info(f"Saved {total_plots} plots to {plots_dir}")

    def _generate_report(self):
        """Generate markdown evaluation report."""
        plots_dir = settings.PLOTS_DIR
        report = []
        report.append("# Model Evaluation Report — AI New Service")
        report.append(f"\n## Dataset Overview\n")
        report.append(f"- **Total Users**: {self.data_info['num_users']}")
        report.append(f"- **Total Products**: {self.data_info['num_products']}")
        report.append(f"- **Action Types**: {self.data_info['num_actions']} ({', '.join(ACTIONS)})")
        report.append(f"- **Total Sequences**: {self.data_info['num_sequences']}")
        report.append(f"- **Sequence Length**: {settings.SEQ_LENGTH}")
        report.append(f"- **Train/Test Split**: {settings.TRAIN_SPLIT}/{1-settings.TRAIN_SPLIT}")

        report.append(f"\n## Hyperparameters\n")
        report.append(f"| Parameter | Value |")
        report.append(f"|---|---|")
        report.append(f"| Embedding Dim | {settings.EMBEDDING_DIM} |")
        report.append(f"| Hidden Dim | {settings.HIDDEN_DIM} |")
        report.append(f"| Max Epochs | {settings.NUM_EPOCHS} |")
        report.append(f"| Batch Size | {settings.BATCH_SIZE} |")
        report.append(f"| Learning Rate | {settings.LEARNING_RATE} |")
        report.append(f"| Optimizer | Adam (weight_decay=1e-4) |")
        report.append(f"| Scheduler | CosineAnnealingLR |")
        report.append(f"| Loss | Weighted CrossEntropy (action) + 0.3*CrossEntropy (product) |")
        report.append(f"| Early Stopping | patience=8 on val F1 |")

        report.append(f"\n## Model Architectures\n")
        report.append(f"### 1. RNN (Vanilla Recurrent Neural Network)")
        report.append(f"- 1-layer RNN")
        report.append(f"- Input: Product Embedding + Action Embedding (concat)")
        report.append(f"- Output: Action classification + Product prediction\n")
        report.append(f"### 2. LSTM (Long Short-Term Memory)")
        report.append(f"- 2-layer LSTM with dropout=0.2")
        report.append(f"- Cell state captures long-term dependencies\n")
        report.append(f"### 3. BiLSTM (Bidirectional LSTM + Attention)")
        report.append(f"- 2-layer Bidirectional LSTM with dropout=0.2")
        report.append(f"- Attention pooling over all timesteps")

        report.append(f"\n## Evaluation Metrics\n")
        report.append("- **Accuracy**: Overall correct prediction rate")
        report.append("- **Precision** (weighted): Correct positive predictions per class")
        report.append("- **Recall** (weighted): Found positive instances per class")
        report.append("- **F1-Score** (weighted): Harmonic mean of precision and recall")
        report.append("- **Confusion Matrix**: Per-class prediction distribution")
        report.append("- **Class Weights**: Applied to handle imbalanced action distribution")

        report.append(f"\n## Results Summary\n")
        report.append("| Model | Accuracy | Precision | Recall | F1-Score | Product Acc | Training Time |")
        report.append("|---|---|---|---|---|---|---|")
        for name in ["RNN", "LSTM", "BiLSTM"]:
            if name in self.results:
                m = self.results[name]["metrics"]
                t = self.results[name].get("training_time", 0)
                best = " ★" if name == self.best_model_name else ""
                report.append(f"| {name}{best} | {m['action_accuracy']:.4f} | {m['action_precision']:.4f} | "
                            f"{m['action_recall']:.4f} | {m['action_f1']:.4f} | {m['product_accuracy']:.4f} | {t:.1f}s |")

        report.append(f"\n## Best Model: **{self.best_model_name}**\n")
        best_m = self.results[self.best_model_name]["metrics"]
        report.append(f"Selected based on highest **F1-Score** = {best_m['action_f1']:.4f}")
        report.append(f"\nSaved at: `{settings.MODELS_DIR}/best_model.pt`")

        report.append(f"\n## Visualization\n")
        report.append(f"### 1. Training Curves\n![Training Curves](plots/training_curves.png)")
        report.append(f"\n### 2. Metrics Comparison\n![Metrics](plots/metrics_comparison.png)")
        report.append(f"\n### 3. Confusion Matrices\n![CM](plots/confusion_matrices.png)")
        report.append(f"\n### 4. Per-Class F1\n![F1](plots/per_class_f1.png)")
        report.append(f"\n### 5. Radar Chart\n![Radar](plots/radar_chart.png)")

        report.append(f"\n## Detailed Classification Report — {self.best_model_name}\n")
        report.append("```")
        cr = self.results[self.best_model_name]["metrics"]["action_classification_report"]
        report.append(f"{'Class':<20} {'Precision':>10} {'Recall':>10} {'F1-Score':>10} {'Support':>10}")
        report.append("-" * 60)
        for action in ACTIONS:
            if action in cr:
                r = cr[action]
                report.append(f"{action:<20} {r['precision']:>10.4f} {r['recall']:>10.4f} {r['f1-score']:>10.4f} {r['support']:>10.0f}")
        report.append("-" * 60)
        for avg_type in ["macro avg", "weighted avg"]:
            if avg_type in cr:
                r = cr[avg_type]
                report.append(f"{avg_type:<20} {r['precision']:>10.4f} {r['recall']:>10.4f} {r['f1-score']:>10.4f} {r['support']:>10.0f}")
        report.append("```")

        report_path = Path(settings.DATA_DIR) / "model_evaluation_report.md"
        report_path.write_text("\n".join(report), encoding="utf-8")
        logger.info(f"Evaluation report saved to {report_path}")
        return str(report_path)

    def train_all(self):
        """Train all 3 models, evaluate, compare, select best."""
        self.training_status = "loading_data"
        self.load_data()

        train_loader, test_loader = create_dataloaders(
            self.data,
            batch_size=settings.BATCH_SIZE,
            train_split=settings.TRAIN_SPLIT,
        )

        class_weights = self.data.get("class_weights", [1.0] * len(ACTIONS))
        models = self._build_models()
        self.training_status = "training"

        for name, model in models.items():
            logger.info(f"Training {name}...")
            start = time.time()
            history = self._train_single(model, train_loader, test_loader,
                                          class_weights=class_weights,
                                          epochs=settings.NUM_EPOCHS)
            training_time = time.time() - start

            logger.info(f"Evaluating {name}...")
            metrics = self._evaluate(model, test_loader)

            self.models[name] = model
            self.results[name] = {
                "history": history,
                "metrics": metrics,
                "training_time": training_time,
            }
            logger.info(f"  {name}: Acc={metrics['action_accuracy']:.4f}, F1={metrics['action_f1']:.4f}, Time={training_time:.1f}s")

        # Select best model by F1 score
        self.best_model_name = max(self.results, key=lambda k: self.results[k]["metrics"]["action_f1"])
        self.best_model = self.models[self.best_model_name]

        # Save models
        models_dir = Path(settings.MODELS_DIR)
        models_dir.mkdir(parents=True, exist_ok=True)
        torch.save({
            "model_name": self.best_model_name,
            "model_state_dict": self.best_model.state_dict(),
            "data_info": self.data_info,
            "user_to_idx": self.data["user_to_idx"],
            "product_to_idx": self.data["product_to_idx"],
            "idx_to_product": self.data["idx_to_product"],
            "metrics": {
                k: {
                    "action_accuracy": v["metrics"]["action_accuracy"],
                    "action_f1": v["metrics"]["action_f1"],
                    "training_time": v["training_time"],
                }
                for k, v in self.results.items()
            },
        }, str(models_dir / "best_model.pt"))

        for name, model in self.models.items():
            torch.save(model.state_dict(), str(models_dir / f"{name.lower()}_model.pt"))

        logger.info(f"Best model: {self.best_model_name}")

        # Generate plots & report
        self.training_status = "generating_report"
        self._plot_results()
        report_path = self._generate_report()

        self.training_status = "completed"
        return {
            "best_model": self.best_model_name,
            "results": {k: {
                "accuracy": v["metrics"]["action_accuracy"],
                "precision": v["metrics"]["action_precision"],
                "recall": v["metrics"]["action_recall"],
                "f1": v["metrics"]["action_f1"],
                "product_accuracy": v["metrics"]["product_accuracy"],
                "training_time": v["training_time"],
            } for k, v in self.results.items()},
            "report_path": report_path,
        }

    def predict_next_action(self, user_id: str, recent_behaviors: list):
        """Predict next action for a user given recent behaviors."""
        if not self.best_model:
            return None

        model = self.best_model
        model.eval()

        user_idx = self.data["user_to_idx"].get(user_id, 0)
        seq_len = settings.SEQ_LENGTH

        from app.training.data_loader import ACTION_TO_IDX

        user_ids = [user_idx] * seq_len
        product_ids = []
        action_ids = []

        for b in recent_behaviors[-seq_len:]:
            pid = self.data["product_to_idx"].get(b.get("product_id", ""), 0)
            aid = ACTION_TO_IDX.get(b.get("action", "view"), 0)
            product_ids.append(pid)
            action_ids.append(aid)

        while len(product_ids) < seq_len:
            product_ids.insert(0, 0)
            action_ids.insert(0, 0)

        with torch.no_grad():
            u = torch.tensor([user_ids], dtype=torch.long).to(self.device)
            p = torch.tensor([product_ids], dtype=torch.long).to(self.device)
            a = torch.tensor([action_ids], dtype=torch.long).to(self.device)
            action_pred, product_pred = model(u, p, a)

            topk_products = product_pred.topk(min(20, product_pred.size(1)), dim=1)
            recommended_products = []
            for idx in topk_products.indices[0].cpu().numpy():
                pid = self.data["idx_to_product"].get(int(idx), None)
                if pid:
                    recommended_products.append(pid)

            predicted_action = ACTIONS[action_pred.argmax(dim=1).item()]

        return {
            "predicted_action": predicted_action,
            "recommended_product_ids": recommended_products,
            "action_probabilities": {
                ACTIONS[i]: float(torch.softmax(action_pred, dim=1)[0][i])
                for i in range(len(ACTIONS))
            },
        }
