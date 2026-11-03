"""Fraud metrics, capacity-constrained policy and documented cost scenarios."""
import numpy as np
from sklearn.metrics import (average_precision_score, brier_score_loss, confusion_matrix,
                            f1_score, precision_score, recall_score, roc_auc_score,
                            precision_recall_curve, roc_curve)


def evaluate(y, probability, amount, threshold: float, config: dict) -> dict:
    y, probability, amount = np.asarray(y), np.asarray(probability), np.asarray(amount)
    flagged = probability >= threshold
    tn, fp, fn, tp = confusion_matrix(y, flagged, labels=[0, 1]).ravel()
    k = max(1, int(np.ceil(len(y) * config["review_capacity_fraction"])))
    top = np.argsort(-probability, kind="stable")[:k]
    missed = float(amount[(y == 1) & ~flagged].sum())
    captured = float(amount[(y == 1) & flagged].sum())
    investigation = float(flagged.sum() * config["investigation_cost"])
    loss = missed * config["missed_fraud_multiplier"]
    return {
        "precision": float(precision_score(y, flagged, zero_division=0)),
        "recall": float(recall_score(y, flagged, zero_division=0)),
        "f1": float(f1_score(y, flagged, zero_division=0)),
        "pr_auc": float(average_precision_score(y, probability)),
        "roc_auc": float(roc_auc_score(y, probability)),
        "brier_score": float(brier_score_loss(y, probability)),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
        "false_positive_rate": float(fp / max(1, tn + fp)),
        "false_negative_rate": float(fn / max(1, fn + tp)),
        "precision_at_k": float(y[top].mean()), "recall_at_k": float(y[top].sum() / max(1, y.sum())),
        "k": k, "fraud_capture_rate": float(tp / max(1, tp + fn)),
        "amount_capture_rate": captured / max(1e-12, captured + missed),
        "fraud_amount_captured": captured, "fraud_amount_missed": missed,
        "legitimate_amount_flagged": float(amount[(y == 0) & flagged].sum()),
        "investigation_cost": investigation, "estimated_fraud_loss": loss,
        "estimated_cost": float(investigation + fp * config["false_positive_cost"] + loss),
        "review_rate": float(flagged.mean()), "threshold": float(threshold), "rows": len(y),
        "prevalence": float(y.mean()),
    }


def select_threshold(y, probability, amount, config: dict) -> tuple[float, list[dict]]:
    # Includes no-review policy even if all scores are equal or exactly one.
    thresholds = np.unique(np.r_[np.linspace(0, 1, config["threshold_grid_size"]), probability, np.nextafter(1., 2.)])
    rows = []
    for threshold in thresholds:
        prediction = probability >= threshold
        fp = int(((y == 0) & prediction).sum())
        cost = prediction.sum() * config["investigation_cost"] + fp * config["false_positive_cost"] + amount[(y == 1) & ~prediction].sum() * config["missed_fraud_multiplier"]
        rows.append({"threshold": float(threshold), "estimated_cost": float(cost), "review_rate": float(prediction.mean()), "recall": float(((y == 1) & prediction).sum() / max(1, (y == 1).sum())), "precision": float(((y == 1) & prediction).sum() / max(1, prediction.sum()))})
    feasible = [r for r in rows if r["review_rate"] <= config["review_capacity_fraction"]]
    best = min(feasible, key=lambda r: (r["estimated_cost"], r["review_rate"], -r["threshold"]))
    return best["threshold"], rows


def curves(y, probability) -> dict:
    precision, recall, _ = precision_recall_curve(y, probability)
    fpr, tpr, _ = roc_curve(y, probability)
    def thin(x, z):
        ix = np.unique(np.linspace(0, len(x) - 1, min(150, len(x))).astype(int))
        return [{"x": float(x[i]), "y": float(z[i])} for i in ix]
    return {"pr": thin(recall, precision), "roc": thin(fpr, tpr)}
