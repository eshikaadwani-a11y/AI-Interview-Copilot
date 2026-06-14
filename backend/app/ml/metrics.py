"""Classification evaluation metrics (pure standard library).

Implements accuracy, precision, recall, F1, ROC-AUC, and the confusion matrix
without numpy/sklearn so evaluation runs in any environment. When sklearn is
available the production trainer uses its implementations; these serve as the
dependency-free path and are independently unit-tested.
"""

from __future__ import annotations

from typing import Dict, List, Sequence


def confusion_matrix(y_true: Sequence[int], y_pred: Sequence[int]) -> Dict[str, int]:
    tp = fp = tn = fn = 0
    for actual, pred in zip(y_true, y_pred):
        if actual == 1 and pred == 1:
            tp += 1
        elif actual == 0 and pred == 1:
            fp += 1
        elif actual == 0 and pred == 0:
            tn += 1
        else:
            fn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def accuracy(y_true: Sequence[int], y_pred: Sequence[int]) -> float:
    if not y_true:
        return 0.0
    correct = sum(1 for a, p in zip(y_true, y_pred) if a == p)
    return correct / len(y_true)


def precision(y_true: Sequence[int], y_pred: Sequence[int]) -> float:
    cm = confusion_matrix(y_true, y_pred)
    denom = cm["tp"] + cm["fp"]
    return cm["tp"] / denom if denom else 0.0


def recall(y_true: Sequence[int], y_pred: Sequence[int]) -> float:
    cm = confusion_matrix(y_true, y_pred)
    denom = cm["tp"] + cm["fn"]
    return cm["tp"] / denom if denom else 0.0


def f1_score(y_true: Sequence[int], y_pred: Sequence[int]) -> float:
    p = precision(y_true, y_pred)
    r = recall(y_true, y_pred)
    return 2 * p * r / (p + r) if (p + r) else 0.0


def roc_auc(y_true: Sequence[int], y_score: Sequence[float]) -> float:
    """ROC-AUC via the rank-sum (Mann-Whitney U) formulation.

    Handles ties by averaging ranks. Returns 0.5 when only one class present.
    """
    pairs = sorted(zip(y_score, y_true), key=lambda t: t[0])
    n = len(pairs)
    n_pos = sum(1 for _, label in pairs if label == 1)
    n_neg = n - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5

    # Assign average ranks (1-based), handling ties.
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = avg_rank
        i = j + 1

    sum_ranks_pos = sum(rank for rank, (_, label) in zip(ranks, pairs) if label == 1)
    u = sum_ranks_pos - n_pos * (n_pos + 1) / 2.0
    return u / (n_pos * n_neg)


def evaluate(
    y_true: Sequence[int], y_score: Sequence[float], threshold: float = 0.5
) -> Dict[str, object]:
    """Return the full metric suite for probability scores."""
    y_pred = [1 if s >= threshold else 0 for s in y_score]
    return {
        "accuracy": round(accuracy(y_true, y_pred), 4),
        "precision": round(precision(y_true, y_pred), 4),
        "recall": round(recall(y_true, y_pred), 4),
        "f1": round(f1_score(y_true, y_pred), 4),
        "roc_auc": round(roc_auc(y_true, y_score), 4),
        "confusion_matrix": confusion_matrix(y_true, y_pred),
        "n_samples": len(y_true),
        "positive_rate": round(sum(y_true) / len(y_true), 4) if y_true else 0.0,
    }
