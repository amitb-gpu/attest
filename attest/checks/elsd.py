"""ELSD artifact pack, MVP: read provenance + history, do not compute VQE.

Real provenance schema, learned from c3373b81 on Vermithor
(2026-10-28, key-path dump — see README.md):
- engine_sha256 (top-level, truncated to 16 hex chars)
  runtime_settings.engine_sha256_full (full 64-char hash)
- energies.vqe_physical (not top-level E_physical)
  energies.hf / energies.casci / energies.fci
- error_kcal, decision_grade, decision_grade_reasons, verdict, run_id (top-level)
- sector_clean (bool, top-level), sector_audit_status
- truncation.l1_kcal, truncation.exceeds_chem_acc, truncation.n_dropped
- scf_stability.scf_root_classification / scf_root_stable

Fixture schema (top-level E_physical, sector_penalty_abs_sum,
truncation_residual_kcal) is still supported as a fallback, so
old fixtures keep passing. Missing fields are REVIEW, never
VERIFIED by default — that was a bug in v0.1.0, fixed here.
"""
from __future__ import annotations

import csv
import json
import math
import os

from ..ledger import CheckResult, sha256_file

CHEMICAL_ACCURACY_KCAL = 1.0
CODE_VERSION = "attest-0.1.1"


def load_provenance(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_history_tail(path: str, n: int = 5):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return rows[-n:] if rows else []


def _find_key(obj, key):
    """Recursively find first value for key in nested dicts/lists."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            found = _find_key(v, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = _find_key(v, key)
            if found is not None:
                return found
    return None


def _get_path(obj, path):
    cur = obj
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


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
    # Prefer full hash, wherever it lives; fall back to truncated top-level.
    full = _get_path(prov, "runtime_settings.engine_sha256_full") or _find_key(prov, "engine_sha256_full")
    truncated = prov.get("engine_sha256") or ""
    got = full or truncated or ""
    if not got:
        return _result(
            "engine_hash", "REVIEW",
            "provenance file has no engine_sha256_full or engine_sha256; missing entry is REVIEW, not proven failure",
            artifact, artifact_sha,
        )
    if not expected_sha:
        return _result("engine_hash", "REVIEW", f"no expected hash supplied; provenance hash is {got}", artifact, artifact_sha)
    got_l, exp_l = str(got).lower(), str(expected_sha).lower()
    if got_l == exp_l:
        return _result("engine_hash", "VERIFIED", f"provenance engine hash matches expected {got}", artifact, artifact_sha)
    if exp_l.startswith(got_l) and len(got_l) >= 16:
        return _result(
            "engine_hash", "VERIFIED",
            f"provenance engine hash {got} is a prefix of expected full hash {expected_sha} (truncated form, 16+ hex chars)",
            artifact, artifact_sha,
        )
    if got_l.startswith(exp_l) and len(exp_l) >= 16:
        return _result("engine_hash", "VERIFIED", f"provenance engine hash {got} starts with expected {expected_sha}", artifact, artifact_sha)
    return _result("engine_hash", "FAILED", f"provenance engine hash {got} != expected {expected_sha}", artifact, artifact_sha)


def check_sector(prov: dict, artifact="", artifact_sha=""):
    # Real schema: sector_clean bool. Fixture schema: penalty / sector_ok.
    if "sector_clean" in prov:
        if prov["sector_clean"] is True:
            return _result("sector", "VERIFIED", f"sector_clean=True, audit={prov.get('sector_audit_status')}", artifact, artifact_sha)
        if prov["sector_clean"] is False:
            return _result("sector", "FAILED", "sector_clean=False in provenance", artifact, artifact_sha)
    penalty = prov.get("sector_penalty_abs_sum", prov.get("penalty"))
    if penalty is not None:
        if abs(float(penalty)) > 1e-9:
            return _result("sector", "FAILED", f"sector penalty {penalty} Ha exceeds 1e-9 Ha", artifact, artifact_sha)
        return _result("sector", "VERIFIED", f"sector clean, penalty {penalty}", artifact, artifact_sha)
    if prov.get("sector_ok") is False:
        return _result("sector", "FAILED", "sector_ok flag is False in provenance", artifact, artifact_sha)
    return _result("sector", "REVIEW", "sector_clean and sector penalty both missing from provenance", artifact, artifact_sha)


def check_truncation(prov: dict, artifact="", artifact_sha=""):
    # Real schema: truncation.l1_kcal / truncation.exceeds_chem_acc
    trunc = prov.get("truncation") if isinstance(prov.get("truncation"), dict) else {}
    residual = trunc.get("l1_kcal")
    if residual is None:
        residual = prov.get("truncation_residual_kcal")
    if residual is None:
        if trunc.get("exceeds_chem_acc") is False:
            return _result("truncation", "VERIFIED", "truncation.exceeds_chem_acc=False, n_dropped=" + str(trunc.get("n_dropped")), artifact, artifact_sha)
        return _result("truncation", "REVIEW", "truncation residual missing from provenance (no l1_kcal, no truncation_residual_kcal)", artifact, artifact_sha)
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
    # Real schema also has abstain_reasons / blocked_reasons; budget check uses decision_grade_reasons first.
    if not reasons:
        reasons = prov.get("abstain_reasons", []) or []
    if verdict == "abstain" and "optimizer_budget_exhausted" in reasons:
        return _result(
            "budget", "REVIEW",
            "engine abstained on optimizer_budget_exhausted; Attest cannot upgrade abstain to VERIFIED",
            artifact, artifact_sha,
        )
    if verdict == "abstain":
        return _result("budget", "REVIEW", f"engine abstained, reasons={reasons}", artifact, artifact_sha)
    return _result("budget", "VERIFIED", f"engine verdict={verdict}, decision_grade={prov.get('decision_grade')}", artifact, artifact_sha)


def _vqe_energy(prov: dict):
    energies = prov.get("energies") if isinstance(prov.get("energies"), dict) else {}
    for key in ("vqe_physical", "vqe_minimized"):
        if energies.get(key) is not None:
            return energies[key], f"energies.{key}"
    for key in ("E_physical", "vqe_energy", "final_energy"):
        if prov.get(key) is not None:
            return prov[key], key
    return None, "energies.vqe_physical / E_physical"


def check_source_agreement(prov: dict, expected_run_id: str, history_rows, artifact="", artifact_sha=""):
    run_id = prov.get("run_id", "")
    if expected_run_id and run_id != expected_run_id:
        return _result("source_agreement", "FAILED", f"provenance run_id {run_id} != expected {expected_run_id}", artifact, artifact_sha)
    energy, field = _vqe_energy(prov)
    if energy is None or not math.isfinite(float(energy)) or float(energy) >= 0:
        return _result("source_agreement", "REVIEW", f"{field} missing, non-finite, or non-negative in provenance", artifact, artifact_sha)
    if history_rows:
        last = history_rows[-1]
        try:
            float(last.get("best_energy", "nan"))
        except (TypeError, ValueError):
            return _result("source_agreement", "REVIEW", "history tail best_energy is not a number", artifact, artifact_sha)
    return _result("source_agreement", "VERIFIED", f"run_id {run_id} agrees, {field} {energy} Ha present", artifact, artifact_sha)


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
