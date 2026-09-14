#!/usr/bin/env bash
# Start both parties for one divorce scenario. Both run the SAME agent — varlow/agent.py,
# Strands — with the same system prompt and the same registry; only the position differs.
#
#   ./divorce/run.sh a-aligned
#   ./divorce/run.sh b-knife-edge
set -euo pipefail
cd "$(dirname "$0")/.."
SCENARIO="${1:?usage: divorce/run.sh <scenario> [run-name]}"
RUNDIR="divorce/runs/${2:-$SCENARIO}"
: "${RUN_SECONDS:=5400}"
[ -d "divorce/$SCENARIO" ] || { echo "no such scenario: $SCENARIO"; exit 1; }

need() { aws ssm get-parameter --name "$1" --with-decryption --region us-east-1 \
         --query Parameter.Value --output text; }
OR=$(need /idntty/bot/openrouter-key)
mkdir -p "$RUNDIR"

side() {   # handle  party  other  role
  IDNTTY_KEY=$(need "/$1/agent-key") OPENROUTER_API_KEY="$OR" RUN_SECONDS="$RUN_SECONDS" \
    SYSTEM="divorce/party.system.md" REGISTRY="divorce/REGISTRY.md" \
    POSITION="divorce/$SCENARIO/$1.md" HANDLE="$1" PARTY="$2" OTHER="$3" \
    THIRD="mediator" ROLE="$4" \
    GROUP_NOTE_FILE="divorce/notes/group.md" PRIVATE_NOTE_FILE="divorce/notes/private.md" \
    RUNTIME="${RUNTIME:-local}" \
    nohup varlow/.venv/bin/python varlow/agent.py > "$RUNDIR/$1.log" 2>&1 &
  echo "$1  pid $!  $SCENARIO/$1.md"
}
side hale   "Ren Hale"    "Marren" "Ren Hale's side"
side marren "Dana Marren" "Hale"   "Dana Marren's side"
