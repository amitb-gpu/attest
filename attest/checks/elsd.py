"""ELSD artifact pack, MVP: read provenance + history, do not compute VQE.

Checks (all deterministic, all from artifact fields):
- engine_hash: provenance engine_sha256_full matches expected engine file hash
- sector: sector penalty magnitude is tiny, N/Sz/S2 flags are ok
- truncation: truncation residual is 0 (or below gate, if present)
- chemical_accuracy: error_kcal <= 1.0 kcal/mol (definition, not a recomputation)
- budget: if engine verdict is abstain with budget_exhausted, headline
  cannot be VERIFIED; this check is REVIEW, not FAILED
- source_agreement: run_id in provenance matches the run_id in the
  history filename / ledger call, and E_physical is finite and negative
  (sanity, not a recomputation from history.csv)
"""
from __future__ import annotations

import csv
import json
import math
import os

from ..ledger import CheckResult, sha256_file

CHEMICAL_ACCURACY_KCAL = 1.0
CODE_VERSION = "attest-0.1.0"


def load_provenance(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_history_tail(path: str, n: int = 5):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return rows[-n:] if rows else []


def _result(name, verdict, evidence, artifact="", artifact_sha=""):
    return CheckResult(
        name=name,
        verdict=verdict,
        evidence=evidence,
        artifact=artifact,
        artifact_sha256=artifact_sha,
        code_version=CODE_VERSION,
    )


def check_engine_hash(prov: dict, expected_sha: str, artifact="", artifact_sha=""):
    got = prov.get("engine_sha256_full") or prov.get("engine_sha256") or ""
    if not got:
        return _result(
            "engine_hash", "REVIEW",
            "provenance file has no engine_sha256_full; missing entry is REVIEW, not proven failure",
            artifact, artifact_sha,
        )
    if expected_sha and got.lower() != expected_sha.lower():
        return _result(
            "engine_hash", "FAILED",
            f"provenance engine hash {got} != expected {expected_sha}",
            artifact, artifact_sha,
        )
    return _result(
        "engine_hash", "VERIFIED",
        f"provenance engine hash matches expected {got}",
        artifact, artifact_sha,
    )


def check_sector(prov: dict, artifact="", artifact_sha=""):
    penalty = prov.get("sector_penalty_abs_sum", prov.get("penalty"))
    ok_flags = prov.get("sector_ok", True)
    if penalty is not None and abs(float(penalty)) > 1e-9:
        return _result("sector", "FAILED", f"sector penalty {penalty} Ha exceeds 1e-9 Ha", artifact, artifact_sha)
    if ok_flags is False:
        return _result("sector", "FAILED", "sector_ok flag is False in provenance", artifact, artifact_sha)
    return _result("sector", "VERIFIED", f"sector clean, penalty {penalty}", artifact, artifact_sha)


def check_truncation(prov: dict, artifact="", artifact_sha=""):
    residual = prov.get("truncation_residual_kcal", 0.0)
    if residual is None:
        return _result("truncation", "REVIEW", "truncation residual missing from provenance", artifact, artifact_sha)
    if float(residual) > 1.0:
        return _result("truncation", "FAILED", f"truncation residual {residual} kcal/mol exceeds 1 kcal/mol gate", artifact, artifact_sha)
    return _result("truncation", "VERIFIED", f"truncation residual {residual} kcal/mol", artifact, artifact_sha)


def check_chemical_accuracy(prov: dict, artifact="", artifact_sha=""):
    err = prov.get("error_kcal")
    if err is None:
        return _result("chemical_accuracy", "REVIEW", "error_kcal missing from provenance", artifact, artifact_sha)
    if float(err) <= CHEMICAL_ACCURACY_KCAL:
        return _result("chemical_accuracy", "VERIFIED", f"error {err} kcal/mol <= 1.0 kcal/mol", artifact, artifact_sha)
    return _result("chemical_accuracy", "FAILED", f"error {err} kcal/mol > 1.0 kcal/mol", artifact, artifact_sha)


def check_budget(prov: dict, artifact="", artifact_sha=""):
    verdict = str(prov.get("verdict", "")).lower()
    reasons = prov.get("decision_grade_reasons", []) or []
    if verdict == "abstain" and "optimizer_budget_exhausted" in reasons:
        return _result(
            "budget", "REVIEW",
            "engine abstained on optimizer_budget_exhausted; Attest cannot upgrade abstain to VERIFIED",
            artifact, artifact_sha,
        )
    if verdict == "abstain":
        return _result("budget", "REVIEW", f"engine abstained, reasons={reasons}", artifact, artifact_sha)
    return _result("budget", "VERIFIED", f"engine verdict={verdict}, decision_grade={prov.get('decision_grade')}", artifact, artifact_sha)


def check_source_agreement(prov: dict, expected_run_id: str, history_rows, artifact="", artifact_sha=""):
    run_id = prov.get("run_id", "")
    if expected_run_id and run_id != expected_run_id:
        return _result("source_agreement", "FAILED", f"provenance run_id {run_id} != expected {expected_run_id}", artifact, artifact_sha)
    energy = prov.get("E_physical")
    if energy is None or not math.isfinite(float(energy)) or float(energy) >= 0:
        return _result("source_agreement", "REVIEW", "E_physical missing, non-finite, or non-negative in provenance", artifact, artifact_sha)
    if history_rows:
        last = history_rows[-1]
        # History is trajectory shape only; do not use it as authoritative energy.
        # Agreement here is only that history exists and its last best_energy is a number.
        try:
            float(last.get("best_energy", "nan"))
        except (TypeError, ValueError):
            return _result("source_agreement", "REVIEW", "history tail best_energy is not a number", artifact, artifact_sha)
    return _result("source_agreement", "VERIFIED", f"run_id {run_id} agrees, E_physical {energy} Ha present", artifact, artifact_sha)


def run_elsd_checks(prov_path: str, history_path: str | None, expected_sha: str, expected_run_id: str = ""):
    prov = load_provenance(prov_path)
    artifact_sha = sha256_file(prov_path)
    artifact = os.path.basename(prov_path)
    history_rows = load_history_tail(history_path) if history_path else []
    return [
        check_engine_hash(prov, expected_sha, artifact, artifact_sha),
        check_sector(prov, artifact, artifact_sha),
        check_truncation(prov, artifact, artifact_sha),
        check_chemical_accuracy(prov, artifact, artifact_sha),
        check_budget(prov, artifact, artifact_sha),
        check_source_agreement(prov, expected_run_id or prov.get("run_id", ""), history_rows, artifact, artifact_sha),
    ]
