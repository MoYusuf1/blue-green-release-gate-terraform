#!/usr/bin/env bash
# The whole drill with no prompts: reject a healthy-but-wrong candidate, promote, break live traffic, roll back.
# Used by `make e2e` and CI. Needs Docker, Terraform and Python 3. Destroys everything it created on exit.
set -euo pipefail
cd "$(dirname "$0")/.."

LIVE=http://127.0.0.1:8080 PREVIEW=http://127.0.0.1:8081
PROBE_LOG=${PROBE_LOG:-$(mktemp)}
tf() { terraform -chdir=terraform "$@"; }
step() { printf '\n== %s\n' "$*"; }
fail() { printf 'E2E FAIL: %s\n' "$*" >&2; exit 1; }
# A replaced container needs a moment before it answers; wait for the expected response instead of sleeping blindly.
wait_for() { for _ in $(seq 30); do curl -fsS "$1" 2>/dev/null | grep -q "$2" && return 0; sleep 1; done; fail "$1 never returned $2"; }
release() { python3 scripts/set_release.py "$@" >/dev/null; tf apply -auto-approve -input=false >/dev/null; }

trap 'tf destroy -auto-approve -input=false >/dev/null 2>&1 || true; rm -rf generated' EXIT

step "Launch Blue (live) and Green (preview)"
cp terraform/lab.auto.tfvars.example.json terraform/lab.auto.tfvars.json
tf init -input=false >/dev/null
tf apply -auto-approve -input=false >/dev/null
wait_for "$LIVE/quote" '"total_cents":1200'
wait_for "$PREVIEW/quote" '"total_cents":1200'
python3 scripts/check_release.py blue v1 --url "$LIVE"
python3 scripts/check_release.py green v2

step "A healthy candidate with the wrong quote is rejected"
release green --version v2-bad --quote-total 999
wait_for "$PREVIEW/health" '"ready":true'
wait_for "$PREVIEW/quote" '"total_cents":999'
if python3 scripts/check_release.py green v2-bad; then fail "the gate passed a wrong quote"; fi
python3 scripts/check_release.py blue v1 --url "$LIVE"

step "Repair Green and promote it"
release green --version v2 --quote-total 1200 --activate
wait_for "$PREVIEW/quote" '"version":"v2"'
python3 scripts/reload_proxy.py
python3 scripts/check_release.py green v2 --url "$LIVE"

step "Break live traffic and roll back while the probe watches"
python3 scripts/probe.py "$LIVE/quote" --seconds 45 --expected-total 1200 >"$PROBE_LOG" 2>/dev/null &
probe=$!
sleep 3
release green --quote-total 999
wait_for "$LIVE/quote" '"total_cents":999'
if python3 scripts/check_release.py green v2 --url "$LIVE"; then fail "the gate passed a wrong live quote"; fi
release blue --activate
python3 scripts/reload_proxy.py
python3 scripts/check_release.py blue v1 --url "$LIVE"
wait "$probe"

step "Probe result"
python3 - "$PROBE_LOG" <<'EOF'
import json, sys
lines = [json.loads(line) for line in open(sys.argv[1])]
summary, samples = lines[-1], lines[:-1]
print(json.dumps(summary))
assert summary["wrong_total"] > 0, "the probe never saw the wrong quote"
assert samples[-1]["ok"], "live traffic was still wrong when the probe stopped"
EOF
echo "E2E PASS"
