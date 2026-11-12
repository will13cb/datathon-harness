"""CLI:  python -m dh {check,split,baseline,board}"""

from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

from . import checks
from .config import load_config
from .data import feature_cols, freeze_split, load_data, train_val
from .evaluate import leaderboard, log_run, score
from .metrics import get_metric


def cmd_check(_):
    cfg = load_config()
    df = load_data(cfg)
    print(f"{cfg.file}: {len(df):,} rows x {df.shape[1]} cols")
    if cfg.time_col:
        print(f"{cfg.time_col}: {df[cfg.time_col].min()} -> {df[cfg.time_col].max()}")
    if cfg.target:
        print(f"target {cfg.target!r}:\n{df[cfg.target].describe()}")
    print(f"split: {cfg.resolved_split}, metric: {cfg.metric or '(unset)'}")
    print(df.head())


def cmd_split(a):
    cfg = load_config()
    out = freeze_split(load_data(cfg), cfg, force=a.force)
    tr, va = train_val(cfg=cfg)
    print(
        f"wrote {out}: train {len(tr):,} / val {len(va):,} ({cfg.resolved_split} split)"
    )
    for p in checks.check_split(tr, va, cfg):
        print("PROBLEM:", p)
    print("Commit splits/val_ids.csv now. Everyone scores on this split.")


def _baseline_preds(tr, va, cfg):
    """Yield (model_name, val predictions). Constant baseline + a gradient-boosting model."""
    from sklearn.ensemble import (
        HistGradientBoostingClassifier,
        HistGradientBoostingRegressor,
    )

    feats = [c for c in feature_cols(tr, cfg) if pd.api.types.is_numeric_dtype(tr[c])]
    y = tr[cfg.target]
    proba = cfg.metric in {"auc", "logloss"}
    classify = cfg.metric in {"auc", "logloss", "accuracy", "f1"}
    if classify:
        if proba:
            yield "constant", pd.Series(y.mean(), index=va.index)
        else:
            yield "constant", pd.Series(y.mode()[0], index=va.index)
        m = HistGradientBoostingClassifier(random_state=cfg.seed).fit(tr[feats], y)
        yield "hgb", m.predict_proba(va[feats])[:, 1] if proba else m.predict(va[feats])
    elif cfg.metric == "sharpe":
        yield "always_long", pd.Series(1.0, index=va.index)
        m = HistGradientBoostingRegressor(random_state=cfg.seed).fit(tr[feats], y)
        yield "hgb_sign", np.where(m.predict(va[feats]) > 0, 1.0, -1.0)
    else:
        yield (
            "constant",
            pd.Series(
                y.median() if cfg.metric in {"mae", "mape"} else y.mean(),
                index=va.index,
            ),
        )
        m = HistGradientBoostingRegressor(random_state=cfg.seed).fit(tr[feats], y)
        yield "hgb", m.predict(va[feats])
    print(f"({len(feats)} numeric features)")


def cmd_baseline(a):
    cfg = load_config()
    if not cfg.target:
        sys.exit(
            "No target in harness.toml: baseline only applies to predictive challenges."
        )
    tr, va = train_val(cfg=cfg)
    for p in checks.check_split(tr, va, cfg) + checks.check_features(
        tr[feature_cols(tr, cfg)], cfg, tr[cfg.target]
    ):
        print("PROBLEM:", p)
    for name, pred in _baseline_preds(tr, va, cfg):
        s = score(va[cfg.target], pred, cfg)
        print(f"{name:>12}: {cfg.metric} = {s:.5f}")
        if not a.no_log:
            log_run(
                s, experiment="baseline", model=name, features="all numeric", cfg=cfg
            )


def cmd_board(a):
    cfg = load_config()
    df = leaderboard(cfg, top=a.top)
    print(df.to_string(index=False) if not df.empty else "results.csv is empty")
    if cfg.metric:
        print(
            f"\n({'higher' if get_metric(cfg.metric)[1] else 'lower'} {cfg.metric} is better)"
        )


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m dh")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="load data and print a summary").set_defaults(
        fn=cmd_check
    )
    s = sub.add_parser("split", help="freeze the train/val split (once, at kickoff)")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_split)
    b = sub.add_parser("baseline", help="score constant + GBM baselines and log them")
    b.add_argument("--no-log", action="store_true")
    b.set_defaults(fn=cmd_baseline)
    l = sub.add_parser("board", help="show the results leaderboard")
    l.add_argument("--top", type=int, default=15)
    l.set_defaults(fn=cmd_board)
    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
