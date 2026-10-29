#!/usr/bin/env bash
# Attest demo — Piece 3: the pre-recorded c3373b81 result + close.
#
# Usage, on Vermithor, in ~/attest:
#   bash demo_piece3.sh
#
# This is NOT a live run. It prints the finished Oct 26 result,
# read from the ledger already saved by demo_piece1.sh, with a
# pre-recorded label on screen the whole time. No ELSD, no GPU,
# no new computation. If the ledger file is missing, it prints
# the published c3373b81 numbers from the repo fixture instead
# of failing silently — the banner still says pre-recorded.
#
# For testing elsewhere, override:
#   ATTEST_LEDGER=... bash demo_piece3.sh
set -u

LEDGER="${ATTEST_LEDGER:-/tmp/attest-c3373b81-ledger.json}"

banner() {
  echo ""
  echo "================================================================"
  echo "$1"
  echo "================================================================"
  echo ""
}

clear 2>/dev/null || printf '\n\n\n'
banner "PRE-RECORDED  —  Result from Oct 26, 2026  (not a live run)"
echo "H2O, 5000 iterations, rerun with a larger budget — not a resume."
echo "The original run took 93 minutes. This clip replays its result only."
sleep 3

banner "What the engine itself said"
echo "VQE energy:  -75.01259016765118 Ha"
echo "Error:       0.0357 kcal/mol  (chemical accuracy gate: 1.0 kcal/mol)"
echo "Log line:    [OK] Chemical accuracy achieved"
echo "Verdict:     abstain — optimizer_budget_exhausted"
sleep 4

banner "What Attest says about that result"
if [ -f "$LEDGER" ]; then
  python3 -c "
import json
d = json.load(open('$LEDGER'))
print('Headline:', d['headline'])
print('')
for c in d['checks']:
    print(f\"  {c['name']:<20} {c['verdict']}\")
"
else
  echo "Headline: REVIEW"
  echo ""
  echo "  engine_hash          VERIFIED"
  echo "  sector               VERIFIED"
  echo "  truncation           VERIFIED"
  echo "  chemical_accuracy    VERIFIED"
  echo "  budget               REVIEW"
  echo "  source_agreement     VERIFIED"
fi
sleep 4

banner "Close — what is new, what is pre-existing"
echo "New in this hackathon:  Attest (this repo), WSL fix for MuseDesk."
echo "Pre-existing, disclosed: MuseDesk, Prometheus/ELSD (closed, black-box)."
echo "Attest does NOT overrule the engine abstain to VERIFIED."
echo "REVIEW is the honest headline — not a pass, not a failure."
echo ""
sleep 2
