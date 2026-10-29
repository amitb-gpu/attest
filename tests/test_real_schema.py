import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from attest.checks.elsd import run_elsd_checks
from attest.ledger import build_ledger

FIX = Path(__file__).resolve().parents[1] / "examples" / "fixtures"
ENGINE = "600b7727151147fb10e98f2e1bef4c17f5cf09c703d7f78479456b136fc57999"


def test_real_schema_c3373b81_headline_is_review():
    results = run_elsd_checks(
        str(FIX / "c3373b81_real_schema.json"),
        str(FIX / "c3373b81_history_tail.csv"),
        ENGINE,
    )
    by_name = {r.name: r.verdict for r in results}
    assert by_name["engine_hash"] == "VERIFIED", by_name
    assert by_name["sector"] == "VERIFIED", by_name
    assert by_name["truncation"] == "VERIFIED", by_name
    assert by_name["chemical_accuracy"] == "VERIFIED", by_name
    assert by_name["budget"] == "REVIEW", by_name
    assert by_name["source_agreement"] == "VERIFIED", by_name
    assert build_ledger("c3373b81", results).headline == "REVIEW"


def test_truncated_engine_hash_prefix_is_verified():
    # Only truncated hash, no full hash anywhere: prefix match, not FAILED.
    import json, tempfile, os
    prov = {
        "run_id": "x", "engine_sha256": "600b7727151147fb",
        "energies": {"vqe_physical": -1.0}, "error_kcal": 0.1,
        "sector_clean": True, "truncation": {"l1_kcal": 0.0},
        "verdict": "abstain", "decision_grade_reasons": ["optimizer_budget_exhausted"],
    }
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "p.json")
        json.dump(prov, open(p, "w"))
        results = run_elsd_checks(p, None, ENGINE)
        assert {r.name: r.verdict for r in results}["engine_hash"] == "VERIFIED"


def test_missing_sector_and_truncation_are_review_not_verified():
    import json, tempfile, os
    prov = {
        "run_id": "x", "engine_sha256": ENGINE,
        "energies": {"vqe_physical": -1.0}, "error_kcal": 0.1,
        "verdict": "abstain", "decision_grade_reasons": ["optimizer_budget_exhausted"],
    }
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "p.json")
        json.dump(prov, open(p, "w"))
        by_name = {r.name: r.verdict for r in run_elsd_checks(p, None, ENGINE)}
        assert by_name["sector"] == "REVIEW", by_name
        assert by_name["truncation"] == "REVIEW", by_name
