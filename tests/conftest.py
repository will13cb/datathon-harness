import numpy as np
import pandas as pd
import pytest

from dh.config import Config


@pytest.fixture
def df():
    rng = np.random.default_rng(0)
    n = 400
    d = pd.DataFrame(
        {
            "id": [f"r{i}" for i in range(n)],
            "date": pd.date_range("2020-01-01", periods=n, freq="D"),
            "ticker": rng.choice(list("ABCDEFGHIJ"), n),
            "x1": rng.normal(size=n),
            "x2": rng.normal(size=n),
        }
    )
    d["y"] = 2 * d.x1 + rng.normal(scale=0.5, size=n)
    return d


@pytest.fixture
def cfg():
    return Config(
        file="t.csv",
        target="y",
        id_col="id",
        time_col="date",
        group_col="ticker",
        metric="rmse",
    )
