"""Attest CLI. Usage: python3 -m attest check --provenance X --history Y --engine-sha Z [--out ledger.json]"""
from __future__ import annotations

import argparse
import sys

from .checks.elsd import run_elsd_checks
from .ledger import build_ledger


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="attest")
    sub = ap.add_subparsers(dest="cmd", required=True)
    chk = sub.add_parser("check", help="check an ELSD artifact set")
    chk.add_argument("--provenance", required=True)
    chk.add_argument("--history", default=None)
    chk.add_argument("--engine-sha", default="")
    chk.add_argument("--run-id", default="")
    chk.add_argument("--out", default=None)
    args = ap.parse_args(argv)

    results = run_elsd_checks(args.provenance, args.history, args.engine_sha, args.run_id)
    run_id = args.run_id
    if not run_id:
        # run_id is taken from the provenance file by the source-agreement check;
        # fall back to the first check's evidence is not needed for the ledger
        # headline, so use the provenance run_id via a re-read here.
        import json as _json
        with open(args.provenance, encoding="utf-8") as fh:
            run_id = _json.load(fh).get("run_id", "")
    ledger = build_ledger(
        run_id,
        results,
        notes=[
            "Attest never computes a number; checks read artifact fields only.",
            "History is trajectory shape only, never the authoritative energy source.",
            "An engine abstain on budget is REVIEW, not VERIFIED and not FAILED.",
        ],
    )
    out = ledger.to_json()
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(out + "\n")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
