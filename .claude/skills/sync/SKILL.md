---
name: sync
description: Merge lane branches (lane/*) into main, run tests, refresh the leaderboard, fan main back out. Use when the user says /sync.
disable-model-invocation: true
---

1. `git worktree list` and `git log --oneline main..<branch>` for each `lane/*` branch. If a worktree has uncommitted changes, stop and ask.
2. From the main checkout, `git merge --no-ff <branch>` one at a time. Conflict in `results.csv`: keep both sides' rows (it's append-only). Other conflicts: resolve only if obvious, otherwise `git merge --abort` and ask.
3. `make test`. If it fails, revert the last merge (`git revert -m 1 HEAD`) and report which lane broke it.
4. `make board` and paste the top 5 into the reply.
5. For each clean worktree: `git -C <path> merge main`.
6. Report what merged, test result, the leaderboard, and anything skipped.
