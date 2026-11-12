import numpy as np
import pytest

from dh import checks
from dh.config import load_config
from dh.data import feature_cols, freeze_split, make_split, train_val
from dh.evaluate import leaderboard, log_run, score
from dh.metrics import max_drawdown, sharpe


def test_time_split_is_strictly_after(df, cfg):
    mask = make_split(df, cfg)
    assert df.loc[~mask, "date"].max() < df.loc[mask, "date"].min()
    assert 0.15 < mask.mean() < 0.25


def test_group_split_has_no_overlap(df, cfg):
    cfg.split_kind = "group"
    tr, va = df[~make_split(df, cfg)], df[make_split(df, cfg)]
    assert not checks.check_split(tr, va, cfg)


def test_freeze_roundtrip_and_refuses_overwrite(df, cfg, tmp_path):
    out = tmp_path / "val_ids.csv"
    freeze_split(df, cfg, out=out)
    tr, va = train_val(df, cfg, split_file=out)
    assert len(tr) + len(va) == len(df) and not set(tr.id) & set(va.id)
    with pytest.raises(SystemExit):
        freeze_split(df, cfg, out=out)


def test_features_exclude_target_and_keys(df, cfg):
    assert set(feature_cols(df, cfg)) == {"x1", "x2"}


def test_leak_detector(df, cfg):
    X = df[["x1", "x2"]].assign(leak=df.y * 1.0001)
    probs = checks.check_features(X, cfg, df.y)
    assert any("leak" in p for p in probs)
    assert checks.check_features(df[["x2"]], cfg, df.y) == []
    assert checks.check_features(df[["y", "x1"]], cfg)  # target used as feature


def test_metrics(cfg):
    assert score([1, 2, 3], [1, 2, 3], cfg) == 0
    assert score([0, 1, 1, 0], [0.1, 0.9, 0.8, 0.2], metric="auc") == 1.0
    assert sharpe([0.01, -0.01] * 10) == pytest.approx(0, abs=1e-9)
    assert sharpe([0.01, 0.02, 0.015]) > 0
    assert max_drawdown([0.1, -0.5, 0.2]) == pytest.approx(-0.5)


def test_log_and_leaderboard(cfg, tmp_path):
    res = tmp_path / "results.csv"
    log_run(0.9, "e1", "a", cfg=cfg, results=res)
    log_run(0.5, "e2", "b", cfg=cfg, results=res)
    board = leaderboard(cfg, results=res)
    assert list(board.model) == ["b", "a"]  # rmse: lower is better


def test_committed_config_parses():
    load_config()


def test_auc_handles_ties_and_matches_hand_value():
    from dh.metrics import auc, f1_macro, logloss, r2

    # pairs (pos,neg): (0.8>0.3) (0.8>0.5) (0.5=0.5 -> 0.5) (0.5>0.3) => 3.5/4
    assert auc([1, 1, 0, 0], [0.8, 0.5, 0.5, 0.3]) == pytest.approx(0.875)
    assert r2([1, 2, 3], [1, 2, 3]) == 1.0
    assert logloss([1, 0], [0.5, 0.5]) == pytest.approx(np.log(2))
    assert f1_macro([0, 1, 1], [0, 1, 0]) == pytest.approx((2 / 3 + 2 / 3) / 2)


def test_llm_mock_is_offline(monkeypatch):
    from dh.llm import ask

    monkeypatch.setenv("LLM_PROVIDER", "mock")
    assert ask("hello").startswith("[mock]")


def test_features_use_only_the_past(df):
    from dh.features import lags, rolling

    out = rolling(
        lags(df, "x1", "date", by="ticker", ns=(1,)),
        "x1",
        "date",
        by="ticker",
        windows=(3,),
    )
    a = out[out.ticker == "A"].sort_values("date")
    assert a.x1_lag1.iloc[1] == a.x1.iloc[0]
    assert a.x1_mean3.iloc[3] == pytest.approx(a.x1.iloc[0:3].mean())


def test_run_ids_unique(cfg, tmp_path):
    res = tmp_path / "r.csv"
    ids = {log_run(1.0, "e", "m", cfg=cfg, results=res) for _ in range(5)}
    assert len(ids) == 5


def test_logging_does_not_mark_later_runs_dirty(cfg, tmp_path, monkeypatch):
    import subprocess

    import pandas as pd

    def git(*a):
        subprocess.run(["git", *a], cwd=tmp_path, check=True, capture_output=True)

    git("init", "-q")
    res = tmp_path / "results.csv"
    res.write_text("")
    (tmp_path / "model.py").write_text("x = 1\n")
    git("add", ".")
    git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init")
    monkeypatch.chdir(tmp_path)
    log_run(1.0, "e", "m", cfg=cfg, results=res)
    log_run(2.0, "e", "m", cfg=cfg, results=res)
    commits = pd.read_csv(res)["commit"].astype(str)
    assert not commits.str.endswith("-dirty").any()
    (tmp_path / "model.py").write_text("x = 2\n")  # real code change -> dirty
    log_run(3.0, "e", "m", cfg=cfg, results=res)
    assert pd.read_csv(res)["commit"].astype(str).iloc[-1].endswith("-dirty")
