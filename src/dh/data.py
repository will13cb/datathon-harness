"""Load the challenge file and apply the frozen split. Everyone goes through here."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import DATA_DIR, SPLIT_FILE, Config, load_config

READERS = {
    ".csv": pd.read_csv,
    ".parquet": pd.read_parquet,
    ".xlsx": pd.read_excel,
    ".xls": pd.read_excel,
    ".json": pd.read_json,
    ".jsonl": lambda p: pd.read_json(p, lines=True),
}


def load_data(
    cfg: Config | None = None, path: Path | str | None = None
) -> pd.DataFrame:
    cfg = cfg or load_config()
    p = Path(path) if path else DATA_DIR / cfg.file
    if not cfg.file and path is None:
        raise SystemExit("harness.toml [data].file is empty: fill it in at kickoff.")
    reader = READERS.get(p.suffix.lower())
    if reader is None:
        raise SystemExit(f"No reader for {p.suffix}; add one to dh/data.py READERS.")
    df = reader(p)
    if cfg.time_col and cfg.time_col in df:
        df[cfg.time_col] = pd.to_datetime(df[cfg.time_col])
    return df


def row_ids(df: pd.DataFrame, cfg: Config) -> pd.Series:
    """Stable row key: the id column if there is one, otherwise the positional index."""
    if cfg.id_col:
        if df[cfg.id_col].duplicated().any():
            raise ValueError(f"id_col {cfg.id_col!r} is not unique")
        return df[cfg.id_col].astype(str)
    return pd.Series(np.arange(len(df)).astype(str), index=df.index)


def make_split(df: pd.DataFrame, cfg: Config) -> pd.Series:
    """Boolean mask, True = validation row."""
    kind = cfg.resolved_split
    if kind == "time":
        cutoff = df[cfg.time_col].quantile(1 - cfg.val_frac)
        return df[cfg.time_col] > cutoff
    rng = np.random.default_rng(cfg.seed)
    if kind == "group":
        groups = df[cfg.group_col].drop_duplicates().to_numpy()
        rng.shuffle(groups)
        n_val = max(1, int(round(len(groups) * cfg.val_frac)))
        return df[cfg.group_col].isin(set(groups[:n_val]))
    if kind == "random":
        return pd.Series(rng.random(len(df)) < cfg.val_frac, index=df.index)
    raise ValueError(f"unknown split kind {kind!r}")


def freeze_split(
    df: pd.DataFrame, cfg: Config, out: Path = SPLIT_FILE, force: bool = False
) -> Path:
    if out.exists() and not force:
        raise SystemExit(
            f"{out} already exists. The split is frozen; use --force only with team agreement."
        )
    mask = make_split(df, cfg)
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"row_id": row_ids(df, cfg)[mask].to_numpy()}).to_csv(out, index=False)
    return out


def train_val(
    df: pd.DataFrame | None = None,
    cfg: Config | None = None,
    split_file: Path = SPLIT_FILE,
):
    """Return (train_df, val_df) using the committed split file."""
    cfg = cfg or load_config()
    df = load_data(cfg) if df is None else df
    if not split_file.exists():
        raise SystemExit(
            "No frozen split yet: run `python -m dh split` once and commit splits/val_ids.csv."
        )
    val_ids = set(pd.read_csv(split_file, dtype=str)["row_id"])
    is_val = row_ids(df, cfg).isin(val_ids).to_numpy()
    return df[~is_val].copy(), df[is_val].copy()


def feature_cols(df: pd.DataFrame, cfg: Config) -> list[str]:
    return [c for c in df.columns if c not in cfg.non_features()]
