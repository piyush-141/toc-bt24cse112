"""
Evaluation Metrics and Statistical Reporting.

Computes:
- Precision, Recall, F1-Score
- Confusion Matrix (TP, FP, TN, FN)
- False Positive Rate (FPR)
- Detection breakdown across anomaly categories (Rule violations vs Behavioral anomalies)
"""

from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> Dict[str, Any]:
    """
    Calculate classification metrics for binary anomaly detection.
    (1 = Anomalous, 0 = Normal)
    """
    y_t = np.array(y_true).astype(int)
    y_p = np.array(y_pred).astype(int)

    cm = confusion_matrix(y_t, y_p, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_t, y_p, pos_label=1, average="binary", zero_division=0
    )

    total_negatives = tn + fp
    fpr = float(fp / total_negatives) if total_negatives > 0 else 0.0
    accuracy = float((tp + tn) / len(y_t)) if len(y_t) > 0 else 0.0

    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "accuracy": accuracy,
        "false_positive_rate": fpr,
        "true_positives": int(tp),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "false_negatives": int(fn),
        "confusion_matrix": {
            "TN": int(tn),
            "FP": int(fp),
            "FN": int(fn),
            "TP": int(tp),
        },
    }


def compute_category_breakdown(
    labels: pd.Series,
    predictions: np.ndarray,
) -> Dict[str, Dict[str, Any]]:
    """
    Analyze recall and catch rate across specific anomaly types.
    """
    df = pd.DataFrame({
        "label": labels.values,
        "pred": predictions,
    })

    categories = df["label"].unique()
    breakdown = {}

    for cat in categories:
        sub = df[df["label"] == cat]
        total = len(sub)
        flagged = int(sub["pred"].sum())
        catch_rate = float(flagged / total) if total > 0 else 0.0

        breakdown[cat] = {
            "total_cases": total,
            "flagged_cases": flagged,
            "catch_rate": catch_rate,
        }

    return breakdown

