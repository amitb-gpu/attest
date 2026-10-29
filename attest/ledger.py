"""Claim ledger: deterministic combination of check results.

Verdict precedence for a headline:
  FAILED > REVIEW/UNRESOLVABLE > VERIFIED
A missing provenance entry is REVIEW/UNRESOLVABLE, never FAILED
on its own, and never VERIFIED by assumption.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CheckResult:
    name: str
    verdict: str  # VERIFIED, FAILED, REVIEW, UNRESOLVABLE, NO-SIGMA
    evidence: str
    artifact: str = ""
    artifact_sha256: str = ""
    code_version: str = "attest-0.1.0"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def headline(results) -> str:
    verdicts = {r.verdict for r in results}
    if "FAILED" in verdicts:
        return "FAILED"
    if verdicts & {"REVIEW", "UNRESOLVABLE", "NO-SIGMA"}:
        return "REVIEW"
    if verdicts == {"VERIFIED"}:
        return "VERIFIED"
    return "REVIEW"


@dataclass
class Ledger:
    run_id: str
    headline: str
    checks: list
    notes: list

    def to_dict(self):
        return {
            "run_id": self.run_id,
            "headline": self.headline,
            "checks": [asdict(c) for c in self.checks],
            "notes": self.notes,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def build_ledger(run_id: str, results, notes=None) -> Ledger:
    return Ledger(
        run_id=run_id,
        headline=headline(results),
        checks=list(results),
        notes=list(notes or []),
    )
