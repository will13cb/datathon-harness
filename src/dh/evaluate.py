"""Score predictions with THE metric and append every run to results.csv."""

from __future__ import annotations

import csv
import getpass
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .config import RESULTS, Config, load_config
from .metrics import get_metric

FIELDS = [
    "run_id",
    "timestamp",
    "author",
    "commit",
    "experiment",
    "model",
    "features",
    "metric",
    "val_score",
    "notes",
]


def score(
    y_true, y_pred, cfg: Config | None = None, metric: str | None = None
) -> float:
    cfg = cfg or load_config()
    name = metric or cfg.metric
    if not name:
        raise SystemExit("harness.toml [eval].metric is empty: fill it in at kickoff.")
    fn, _ = get_metric(name)
    return fn(y_true, y_pred)


def _git(*args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], capture_output=True, text=True, check=True
        ).stdout.strip()
    except Exception:
        return ""


def log_run(
    val_score: float,
    experiment: str,
    model: str,
    features: str = "",
    notes: str = "",
    cfg: Config | None = None,
    results: Path = RESULTS,
) -> str:
    """Append one row to results.csv. Commit your code first so `commit` points at it."""
    cfg = cfg or load_config()
    commit = _git("rev-parse", "--short", "HEAD") or "uncommitted"
    if _git("status", "--porcelain", "--untracked-files=no"):
        commit += "-dirty"
    now = datetime.now(timezone.utc)
    author = (
        os.environ.get("DH_AUTHOR") or _git("config", "user.name") or getpass.getuser()
    )
    run_id = f"{now:%m%d-%H%M%S}-{author.split()[0].lower()}-{os.urandom(2).hex()}"
    new = not results.exists() or results.stat().st_size == 0
    with results.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(
            dict(
                run_id=run_id,
                timestamp=now.isoformat(timespec="seconds"),
                author=author,
                commit=commit,
                experiment=experiment,
                model=model,
                features=features,
                metric=cfg.metric,
                val_score=f"{val_score:.6g}",
                notes=notes,
            )
        )
    return run_id


def leaderboard(
    cfg: Config | None = None, results: Path = RESULTS, top: int = 15
) -> pd.DataFrame:
    cfg = cfg or load_config()
    df = pd.read_csv(results)
    if df.empty:
        return df
    df = df[df["metric"] == cfg.metric] if cfg.metric else df
    try:
        _, gib = get_metric(cfg.metric)
    except KeyError:
        gib = cfg.greater_is_better
    return df.sort_values("val_score", ascending=not gib).head(top)
