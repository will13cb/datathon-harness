"""Shared feature functions. One function per feature group: DataFrame in, DataFrame out.
Name the groups you used in the `features` column of results.csv.
Time-ordered data: only use the past (shift BEFORE rolling)."""

from __future__ import annotations

import pandas as pd


def _per_entity(df: pd.DataFrame, col: str, by: str | None, fn) -> pd.Series:
    return df.groupby(by)[col].transform(fn) if by else fn(df[col])


def lags(
    df: pd.DataFrame, col: str, time: str, by: str | None = None, ns=(1, 5, 20)
) -> pd.DataFrame:
    df = df.sort_values(time)
    return df.assign(
        **{
            f"{col}_lag{n}": _per_entity(df, col, by, lambda s, n=n: s.shift(n))
            for n in ns
        }
    )


def rolling(
    df: pd.DataFrame, col: str, time: str, by: str | None = None, windows=(5, 20)
) -> pd.DataFrame:
    """Mean/std over the previous `w` rows (today's value excluded)."""
    df = df.sort_values(time)
    out = {}
    for w in windows:
        out[f"{col}_mean{w}"] = _per_entity(
            df, col, by, lambda s, w=w: s.shift(1).rolling(w, min_periods=2).mean()
        )
        out[f"{col}_std{w}"] = _per_entity(
            df, col, by, lambda s, w=w: s.shift(1).rolling(w, min_periods=2).std()
        )
    return df.assign(**out)
