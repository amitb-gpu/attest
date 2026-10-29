import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from attest.benchmark import run_benchmark
from attest.checks.cusod import replay_cusod
from attest.checks.spectrans import run_spectrans_checks
from attest.report import render_markdown
from attest.ledger import build_ledger
from attest.checks.elsd import run_elsd_checks

FIX = Path(__file__).resolve().parents[1] / "examples" / "fixtures"
ENGINE = "600b7727151147fb10e98f2e1bef4c17f5cf09c703d7f78479456b136fc57999"


def test_cusod_disagreement_is_review():
    r = replay_cusod({"source_a": 9.2, "source_b": 3.46}, 3.46)
    assert r.verdict == "REVIEW"
    assert "not presented as settled truth" in r.evidence or "not" in r.evidence


def test_spectrans_two_checks():
    checks = run_spectrans_checks({"tests_passed": 160, "tests_total": 160, "code_version": "v1", "seed": 0})
    assert [c.verdict for c in checks] == ["VERIFIED", "VERIFIED"]
    checks = run_spectrans_checks({"tests_passed": 159, "tests_total": 160})
    assert checks[0].verdict == "FAILED"
    assert checks[1].verdict == "REVIEW"


def test_benchmark_detects_injected_faults_and_reports_miss():
    b = run_benchmark(str(FIX))
    assert b["injected_faults"] == 5
    assert b["detected"] == 5
    assert b["detection_rate"] == 1.0
    assert b["honest_miss"] == "history_energy_drift_small"


def test_report_renders_headline():
    checks = run_elsd_checks(str(FIX / "c3373b81_provenance.json"), str(FIX / "c3373b81_history_tail.csv"), ENGINE)
    ledger = build_ledger("c3373b81", checks, notes=["test"])
    md = render_markdown(ledger)
    assert "Headline: REVIEW" in md
    assert "chemical_accuracy" in md
