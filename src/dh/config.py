from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "raw"
SPLIT_FILE = ROOT / "splits" / "val_ids.csv"
RESULTS = ROOT / "results.csv"


@dataclass
class Config:
    file: str = ""
    target: str = ""
    id_col: str = ""
    time_col: str = ""
    group_col: str = ""
    drop_cols: list[str] = field(default_factory=list)
    split_kind: str = "auto"
    val_frac: float = 0.2
    seed: int = 2026
    metric: str = ""
    greater_is_better: bool = True

    @property
    def resolved_split(self) -> str:
        if self.split_kind != "auto":
            return self.split_kind
        if self.time_col:
            return "time"
        if self.group_col:
            return "group"
        return "random"

    def non_features(self) -> set[str]:
        cols = {
            self.target,
            self.id_col,
            self.time_col,
            self.group_col,
            *self.drop_cols,
        }
        return {c for c in cols if c}


def load_config(path: Path | str | None = None) -> Config:
    path = Path(path) if path else ROOT / "harness.toml"
    raw = tomllib.loads(path.read_text())
    d, s, e = raw.get("data", {}), raw.get("split", {}), raw.get("eval", {})
    return Config(
        file=d.get("file", ""),
        target=d.get("target", ""),
        id_col=d.get("id_col", ""),
        time_col=d.get("time_col", ""),
        group_col=d.get("group_col", ""),
        drop_cols=list(d.get("drop_cols", [])),
        split_kind=s.get("kind", "auto"),
        val_frac=float(s.get("val_frac", 0.2)),
        seed=int(s.get("seed", 2026)),
        metric=e.get("metric", ""),
        greater_is_better=bool(e.get("greater_is_better", True)),
    )
