"""Leakage and sanity checks. Run them on every feature set before you trust a score."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import Config


def check_features(
    X: pd.DataFrame,
    cfg: Config,
    y: pd.Series | None = None,
    corr_threshold: float = 0.98,
) -> list[str]:
    """Return a list of problems (empty list = clean)."""
    problems = []
    banned = cfg.non_features() & set(X.columns)
    if banned:
        problems.append(f"non-feature columns used as features: {sorted(banned)}")
    if y is not None:
        num = X.select_dtypes("number")
        yv = pd.to_numeric(y, errors="coerce")
        if yv.notna().any() and yv.nunique() > 1:
            for c in num.columns:
                if num[c].nunique() > 1:
                    r = np.corrcoef(
                        num[c].fillna(num[c].median()), yv.fillna(yv.median())
                    )[0, 1]
                    if abs(r) >= corr_threshold:
                        problems.append(
                            f"{c!r} has |corr| {abs(r):.3f} with target: probable leak"
                        )
    return problems


def check_split(train: pd.DataFrame, val: pd.DataFrame, cfg: Config) -> list[str]:
    problems = []
    if cfg.time_col and cfg.resolved_split == "time":
        if train[cfg.time_col].max() > val[cfg.time_col].min():
            problems.append(
                "time split violated: train has rows after the first val row"
            )
    if cfg.group_col and cfg.resolved_split == "group":
        overlap = set(train[cfg.group_col]) & set(val[cfg.group_col])
        if overlap:
            problems.append(f"{len(overlap)} groups appear in both train and val")
    if cfg.id_col:
        dup = set(train[cfg.id_col]) & set(val[cfg.id_col])
        if dup:
            problems.append(f"{len(dup)} ids in both train and val")
    return problems
