# Technical documentation

## Data
Sources, rows, date range, cleaning (copy from CONTEXT.md "Verified").

## Validation
Split (`harness.toml`, `splits/val_ids.csv`), metric, leakage checks.

## Approach
Baseline → final model. Table from `make board` (run_id, model, features, val score).

## Explainability
Feature importance / SHAP / LLM rationale, plus what a portfolio manager should take from it.

## Architecture (AWS)
See aws/architecture.md. Each service: what it does, why it's that service, how it scales.

## Reproduce
`make setup && make data && make split && make baseline` + the final experiment script.

## Limitations
