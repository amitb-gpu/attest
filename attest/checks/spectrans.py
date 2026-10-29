"""SpectraNS-3D pack, MVP scope: exactly 2 checks.

1. tests_pass: a run report must state passed/total tests, with no failures.
2. reproducibility: a run report must state a code version / commit and a seed
   (or 'deterministic' flag), otherwise the run cannot be reproduced from the report.
Both are deterministic reads of a report dict, not recomputations.
"""
from __future__ import annotations

from ..ledger import CheckResult


def check_tests_pass(report: dict):
    passed = report.get("tests_passed")
    total = report.get("tests_total")
    if passed is None or total is None:
        return CheckResult(name="spectrans_tests_pass", verdict="REVIEW",
                           evidence="report missing tests_passed/tests_total", code_version="attest-0.1.0")
    if passed == total:
        return CheckResult(name="spectrans_tests_pass", verdict="VERIFIED",
                           evidence=f"tests {passed}/{total} passed", code_version="attest-0.1.0")
    return CheckResult(name="spectrans_tests_pass", verdict="FAILED",
                       evidence=f"tests {passed}/{total} passed, failures present", code_version="attest-0.1.0")


def check_reproducibility(report: dict):
    version = report.get("code_version") or report.get("commit")
    seed = report.get("seed")
    deterministic = report.get("deterministic")
    if version and (seed is not None or deterministic):
        return CheckResult(name="spectrans_reproducibility", verdict="VERIFIED",
                           evidence=f"code_version/commit={version}, seed={seed}, deterministic={deterministic}",
                           code_version="attest-0.1.0")
    return CheckResult(name="spectrans_reproducibility", verdict="REVIEW",
                       evidence="report missing code version/commit or seed/deterministic flag",
                       code_version="attest-0.1.0")


def run_spectrans_checks(report: dict):
    return [check_tests_pass(report), check_reproducibility(report)]
