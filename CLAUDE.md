# CLAUDE.md — PolyFinances Datathon 2026 (Polytechnique Montréal)

> Agents: read this, then CONTEXT.md, before doing anything. Humans: fill the TODOs at kickoff (10 min).

## The challenge (fill at kickoff)
- **Problem statement:** TODO (paste it)
- **Data:** TODO (files, where they live: S3 / download link)
- **What we submit:** video + one-pager + technical documentation (confirm at kickoff). Deadline: TODO (2025 pattern: Monday 14:00, AWS accounts wiped 13:59)
- **Judging criteria:** TODO (paste them. 2025 = financial relevance & explainability + use of AWS: architecture quality, scalability)
- **Our angle, one sentence:** TODO
- **Sponsor services we showcase:** TODO (e.g. S3 + Bedrock + SageMaker. Name them in every deliverable)

## Team & lanes
| Lane | Who | Owns (only edit these) |
|---|---|---|
| eda | TODO | `experiments/eda/`, "Verified" facts in CONTEXT.md |
| features / models | TODO | `src/dh/features.py`, `experiments/models/` |
| aws | TODO | `src/dh/llm.py`, `aws/`, the architecture diagram |
| pitch | TODO | `deliverables/` |
| shared (ask first) | anyone, announce in chat | `harness.toml`, `splits/`, `src/dh/{data,metrics,evaluate}.py`, this file |

## How we work
1. **One split, one metric.** Set `harness.toml` at kickoff, then `make split` ONCE and commit `splits/val_ids.csv`. Nobody re-splits.
2. **Every result goes in `results.csv`** through `dh.log_run(...)` (or `make baseline`). Commit your code first so the run points at a commit. `make board` shows the leaderboard.
3. **No number goes in the pitch unless it's in results.csv or under "Verified" in CONTEXT.md.**
4. **Data never goes in git** (`data/` is gitignored). Notebooks are for exploring. Anything others depend on goes in `src/dh/` as a `.py` file.
5. **LLM calls only through `dh.llm.ask`** (mock offline, Bedrock for real, cached).
6. **Small commits, merge often.** Pull main every ~2h. On conflict in a shared file, ask its lane.
7. **Never commit AWS keys.** The guard hook blocks it, and blocks cloud deletes and force-push.
8. **Before the deadline:** `make backup`. The AWS account disappears.
9. **Ask, don't guess.** If an official source (event site, rules, sponsor brief, data docs) can't be reached, or key facts are missing, stop and ask the user before building on search results or assumptions. Ask for the document, or for network access to the host.

## Commands
| | |
|---|---|
| `make setup` | venv + deps + .env |
| `make data` | pull data from S3 into data/raw |
| `make check` | load data, print shape/target/dates |
| `make split` | freeze train/val split (once!) |
| `make baseline` | constant + GBM baselines, logged |
| `make board` | leaderboard from results.csv |
| `make test` | tests |
| `make worktrees` | one worktree per lane, for parallel agents |
| `make backup` | commit+push results/deliverables before AWS teardown |

```python
from dh import load_config, train_val, score, log_run
cfg = load_config(); tr, va = train_val()
pred = my_model.fit(tr[feats], tr[cfg.target]).predict(va[feats])
log_run(score(va[cfg.target], pred), experiment="lgbm-lags", model="lgbm", features="lags+vol", notes="...")
```

## Decisions log (one line each: time — decision — why)
- TODO
