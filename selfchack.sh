#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
command -v python3 >/dev/null || { echo 'python3 missing'; exit 1; }
python3 -m py_compile "$ROOT/bot.py" "$ROOT/node-agent.py"
bash -n "$ROOT/setup.sh" "$ROOT/install_node.sh"
node --check "$ROOT/ecosystem.config.js"
! grep -n 'params = {"api_key"' "$ROOT/bot.py" "$ROOT/node-agent.py" >/dev/null || { echo 'query-string API key path detected'; exit 1; }
grep -q 'PINGGY_SSH_PORT=443' "$ROOT/.env" || { echo 'Pinggy server port must be 443'; exit 1; }
! grep -q 'Reconnect SSHX' "$ROOT/bot.py" || { echo 'Removed UI action still references Reconnect SSHX'; exit 1; }
printf 'RGNODES ultra self-check: PASS\n'
