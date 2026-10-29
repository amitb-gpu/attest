"""Cu-SOD replay: inconsistent-source detection, not settled truth.

Given values for the same quantity from different sources, plus a
value recomputed from a single consistent source, report whether
the sources agree. Disagreement is REVIEW (inconsistent-source
detection), not FAILED, and the recomputed value is reported as
a consistent-source recomputation, not as a settled physical truth.
Sigma reconciliation for Cu-SOD is still open; see README.md.
"""
from __future__ import annotations

from ..ledger import CheckResult


def replay_cusod(sources: dict, recomputed: float, tolerance: float = 0.1):
    """sources: mapping source name -> reported value. recomputed: float."""
    values = list(sources.values())
    if not values:
        return CheckResult(
            name="cusod_source_agreement", verdict="REVIEW",
            evidence="no source values supplied", code_version="attest-0.1.0",
        )
    spread = max(values) - min(values)
    if spread <= tolerance:
        return CheckResult(
            name="cusod_source_agreement", verdict="VERIFIED",
            evidence=f"sources agree within {tolerance}: {sources}, recomputed {recomputed}",
            code_version="attest-0.1.0",
        )
    return CheckResult(
        name="cusod_source_agreement", verdict="REVIEW",
        evidence=(
            f"sources disagree: {sources} (spread {spread}); "
            f"consistent-source recomputation is {recomputed}, "
            "not presented as settled truth; sigma reconciliation open"
        ),
        code_version="attest-0.1.0",
    )
