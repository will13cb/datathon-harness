"""Metric registry in plain numpy (no sklearn needed to score).

If the organizers name an official metric that is not here, add it here FIRST,
write a test against a hand-computed value, and only then start logging runs.
"""

from __future__ import annotations

import numpy as np

TRADING_DAYS = 252


def _arr(*xs):
    return [np.asarray(x, dtype=float) for x in xs]


def rmse(y, p):
    y, p = _arr(y, p)
    return float(np.sqrt(np.mean((y - p) ** 2)))


def mae(y, p):
    y, p = _arr(y, p)
    return float(np.mean(np.abs(y - p)))


def mape(y, p):
    y, p = _arr(y, p)
    m = y != 0
    return float(np.mean(np.abs((y[m] - p[m]) / y[m])))


def r2(y, p):
    y, p = _arr(y, p)
    return float(1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2))


def auc(y, p):
    """ROC AUC via the rank-sum (Mann-Whitney) formula, ties averaged."""
    y, p = _arr(y, p)
    order = np.argsort(p, kind="mergesort")
    ranks = np.empty(len(p))
    sp = p[order]
    i = 0
    while i < len(sp):  # average ranks over ties
        j = i
        while j + 1 < len(sp) and sp[j + 1] == sp[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2 + 1
        i = j + 1
    pos = y == 1
    n_pos, n_neg = pos.sum(), (~pos).sum()
    return float((ranks[pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def logloss(y, p, eps=1e-15):
    y, p = _arr(y, p)
    p = np.clip(p, eps, 1 - eps)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def accuracy(y, p):
    return float(np.mean(np.asarray(y) == np.asarray(p)))


def f1_macro(y, p):
    y, p = np.asarray(y), np.asarray(p)
    scores = []
    for c in np.unique(np.concatenate([y, p])):
        tp = np.sum((p == c) & (y == c))
        fp = np.sum((p == c) & (y != c))
        fn = np.sum((p != c) & (y == c))
        scores.append(0.0 if tp == 0 else 2 * tp / (2 * tp + fp + fn))
    return float(np.mean(scores))


def sharpe(returns, periods_per_year: int = TRADING_DAYS) -> float:
    """Annualised Sharpe of a return series (risk-free = 0)."""
    (r,) = _arr(returns)
    sd = r.std(ddof=1)
    return float(np.sqrt(periods_per_year) * r.mean() / sd) if sd > 0 else 0.0


def max_drawdown(returns) -> float:
    """Most negative peak-to-trough drop of the compounded equity curve (e.g. -0.23)."""
    (r,) = _arr(returns)
    equity = np.cumprod(1 + r)
    peak = np.maximum.accumulate(equity)
    return float((equity / peak - 1).min())


def strategy_sharpe(asset_returns, positions):
    """y_true = next-period asset returns, y_pred = position in [-1, 1] taken BEFORE that period."""
    r, w = _arr(asset_returns, positions)
    return sharpe(r * w)


# name -> (fn(y_true, y_pred), greater_is_better)
METRICS = {
    "rmse": (rmse, False),
    "mae": (mae, False),
    "mape": (mape, False),
    "r2": (r2, True),
    "auc": (auc, True),
    "logloss": (logloss, False),
    "accuracy": (accuracy, True),
    "f1": (f1_macro, True),
    "sharpe": (strategy_sharpe, True),
}


def get_metric(name: str):
    if name not in METRICS:
        raise KeyError(f"unknown metric {name!r}; known: {sorted(METRICS)}")
    return METRICS[name]
