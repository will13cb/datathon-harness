#!/usr/bin/env bash
# Pull the challenge data into data/raw/ (gitignored). Usage: scripts/get-data.sh [s3://bucket/prefix]
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; [ -f .env ] && . ./.env; set +a
src="${1:-s3://${S3_BUCKET:?set S3_BUCKET in .env or pass s3://...}}"
mkdir -p data/raw
aws s3 sync "$src" data/raw/
ls -lh data/raw/
echo "Now: record file names / row counts / date ranges in CONTEXT.md (Verified)."
