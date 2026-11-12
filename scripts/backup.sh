#!/usr/bin/env bash
# The event AWS accounts are closed and wiped at the deadline. Run this before the deadline:
# it pulls outputs/ from S3 (if used) and commits + pushes everything that matters.
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; [ -f .env ] && . ./.env; set +a
if [ -n "${S3_BUCKET:-}" ]; then mkdir -p outputs && aws s3 sync "s3://$S3_BUCKET/outputs" outputs/ || true; fi
git add -A results.csv CONTEXT.md deliverables/ 2>/dev/null || true
git commit -m "backup before AWS teardown" || true
git push
echo "Also save locally: the video file, slide/one-pager PDFs, any screenshots of the AWS console/architecture."
