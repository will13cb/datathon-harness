#!/usr/bin/env bash
# One git worktree per lane, so parallel agents never edit the same checkout.
# Usage: scripts/worktrees.sh [lane ...]   (default: eda features models aws pitch)
set -euo pipefail
root="$(git rev-parse --show-toplevel)"; repo="$(basename "$root")"; cd "$root"
names=("$@"); [ ${#names[@]} -eq 0 ] && names=(eda features models aws pitch)
for n in "${names[@]}"; do
  path="$(dirname "$root")/${repo}-${n}"
  [ -d "$path" ] && { echo "• $path exists"; continue; }
  if git show-ref --verify --quiet "refs/heads/lane/$n"; then git worktree add -q "$path" "lane/$n"
  else git worktree add -q "$path" -b "lane/$n"; fi
  [ -f .env ] && cp .env "$path/.env"
  [ -d data/raw ] && ln -sfn "$root/data/raw" "$path/data/raw"   # share data, don't copy it
  echo "✓ $path (lane/$n)"
done
echo "Then: cd ../${repo}-<lane> && claude   |   merge back with: git merge lane/<lane>"
