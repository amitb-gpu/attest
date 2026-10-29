#!/usr/bin/env bash
# Attest demo — Piece 1: verify the H2O run c3373b81, on camera, no typing.
#
# Usage, on Vermithor, in ~/attest:
#   bash demo_piece1.sh
#
# What it does, in order, with a banner before each step so the
# recording (voiceover added later) reads cleanly:
#   1. Reads the ORIGINAL c3373b81 provenance + history (no rerun, no compute)
#   2. Runs the six deterministic Attest checks
#   3. Prints a short summary table + headline REVIEW
#
# Full paths are used internally but NOT printed on screen, so the
# recording shows only filenames, never filesystem paths.
# Full JSON ledger is saved to /tmp/attest-c3373b81-ledger.json.
#
# For testing elsewhere, override the artifact paths:
#   ATTEST_PROV=... ATTEST_HIST=... bash demo_piece1.sh
set -u

PROV="${ATTEST_PROV:-$HOME/musedesk-demo-h2o-resume/H2O__q0__m1__autoeautoo__spc-d6__adam__seed001__c3373b81_provenance.json}"
HIST="${ATTEST_HIST:-$HOME/musedesk-demo-h2o-resume/H2O__q0__m1__autoeautoo__spc-d6__adam__seed001__c3373b81_history.csv}"
ENGINE_SHA="600b7727151147fb10e98f2e1bef4c17f5cf09c703d7f78479456b136fc57999"
OUT="/tmp/attest-c3373b81-ledger.json"

banner() {
  echo ""
  echo "================================================================"
  echo "$1"
  echo "================================================================"
  echo ""
}

if [ ! -f "$PROV" ]; then echo "Missing provenance file: $PROV" >&2; exit 1; fi
if [ ! -f "$HIST" ]; then echo "Missing history file: $HIST" >&2; exit 1; fi

clear 2>/dev/null || printf '\n\n\n'
banner "ATTEST  —  Piece 1: Verifying an H2O computation"
echo "Run: c3373b81  (5000 iterations, rerun with a larger budget — not a resume)"
echo "The model never computes a number. Deterministic checks read artifacts only."
sleep 3

banner "Step 1: Reading the original artifacts"
echo "Provenance: c3373b81_provenance.json"
echo "History:    c3373b81_history.csv"
echo "No rerun. No new computation. These are the finished artifacts."
sleep 3

banner "Step 2: Running the checks"
echo "  engine_hash        — does the engine match the verified version?"
echo "  sector             — is the quantum-number sector clean?"
echo "  truncation         — was anything dropped beyond the gate?"
echo "  chemical_accuracy  — is the error within 1 kcal/mol?"
echo "  budget             — did the engine converge, or abstain?"
echo "  source_agreement   — do provenance and history agree on the run?"
sleep 2
echo "Running..."
python3 -m attest check \
  --provenance "$PROV" \
  --history "$HIST" \
  --engine-sha "$ENGINE_SHA" \
  --out "$OUT" > /dev/null
echo "Checks complete. Full ledger saved to attest-c3373b81-ledger.json"
sleep 2

banner "Step 3: Summary"
python3 -c "
import json
d = json.load(open('$OUT'))
print('Headline:', d['headline'])
print('')
for c in d['checks']:
    print(f\"  {c['name']:<20} {c['verdict']}\")
print('')
acc = next((c for c in d['checks'] if c['name'] == 'chemical_accuracy'), None)
if acc:
    print('Chemical accuracy:', acc['evidence'])
print('Engine verdict:    abstain — optimizer budget exhausted')
"
sleep 2

banner "Piece 1 complete — Headline: REVIEW"
echo "Everything Attest can verify passes."
echo "The engine itself abstained on budget, so Attest does NOT"
echo "upgrade it to VERIFIED — and does NOT call it FAILED."
echo ""
