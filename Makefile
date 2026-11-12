SHELL := /bin/bash
ENV   := set -a; [ -f .env ] && . ./.env; set +a;
PY    := .venv/bin/python
.DEFAULT_GOAL := help
.PHONY: help setup data check split baseline board test worktrees backup scan claude

help: ## List targets
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup: ## venv + deps + .env
	@if command -v uv >/dev/null; then uv venv -q .venv && uv pip install -q -p .venv -e '.[dev]'; \
	 else python3 -m venv .venv && $(PY) -m pip install -q -e '.[dev]'; fi
	@[ -f .env ] || { cp .env.example .env; echo "created .env, fill it in"; }
	@echo "setup done"

data: ## Pull challenge data from S3 into data/raw/
	@bash scripts/get-data.sh

check: ## Load the data and print a summary
	@$(ENV) $(PY) -m dh check

split: ## Freeze the train/val split (run ONCE, then commit splits/)
	@$(ENV) $(PY) -m dh split

baseline: ## Score constant + GBM baselines and log them
	@$(ENV) $(PY) -m dh baseline

board: ## Leaderboard from results.csv
	@$(PY) -m dh board

test: ## Run tests (offline)
	@LLM_PROVIDER=mock $(PY) -m pytest -q

worktrees: ## One worktree per lane: make worktrees [NAMES="eda models"]
	@bash scripts/worktrees.sh $(NAMES)

backup: ## Commit + push results and deliverables (before AWS teardown!)
	@bash scripts/backup.sh

scan: ## Scan git history for secrets before going public
	@bash scripts/scan-secrets.sh

claude: ## Launch Claude Code with .env loaded
	@$(ENV) claude
