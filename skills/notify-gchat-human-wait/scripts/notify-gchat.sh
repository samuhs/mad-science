#!/usr/bin/env bash
# notify-gchat.sh — thin wrapper that notifies Google Chat when the Claude turn
# is waiting for human input.
#
# This script only locates `.env`, exports GCHAT_WEBHOOK_URL and delegates the
# payload/formatting work to notify_gchat.py (a cardsV2 card, which Google Chat
# actually renders). Keep formatting logic out of bash.
#
# Usage:
#   notify-gchat.sh "question awaiting a response" ["project name"] ["waiting"|"done"]
#
# Behavior:
#   * Reads GCHAT_WEBHOOK_URL from .env at the repository root.
#   * Never prints the webhook value.
#   * Fail-silent: on any failure it warns on stderr and exits 0.
#
# Requirements: bash + python3 (system python3 is enough — stdlib only).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SENDER="$SCRIPT_DIR/notify_gchat.py"

# Repo root: walk up until .env is found. Start from the working directory —
# when installed as a plugin the script lives outside the project — and fall
# back to the script's own location for skills vendored inside the repo.
find_env_root() {
  local dir="$1"
  while [[ ! -f "$dir/.env" && "$dir" != "/" ]]; do
    dir="$(dirname "$dir")"
  done
  [[ -f "$dir/.env" ]] && echo "$dir"
}
ROOT="$(find_env_root "$PWD" || find_env_root "$SCRIPT_DIR" || true)"
[[ -n "$ROOT" ]] || { echo "notify-gchat: .env not found" >&2; exit 1; }

# Read GCHAT_WEBHOOK_URL from .env without `source`: values may contain shell
# metacharacters (e.g. the URL's `&`), which `source` would interpret as
# operators and silently break. Extract the value after KEY= (trim spaces).
# NOTE: `read -r` returns non-zero on a final line with no trailing newline, so
# the loop must be written `while read -r _line || [[ -n "$_line" ]]` — a plain
# `while read` would silently skip a single-line .env (very common) and report
# the webhook as "not configured".
ENV_FILE="$ROOT/.env"
while IFS= read -r _line || [[ -n "$_line" ]]; do
  [[ "$_line" =~ ^[[:space:]]*$ ]] && continue          # skip blank
  [[ "$_line" =~ ^[[:space:]]*# ]] && continue          # skip comments
  _key="${_line%%=*}"
  if [[ "$_key" == "GCHAT_WEBHOOK_URL" ]]; then
    export GCHAT_WEBHOOK_URL="${_line#*=}"
    break
  fi
done < "$ENV_FILE"

QUESTION="${1:?question is required}"
PROJECT="${2:-$(basename "$ROOT")}"
KIND="${3:-waiting}"

# Delegate formatting + delivery. Prefer the repo venv when present; the script
# is stdlib-only, so any python3 works.
PYTHON="$ROOT/.venv/bin/python"
[[ -x "$PYTHON" ]] || PYTHON="$(command -v python3)"

exec "$PYTHON" "$SENDER" --project "$PROJECT" --kind "$KIND" --message "$QUESTION"