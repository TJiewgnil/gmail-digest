#!/usr/bin/env bash
# Local runner for the daily email digest (macOS / Linux).
# Mirrors run_local.ps1: load .env, fetch -> summarize.py -> send.
#
# Manual test:   ./run_local.sh
# Cron (08:00 daily, logging to a file):
#   0 8 * * *  cd /path/to/gmail-digest && ./run_local.sh >> digest.log 2>&1
set -euo pipefail

cd "$(dirname "$0")"

# Force UTF-8 so Chinese subjects / bodies / emoji survive the pipeline.
export PYTHONUTF8=1
export LC_ALL="${LC_ALL:-C.UTF-8}"

PY="${PYTHON:-python3}"
HOURS="${DIGEST_HOURS:-24}"

# --- load .env into the environment (real env vars still win) ---
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
else
  echo ".env not found — copy .env.example to .env and fill in credentials, or run: python setup.py" >&2
  exit 1
fi

# --- 1. fetch last N hours of mail ---
"$PY" fetch_inbox.py --hours "$HOURS" > inbox.json
echo "Fetched inbox.json"

# --- 2. summarize via the Anthropic API (needs ANTHROPIC_API_KEY) ---
"$PY" summarize.py inbox.json --out digest.md > /dev/null
echo "Wrote digest.md"

# --- 3. email the digest ---
"$PY" send_digest.py digest.md
echo "Done: digest sent."
