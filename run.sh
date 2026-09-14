#!/usr/bin/env bash
# Start both negotiators for one scenario.
#
#   ./run.sh b-knife-edge                          # default accounts varlow / ninebark
#   ./run.sh b-knife-edge second-take               # same pair, its own run directory
#   ./run.sh c-no-zone c-take2 buyside sellside     # a second pair, so two runs can overlap
#
# The account pair matters: one idntty account cannot hold two positions at once, so a
# parallel scenario needs its own pair of agents. The run name matters too: a run started
# under the scenario name overwrites the previous run of that scenario, logs and all.
set -euo pipefail
cd "$(dirname "$0")"
SCENARIO="${1:?usage: ./run.sh <scenario> [run-name] [buyer-handle seller-handle]}"
RUNDIR="acquihire/runs/${2:-$SCENARIO}"
BUYER="${3:-varlow}"; SELLER="${4:-ninebark}"
: "${RUN_SECONDS:=5400}"
[ -d "acquihire/positions/$SCENARIO" ] || { echo "no such scenario: $SCENARIO"; exit 1; }

need() { aws ssm get-parameter --name "$1" --with-decryption --region us-east-1 \
         --query Parameter.Value --output text; }
OR=$(need /idntty/bot/openrouter-key)
mkdir -p "$RUNDIR"

IDNTTY_KEY=$(need "/$BUYER/agent-key") OPENROUTER_API_KEY="$OR" RUN_SECONDS="$RUN_SECONDS" \
  POSITION="acquihire/positions/$SCENARIO/buyer.md" HANDLE="$BUYER" PARTY="Varlow Systems" \
  nohup varlow/.venv/bin/python varlow/agent.py > "$RUNDIR/$BUYER.log" 2>&1 &
echo "buyer  $BUYER  pid $!  $SCENARIO/buyer.md"

IDNTTY_KEY=$(need "/$SELLER/agent-key") PRIVATE_BASE_URL=https://openrouter.ai/api/v1 \
  PRIVATE_API_KEY="$OR" RUN_SECONDS="$RUN_SECONDS" \
  POSITION="acquihire/positions/$SCENARIO/seller.md" HANDLE="$SELLER" PARTY="Ninebark Labs" \
  nohup ninebark/.venv/bin/python ninebark/agent.py > "$RUNDIR/$SELLER.log" 2>&1 &
echo "seller $SELLER pid $!  $SCENARIO/seller.md"
