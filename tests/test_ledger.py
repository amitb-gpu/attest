import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from attest.checks.elsd import run_elsd_checks
from attest.ledger import build_ledger

FIX = Path(__file__).resolve().parents[1] / "examples" / "fixtures"
ENGINE = "600b7727151147fb10e98f2e1bef4c17f5cf09c703d7f78479456b136fc57999"


def test_c3373b81_headline_is_review_not_verified():
    results = run_elsd_checks(
        str(FIX / "c3373b81_provenance.json"),
        str(FIX / "c3373b81_history_tail.csv"),
        ENGINE,
    )
    by_name = {r.name: r.verdict for r in results}
    assert by_name["engine_hash"] == "VERIFIED"
    assert by_name["sector"] == "VERIFIED"
    assert by_name["truncation"] == "VERIFIED"
    assert by_name["chemical_accuracy"] == "VERIFIED"
    assert by_name["budget"] == "REVIEW"
    ledger = build_ledger("H2O__q0__m1__autoeautoo__spc-d6__adam__seed001__c3373b81", results)
    assert ledger.headline == "REVIEW"


def test_engine_hash_mismatch_is_failed():
    results = run_elsd_checks(
        str(FIX / "c3373b81_provenance.json"),
        str(FIX / "c3373b81_history_tail.csv"),
        "0" * 64,
    )
    by_name = {r.name: r.verdict for r in results}
    assert by_name["engine_hash"] == "FAILED"
    assert build_ledger("x", results).headline == "FAILED"


def test_cli():
    import json
    import subprocess
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "ledger.json")
        subprocess.run(
            [
                sys.executable, "-m", "attest", "check",
                "--provenance", str(FIX / "c3373b81_provenance.json"),
                "--history", str(FIX / "c3373b81_history_tail.csv"),
                "--engine-sha", ENGINE,
                "--out", out,
            ],
            check=True, cwd=str(Path(__file__).resolve().parents[1]),
            capture_output=True, text=True,
        )
        data = json.load(open(out))
        assert data["headline"] == "REVIEW"
        assert data["run_id"].endswith("c3373b81")
