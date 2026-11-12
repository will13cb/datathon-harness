# datathon-harness: PolyFinances Datathon 2026

A small coordination harness for a team of 4 (humans + coding agents) at the
[PolyFinances Datathon](https://polyfinances.ca/datathon) at Polytechnique Montréal (Nov 14–15, 2026; headline partners Banque Nationale + AWS).
It's built from [hackathon-template](https://github.com/will13cb/hackathon-template) (guard hook, Makefile, worktrees, Bedrock helper).
It's adapted for data work: **one frozen split, one scoring function, and one shared results log**, so everyone's numbers are comparable and every number in the pitch is real.

```
CLAUDE.md / AGENTS.md   brief, lanes, rules, decisions log  ← fill at kickoff
CONTEXT.md              facts: Verified vs Assumed (pre-filled with what we know about the event)
harness.toml            data file, target, time/group columns, split, metric  ← fill at kickoff
results.csv             every run, append-only (merge=union, so no conflicts)
splits/val_ids.csv      the frozen validation set (created once by `make split`)
src/dh/                 data.py (load + split), metrics.py, evaluate.py (score/log/board),
                        checks.py (leakage), features.py (shared features), llm.py (mock|Bedrock, cached)
experiments/            per-lane scratch (notebooks OK)
deliverables/           one-pager, video script, technical doc templates
aws/architecture.md     architecture diagram (judged!)
app/app.py              demo application (Streamlit). It is a deliverable!
scripts/                get-data, worktrees, backup, scan-secrets
```

## Kickoff (first 45 min after the challenge drops)

1. `make setup` (everyone). Then `aws configure --profile datathon` with the event account and set `.env`.
2. Read the challenge **together** and fill the TODOs in `CLAUDE.md` (problem, deliverables, deadline, judging criteria, lanes).
   Move confirmed items in `CONTEXT.md` from Assumed → Verified.
3. One person: `make data` (or drop files into `data/raw/`), fill `harness.toml`, then `make check`.
4. Same person: `make split`, then `make baseline`, then commit + push `harness.toml splits/ results.csv`. **Everyone branches after this.**
5. Lanes: `git switch -c lane/<name>`, or for parallel agents `make worktrees`.

If the challenge isn't a prediction task (e.g. a GenAI / document analysis one), skip `split`/`baseline`. Still use
`dh.llm.ask` (cached Bedrock) and `log_run` for any evaluation you do (e.g. accuracy on a hand-labelled set).

## During

- Score with `dh.score`, log with `dh.log_run` and check `make board`. Commit before logging.
- Merge to main every ~2h (`/sync` in Claude Code if you're running worktrees).
- Shared decisions (metric, split, final model) → one line in the CLAUDE.md decisions log.

## Timeline (official schedule in CONTEXT.md)

| When | What |
|---|---|
| Sat 10:30 | Challenge presentation: fill CLAUDE.md TODOs live. |
| Sat 12:00–14:00 | Hacking starts. Kickoff steps above. Baseline logged + app skeleton running. |
| Sat PM–night | EDA → features → models. AWS/app lane: pipeline + diagram + `make app` showing real output by midnight. |
| Sun AM | Pick the final approach (decisions log). Feature freeze ~13:00. |
| Sun 13:00–16:00 | Explainability, app polish, record video footage while still on site. |
| **Sun 23:59** | **GitHub repo + application due.** Do the final push by 22:00. |
| Mon AM | One-pager, tech doc, video edit. `make backup` before **13:59** (AWS wiped). |
| **Mon 14:00** | **Video + one-pager + technical doc due.** |
| Fri Nov 20, 14:00 | Finalist pitches (M-5519, Lassonde). |

## Safety

`.claude/hooks/guard_bash.py` blocks agents from cloud deletes, force-pushes, force-adding ignored files and committing keys.
`data/`, `.env` and `*.csv` (except `results.csv`/`splits/`) are gitignored. Run `make scan` before making the repo public.
